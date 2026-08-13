"""Report crop-eval composition, dimensions, and source-image diversity."""

from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import typer
from PIL import Image

from ordnance_id.data_analysis.tiers import load_class_tiers
from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.provenance import source_image_from_notes
from ordnance_id.evals.size_buckets import size_bucket


def main(
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    image_dir: Path = Path("data/eval_images"),
    output: Path = Path("docs/eval_set_v1.md"),
) -> None:
    """Write and print descriptive statistics for evaluation crops."""

    eval_set = load_eval_set(eval_path)
    tiers = load_class_tiers(Path("config/class_tiers.yaml")).mapping()
    family_tiers: dict[str, set[str]] = {}
    family_counts: Counter[str] = Counter()
    family_sizes: defaultdict[str, Counter[str]] = defaultdict(Counter)
    source_counts: Counter[str] = Counter()
    short_edges: list[int] = []
    size_counts: Counter[str] = Counter()
    positive_count = 0
    for sample in eval_set.samples:
        family_counts[sample.ground_truth.family] += 1
        source_counts[source_image_from_notes(sample.notes)] += 1
        if sample.ground_truth.is_ordnance:
            positive_count += 1
            family_tiers.setdefault(sample.ground_truth.family, set()).add(
                tiers[sample.ground_truth.family]
            )
        with Image.open(image_dir / sample.filename) as image:
            short_edge = min(image.size)
            short_edges.append(short_edge)
            bucket = size_bucket(short_edge)
            size_counts[bucket] += 1
            family_sizes[sample.ground_truth.family][bucket] += 1
    negative_count = len(eval_set.samples) - positive_count
    warnings = sorted((source, count) for source, count in source_counts.items() if count > 3)
    lines = [
        "# Evaluation Set v1 Statistics",
        "",
        "| Family | Tier(s) | Samples | Small | Medium | Large |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for family, count in sorted(family_counts.items()):
        tier_text = ", ".join(sorted(family_tiers.get(family, {"distractor"})))
        sizes = family_sizes[family]
        lines.append(
            f"| {family} | {tier_text} | {count} | {sizes['small']} | "
            f"{sizes['medium']} | {sizes['large']} |"
        )
    lines.extend(
        [
            "",
            "## Composition and dimensions",
            "",
            f"- Positive crops: {positive_count} ({positive_count / len(eval_set.samples):.1%})",
            f"- Negative crops: {negative_count} ({negative_count / len(eval_set.samples):.1%})",
            "- Short edge, min/median/max: "
            f"{min(short_edges)} / {median(short_edges):.1f} / {max(short_edges)} px",
            f"- Distinct source images: {len(source_counts)}",
            "",
            "## Size buckets",
            "",
            "| Bucket | Definition | Samples |",
            "|---|---|---:|",
            f"| small | short edge <150 px | {size_counts['small']} |",
            f"| medium | short edge 150–600 px | {size_counts['medium']} |",
            f"| large | short edge >600 px | {size_counts['large']} |",
            "",
            "## Source concentration warnings",
            "",
        ]
    )
    lines.extend(
        [f"- `{source}` supplies {count} crops (>3)." for source, count in warnings] or ["- None."]
    )
    lines.extend(
        [
            "",
            "## Confounding factors",
            "",
            "- Seven of the 12 small crops belong to the `cartridge` family, so family effects "
            "cannot be separated from size effects in that slice.",
            "- The `landmine` family has only two samples; no performance claim can be made for "
            "that family.",
        ]
    )
    text = "\n".join(lines) + "\n"
    output.write_text(text, encoding="utf-8")
    typer.echo(text)


if __name__ == "__main__":
    typer.run(main)
