"""Generate the full observation report and its decision-analysis figures."""

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import typer

try:
    from scripts.inspect_observations import PROHIBITED_PATTERNS, _strings
except ModuleNotFoundError:  # Direct `python scripts/observation_report.py` execution.
    from inspect_observations import PROHIBITED_PATTERNS, _strings

FIELDS = (
    "image_quality_sufficient",
    "body_shape",
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_visible",
    "markings_text",
    "color_bands",
    "surface_condition",
    "embedded_in_ground",
    "length_to_width_ratio",
    "looks_manufactured",
)
DISCRIMINATIVE_FIELDS = (
    "looks_manufactured",
    "body_shape",
    "surface_condition",
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_visible",
    "embedded_in_ground",
)


def _load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _group(row: dict[str, Any]) -> str:
    return "negative" if row["family"] == "not_ordnance" else "positive"


def _display(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(map(str, value)) if value else "[]"
    if value is None:
        return "None"
    return str(value)


def total_variation(positive: Counter[Any], negative: Counter[Any]) -> float:
    """Return total variation distance between two empirical distributions."""

    values = set(positive) | set(negative)
    p_total, n_total = positive.total(), negative.total()
    if not p_total or not n_total:
        return 0.0
    return 0.5 * sum(
        abs(positive[value] / p_total - negative[value] / n_total) for value in values
    )


def _distribution(rows: list[dict[str, Any]], field: str) -> Counter[Any]:
    return Counter(row["observation"].get(field) for row in rows if row.get("observation"))


def _fill_rate(rows: list[dict[str, Any]], field: str) -> str:
    observations = [row["observation"] for row in rows if row.get("observation")]
    if not observations:
        return "n/a"
    filled = sum(observation.get(field) is not None for observation in observations)
    return f"{filled / len(observations):.1%}"


def _figures(
    rows: list[dict[str, Any]], scores: list[tuple[str, float]], output_dir: Path
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    buckets = ("small", "medium", "large")
    x = np.arange(len(FIELDS))
    width = 0.25
    fig, axis = plt.subplots(figsize=(14, 6))
    for index, bucket in enumerate(buckets):
        subset = [row for row in rows if row["size_bucket"] == bucket]
        rates = [float(_fill_rate(subset, field).rstrip("%")) for field in FIELDS]
        axis.bar(x + (index - 1) * width, rates, width, label=bucket)
    axis.set_ylabel("Filled (%)")
    axis.set_xticks(x, FIELDS, rotation=55, ha="right")
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "field_completion_by_size.png", dpi=160)
    plt.close(fig)

    body_values = sorted(
        {row["observation"]["body_shape"] for row in rows if row.get("observation")}
    )
    positive = [row for row in rows if _group(row) == "positive"]
    negative = [row for row in rows if _group(row) == "negative"]
    pos_dist, neg_dist = _distribution(positive, "body_shape"), _distribution(
        negative, "body_shape"
    )
    fig, axis = plt.subplots(figsize=(10, 5))
    x = np.arange(len(body_values))
    axis.bar(x - 0.2, [pos_dist[v] / len(positive) for v in body_values], 0.4, label="positive")
    axis.bar(x + 0.2, [neg_dist[v] / len(negative) for v in body_values], 0.4, label="negative")
    axis.set_xticks(x, body_values, rotation=35, ha="right")
    axis.set_ylabel("Proportion")
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "body_shape_positive_negative.png", dpi=160)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(9, 5))
    names, values = zip(*reversed(scores), strict=True)
    axis.barh(names, values)
    axis.set_xlabel("Total variation distance")
    axis.set_xlim(0, 1)
    fig.tight_layout()
    fig.savefig(output_dir / "discriminativeness_ranking.png", dpi=160)
    plt.close(fig)


