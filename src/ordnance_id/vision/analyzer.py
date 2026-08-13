"""Request schema-constrained physical observations through the model gateway."""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from ordnance_id.gateway.base import LLMProvider, Message
from ordnance_id.ingest.scale import ScaleReference
from ordnance_id.vision.schema import OrdnanceObservation


class VisionAnalyzer:
    """Observe visible features while keeping identification outside this layer."""

    def __init__(
        self,
        gateway: LLMProvider,
        *,
        prompt_path: Path = Path("prompts/observe_v1.md"),
    ) -> None:
        self._gateway = gateway
        self.prompt_path = prompt_path
        self.prompt_version = prompt_path.stem

    async def observe(
        self, image_bytes: bytes, scale_ref: ScaleReference | None = None
    ) -> OrdnanceObservation:
        """Return only schema-valid observations, retaining unknowns instead of guessing."""

        scale = scale_ref or ScaleReference()
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = (image.format or "JPEG").lower()
        media_type = "image/jpeg" if image_format in {"jpg", "jpeg"} else f"image/{image_format}"
        messages: list[Message] = [
            {
                "role": "user",
                "content": (
                    f"{self.system_prompt()}\n\nObserve the attached crop. Manual scale reference: "
                    f"{scale.model_dump_json()}. Return only visible physical properties."
                ),
            }
        ]
        observation = await self._gateway.complete_structured(
            messages,
            OrdnanceObservation,
            images=[
                {
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                    "media_type": media_type,
                }
            ],
        )
        if scale.reference_type == "none" or scale.pixels_per_mm is None:
            observation.estimated_length_cm = None
            if "estimated_length_cm" not in observation.unclear_features:
                observation.unclear_features.append("estimated_length_cm")
        return observation

    def system_prompt(self) -> str:
        """Load the versioned observation policy verbatim."""

        return self.prompt_path.read_text(encoding="utf-8")
