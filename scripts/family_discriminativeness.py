"""Measure family-level discriminativeness in the completed positive observations."""

import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import typer

from ordnance_id.evals.discriminativeness import (
    interval_overlap,
    mutual_information,
    total_variation,
)

CATEGORICAL_FIELDS = (
    "image_quality_sufficient",
    "body_shape",
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_visible",
    "surface_condition",
    "embedded_in_ground",
    "looks_manufactured",
)
ELIGIBLE_TIERS = {"reportable", "limited"}
FOCUS_PAIRS = {
    frozenset(("mortar", "projectile")),
    frozenset(("grenade", "projectile")),
    frozenset(("cartridge", "fuze")),
}


def _load(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [row for row in rows if row["family"] != "not_ordnance" and row["observation"]]


def _value(row: dict[str, Any], field: str) -> Any:
    value = row["observation"].get(field)
    return "unobserved" if value is None else value


def _dist(rows: list[dict[str, Any]], family: str, field: str) -> Counter[Any]:
    return Counter(_value(row, field) for row in rows if row["family"] == family)


def _quartiles(values: list[float]) -> tuple[float, float, float]:
    q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
    return float(q1), float(median), float(q3)


def _heatmaps(
    rows: list[dict[str, Any]], families: list[str], figures_dir: Path
) -> dict[str, dict[tuple[str, str], float]]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[tuple[str, str], float]] = {}
    for field in CATEGORICAL_FIELDS:
        matrix = np.zeros((len(families), len(families)))
        pairs: dict[tuple[str, str], float] = {}
        for left_index, left in enumerate(families):
            for right_index, right in enumerate(families):
                score = total_variation(_dist(rows, left, field), _dist(rows, right, field))
                matrix[left_index, right_index] = score
                if left_index < right_index:
                    pairs[(left, right)] = score
        results[field] = pairs
        fig, axis = plt.subplots(figsize=(8, 7))
        image = axis.imshow(matrix, vmin=0, vmax=1, cmap="viridis")
        axis.set_xticks(range(len(families)), families, rotation=45, ha="right")
        axis.set_yticks(range(len(families)), families)
        axis.set_title(field)
        for row_index in range(len(families)):
            for column_index in range(len(families)):
                axis.text(
                    column_index,
                    row_index,
                    f"{matrix[row_index, column_index]:.2f}",
                    ha="center",
                    va="center",
                    color="white" if matrix[row_index, column_index] < 0.55 else "black",
                    fontsize=7,
                )
        fig.colorbar(image, ax=axis, label="Total variation distance")
        fig.tight_layout()
        fig.savefig(figures_dir / f"family_tvd_{field}.png", dpi=160)
        plt.close(fig)
    return results


