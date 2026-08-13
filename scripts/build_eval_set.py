"""Build a bounded evaluation YAML from verified CTX-UXO test annotations."""

import json
from pathlib import Path
from typing import Annotated

import typer

from ordnance_id.data_sources import ManifestEntry, load_catalog
from ordnance_id.evals.builder import (
    build_eval_set,
    collect_test_candidates,
    load_class_mapping,
)
from ordnance_id.evals.io import write_eval_set


def main(
    max_per_class: Annotated[int, typer.Option(min=1)] = 25,
    dataset_root: Path = Path("data/raw/ctx-uxo"),
    output: Path = Path("evals/ctx_uxo_eval.yaml"),
    image_dir: Path = Path("data/eval_images"),
) -> None:
    """Create a deterministic, class-balanced CTX-UXO test subset."""

    source = load_catalog(Path("config/data_sources.yaml")).by_name("ctx-uxo-v2")
    manifest_values = json.loads(Path("data/raw/manifest.json").read_text(encoding="utf-8"))
    manifest = next(
        ManifestEntry.model_validate(value)
        for value in manifest_values
        if value.get("name") == source.name
    )
    candidates = collect_test_candidates(dataset_root)
    mapping = load_class_mapping(Path("config/class_mapping.yaml"))
    eval_set = build_eval_set(
        candidates,
        mapping,
        source,
        manifest,
        image_dir,
        max_per_class=max_per_class,
    )
    write_eval_set(eval_set, output)
    typer.echo(f"Wrote {len(eval_set.samples)} samples to {output}")


if __name__ == "__main__":
    typer.run(main)

