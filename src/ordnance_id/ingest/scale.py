"""Represent manual scale references without inventing physical dimensions."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class ScaleReference(BaseModel):
    """Describe a manually supplied reference; automatic detection is a Phase 2+ TODO."""

    reference_type: Literal["ruler", "coin", "hand", "none"] = "none"
    known_dimension_mm: float | None = Field(default=None, gt=0)
    pixels_per_mm: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        """Prevent numeric scale claims when no reference was supplied."""

        if self.reference_type == "none" and (
            self.known_dimension_mm is not None or self.pixels_per_mm is not None
        ):
            raise ValueError("reference_type=none cannot include scale measurements")
        return self


class DimensionEstimate(BaseModel):
    """Express dimensions as uncertainty intervals rather than exact claims."""

    width_mm_min: float
    width_mm_max: float
    height_mm_min: float
    height_mm_max: float


def estimate_dimensions(
    bbox_pixels: tuple[float, float], scale: ScaleReference
) -> DimensionEstimate | None:
    """Convert pixel dimensions with ±5% uncertainty, or return None without scale."""

    if scale.reference_type == "none" or scale.pixels_per_mm is None:
        return None
    width, height = bbox_pixels
    if width <= 0 or height <= 0:
        raise ValueError("bounding-box dimensions must be positive")
    width_mm = width / scale.pixels_per_mm
    height_mm = height / scale.pixels_per_mm
    return DimensionEstimate(
        width_mm_min=width_mm * 0.95,
        width_mm_max=width_mm * 1.05,
        height_mm_min=height_mm * 0.95,
        height_mm_max=height_mm * 1.05,
    )

