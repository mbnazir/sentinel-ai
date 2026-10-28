from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sentinel AI"
    app_version: str = "0.13.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True
    log_level: str = "INFO"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "sentinel_ai"
    postgres_user: str = "sentinel"
    postgres_password: str = Field(default="sentinel_dev_only", repr=False)

    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = Field(default="change-me-development-only-32-bytes-minimum", repr=False)
    jwt_algorithm: str = "HS256"
    jwt_access_minutes: int = 30
    jwt_audience: str = "sentinel-ai-api"
    cors_origins: str = "http://localhost:5173"
    security_headers_enabled: bool = True

    quartz_api_bearer_token: str | None = Field(default=None, repr=False)
    ai_provider: str = "disabled"
    ai_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = Field(default=None, repr=False)
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_base_url: str = "https://api.openai.com/v1"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
