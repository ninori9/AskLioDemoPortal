from functools import lru_cache
import weaviate
from app.core.config import settings


@lru_cache(maxsize=1)
def get_client() -> weaviate.WeaviateClient:
    """
    Weaviate v4.8.1: use connect_to_local for docker-compose setups.
    """
    return weaviate.connect_to_local(
        host=settings.WEAVIATE_HTTP_HOST,
        port=settings.WEAVIATE_HTTP_PORT,
        grpc_port=settings.WEAVIATE_GRPC_PORT,
    )