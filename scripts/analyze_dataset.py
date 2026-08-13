"""Discover CTX-UXO annotation repositories and produce descriptive reports."""

from pathlib import Path

import typer

from ordnance_id.data_analysis.discovery import analyze_dataset
from ordnance_id.data_analysis.reporting import write_report


def main(
    dataset_root: Path = Path("data/raw/ctx-uxo"),
    output: Path = Path("docs/dataset_analysis.md"),
    figures: Path = Path("reports/figures"),
) -> None:
    """Analyze every discovered COCO/YOLO repository under the supplied root."""

    report = analyze_dataset(dataset_root)
    write_report(report, output, figures)
    typer.echo(f"Analyzed {len(report.repositories)} repositories; report written to {output}")


if __name__ == "__main__":
    typer.run(main)

