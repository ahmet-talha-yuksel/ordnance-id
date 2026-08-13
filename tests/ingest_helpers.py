from io import BytesIO

import numpy as np
from PIL import Image

from ordnance_id.config import Settings


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "VISION_MODEL": "vision-test",
        "TEXT_MODEL": "text-test",
        "FAST_MODEL": "fast-test",
        "GEMINI_VISION_MODEL": "gemini-vision-test",
        "GEMINI_TEXT_MODEL": "gemini-text-test",
        "DATABASE_URL": "postgresql://localhost/test",
        "QDRANT_URL": "http://localhost:6333",
        "LLM_PROVIDER": "ollama",
        "MIN_IMAGE_QUALITY_SCORE": 0.5,
        "MIN_BLUR_SCORE": 0.2,
        "MIN_BRIGHTNESS_SCORE": 0.2,
        "MIN_IMAGE_WIDTH": 640,
        "MIN_IMAGE_HEIGHT": 480,
        "MAX_UPLOAD_BYTES": 2_000_000,
        "_env_file": None,
    }
    values.update(overrides)
    return Settings.model_validate(values)


def image_bytes(
    kind: str = "noise", width: int = 800, height: int = 600, image_format: str = "JPEG"
) -> bytes:
    rng = np.random.default_rng(42)
    if kind == "noise":
        pixels = rng.integers(40, 215, size=(height, width, 3), dtype=np.uint8)
    elif kind == "dark":
        pixels = np.zeros((height, width, 3), dtype=np.uint8)
    elif kind == "blurred":
        pixels = np.full((height, width, 3), 128, dtype=np.uint8)
    else:
        raise ValueError(kind)
    output = BytesIO()
    Image.fromarray(pixels).save(output, format=image_format)
    return output.getvalue()
