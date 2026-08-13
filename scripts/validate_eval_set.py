"""Validate an evaluation YAML, referenced files, and family distribution."""

from collections import Counter
from pathlib import Path

import typer

from ordnance_id.evals.io import load_eval_set


def main(
    eval_path: Path = Path("evals/ctx_uxo_eval.yaml"),
    image_dir: Path = Path("data/eval_images"),
) -> None:
    """Validate schema and verify that every referenced image exists."""

    eval_set = load_eval_set(eval_path)
    missing = [
        sample.filename
        for sample in eval_set.samples
        if not (image_dir / sample.filename).is_file()
    ]
    if missing:
        raise typer.BadParameter("Missing eval images: " + ", ".join(missing))
    counts = Counter(sample.ground_truth.family for sample in eval_set.samples)
    typer.echo(f"Eval set {eval_set.version}: {len(eval_set.samples)} samples")
    for family, count in sorted(counts.items()):
        typer.echo(f"  {family}: {count}")


if __name__ == "__main__":
    typer.run(main)
