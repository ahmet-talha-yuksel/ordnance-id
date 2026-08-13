"""Quantify possible dataset shortcuts in three high-salience observation fields."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import typer

from ordnance_id.evals.discriminativeness import mutual_information, total_variation

FIELDS = ("surface_condition", "looks_manufactured", "body_shape")


def _load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _value(row: dict[str, Any], field: str) -> Any:
    value = row["observation"].get(field)
    return "unobserved" if value is None else value


def _dist(rows: list[dict[str, Any]], field: str) -> Counter[Any]:
    return Counter(_value(row, field) for row in rows)


def build_report(rows: list[dict[str, Any]]) -> str:
    """Build numeric shortcut diagnostics and a threshold-based suspicion list."""

    rows = [row for row in rows if row.get("observation")]
    positive = [row for row in rows if row["family"] != "not_ordnance"]
    negative = [row for row in rows if row["family"] == "not_ordnance"]
    family_labels = [row["family"] for row in positive]
    size_labels = [row["size_bucket"] for row in rows]
    metrics: dict[str, tuple[float, float, float]] = {}
    lines = [
        "# Shortcut suspicion analysis",
        "",
        f"Observations: {len(rows)}; positive: {len(positive)}; negative: {len(negative)}.",
        "`None` is counted as `unobserved`. MI is reported in nats.",
        "",
        "## Association summary",
        "",
        "| Field | Positive/negative TVD | MI with positive-family label | MI with size bucket |",
        "|---|---:|---:|---:|",
    ]
    for field in FIELDS:
        pn_tvd = total_variation(_dist(positive, field), _dist(negative, field))
        family_mi = mutual_information(
            [_value(row, field) for row in positive], family_labels
        )
        size_mi = mutual_information([_value(row, field) for row in rows], size_labels)
        metrics[field] = (pn_tvd, family_mi, size_mi)
        lines.append(f"| {field} | {pn_tvd:.3f} | {family_mi:.4f} | {size_mi:.4f} |")

    for field in FIELDS:
        lines.extend(
            [
                "",
                f"## {field}",
                "",
                "### Distribution by family",
                "",
                "| Family | n | Distribution |",
                "|---|---:|---|",
            ]
        )
        for family in sorted({row["family"] for row in rows}):
            subset = [row for row in rows if row["family"] == family]
            lines.append(f"| {family} | {len(subset)} | `{dict(_dist(subset, field))}` |")
        lines.extend(
            [
                "",
                "### Distribution by size bucket",
                "",
                "| Size bucket | n | Distribution |",
                "|---|---:|---|",
            ]
        )
        for bucket in ("small", "medium", "large"):
            subset = [row for row in rows if row["size_bucket"] == bucket]
            lines.append(f"| {bucket} | {len(subset)} | `{dict(_dist(subset, field))}` |")
        lines.extend(
            [
                "",
                "### Negative distribution",
                "",
                f"- n: {len(negative)}",
                f"- Counts: `{dict(_dist(negative, field))}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Suspected shortcuts",
            "",
            "Flag rule: positive/negative TVD ≥ 0.50 and either family MI ≥ 0.10 "
            "or size-bucket MI ≥ 0.05.",
            "",
        ]
    )
    flagged = [
        (field, values)
        for field, values in metrics.items()
        if values[0] >= 0.5 and (values[1] >= 0.1 or values[2] >= 0.05)
    ]
    lines.extend(
        f"- `{field}` — TVD={values[0]:.3f}, family MI={values[1]:.4f}, "
        f"size MI={values[2]:.4f}"
        for field, values in flagged
    )
    if not flagged:
        lines.append("- None under the stated rule.")
    lines.append("")
    return "\n".join(lines)


def main(
    results: Path = Path(
        "evals/results/observations_v2_gemini_gemini-2.5-flash_full.jsonl"
    ),
    output: Path = Path("docs/shortcut_analysis.md"),
) -> None:
    """Write numeric shortcut diagnostics for the completed observation run."""

    report = build_report(_load(results))
    output.write_text(report + "\n", encoding="utf-8")
    typer.echo(report)


if __name__ == "__main__":
    typer.run(main)
