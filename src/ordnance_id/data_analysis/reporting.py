"""Render normalized dataset statistics as Markdown tables and committed figures."""

from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

from ordnance_id.data_analysis.models import DatasetReport
from ordnance_id.data_analysis.tiers import ClassTier
from ordnance_id.evals.schema import OrdnanceFamily


def _save_histogram(values: list[float], title: str, xlabel: str, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.hist(values or [0.0], bins=min(30, max(1, len(values))))
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel("Count")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def write_report(
    report: DatasetReport,
    markdown_path: Path,
    figures_dir: Path,
    family_tiers: dict[OrdnanceFamily, ClassTier],
    class_mapping: dict[str, OrdnanceFamily],
) -> None:
    """Write tables, explicit limitations, and distribution charts."""

    figures_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# CTX-UXO Dataset Analysis", "", f"Analyzed root: `{report.source_root}`", ""]
    for index, repository in enumerate(report.repositories, start=1):
        lines.extend(
            [
                f"## {repository.name}",
                "",
                f"- Format: `{repository.format}`",
                f"- Detected purpose: `{repository.purpose}`",
                f"- Annotation root: `{repository.root}`",
                "",
                "| Split | Images | Instances | Average instances/image |",
                "|---|---:|---:|---:|",
            ]
        )
        class_counts: Counter[str] = Counter()
        bbox_areas: list[float] = []
        widths: list[float] = []
        heights: list[float] = []
        for split in repository.splits:
            average = split.instance_count / split.image_count if split.image_count else 0.0
            lines.append(
                f"| {split.name} | {split.image_count} | {split.instance_count} | {average:.2f} |"
            )
            class_counts.update(split.class_counts)
            bbox_areas.extend(split.bbox_area_fractions)
            widths.extend(float(width) for width, _height in split.resolutions)
            heights.extend(float(height) for _width, height in split.resolutions)
        total = sum(class_counts.values())
        missing_mapping = sorted(set(class_counts) - class_mapping.keys())
        if missing_mapping:
            raise ValueError(
                "Classes missing from class_mapping.yaml: " + ", ".join(missing_mapping)
            )
        lines.extend(["", "| Class | Instances | Percentage | Assessment |", "|---|---:|---:|---|"])
        for class_name, count in class_counts.most_common():
            percentage = count / total * 100 if total else 0.0
            family = class_mapping[class_name]
            if family not in family_tiers:
                raise ValueError(f"Family missing from class_tiers.yaml: {family}")
            assessment = family_tiers[family]
            lines.append(f"| {class_name} | {count} | {percentage:.2f}% | {assessment} |")
        if repository.warnings:
            lines.extend(["", "Warnings:", *[f"- {warning}" for warning in repository.warnings]])

        slug = f"repository_{index}"
        class_figure = figures_dir / f"{slug}_class_distribution.png"
        figure, axis = plt.subplots(figsize=(10, 5))
        axis.bar(list(class_counts), list(class_counts.values()))
        axis.tick_params(axis="x", rotation=60)
        axis.set_title(f"Class distribution — {repository.name}")
        axis.set_ylabel("Instances")
        figure.tight_layout()
        figure.savefig(class_figure, dpi=150)
        plt.close(figure)
        _save_histogram(
            bbox_areas,
            f"Bounding-box area distribution — {repository.name}",
            "Bounding-box fraction of image",
            figures_dir / f"{slug}_bbox_area.png",
        )
        _save_histogram(
            widths + heights,
            f"Resolution distribution — {repository.name}",
            "Width and height (pixels)",
            figures_dir / f"{slug}_resolution.png",
        )
        lines.extend(
            [
                "",
                f"![Class distribution](../reports/figures/{class_figure.name})",
                "",
                f"![Bounding-box area distribution](../reports/figures/{slug}_bbox_area.png)",
                "",
                f"![Resolution distribution](../reports/figures/{slug}_resolution.png)",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitations",
            "",
            "- Serious class imbalance limits meaningful comparisons and makes rare-class "
            "claims unsafe.",
            "- The dataset includes replicas as well as real ordnance; results may not transfer "
            "to field objects.",
            "- A single geographic and institutional source limits environmental and domain "
            "diversity.",
            "- These descriptive statistics do not validate identification performance or "
            "operational use.",
            "- A region without an annotation is not proof that no ordnance is present; "
            "background distractor labels therefore have medium confidence only.",
            "",
        ]
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
