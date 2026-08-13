"""Build crop-based evaluation sets from the primary CTX-UXO YOLO bbox repository."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import cast, get_args

import numpy as np
import yaml
from PIL import Image
from pydantic import BaseModel

from ordnance_id.data_analysis.tiers import ClassTier
from ordnance_id.data_sources import DataSource, ManifestEntry
from ordnance_id.evals.schema import EvalSample, EvalSet, GroundTruth, OrdnanceFamily


class Box(BaseModel):
    """Represent an absolute XYWH source-image bounding box."""

    x: float
    y: float
    width: float
    height: float


class Annotation(BaseModel):
    """Associate one source class and bounding box with its image."""

    image: Path
    source_class: str
    bbox: Box


def load_class_mapping(path: Path) -> dict[str, OrdnanceFamily]:
    """Load the explicit source-class to family mapping."""

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    mapping = value.get("classes") if isinstance(value, dict) else None
    if not isinstance(mapping, dict):
        raise ValueError("class mapping must contain a classes mapping")
    allowed = set(get_args(OrdnanceFamily))
    result: dict[str, OrdnanceFamily] = {}
    for source_class, family in mapping.items():
        if family not in allowed:
            raise ValueError(f"Invalid family {family!r} for source class {source_class!r}")
        result[str(source_class)] = cast(OrdnanceFamily, family)
    return result


def load_yolo_test_annotations(dataset_root: Path) -> list[Annotation]:
    """Read only the primary yolo_bbox test split and convert labels to absolute boxes."""

    repository = dataset_root / "yolo_bbox"
    config = yaml.safe_load((repository / "data.yaml").read_text(encoding="utf-8"))
    names = {index: str(name) for index, name in enumerate(config["names"])}
    image_root = dataset_root / "images" / "test" / "images"
    label_root = repository / "test" / "labels"
    annotations: list[Annotation] = []
    seen_classes: set[str] = set()
    for image_path in sorted(image_root.glob("*")):
        label_path = label_root / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue
        with Image.open(image_path) as image:
            image_width, image_height = image.size
        for line in label_path.read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) != 5:
                raise ValueError(f"Expected YOLO bbox row in {label_path}: {line}")
            class_id, center_x, center_y, width, height = map(float, fields)
            source_class = names[int(class_id)]
            seen_classes.add(source_class)
            absolute_width = width * image_width
            absolute_height = height * image_height
            annotations.append(
                Annotation(
                    image=image_path,
                    source_class=source_class,
                    bbox=Box(
                        x=center_x * image_width - absolute_width / 2,
                        y=center_y * image_height - absolute_height / 2,
                        width=absolute_width,
                        height=absolute_height,
                    ),
                )
            )
    if not annotations:
        raise ValueError(f"No YOLO bbox test annotations found below {repository}")
    return annotations


def padded_bounds(box: Box, image_size: tuple[int, int], padding: float = 0.15) -> Box:
    """Add proportional context and clamp the crop to image boundaries."""

    image_width, image_height = image_size
    x1 = max(0.0, box.x - box.width * padding)
    y1 = max(0.0, box.y - box.height * padding)
    x2 = min(float(image_width), box.x + box.width * (1 + padding))
    y2 = min(float(image_height), box.y + box.height * (1 + padding))
    return Box(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


def intersection_over_union(first: Box, second: Box) -> float:
    """Calculate IoU for two absolute XYWH boxes."""

    x1 = max(first.x, second.x)
    y1 = max(first.y, second.y)
    x2 = min(first.x + first.width, second.x + second.width)
    y2 = min(first.y + first.height, second.y + second.height)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = first.width * first.height + second.width * second.height - intersection
    return intersection / union if union else 0.0


def _select_positives(
    annotations: list[Annotation],
    tiers: dict[str, ClassTier],
    max_per_class: int,
    rng: random.Random,
) -> list[Annotation]:
    grouped: defaultdict[str, list[Annotation]] = defaultdict(list)
    for annotation in annotations:
        grouped[annotation.source_class].append(annotation)
    selected: list[Annotation] = []
    for source_class in sorted(grouped):
        values = grouped[source_class][:]
        rng.shuffle(values)
        unique_first = sorted(values, key=lambda item: str(item.image))
        unique_by_image: dict[Path, Annotation] = {}
        for item in unique_first:
            unique_by_image.setdefault(item.image, item)
        diverse = list(unique_by_image.values())
        remaining = [item for item in values if item not in diverse]
        limit = len(values) if tiers[source_class] == "insufficient" else max_per_class
        selected.extend((diverse + remaining)[:limit])
    return selected


def _clean_previous_outputs(output_images: Path) -> None:
    manifest = output_images / ".eval_builder_manifest.json"
    if manifest.exists():
        for filename in json.loads(manifest.read_text(encoding="utf-8")):
            target = output_images / str(filename)
            if target.parent == output_images and target.is_file():
                target.unlink()


def _save_crop(image: Image.Image, box: Box, path: Path) -> None:
    crop = image.crop((box.x, box.y, box.x + box.width, box.y + box.height))
    crop.convert("RGB").save(path, format="JPEG", quality=92)


def build_crop_eval_set(
    annotations: list[Annotation],
    mapping: dict[str, OrdnanceFamily],
    tiers: dict[str, ClassTier],
    source: DataSource,
    manifest: ManifestEntry,
    output_images: Path,
    *,
    max_per_class: int = 20,
    seed: int = 42,
) -> EvalSet:
    """Produce bounded positive crops and approximately 30% background distractors."""

    source_classes = {annotation.source_class for annotation in annotations}
    missing_mapping = sorted(source_classes - mapping.keys())
    missing_tiers = sorted(source_classes - tiers.keys())
    if missing_mapping:
        raise ValueError("Unmapped source classes: " + ", ".join(missing_mapping))
    if missing_tiers:
        raise ValueError("Untiered source classes: " + ", ".join(missing_tiers))
    rng = random.Random(seed)
    selected = _select_positives(annotations, tiers, max_per_class, rng)
    output_images.mkdir(parents=True, exist_ok=True)
    _clean_previous_outputs(output_images)
    samples: list[EvalSample] = []
    created: list[str] = []
    positive_sizes: list[tuple[int, int]] = []
    for annotation in selected:
        with Image.open(annotation.image) as image:
            bounds = padded_bounds(annotation.bbox, image.size)
            if min(bounds.width, bounds.height) < 100:
                continue
            sample_id = f"eval_{len(samples) + 1:03d}"
            filename = f"{sample_id}.jpg"
            _save_crop(image, bounds, output_images / filename)
        positive_sizes.append((round(bounds.width), round(bounds.height)))
        created.append(filename)
        samples.append(
            EvalSample(
                id=sample_id,
                filename=filename,
                source_url=str(source.landing_page),
                license=source.license,
                attribution=f"{source.title} — {', '.join(source.authors)} — DOI {source.doi}",
                retrieved=manifest.downloaded_at.date(),
                ground_truth=GroundTruth(
                    is_ordnance=True,
                    family=mapping[annotation.source_class],
                    confidence_of_label="high",
                ),
                notes=(
                    f"source_image={annotation.image.name}; "
                    f"source_class={annotation.source_class}; "
                    f"original_bbox_xywh={annotation.bbox.model_dump()}; context_padding=15%"
                ),
            )
        )

    by_image: defaultdict[Path, list[Box]] = defaultdict(list)
    for annotation in annotations:
        by_image[annotation.image].append(annotation.bbox)
    target_negatives = round(len(samples) * 0.30)
    image_paths = sorted(by_image)
    attempts = 0
    while sum(not sample.ground_truth.is_ordnance for sample in samples) < target_negatives:
        attempts += 1
        if attempts > max(1000, target_negatives * 100):
            break
        image_path = rng.choice(image_paths)
        width, height = rng.choice(positive_sizes)
        with Image.open(image_path) as image:
            if width > image.width or height > image.height:
                continue
            box = Box(
                x=rng.randint(0, image.width - width),
                y=rng.randint(0, image.height - height),
                width=width,
                height=height,
            )
            if any(
                intersection_over_union(box, annotated) > 0.02 for annotated in by_image[image_path]
            ):
                continue
            crop = image.crop((box.x, box.y, box.x + box.width, box.y + box.height)).convert("RGB")
            if float(np.asarray(crop).var()) < 25.0:
                continue
            sample_id = f"eval_{len(samples) + 1:03d}"
            filename = f"{sample_id}.jpg"
            crop.save(output_images / filename, format="JPEG", quality=92)
        created.append(filename)
        samples.append(
            EvalSample(
                id=sample_id,
                filename=filename,
                source_url=str(source.landing_page),
                license=source.license,
                attribution=f"{source.title} — {', '.join(source.authors)} — DOI {source.doi}",
                retrieved=manifest.downloaded_at.date(),
                ground_truth=GroundTruth(
                    is_ordnance=False,
                    family="not_ordnance",
                    confidence_of_label="medium",
                    label_rationale=(
                        "background region with no annotated ordnance; absence of annotation is "
                        "not a guarantee of absence"
                    ),
                ),
                notes=(
                    f"source_image={image_path.name}; sampled_bbox_xywh={box.model_dump()}; "
                    f"seed={seed}; unannotated background is not guaranteed ordnance-free"
                ),
            )
        )
    (output_images / ".eval_builder_manifest.json").write_text(
        json.dumps(created, indent=2) + "\n", encoding="utf-8"
    )
    return EvalSet(
        version="1",
        description=(
            "CTX-UXO YOLO-bbox test crops with context and medium-confidence "
            "background distractors."
        ),
        samples=samples,
    )
