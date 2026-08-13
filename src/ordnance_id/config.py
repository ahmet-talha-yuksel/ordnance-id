"""Load validated application configuration without exposing secrets."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LLM_PROVIDER: Literal["anthropic", "openai", "ollama", "gemini"] = "anthropic"
    ANTHROPIC_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None
    GEMINI_API_KEY: SecretStr | None = None
    GEMINI_VISION_MODEL: str
    GEMINI_TEXT_MODEL: str
    GEMINI_RPM: int = Field(default=10, gt=0)
    GEMINI_RPD: int = Field(default=250, gt=0)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    VISION_MODEL: str
    VISION_MAX_EDGE_PX: int = Field(default=768, gt=0)
    TEXT_MODEL: str
    FAST_MODEL: str
    DATABASE_URL: str
    QDRANT_URL: str
    CONFIDENCE_THRESHOLD: float = Field(default=0.7, ge=0.0, le=1.0)
    MIN_IMAGE_QUALITY_SCORE: float = Field(default=0.5, ge=0.0, le=1.0)
    MIN_BLUR_SCORE: float = Field(default=0.25, ge=0.0, le=1.0)
    BLUR_VARIANCE_REFERENCE: float = Field(default=500.0, gt=0.0)
    MIN_BRIGHTNESS_SCORE: float = Field(default=0.25, ge=0.0, le=1.0)
    MIN_IMAGE_WIDTH: int = Field(default=640, gt=0)
    MIN_IMAGE_HEIGHT: int = Field(default=480, gt=0)
    MAX_UPLOAD_BYTES: int = Field(default=10 * 1024 * 1024, gt=0)
    KEEP_EXIF_GPS: bool = False
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""

    return Settings()  # type: ignore[call-arg]
