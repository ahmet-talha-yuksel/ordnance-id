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
        max_edge_px: int = 768,
    ) -> None:
        self._gateway = gateway
        self.prompt_path = prompt_path
        self.prompt_version = prompt_path.stem
        self.max_edge_px = max_edge_px

    def _optimize_image(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Downscale oversized images without ever upscaling smaller crops."""

        with Image.open(BytesIO(image_bytes)) as image:
            image_format = (image.format or "JPEG").lower()
            if max(image.size) <= self.max_edge_px:
                return image_bytes, image_format
            resized = image.copy()
            resized.thumbnail((self.max_edge_px, self.max_edge_px), Image.Resampling.LANCZOS)
            if resized.mode not in {"L", "RGB"}:
                resized = resized.convert("RGB")
            output = BytesIO()
            save_format = "JPEG" if image_format in {"jpg", "jpeg"} else image_format.upper()
            resized.save(output, format=save_format, quality=90)
            return output.getvalue(), image_format

    async def observe(
        self, image_bytes: bytes, scale_ref: ScaleReference | None = None
    ) -> OrdnanceObservation:
        """Return only schema-valid observations, retaining unknowns instead of guessing."""

        scale = scale_ref or ScaleReference()
        optimized_bytes, image_format = self._optimize_image(image_bytes)
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
                    "data": base64.b64encode(optimized_bytes).decode("ascii"),
                    "media_type": media_type,
                }
            ],
        )
        if scale.reference_type == "none" or scale.pixels_per_mm is None:
            observation.estimated_length_cm = None
            has_length_reason = any(
                item.startswith("estimated_length_cm:")
                for item in observation.unclear_features
            )
            if not has_length_reason:
                observation.unclear_features.append(
                    "estimated_length_cm: no manual scale reference"
                )
        return observation

    def system_prompt(self) -> str:
        """Load the versioned observation policy verbatim."""

        return self.prompt_path.read_text(encoding="utf-8")
