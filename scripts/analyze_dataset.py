"""Discover CTX-UXO annotation repositories and produce descriptive reports."""

from pathlib import Path

import typer

from ordnance_id.data_analysis.discovery import analyze_dataset
from ordnance_id.data_analysis.reporting import write_report
from ordnance_id.data_analysis.tiers import load_class_tiers
from ordnance_id.evals.builder import load_class_mapping


def main(
    dataset_root: Path = Path("data/raw/ctx-uxo"),
    output: Path = Path("docs/dataset_analysis.md"),
    figures: Path = Path("reports/figures"),
) -> None:
    """Analyze every discovered COCO/YOLO repository under the supplied root."""

    report = analyze_dataset(dataset_root)
    tiers = load_class_tiers(Path("config/class_tiers.yaml")).mapping()
    mapping = load_class_mapping(Path("config/class_mapping.yaml"))
    write_report(report, output, figures, tiers, mapping)
    typer.echo(f"Analyzed {len(report.repositories)} repositories; report written to {output}")


if __name__ == "__main__":
    typer.run(main)
