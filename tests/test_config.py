import pytest
from pydantic import SecretStr, ValidationError

from ordnance_id.config import Settings

REQUIRED = {
    "VISION_MODEL": "vision-test",
    "TEXT_MODEL": "text-test",
    "FAST_MODEL": "fast-test",
    "GEMINI_VISION_MODEL": "gemini-vision-test",
    "GEMINI_TEXT_MODEL": "gemini-text-test",
    "DATABASE_URL": "postgresql://localhost/test",
    "QDRANT_URL": "http://localhost:6333",
}


def test_settings_load_values_and_keep_keys_secret() -> None:
    settings = Settings(
        **REQUIRED,
        ANTHROPIC_API_KEY="top-secret",
        CONFIDENCE_THRESHOLD=0.8,
        _env_file=None,
    )

    assert isinstance(settings.ANTHROPIC_API_KEY, SecretStr)
    assert settings.ANTHROPIC_API_KEY.get_secret_value() == "top-secret"
    assert "top-secret" not in repr(settings)
    assert settings.CONFIDENCE_THRESHOLD == 0.8
    assert settings.KEEP_EXIF_GPS is False


def test_settings_reject_missing_required_values() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
