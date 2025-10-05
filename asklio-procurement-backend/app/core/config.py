from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    APP_NAME: str = "askLio Procurement API"
    API_PREFIX: str = "/api"

    # --- Postgres ---
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "asklio"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: str | None = None

    # --- Weaviate ---
    WEAVIATE_HTTP_HOST: str = "weaviate"
    WEAVIATE_HTTP_PORT: int = 8080
    WEAVIATE_GRPC_HOST: str = "weaviate"
    WEAVIATE_GRPC_PORT: int = 50051
    WEAVIATE_HTTP_SECURE: bool = False
    WEAVIATE_GRPC_SECURE: bool = False

    # --- Auth ---
    SECRET_KEY: str = "dev-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    OPENAI_API_KEY: str | None = None
    SHARED_CLIENT_API_KEY: str | None = None

    # --- Environment / boot flags ---
    ENV: Literal["local", "dev", "prod"] = "local"
    SEED_ON_START: bool | None = None  # if None, infer from ENV

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_uri(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def should_seed(self) -> bool:
        # Default: seed only in local unless explicitly overridden
        if self.SEED_ON_START is not None:
            return bool(self.SEED_ON_START)
        return self.ENV == "local"

settings = Settings()