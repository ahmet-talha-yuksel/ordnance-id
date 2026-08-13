"""Define visual observations without identification, danger, or advice fields."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrdnanceObservation(BaseModel):
    """Contain only directly observable physical and image-quality attributes."""

    model_config = ConfigDict(extra="forbid")

    body_shape: Literal[
        "cylindrical",
        "conical",
        "ogive",
        "spherical",
        "boxy",
        "irregular",
        "fragmented",
        "unclear",
    ]
    fins_or_tail_visible: bool | None
    fuze_visible: bool | None
    driving_band_visible: bool | None
    markings_visible: bool | None
    markings_text: str | None
    color_bands: list[str] = Field(default_factory=list)
    surface_condition: Literal[
        "clean", "weathered", "corroded", "heavily_corroded", "unclear"
    ]
    embedded_in_ground: bool | None
    estimated_length_cm: float | None = Field(default=None, gt=0)
    length_to_width_ratio: float | None = Field(default=None, gt=0)
    looks_manufactured: bool | None
    image_quality_sufficient: bool
    unclear_features: list[str] = Field(default_factory=list)
    observation_notes: str

    @model_validator(mode="after")
    def record_nullable_uncertainty(self) -> Self:
        """Make every unknown nullable visual property explicitly traceable."""

        nullable = (
            "fins_or_tail_visible",
            "fuze_visible",
            "driving_band_visible",
            "markings_visible",
            "markings_text",
            "embedded_in_ground",
            "length_to_width_ratio",
            "looks_manufactured",
        )
        existing = set(self.unclear_features)
        for field_name in nullable:
            has_reason = any(item.startswith(f"{field_name}:") for item in existing)
            if getattr(self, field_name) is None and not has_reason:
                self.unclear_features.append(f"{field_name}: reason not provided by model")
        return self
