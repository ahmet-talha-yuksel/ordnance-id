"""Render separate positive, negative, and smallest-crop evaluation contact sheets."""

from collections import defaultdict
from pathlib import Path

import typer
from PIL import Image, ImageDraw, ImageFont, ImageOps

from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.schema import EvalSample

THUMBNAIL_SIZE = (220, 180)
LABEL_HEIGHT = 28


def _contact_sheet(samples: list[EvalSample], image_dir: Path, output: Path, columns: int) -> None:
    rows = (len(samples) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * THUMBNAIL_SIZE[0], rows * (180 + LABEL_HEIGHT)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    for index, sample in enumerate(samples):
        with Image.open(image_dir / sample.filename) as source:
            thumbnail = ImageOps.contain(source.convert("RGB"), THUMBNAIL_SIZE)
        column, row = index % columns, index // columns
        x = column * THUMBNAIL_SIZE[0] + (THUMBNAIL_SIZE[0] - thumbnail.width) // 2
        y = row * (THUMBNAIL_SIZE[1] + LABEL_HEIGHT)
        sheet.paste(thumbnail, (x, y))
        label = f"{sample.id} · {sample.ground_truth.family}"
        draw.text(
            (column * THUMBNAIL_SIZE[0] + 5, y + THUMBNAIL_SIZE[1] + 5),
            label,
            fill="black",
            font=font,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="JPEG", quality=90)


def main(
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    image_dir: Path = Path("data/eval_images"),
    figures_dir: Path = Path("reports/figures"),
) -> None:
    """Create deterministic visual-review sheets from the crop eval set."""

    eval_set = load_eval_set(eval_path)
    positives: defaultdict[str, list[EvalSample]] = defaultdict(list)
    negatives: list[EvalSample] = []
    for sample in eval_set.samples:
        if sample.ground_truth.is_ordnance:
            positives[sample.ground_truth.family].append(sample)
        else:
            negatives.append(sample)
    positive_preview = [sample for family in sorted(positives) for sample in positives[family][:4]]
    negative_preview = negatives[:12]
    sizes: list[tuple[int, EvalSample]] = []
    for sample in eval_set.samples:
        with Image.open(image_dir / sample.filename) as image:
            sizes.append((min(image.size), sample))
    smallest = [
        sample for _size, sample in sorted(sizes, key=lambda item: (item[0], item[1].id))[:12]
    ]
    _contact_sheet(positive_preview, image_dir, figures_dir / "eval_crops_positive.jpg", 4)
    _contact_sheet(negative_preview, image_dir, figures_dir / "eval_crops_negative.jpg", 4)
    _contact_sheet(smallest, image_dir, figures_dir / "eval_crops_smallest.jpg", 4)
    typer.echo(
        f"Rendered {len(positive_preview)} positive, {len(negative_preview)} negative, "
        f"and {len(smallest)} smallest crops."
    )


if __name__ == "__main__":
    typer.run(main)
