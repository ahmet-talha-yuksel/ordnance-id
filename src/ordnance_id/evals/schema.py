"""Validate evaluation samples, provenance, and internally consistent labels."""

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

OrdnanceFamily = Literal[
    "mortar",
    "projectile",
    "grenade",
    "aviation_bomb",
    "rocket",
    "landmine",
    "submunition",
    "cartridge",
    "fuze",
    "not_ordnance",
    "indeterminate",
]


class GroundTruth(BaseModel):
    """Describe a family-level reference label and its evidentiary confidence."""

    is_ordnance: bool
    family: OrdnanceFamily
    confidence_of_label: Literal["high", "medium", "low"]
    label_rationale: str | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        """Reject contradictory or insufficiently explained labels."""

        if self.is_ordnance and self.family == "not_ordnance":
            raise ValueError("ordnance samples cannot have family=not_ordnance")
        if not self.is_ordnance and self.family not in {"not_ordnance", "indeterminate"}:
            raise ValueError("non-ordnance samples must be not_ordnance or indeterminate")
        if self.confidence_of_label in {"medium", "low"} and not self.label_rationale:
            raise ValueError("medium/low confidence labels require label_rationale")
        if self.family == "indeterminate" and self.confidence_of_label == "high":
            raise ValueError("indeterminate labels cannot have high confidence")
        return self


class SampleAttributes(BaseModel):
    """Record observable evaluation conditions without inferring an identity."""

    partially_buried: bool = False
    corroded: bool = False
    fragmented: bool = False
    scale_reference_present: bool = False
    poor_lighting: bool = False
    distant_or_small_in_frame: bool = False


class EvalSample(BaseModel):
    """Describe one licensed evaluation image and its reference label."""

    id: str = Field(pattern=r"^eval_\d{3,}$")
    filename: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    license: str
    attribution: str = Field(min_length=1)
    retrieved: date
    ground_truth: GroundTruth
    attributes: SampleAttributes = Field(default_factory=SampleAttributes)
    notes: str | None = None

    @field_validator("license")
    @classmethod
    def validate_license(cls, value: str) -> str:
        """Exclude samples whose reuse terms are empty or unknown."""

        normalized = value.strip()
        if normalized.lower() in {"", "unknown", "n/a"}:
            raise ValueError("a verified license is required")
        return normalized


class EvalSet(BaseModel):
    """Contain a versioned set with unique IDs and image paths."""

    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    samples: list[EvalSample]

    @model_validator(mode="after")
    def validate_uniqueness(self) -> Self:
        """Reject duplicate IDs or filenames."""

        ids = [sample.id for sample in self.samples]
        filenames = [sample.filename for sample in self.samples]
        if len(ids) != len(set(ids)):
            raise ValueError("evaluation sample IDs must be unique")
        if len(filenames) != len(set(filenames)):
            raise ValueError("evaluation filenames must be unique")
        return self
