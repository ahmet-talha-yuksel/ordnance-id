"""Select a deterministic, tier-stratified observation pilot."""

import random
from collections import defaultdict
from pathlib import Path

from PIL import Image
from pydantic import BaseModel

from ordnance_id.data_analysis.tiers import ClassTier
from ordnance_id.evals.provenance import source_class_from_notes
from ordnance_id.evals.schema import EvalSample, OrdnanceFamily
from ordnance_id.evals.size_buckets import SizeBucket, size_bucket


class PilotSample(BaseModel):
    """Pair a selected sample with derived tier and image-size metadata."""

    sample: EvalSample
    tier: ClassTier | None
    size_bucket: SizeBucket


def _metadata(
    sample: EvalSample, image_dir: Path, tiers: dict[OrdnanceFamily, ClassTier]
) -> PilotSample:
    with Image.open(image_dir / sample.filename) as image:
        bucket = size_bucket(min(image.size))
    source_class = source_class_from_notes(sample.notes)
    tier = tiers[sample.ground_truth.family] if source_class is not None else None
    return PilotSample(sample=sample, tier=tier, size_bucket=bucket)


def select_pilot(
    samples: list[EvalSample],
    image_dir: Path,
    tiers: dict[OrdnanceFamily, ClassTier],
    *,
    seed: int = 0,
) -> list[PilotSample]:
    """Select 4 reportable, 2 limited, 1 insufficient, and 3 negative samples."""

    rng = random.Random(seed)
    enriched = [_metadata(sample, image_dir, tiers) for sample in samples]
    positives: defaultdict[ClassTier, list[PilotSample]] = defaultdict(list)
    negatives: list[PilotSample] = []
    for item in enriched:
        if item.sample.ground_truth.is_ordnance:
            assert item.tier is not None
            positives[item.tier].append(item)
        else:
            negatives.append(item)
    selected: list[PilotSample] = []
    reportable_by_family: defaultdict[OrdnanceFamily, list[PilotSample]] = defaultdict(list)
    for item in positives["reportable"]:
        reportable_by_family[item.sample.ground_truth.family].append(item)
    families = sorted(reportable_by_family)
    rng.shuffle(families)
    for family in families[:4]:
        values = reportable_by_family[family]
        selected.append(values[rng.randrange(len(values))])
    tier_targets: tuple[tuple[ClassTier, int], ...] = (("limited", 2), ("insufficient", 1))
    for tier, count in tier_targets:
        values = positives[tier][:]
        rng.shuffle(values)
        selected.extend(values[:count])
    rng.shuffle(negatives)
    selected.extend(negatives[:3])
    if len(selected) != 10:
        raise ValueError("Eval set cannot satisfy the requested 10-sample pilot strata")
    if not any(item.size_bucket == "small" for item in selected):
        small_candidates = [item for item in enriched if item.size_bucket == "small"]
        if not small_candidates:
            raise ValueError("Eval set has no small sample for the pilot")
        replacement = small_candidates[rng.randrange(len(small_candidates))]
        replace_at = next(
            (
                index
                for index, item in enumerate(selected)
                if item.tier == replacement.tier
                and item.sample.ground_truth.is_ordnance
                == replacement.sample.ground_truth.is_ordnance
            ),
            None,
        )
        if replace_at is None:
            raise ValueError("Cannot preserve pilot strata while adding a small sample")
        selected[replace_at] = replacement
    return selected
