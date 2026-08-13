"""Print the deterministic tier-stratified observation pilot."""

from pathlib import Path

import typer

from ordnance_id.data_analysis.tiers import load_class_tiers
from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.pilot import select_pilot


def main(
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    image_dir: Path = Path("data/eval_images"),
    seed: int = 0,
) -> None:
    """List selected IDs, labels, tiers, and size buckets without calling a model."""

    eval_set = load_eval_set(eval_path)
    tiers = load_class_tiers(Path("config/class_tiers.yaml")).mapping()
    selected = select_pilot(eval_set.samples, image_dir, tiers, seed=seed)
    typer.echo("sample_id | family | tier | size_bucket")
    for item in selected:
        typer.echo(
            f"{item.sample.id} | {item.sample.ground_truth.family} | "
            f"{item.tier or 'distractor'} | {item.size_bucket}"
        )


if __name__ == "__main__":
    typer.run(main)

