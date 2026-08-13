"""Define durable records and descriptive summaries for VLM observation runs."""

from collections import Counter
from pathlib import Path

from PIL import Image
from pydantic import BaseModel, Field

from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.size_buckets import size_bucket
from ordnance_id.gateway.metrics import CallMetrics
from ordnance_id.vision.schema import OrdnanceObservation


class ObservationRecord(BaseModel):
    """Record one eval sample's observation outcome and operational telemetry."""

    sample_id: str
    observation: OrdnanceObservation | None = None
    duration_ms: float = Field(ge=0)
    metrics: CallMetrics
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    error: str | None = None


def write_observation_report(
    records: list[ObservationRecord],
    eval_path: Path,
    output: Path,
    image_dir: Path = Path("data/eval_images"),
) -> None:
    """Summarize completeness and consistency without claiming identification accuracy."""

    eval_set = load_eval_set(eval_path)
    truth = {sample.id: sample.ground_truth for sample in eval_set.samples}
    buckets: dict[str, str] = {}
    for sample in eval_set.samples:
        with Image.open(image_dir / sample.filename) as image:
            buckets[sample.id] = size_bucket(min(image.size))
    successful = [
        (record, record.observation) for record in records if record.observation is not None
    ]
    nullable_fields = [
        "fins_or_tail_visible",
        "fuze_visible",
        "driving_band_visible",
        "markings_or_stencil_text",
        "embedded_in_ground",
        "estimated_length_cm",
        "length_to_width_ratio",
        "looks_manufactured",
    ]
    lines = [
        "# Observation Report v1",
        "",
        "> This report measures schema completeness and operational behavior, not identification "
        "accuracy.",
        "",
        f"- Records: {len(records)}",
        f"- Successful observations: {len(successful)}",
        f"- Errors: {sum(record.error is not None for record in records)}",
        f"- Cache hits: {sum(record.metrics.cache_hit for record in records)}",
        "",
        "## Nullable field completion",
        "",
        "| Field | None count | None rate |",
        "|---|---:|---:|",
    ]
    for field_name in nullable_fields:
        none_count = sum(
            getattr(observation, field_name) is None
            for _record, observation in successful
        )
        rate = none_count / len(successful) * 100 if successful else 0.0
        lines.append(f"| {field_name} | {none_count} | {rate:.1f}% |")
    unclear = Counter(
        feature for _record, observation in successful for feature in observation.unclear_features
    )
    lines.extend(["", "## Most frequent unclear features", ""])
    lines.extend(f"- {feature}: {count}" for feature, count in unclear.most_common(10))
    poor_quality = sum(
        not observation.image_quality_sufficient for _record, observation in successful
    )
    negatives = [
        (record, observation)
        for record, observation in successful
        if truth.get(record.sample_id) is not None
        and not truth[record.sample_id].is_ordnance
    ]
    manufactured = Counter(observation.looks_manufactured for _record, observation in negatives)
    lines.extend(
        [
            "",
            "## Results by size bucket",
            "",
            "| Bucket | Records | Successful | Quality insufficient |",
            "|---|---:|---:|---:|",
        ]
    )
    for bucket in ("small", "medium", "large"):
        bucket_records = [record for record in records if buckets.get(record.sample_id) == bucket]
        bucket_success = [record for record in bucket_records if record.observation is not None]
        bucket_poor = sum(
            not record.observation.image_quality_sufficient
            for record in bucket_success
            if record.observation is not None
        )
        lines.append(
            f"| {bucket} | {len(bucket_records)} | {len(bucket_success)} | {bucket_poor} |"
        )
    average_duration = (
        sum(record.duration_ms for record in records) / len(records) if records else 0.0
    )
    lines.extend(
        [
            "",
            "## Operational summary",
            "",
            f"- Image quality insufficient: {poor_quality}/{len(successful)}",
            f"- Negative looks_manufactured distribution: `{dict(manufactured)}`",
            f"- Average duration: {average_duration:.1f} ms",
            f"- Total input tokens: {sum(record.metrics.input_tokens for record in records)}",
            f"- Total output tokens: {sum(record.metrics.output_tokens for record in records)}",
            f"- Total retries: {sum(record.metrics.retries for record in records)}",
            f"- Total estimated cost: ${sum(record.estimated_cost_usd for record in records):.4f}",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
