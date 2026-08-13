"""Load validated application configuration without exposing secrets."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LLM_PROVIDER: Literal["anthropic", "openai", "ollama"] = "anthropic"
    ANTHROPIC_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    VISION_MODEL: str
    TEXT_MODEL: str
    FAST_MODEL: str
    DATABASE_URL: str
    QDRANT_URL: str
    CONFIDENCE_THRESHOLD: float = 0.7
    MIN_IMAGE_QUALITY_SCORE: float = 0.5
    KEEP_EXIF_GPS: bool = False
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""

    return Settings()  # type: ignore[call-arg]

