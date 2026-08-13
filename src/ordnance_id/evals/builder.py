"""Build bounded, balanced eval sets from detected CTX-UXO test annotations."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, cast, get_args

import yaml

from ordnance_id.data_analysis.discovery import IMAGE_SUFFIXES, discover_repositories
from ordnance_id.data_sources import DataSource, ManifestEntry
from ordnance_id.evals.schema import EvalSample, EvalSet, GroundTruth, OrdnanceFamily


class Candidate:
    """Represent one source image and its source-class label."""

    def __init__(self, image: Path, source_class: str) -> None:
        self.image = image
        self.source_class = source_class


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


def _find_image(annotation_root: Path, filename: str) -> Path:
    direct = annotation_root / filename
    if direct.exists():
        return direct
    matches = list(annotation_root.parent.rglob(Path(filename).name))
    if len(matches) != 1:
        raise ValueError(f"Could not uniquely resolve annotated image {filename!r}")
    return matches[0]


def _coco_candidates(annotation_root: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    test_files = [path for path in annotation_root.glob("*.json") if "test" in path.stem.lower()]
    for annotation_file in test_files:
        data = cast(dict[str, Any], json.loads(annotation_file.read_text(encoding="utf-8")))
        categories = {
            int(item["id"]): str(item["name"])
            for item in cast(list[dict[str, Any]], data.get("categories", []))
        }
        images = {
            int(item["id"]): str(item["file_name"])
            for item in cast(list[dict[str, Any]], data.get("images", []))
        }
        labels: dict[int, set[str]] = defaultdict(set)
        for annotation in cast(list[dict[str, Any]], data.get("annotations", [])):
            labels[int(annotation["image_id"])].add(categories[int(annotation["category_id"])])
        for image_id, filename in images.items():
            image_labels = labels[image_id]
            if len(image_labels) != 1:
                continue
            candidates.append(Candidate(_find_image(annotation_root, filename), image_labels.pop()))
    return candidates


def _yolo_candidates(annotation_root: Path) -> list[Candidate]:
    yaml_files = [*annotation_root.glob("*.yaml"), *annotation_root.glob("*.yml")]
    config_path = next(path for path in yaml_files if "names" in yaml.safe_load(path.read_text()))
    config = cast(dict[str, Any], yaml.safe_load(config_path.read_text(encoding="utf-8")))
    names_value = config["names"]
    names = (
        {index: str(name) for index, name in enumerate(names_value)}
        if isinstance(names_value, list)
        else {int(index): str(name) for index, name in names_value.items()}
    )
    configured = config.get("test")
    if configured is None:
        return []
    base = Path(str(config.get("path", ".")))
    if not base.is_absolute():
        base = (annotation_root / base).resolve()
    image_root = Path(str(configured))
    if not image_root.is_absolute():
        image_root = (base / image_root).resolve()
    if not image_root.exists():
        alternatives = [
            path
            for path in annotation_root.parent.rglob("images")
            if path.is_dir()
            and "test" in path.parts
            and any(item.suffix.lower() in IMAGE_SUFFIXES for item in path.iterdir())
        ]
        if len(alternatives) != 1:
            raise ValueError("Could not uniquely resolve the YOLO test image directory")
        image_root = alternatives[0]
    images = [path for path in image_root.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES]
    candidates: list[Candidate] = []
    for image in images:
        label = annotation_root / "test" / "labels" / f"{image.stem}.txt"
        class_ids = {
            int(float(line.split()[0]))
            for line in label.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if len(class_ids) != 1:
            continue
        candidates.append(Candidate(image, names[class_ids.pop()]))
    return candidates


def collect_test_candidates(dataset_root: Path) -> list[Candidate]:
    """Collect labeled images only from discovered test splits."""

    for root, annotation_format in discover_repositories(dataset_root):
        candidates = (
            _coco_candidates(root) if annotation_format == "coco" else _yolo_candidates(root)
        )
        if candidates:
            return candidates
    raise ValueError(f"No test-split samples found below {dataset_root}")


def build_eval_set(
    candidates: list[Candidate],
    mapping: dict[str, OrdnanceFamily],
    source: DataSource,
    manifest: ManifestEntry,
    output_images: Path,
    *,
    max_per_class: int,
) -> EvalSet:
    """Select a deterministic class-balanced subset and copy its images."""

    missing = sorted({candidate.source_class for candidate in candidates} - mapping.keys())
    if missing:
        raise ValueError(
            "Unmapped source classes: " + ", ".join(missing) + ". Update config/class_mapping.yaml."
        )
    selected_per_family: defaultdict[OrdnanceFamily, int] = defaultdict(int)
    samples: list[EvalSample] = []
    output_images.mkdir(parents=True, exist_ok=True)
    for candidate in sorted(candidates, key=lambda item: str(item.image)):
        family = mapping[candidate.source_class]
        if selected_per_family[family] >= max_per_class:
            continue
        selected_per_family[family] += 1
        sample_id = f"eval_{len(samples) + 1:03d}"
        destination_name = f"{sample_id}{candidate.image.suffix.lower()}"
        shutil.copy2(candidate.image, output_images / destination_name)
        samples.append(
            EvalSample(
                id=sample_id,
                filename=destination_name,
                source_url=str(source.landing_page),
                license=source.license,
                attribution=f"{source.title} — {', '.join(source.authors)} — DOI {source.doi}",
                retrieved=manifest.downloaded_at.date(),
                ground_truth=GroundTruth(
                    is_ordnance=True,
                    family=family,
                    confidence_of_label="high",
                ),
                notes=f"Source class: {candidate.source_class}; no manual relabeling.",
            )
        )
    return EvalSet(
        version=date.today().isoformat(),
        description=(
            "Balanced CTX-UXO test-split subset; source labels retained without relabeling."
        ),
        samples=samples,
    )
