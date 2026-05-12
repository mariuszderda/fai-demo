from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-sonnet-4-5")
    otx_api_key: str | None = Field(default=None)
    use_stub_llm: bool = Field(default=False)
    approval_ttl_seconds: int = Field(default=30)
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:8080")

    @property
    def cors_origins_list(self) -> list[str]:
        """Return the configured CORS origins as a cleaned list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()