def build_report(rows: list[dict[str, Any]], figures_dir: Path) -> str:
    """Build the family MI, pairwise TVD, and numeric-overlap report."""

    counts = Counter(row["family"] for row in rows)
    labels = [row["family"] for row in rows]
    mi_scores = sorted(
        (
            (field, mutual_information([_value(row, field) for row in rows], labels))
            for field in CATEGORICAL_FIELDS
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    families = sorted(
        family
        for family in counts
        if any(row["family"] == family and row["tier"] in ELIGIBLE_TIERS for row in rows)
    )
    tvd = _heatmaps(rows, families, figures_dir)
    lines = [
        "# Family-level discriminativeness",
        "",
        f"Positive observations only: **n={len(rows)}**.",
        "`None` is represented as the categorical value `unobserved`.",
        "Mutual information is empirical MI in natural-log units (nats).",
        "",
        "## Sample sizes",
        "",
        "| Family | n | Status |",
        "|---|---:|---|",
    ]
    for family, count in sorted(counts.items()):
        status = "no inference" if family == "landmine" else (
            "indicative only" if count < 10 else "descriptive"
        )
        lines.append(f"| {family} | {count} | {status} |")
    lines.extend(
        [
            "",
            "## 1. Mutual information with family label",
            "",
            "| Rank | Field | MI (nats) |",
            "|---:|---|---:|",
        ]
    )
    lines.extend(
        f"| {rank} | {field} | {score:.4f} |"
        for rank, (field, score) in enumerate(mi_scores, 1)
    )
    lines.extend(
        [
            "",
            "## 2. Pairwise family TVD",
            "",
            "Reportable and limited families only. Values range from 0 (same empirical "
            "distribution) to 1 (disjoint empirical distributions).",
            "",
            "### Requested family pairs",
            "",
            "| Pair | Field | TVD |",
            "|---|---|---:|",
        ]
    )
    for pair in sorted(FOCUS_PAIRS, key=lambda item: sorted(item)):
        left, right = sorted(pair)
        for field in CATEGORICAL_FIELDS:
            key = (left, right) if (left, right) in tvd[field] else (right, left)
            lines.append(f"| {left} vs {right} | {field} | {tvd[field][key]:.3f} |")
    lines.extend(["", "### Heatmaps", ""])
    lines.extend(
        f"- [{field}](../reports/figures/family_tvd_{field}.png)"
        for field in CATEGORICAL_FIELDS
    )

    ratio_stats: dict[str, tuple[int, float, float, float]] = {}
    ratio_values: dict[str, list[float]] = {}
    for family in sorted(counts):
        values = [
            row["observation"]["length_to_width_ratio"]
            for row in rows
            if row["family"] == family
            and row["observation"]["length_to_width_ratio"] is not None
        ]
        if values:
            ratio_values[family] = values
            q1, median, q3 = _quartiles(values)
            ratio_stats[family] = (len(values), q1, median, q3)
    lines.extend(
        [
            "",
            "## 3. Length-to-width ratio",
            "",
            "| Family | n filled | Q1 | Median | Q3 | Status |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for family in sorted(counts):
        status = "no inference" if family == "landmine" else "descriptive"
        if family in ratio_stats:
            n, q1, median, q3 = ratio_stats[family]
            if n < 10 and family != "landmine":
                status = "indicative only (filled n<10)"
            lines.append(f"| {family} | {n} | {q1:.2f} | {median:.2f} | {q3:.2f} | {status} |")
        else:
            lines.append(f"| {family} | 0 | n/a | n/a | n/a | {status} |")
    lines.extend(
        [
            "",
            "IQR overlap is intersection-over-union of the two family IQR intervals. "
            "Empirical overlap is 1−TVD over the exact observed ratio values.",
            "",
            "| Family pair | IQR overlap | Empirical overlap |",
            "|---|---:|---:|",
        ]
    )
    overlaps = []
    eligible_ratio_families = sorted(set(ratio_stats) - {"landmine"})
    for left, right in combinations(eligible_ratio_families, 2):
        left_stats, right_stats = ratio_stats[left], ratio_stats[right]
        overlap = interval_overlap((left_stats[1], left_stats[3]), (right_stats[1], right_stats[3]))
        empirical = 1 - total_variation(
            Counter(ratio_values[left]), Counter(ratio_values[right])
        )
        overlaps.append((empirical, overlap, left, right))
    lines.extend(
        f"| {left} vs {right} | {iqr_overlap:.3f} | {empirical:.3f} |"
        for empirical, iqr_overlap, left, right in sorted(overlaps, reverse=True)
    )
    lines.extend(
        [
            "",
            "## 4. Sample-size warning",
            "",
            "- Families with n<10 are marked `indicative only`.",
            "- `landmine` (n=2) is marked `no inference`; no family-separation claim is made.",
            "",
        ]
    )
    return "\n".join(lines)


def main(
    results: Path = Path(
        "evals/results/observations_v2_gemini_gemini-2.5-flash_full.jsonl"
    ),
    output: Path = Path("docs/family_discriminativeness.md"),
    figures_dir: Path = Path("reports/figures"),
) -> None:
    """Write family discriminativeness tables and heatmaps."""

    report = build_report(_load(results), figures_dir)
    output.write_text(report + "\n", encoding="utf-8")
    typer.echo(report)


if __name__ == "__main__":
    typer.run(main)
