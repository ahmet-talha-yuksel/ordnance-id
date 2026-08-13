import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from ordnance_id.gateway.base import ImageInput, Message, SchemaT
from ordnance_id.gateway.metrics import CallMetrics
from ordnance_id.vision.analyzer import VisionAnalyzer
from ordnance_id.vision.schema import OrdnanceObservation
from tests.ingest_helpers import image_bytes


class FakeGateway:
    received_size: tuple[int, int] | None = None

    @property
    def last_metrics(self) -> CallMetrics | None:
        return None

    async def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        return "unused"

    async def complete_structured(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        *,
        images: list[ImageInput] | None = None,
    ) -> SchemaT:
        assert images and images[0]["media_type"] == "image/jpeg"
        with Image.open(BytesIO(base64.b64decode(images[0]["data"]))) as image:
            self.received_size = image.size
        return schema.model_validate(
            {
                "body_shape": "irregular",
                "fins_or_tail_visible": None,
                "fuze_visible": None,
                "driving_band_visible": None,
                "markings_visible": None,
                "markings_text": None,
                "color_bands": [],
                "surface_condition": "unclear",
                "embedded_in_ground": None,
                "estimated_length_cm": 12,
                "length_to_width_ratio": None,
                "looks_manufactured": None,
                "image_quality_sufficient": True,
                "unclear_features": [],
                "observation_notes": "Visible properties are limited.",
            }
        )


async def test_analyzer_clears_length_without_scale(tmp_path: Path) -> None:
    prompt = tmp_path / "observe_v1.md"
    prompt.write_text("Observe only visible features.")
    analyzer = VisionAnalyzer(FakeGateway(), prompt_path=prompt)
    observation = await analyzer.observe(image_bytes())
    assert isinstance(observation, OrdnanceObservation)
    assert observation.estimated_length_cm is None
    assert any(item.startswith("estimated_length_cm:") for item in observation.unclear_features)


async def test_analyzer_downscales_only_oversized_images(tmp_path: Path) -> None:
    prompt = tmp_path / "observe_v1.md"
    prompt.write_text("Observe only visible features.")
    gateway = FakeGateway()
    analyzer = VisionAnalyzer(gateway, prompt_path=prompt, max_edge_px=768)

    await analyzer.observe(image_bytes(width=1200, height=600))
    assert gateway.received_size == (768, 384)

    original = image_bytes(width=400, height=200)
    await analyzer.observe(original)
    assert gateway.received_size == (400, 200)
