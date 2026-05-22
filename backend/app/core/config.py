from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "PresentIQ"
    environment: str = "development"

    # Infrastructure
    database_url: str
    redis_url: str

    # Security
    secret_key: str
    access_token_expire_minutes: int = 60 * 24 * 7

    # API
    api_v1_prefix: str = "/api/v1"

    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # File Uploads
    uploads_dir: str = "uploads"
    max_upload_size_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()