def build_report(rows: list[dict[str, Any]], figures_dir: Path) -> str:
    """Build the requested full-set report and write its figures."""

    successful = [row for row in rows if row.get("observation")]
    positive = [row for row in successful if _group(row) == "positive"]
    negative = [row for row in successful if _group(row) == "negative"]
    violations: list[tuple[str, str, str, str]] = []
    for row in successful:
        for field, text in _strings(row["observation"]):
            for rule, pattern in PROHIBITED_PATTERNS.items():
                if pattern.search(text):
                    violations.append((row["sample_id"], field, rule, text))

    scores = sorted(
        (
            (
                field,
                total_variation(
                    _distribution(positive, field), _distribution(negative, field)
                ),
            )
            for field in DISCRIMINATIVE_FIELDS
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    _figures(rows, scores, figures_dir)
    total_duration = sum(row["duration_ms"] for row in rows)
    metrics = [row["metrics"] for row in rows]
    lines = [
        "# Observation Report v1",
        "",
        "## 1. Run identity",
        "",
        "- Model: `gemini-2.5-flash`",
        "- Prompt: `observe_v2`",
        f"- Date: {date.today().isoformat()}",
        f"- Samples: {len(rows)} ({len(successful)} successful, "
        f"{len(rows) - len(successful)} errors)",
        f"- Total recorded duration: {total_duration / 1000:.1f} s",
        f"- Tokens: {sum(m['input_tokens'] for m in metrics)} input, "
        f"{sum(m['output_tokens'] for m in metrics)} output",
        f"- HTTP 429: {sum(m['rate_limit_429s'] for m in metrics)}; "
        f"retries: {sum(m['retries'] for m in metrics)}",
        f"- Cache hit rate: {sum(m['cache_hit'] for m in metrics) / len(rows):.1%}",
        "",
        "## 2. Rule violation scan",
        "",
        f"Violations: **{len(violations)}**",
        "",
    ]
    if violations:
        lines.extend(
            f"- `{sample}` · `{field}` · `{rule}`: “{text}”"
            for sample, field, rule, text in violations
        )
    else:
        lines.append("- No prohibited text found.")

    lines.extend(
        [
            "",
            "## 3. Field completion",
            "",
            "`estimated_length_cm`: **not applicable in this eval set "
            "(no scale references present)**; excluded from all completion averages.",
            "",
            "| Field | Overall | Small | Medium | Large | Positive | Negative |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for field in FIELDS:
        groups = [
            successful,
            [row for row in successful if row["size_bucket"] == "small"],
            [row for row in successful if row["size_bucket"] == "medium"],
            [row for row in successful if row["size_bucket"] == "large"],
            positive,
            negative,
        ]
        rates = " | ".join(_fill_rate(group, field) for group in groups)
        lines.append(f"| {field} | {rates} |")

    lines.extend(
        [
            "",
            "![Field completion by size](../reports/figures/field_completion_by_size.png)",
            "",
            "## 4. Discriminativeness analysis",
            "",
            "| Rank | Field | Positive distribution | Negative distribution | TV distance |",
            "|---:|---|---|---|---:|",
        ]
    )
    for rank, (field, score) in enumerate(scores, 1):
        lines.append(
            f"| {rank} | {field} | `{dict(_distribution(positive, field))}` | "
            f"`{dict(_distribution(negative, field))}` | {score:.3f} |"
        )
    lines.extend(
        [
            "",
            "![Body-shape distributions](../reports/figures/body_shape_positive_negative.png)",
            "",
            "![Discriminativeness ranking](../reports/figures/discriminativeness_ranking.png)",
            "",
            "## 5. Family profiles",
            "",
            "| Family | n | Field | Modal value | Count | Rate |",
            "|---|---:|---|---|---:|---:|",
        ]
    )
    for family in sorted({row["family"] for row in successful}):
        family_rows = [row for row in successful if row["family"] == family]
        for field in DISCRIMINATIVE_FIELDS:
            counts = _distribution(family_rows, field)
            mode, count = counts.most_common(1)[0]
            lines.append(
                f"| {family} | {len(family_rows)} | {field} | {_display(mode)} | "
                f"{count} | {count / len(family_rows):.1%} |"
            )

    lines.extend(
        [
            "",
            "## 6. Length-to-width ratio by family",
            "",
            "| Family | n | Q1 | Median | Q3 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for family in sorted({row["family"] for row in successful}):
        values = [
            row["observation"]["length_to_width_ratio"]
            for row in successful
            if row["family"] == family
            and row["observation"]["length_to_width_ratio"] is not None
        ]
        if values:
            q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
            lines.append(f"| {family} | {len(values)} | {q1:.2f} | {median:.2f} | {q3:.2f} |")
        else:
            lines.append(f"| {family} | 0 | n/a | n/a | n/a |")

    reasons: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in successful:
        for item in row["observation"]["unclear_features"]:
            field, separator, reason = item.partition(":")
            reasons[field.strip()][reason.strip() if separator else "unformatted"] += 1
    flattened = sorted(
        (
            (count, field, reason)
            for field, values in reasons.items()
            for reason, count in values.items()
        ),
        reverse=True,
    )[:15]
    lines.extend(
        [
            "",
            "## 7. Most frequent unclear-feature reasons",
            "",
            "| Rank | Field | Reason | Count |",
            "|---:|---|---|---:|",
        ]
    )
    lines.extend(
        f"| {rank} | {field} | {reason} | {count} |"
        for rank, (count, field, reason) in enumerate(flattened, 1)
    )
    lines.extend(
        [
            "",
            "## 8. Limitations",
            "",
            "- The sample is small; landmine has 2 samples and the insufficient tier is "
            "generally inadequate.",
            "- Most small samples are cartridge; size and family effects cannot be disentangled.",
            "- Negatives rely on annotation absence; no independent ‘not ordnance’ "
            "verification was performed.",
            "- Crops come from one dataset and include replicas.",
            "- This is one model and one run; variance was not measured.",
            "- This report measures observation consistency; it **does not measure "
            "identification accuracy**.",
            "",
        ]
    )
    return "\n".join(lines)


def main(
    results: Path = Path(
        "evals/results/observations_v2_gemini_gemini-2.5-flash_full.jsonl"
    ),
    output: Path = Path("docs/observation_report_v1.md"),
    figures_dir: Path = Path("reports/figures"),
) -> None:
    """Write the full Markdown observation report and PNG figures."""

    report = build_report(_load(results), figures_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report + "\n", encoding="utf-8")
    typer.echo(report)


if __name__ == "__main__":
    typer.run(main)
