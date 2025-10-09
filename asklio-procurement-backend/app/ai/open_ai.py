from __future__ import annotations
import logging
from typing import Any, Dict, Iterable, List, Tuple, Type
from pydantic import BaseModel
from openai import OpenAI

from app.ai.base import AIClient

logger = logging.getLogger(__name__)

class OpenAIClient(AIClient):
    def __init__(
        self,
        *,
        api_key: str,
        chat_model: str = "gpt-5-2025-08-07",
        embed_model: str = "text-embedding-3-large",
        default_temperature: float = 0.2,
        default_max_output_tokens: int = 800,
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.default_temperature = default_temperature
        self.default_max_output_tokens = default_max_output_tokens

    # ---------- PLAIN TEXT ----------
    def complete_text(
        self,
        messages: List[Dict[str, Any]],
        model: str | None = None,
    ) -> Tuple[str, Dict[str, Any]]:
        model_to_use = model or self.chat_model
        # Using Responses API for simple text
        resp = self.client.responses.create(
            model=model_to_use,
            input=messages,
            rreasoning=None if model else {"effort": "medium"},
        )
        text = getattr(resp, "output_text", "") or ""
        meta = {"id": getattr(resp, "id", None), "model": getattr(resp, "model", self.chat_model)}
        return text, meta

    # ---------- Pydantic structured output ----------
    def complete_pydantic(
        self,
        messages: List[Dict[str, Any]],
        *,
        response_model: Type[BaseModel],
        model: str | None = None,
    ) -> Tuple[BaseModel, Dict[str, Any]]:
        """
        Use the new responses.parse API with Pydantic (SDK >= 1.40).
        """
        model_to_use = model or self.chat_model
        response = self.client.responses.parse(
            model=model_to_use,
            input=messages,
            reasoning=None if model else {"effort": "medium"},
            text_format=response_model,
        )

        # handle refusals explicitly
        if getattr(response, "refusal", None):
            raise RuntimeError(f"Model refused: {response.refusal}")

        parsed = self._first_parsed_from_response(response)

        meta = {
            "id": response.id,
            "model": response.model,
            "usage": getattr(response, "usage", None),
        }

        logger.debug(
            f"[OpenAIClient] Parsed structured output from {response.model}: {parsed.model_dump()}"
        )

        return parsed, meta

    # ---------- Embeddings ----------
    def embed(self, text: str) -> List[float]:
        out = self.client.embeddings.create(model=self.embed_model, input=text)
        return out.data[0].embedding

    def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        texts_list = list(texts)
        if not texts_list:
            return []
        out = self.client.embeddings.create(model=self.embed_model, input=texts_list)
        return [row.embedding for row in out.data]

    def _t(self, t: float | None) -> float:
        return self.default_temperature if t is None else t

    def _m(self, m: int | None) -> int:
        return self.default_max_output_tokens if m is None else m
    
    def _first_parsed_from_response(self, response):
        """
        Works with current OpenAI responses.parse output:
        response.output[*].content[*].parsed holds the Pydantic object.
        """
        for msg in getattr(response, "output", []) or []:
            for chunk in getattr(msg, "content", []) or []:
                parsed = getattr(chunk, "parsed", None)
                if parsed is not None:
                    return parsed
        raise RuntimeError("Structured output missing: no content chunk contained `.parsed`.")