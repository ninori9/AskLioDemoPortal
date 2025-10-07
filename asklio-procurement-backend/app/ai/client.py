from functools import lru_cache
from app.core.config import settings
from app.ai.open_ai import OpenAIClient
from app.ai.base import AIClient

DEFAULT_GEN_MODEL = "gpt-4.1-2025-04-14"
DEFAULT_EMBED_MODEL = "text-embedding-3-large"

@lru_cache(maxsize=1)
def get_ai_client() -> AIClient:
    api_key = settings.OPENAI_API_KEY or ""
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAIClient(
        api_key=api_key,
        chat_model=DEFAULT_GEN_MODEL,
        embed_model=DEFAULT_EMBED_MODEL,
        default_temperature=0.2,
        default_max_output_tokens=800,
    )