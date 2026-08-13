from pathlib import Path

from ordnance_id.gateway.base import ImageInput, Message, SchemaT
from ordnance_id.gateway.metrics import CallMetrics
from ordnance_id.vision.analyzer import VisionAnalyzer
from ordnance_id.vision.schema import OrdnanceObservation
from tests.ingest_helpers import image_bytes


class FakeGateway:
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
        return schema.model_validate(
            {
                "body_shape": "irregular",
                "fins_or_tail_visible": None,
                "fuze_visible": None,
                "driving_band_visible": None,
                "markings_or_stencil_text": None,
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
    assert "estimated_length_cm" in observation.unclear_features
