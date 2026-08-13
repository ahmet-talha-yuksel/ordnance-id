"""Load and validate explicit evidence tiers for source dataset classes."""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, model_validator

ClassTier = Literal["reportable", "limited", "insufficient"]


class ClassTiers(BaseModel):
    """Assign every source class to exactly one evidence tier."""

    reportable: list[str]
    limited: list[str]
    insufficient: list[str]

    @model_validator(mode="after")
    def unique_classes(self) -> Self:
        values = self.reportable + self.limited + self.insufficient
        if len(values) != len(set(values)):
            raise ValueError("Each source class must occur in exactly one tier")
        return self

    def mapping(self) -> dict[str, ClassTier]:
        return {
            **{name: "reportable" for name in self.reportable},
            **{name: "limited" for name in self.limited},
            **{name: "insufficient" for name in self.insufficient},
        }


def load_class_tiers(path: Path) -> ClassTiers:
    """Load a validated tier catalog from YAML."""

    return ClassTiers.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
