"""Inspect pilot observations for policy violations, completeness, and useful contrasts."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import typer

from ordnance_id.evals.observations import ObservationRecord

PROHIBITED_PATTERNS = {
    "ordnance_type_or_model": re.compile(
        r"\b(mortar|grenade|projectile|rocket|rpg|landmine|land mine|sea mine|"
        r"aviation bomb|aerial bomb|cartridge|torpedo|shell|warhead|"
        r"mühimmat|havan|el bombası|roket|mayın)\b",
        re.IGNORECASE,
    ),
    "caliber_or_diameter_claim": re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:mm|millimet(?:er|re)|cm|inch|inches|inç)\b",
        re.IGNORECASE,
    ),
    "danger_or_risk": re.compile(
        r"\b(explosive|dangerous|hazardous|risk|detonat(?:e|ion)|unsafe|"
        r"patlayıcı|tehlikeli|riskli|patlama)\b",
        re.IGNORECASE,
    ),
    "safety_advice": re.compile(
        r"\b(do not approach|keep away|stay back|call (?:the )?(?:police|authorities)|"
        r"do not touch|yaklaşmayın|uzak durun|dokunmayın|yetkilileri arayın)\b",
        re.IGNORECASE,
    ),
}

NULLABLE_FIELDS = (
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_or_stencil_text",
    "embedded_in_ground",
    "estimated_length_cm",
    "length_to_width_ratio",
    "looks_manufactured",
)


def _strings(value: Any, path: str = "observation") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        return [
            item
            for key, nested in value.items()
            for item in _strings(nested, f"{path}.{key}")
        ]
    if isinstance(value, list):
        return [
            item
            for index, nested in enumerate(value)
            for item in _strings(nested, f"{path}[{index}]")
        ]
    return []


def inspect(records: list[ObservationRecord]) -> str:
    """Render the complete human-readable pilot inspection report."""

    violations: list[tuple[str, str, str, str]] = []
    successful = [record for record in records if record.observation is not None]
    for record in successful:
        assert record.observation is not None
        for field_name, text in _strings(record.observation.model_dump()):
            for rule, pattern in PROHIBITED_PATTERNS.items():
                if pattern.search(text):
                    violations.append((record.sample_id, field_name, rule, text))
    lines = [
        "# Gemini observation pilot inspection",
        "",
        "## 1. Rule violation scan",
        "",
        f"Violations: **{len(violations)}**",
        "",
    ]
    lines.extend(
        f"- `{sample_id}` · `{field}` · `{rule}`: “{text}”"
        for sample_id, field, rule, text in violations
    )
    if not violations:
        lines.append(
            "- No prohibited identification, caliber, danger, or safety-advice text found."
        )

    lines.extend(
        [
            "",
            "## 2. Nullable-field rates by size bucket",
            "",
            "| Bucket | Field | None | Total | None rate |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for bucket in ("small", "medium", "large"):
        bucket_records = [record for record in successful if record.size_bucket == bucket]
        for field_name in NULLABLE_FIELDS:
            none_count = sum(
                getattr(record.observation, field_name) is None
                for record in bucket_records
                if record.observation is not None
            )
            rate = none_count / len(bucket_records) if bucket_records else 0.0
            lines.append(
                f"| {bucket} | {field_name} | {none_count} | {len(bucket_records)} | {rate:.1%} |"
            )

    unclear = Counter(
        feature
        for record in successful
        if record.observation is not None
        for feature in record.observation.unclear_features
    )
    lines.extend(["", "## 3. Unclear features", ""])
    lines.extend(f"- `{feature}`: {count}" for feature, count in unclear.most_common())
    if not unclear:
        lines.append("- None.")

    lines.extend(["", "## 4. Positive versus negative distributions", ""])
    for field_name in ("looks_manufactured", "body_shape", "surface_condition"):
        distributions: defaultdict[str, Counter[object]] = defaultdict(Counter)
        for record in successful:
            assert record.observation is not None
            group = "negative" if record.family == "not_ordnance" else "positive"
            distributions[group][getattr(record.observation, field_name)] += 1
        lines.extend(
            [
                f"### {field_name}",
                "",
                f"- Positive: `{dict(distributions['positive'])}`",
                f"- Negative: `{dict(distributions['negative'])}`",
                "",
            ]
        )

    lines.extend(["## 5. Raw observations", ""])
    for record in records:
        lines.extend(
            [
                f"### {record.sample_id} · {record.family} · {record.size_bucket}",
                "",
                "```json",
                json.dumps(
                    record.observation.model_dump(mode="json") if record.observation else None,
                    ensure_ascii=False,
                    indent=2,
                ),
                "```",
                "",
            ]
        )

    average_duration = sum(record.duration_ms for record in records) / len(records)
    schema_error_count = sum(
        "ValidationError" in (record.error or "") for record in records
    )
    lines.extend(
        [
            "## 6. Operational metrics",
            "",
            f"- Records: {len(records)}",
            f"- Errors: {sum(record.error is not None for record in records)}",
            f"- Schema-validation errors: {schema_error_count}",
            f"- Retries: {sum(record.metrics.retries for record in records)}",
            f"- HTTP 429 responses: {sum(record.metrics.rate_limit_429s for record in records)}",
            f"- Cache hits: {sum(record.metrics.cache_hit for record in records)}",
            f"- Average duration: {average_duration:.1f} ms",
            f"- Input tokens: {sum(record.metrics.input_tokens for record in records)}",
            f"- Output tokens: {sum(record.metrics.output_tokens for record in records)}",
            f"- Total cost: ${sum(record.estimated_cost_usd for record in records):.4f}",
            "",
        ]
    )
    return "\n".join(lines)


def main(
    results: Path = Path(
        "evals/results/observations_v1_gemini_gemini-2.5-flash_pilot.jsonl"
    ),
    output: Path = Path("docs/observation_pilot_inspection.md"),
) -> None:
    """Inspect a JSONL pilot and write the same readable report printed to stdout."""

    records = [
        ObservationRecord.model_validate_json(line)
        for line in results.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = inspect(records)
    output.write_text(report + "\n", encoding="utf-8")
    typer.echo(report)


if __name__ == "__main__":
    typer.run(main)
