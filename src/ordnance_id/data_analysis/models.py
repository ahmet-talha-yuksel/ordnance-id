"""Define normalized dataset-analysis results independent of annotation format."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class SplitReport(BaseModel):
    """Summarize one normalized dataset split."""

    name: str
    image_count: int = 0
    instance_count: int = 0
    class_counts: dict[str, int] = Field(default_factory=dict)
    resolutions: list[tuple[int, int]] = Field(default_factory=list)
    bbox_area_fractions: list[float] = Field(default_factory=list)


class RepositoryReport(BaseModel):
    """Summarize one independently annotated repository."""

    name: str
    root: Path
    format: Literal["coco", "yolo"]
    purpose: Literal["binary_classification", "multiclass_detection", "instance_segmentation"]
    splits: list[SplitReport]
    warnings: list[str] = Field(default_factory=list)


class DatasetReport(BaseModel):
    """Contain every repository discovered below a dataset root."""

    source_root: Path
    repositories: list[RepositoryReport]

