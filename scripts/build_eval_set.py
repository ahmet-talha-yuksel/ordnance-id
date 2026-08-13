"""Build a crop-based evaluation set from the CTX-UXO YOLO bbox test split."""

import json
from pathlib import Path
from typing import Annotated

import typer

from ordnance_id.data_analysis.tiers import load_class_tiers
from ordnance_id.data_sources import ManifestEntry, load_catalog
from ordnance_id.evals.builder import (
    build_crop_eval_set,
    load_class_mapping,
    load_yolo_test_annotations,
)
from ordnance_id.evals.io import write_eval_set


def main(
    max_per_class: Annotated[int, typer.Option(min=1)] = 20,
    seed: int = 42,
    dataset_root: Path = Path("data/raw/ctx-uxo"),
    output: Path = Path("evals/datasets/eval_set_v1.yaml"),
    image_dir: Path = Path("data/eval_images"),
) -> None:
    """Create deterministic bbox crops and background distractors."""

    source = load_catalog(Path("config/data_sources.yaml")).by_name("ctx-uxo-v2")
    manifest_values = json.loads(Path("data/raw/manifest.json").read_text(encoding="utf-8"))
    manifest = next(
        ManifestEntry.model_validate(value)
        for value in manifest_values
        if value.get("name") == source.name
    )
    eval_set = build_crop_eval_set(
        load_yolo_test_annotations(dataset_root),
        load_class_mapping(Path("config/class_mapping.yaml")),
        load_class_tiers(Path("config/class_tiers.yaml")).mapping(),
        source,
        manifest,
        image_dir,
        max_per_class=max_per_class,
        seed=seed,
    )
    write_eval_set(eval_set, output)
    typer.echo(f"Wrote {len(eval_set.samples)} crop samples to {output}")


if __name__ == "__main__":
    typer.run(main)
