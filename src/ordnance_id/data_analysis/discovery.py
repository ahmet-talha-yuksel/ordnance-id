"""Discover COCO and YOLO repositories and calculate normalized statistics."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from PIL import Image, UnidentifiedImageError

from ordnance_id.data_analysis.models import DatasetReport, RepositoryReport, SplitReport

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _split_name(value: str) -> str:
    name = value.lower()
    if name in {"val", "valid", "validation"}:
        return "validation"
    if name.startswith("train"):
        return "train"
    if name.startswith("test"):
        return "test"
    return name


def _split_from_filename(path: Path) -> str:
    stem = path.stem.lower()
    for token in stem.replace("-", "_").split("_"):
        normalized = _split_name(token)
        if normalized in {"train", "validation", "test"}:
            return normalized
    return stem


def discover_repositories(root: Path) -> list[tuple[Path, str]]:
    """Find annotation roots by inspecting contents rather than assuming directory names."""

    found: set[tuple[Path, str]] = set()
    for json_path in root.rglob("*.json"):
        try:
            value = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and all(key in value for key in ("images", "annotations")):
            found.add((json_path.parent, "coco"))
    for yaml_path in [*root.rglob("*.yaml"), *root.rglob("*.yml")]:
        try:
            value = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        if isinstance(value, dict) and "names" in value and any(
            split in value for split in ("train", "val", "validation", "test")
        ):
            found.add((yaml_path.parent, "yolo"))
    return sorted(found, key=lambda item: (str(item[0]), item[1]))


def _purpose(
    class_count: int, has_segmentation: bool
) -> Literal["binary_classification", "multiclass_detection", "instance_segmentation"]:
    if has_segmentation:
        return "instance_segmentation"
    if class_count <= 2:
        return "binary_classification"
    return "multiclass_detection"


def _analyze_coco(root: Path) -> RepositoryReport:
    splits: list[SplitReport] = []
    all_classes: set[str] = set()
    has_segmentation = False
    warnings: list[str] = []
    for annotation_file in sorted(root.glob("*.json")):
        value = json.loads(annotation_file.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or "images" not in value or "annotations" not in value:
            continue
        data = cast(dict[str, Any], value)
        categories = {
            int(item["id"]): str(item["name"])
            for item in cast(list[dict[str, Any]], data.get("categories", []))
        }
        all_classes.update(categories.values())
        images = {
            int(item["id"]): item for item in cast(list[dict[str, Any]], data.get("images", []))
        }
        counts: Counter[str] = Counter()
        areas: list[float] = []
        annotations = cast(list[dict[str, Any]], data.get("annotations", []))
        for annotation in annotations:
            category = categories.get(int(annotation["category_id"]), "unknown")
            counts[category] += 1
            image = images.get(int(annotation["image_id"]))
            bbox = annotation.get("bbox")
            if image and isinstance(bbox, list) and len(bbox) >= 4:
                image_area = float(image.get("width", 0)) * float(image.get("height", 0))
                if image_area > 0:
                    areas.append(max(0.0, float(bbox[2]) * float(bbox[3]) / image_area))
            has_segmentation = has_segmentation or bool(annotation.get("segmentation"))
        resolutions = [
            (int(item["width"]), int(item["height"]))
            for item in images.values()
            if item.get("width") and item.get("height")
        ]
        split = _split_from_filename(annotation_file)
        splits.append(
            SplitReport(
                name=split,
                image_count=len(images),
                instance_count=len(annotations),
                class_counts=dict(counts),
                resolutions=resolutions,
                bbox_area_fractions=areas,
            )
        )
    return RepositoryReport(
        name=root.name,
        root=root,
        format="coco",
        purpose=_purpose(len(all_classes), has_segmentation),
        splits=splits,
        warnings=warnings,
    )


def _names(value: object) -> dict[int, str]:
    if isinstance(value, list):
        return {index: str(name) for index, name in enumerate(value)}
    if isinstance(value, dict):
        return {int(index): str(name) for index, name in value.items()}
    raise ValueError("YOLO names must be a list or mapping")


def _resolve_yolo_images(config_path: Path, configured: object, base: Path) -> list[Path]:
    values = configured if isinstance(configured, list) else [configured]
    paths: list[Path] = []
    for value in values:
        candidate = Path(str(value))
        if not candidate.is_absolute():
            candidate = (base / candidate).resolve()
        if not candidate.exists():
            relative = Path(str(value))
            tail = relative.parts
            search_root = config_path.parent.parent
            alternatives = [
                path
                for path in search_root.rglob(relative.name)
                if path.is_dir()
                and (
                    path.parts[-len(tail) :] == tail
                    or path.parts[-(len(tail) + 1) :] == ("images", *tail)
                )
            ]
            populated = [
                path
                for path in alternatives
                if any(item.suffix.lower() in IMAGE_SUFFIXES for item in path.iterdir())
            ]
            if len(populated) == 1:
                candidate = populated[0]
        if candidate.is_file() and candidate.suffix == ".txt":
            paths.extend(
                (candidate.parent / line.strip()).resolve()
                for line in candidate.read_text().splitlines()
                if line.strip()
            )
        elif candidate.is_dir():
            paths.extend(
                path for path in candidate.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES
            )
        elif candidate.suffix.lower() in IMAGE_SUFFIXES:
            paths.append(candidate)
    return sorted(set(paths))


def _label_path(image: Path) -> Path:
    parts = list(image.parts)
    if "images" in parts:
        reverse_index = parts[::-1].index("images")
        parts[len(parts) - reverse_index - 1] = "labels"
        return Path(*parts).with_suffix(".txt")
    return image.with_suffix(".txt")


def _analyze_yolo(root: Path) -> RepositoryReport:
    config_path = next(
        path
        for path in sorted([*root.glob("*.yaml"), *root.glob("*.yml")])
        if isinstance(yaml.safe_load(path.read_text()), dict)
        and "names" in yaml.safe_load(path.read_text())
    )
    config = cast(dict[str, Any], yaml.safe_load(config_path.read_text(encoding="utf-8")))
    names = _names(config["names"])
    configured_root = Path(str(config.get("path", ".")))
    base = configured_root if configured_root.is_absolute() else (root / configured_root).resolve()
    splits: list[SplitReport] = []
    warnings: list[str] = []
    has_segmentation = False
    for split_key in ("train", "val", "validation", "test"):
        if split_key not in config:
            continue
        images = _resolve_yolo_images(config_path, config[split_key], base)
        configured_split = Path(str(config[split_key])).parts[0]
        label_root = root / configured_split / "labels"
        counts: Counter[str] = Counter()
        resolutions: list[tuple[int, int]] = []
        areas: list[float] = []
        instance_count = 0
        for image_path in images:
            try:
                with Image.open(image_path) as image:
                    resolutions.append(image.size)
            except (OSError, UnidentifiedImageError):
                warnings.append(f"Unreadable image: {image_path}")
            label_path = label_root / f"{image_path.stem}.txt"
            if not label_path.exists():
                continue
            for line in label_path.read_text(encoding="utf-8").splitlines():
                fields = line.split()
                if len(fields) < 5:
                    warnings.append(f"Invalid YOLO label row: {label_path}")
                    continue
                has_segmentation = has_segmentation or len(fields) > 5
                class_id = int(float(fields[0]))
                counts[names.get(class_id, f"unknown_{class_id}")] += 1
                areas.append(max(0.0, float(fields[3]) * float(fields[4])))
                instance_count += 1
        splits.append(
            SplitReport(
                name=_split_name(split_key),
                image_count=len(images),
                instance_count=instance_count,
                class_counts=dict(counts),
                resolutions=resolutions,
                bbox_area_fractions=areas,
            )
        )
    return RepositoryReport(
        name=root.name,
        root=root,
        format="yolo",
        purpose=_purpose(len(names), has_segmentation),
        splits=splits,
        warnings=warnings,
    )


def analyze_repository(root: Path, annotation_format: str) -> RepositoryReport:
    """Analyze one discovered repository in its detected annotation format."""

    if annotation_format == "coco":
        return _analyze_coco(root)
    if annotation_format == "yolo":
        return _analyze_yolo(root)
    raise ValueError(f"Unsupported annotation format: {annotation_format}")


def analyze_dataset(root: Path) -> DatasetReport:
    """Discover and analyze every supported repository below a dataset root."""

    repositories = [
        analyze_repository(path, annotation_format)
        for path, annotation_format in discover_repositories(root)
    ]
    if not repositories:
        raise ValueError(f"No COCO or YOLO repositories discovered below {root}")
    return DatasetReport(source_root=root, repositories=repositories)
