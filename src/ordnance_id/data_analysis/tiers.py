"""Load family-level evidence tiers derived after source-class mapping."""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, Field, model_validator

from ordnance_id.evals.schema import OrdnanceFamily

ClassTier = Literal["reportable", "limited", "insufficient"]


class TierThresholds(BaseModel):
    """Define configurable instance thresholds for family-level tiers."""

    reportable_min_instances: int = Field(gt=0)
    limited_min_instances: int = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.reportable_min_instances <= self.limited_min_instances:
            raise ValueError("reportable threshold must exceed limited threshold")
        return self

    def tier_for_count(self, count: int) -> ClassTier:
        """Classify a mapped family total using YAML-defined thresholds."""

        if count >= self.reportable_min_instances:
            return "reportable"
        if count >= self.limited_min_instances:
            return "limited"
        return "insufficient"


class FamilyTier(BaseModel):
    """Record one post-mapping family total and its evidence tier."""

    tier: ClassTier
    mapped_instance_count: int = Field(ge=0)


class ClassTiers(BaseModel):
    """Assign exactly one validated tier to each mapped ordnance family."""

    thresholds: TierThresholds
    families: dict[OrdnanceFamily, FamilyTier]

    @model_validator(mode="after")
    def tiers_match_thresholds(self) -> Self:
        for family, value in self.families.items():
            computed = self.thresholds.tier_for_count(value.mapped_instance_count)
            if value.tier != computed:
                raise ValueError(
                    f"Family {family} is {value.tier}, but mapped count requires {computed}"
                )
        return self

    def mapping(self) -> dict[OrdnanceFamily, ClassTier]:
        """Return the single tier assigned to each post-mapping family."""

        return {family: value.tier for family, value in self.families.items()}


def load_class_tiers(path: Path) -> ClassTiers:
    """Load a validated family-tier catalog from YAML."""

    return ClassTiers.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

