"""Recheck every negative crop against every source-image annotation."""

from collections import defaultdict
from pathlib import Path

import typer

from ordnance_id.evals.builder import Box, load_yolo_test_annotations
from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.provenance import bbox_from_notes, source_image_from_notes


def intersection_area(first: Box, second: Box) -> float:
    """Return absolute intersection area, including partial containment cases."""

    width = max(0.0, min(first.x + first.width, second.x + second.width) - max(first.x, second.x))
    height = max(
        0.0, min(first.y + first.height, second.y + second.height) - max(first.y, second.y)
    )
    return width * height


def main(
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    dataset_root: Path = Path("data/raw/ctx-uxo"),
) -> None:
    """List negatives having any overlap with a source annotation; do not mutate the set."""

    annotations: defaultdict[str, list[Box]] = defaultdict(list)
    for annotation in load_yolo_test_annotations(dataset_root):
        annotations[annotation.image.name].append(annotation.bbox)
    eval_set = load_eval_set(eval_path)
    contaminated: list[tuple[str, str, float]] = []
    negative_count = 0
    for sample in eval_set.samples:
        if sample.ground_truth.is_ordnance:
            continue
        negative_count += 1
        source_image = source_image_from_notes(sample.notes)
        sampled_box = bbox_from_notes(sample.notes)
        overlap = max(
            (intersection_area(sampled_box, annotated) for annotated in annotations[source_image]),
            default=0.0,
        )
        if overlap > 0:
            contaminated.append((sample.id, source_image, overlap))
    typer.echo(f"Checked {negative_count} negatives against all source-image boxes.")
    if contaminated:
        typer.echo(f"CONTAMINATED: {len(contaminated)}; recommend removal from eval set")
        for sample_id, source_image, overlap in contaminated:
            typer.echo(f"  {sample_id} source={source_image} overlap_px2={overlap:.2f}")
        raise typer.Exit(code=2)
    typer.echo("No negative crop has any annotated-box intersection.")


if __name__ == "__main__":
    typer.run(main)

