from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "ClaimShield AI"
    secret_key: str = "development-only-change-me-claimshield"
    access_token_minutes: int = 480
    database_url: str = "sqlite:///./claimshield.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    cors_origins: str = "http://localhost:3000"

    storage_backend: str = "local"
    local_storage_path: str = "./storage"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "claimshield"
    s3_secret_key: str = "claimshield_dev"
    s3_bucket: str = "claimshield-media"
    s3_region: str = "us-east-1"

    max_upload_bytes: int = 15 * 1024 * 1024
    min_image_width: int = 640
    min_image_height: int = 480

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def local_storage_directory(self) -> Path:
        path = Path(self.local_storage_path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

