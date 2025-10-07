from __future__ import annotations
from typing import Any, Dict, Iterable, List, Tuple, Protocol, Type
from pydantic import BaseModel

class AIClient(Protocol):
    def complete_text(
        self,
        messages: List[Dict[str, Any]],
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> Tuple[str, Dict[str, Any]]:
        ...

    def complete_pydantic(
        self,
        messages: List[Dict[str, Any]],
        *,
        response_model: Type[BaseModel],  # Pydantic model class
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> Tuple[BaseModel, Dict[str, Any]]:
        ...

    def embed(self, text: str) -> List[float]: ...
    def embed_batch(self, texts: Iterable[str]) -> List[List[float]]: ...