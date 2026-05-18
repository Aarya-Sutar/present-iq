from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "PresentIQ"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://presentiq:presentiq@db:5432/presentiq"
    redis_url: str = "redis://redis:6379/0"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24 * 7

    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()