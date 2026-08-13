"""Parse traceable crop provenance stored in evaluation sample notes."""

import ast
import re

from ordnance_id.evals.builder import Box

SOURCE_IMAGE_PATTERN = re.compile(r"(?:^|; )source_image=([^;]+)")
BBOX_PATTERN = re.compile(r"(?:original|sampled)_bbox_xywh=(\{[^}]+\})")
SOURCE_CLASS_PATTERN = re.compile(r"(?:^|; )source_class=([^;]+)")


def source_image_from_notes(notes: str | None) -> str:
    """Return the source filename embedded by the crop builder."""

    match = SOURCE_IMAGE_PATTERN.search(notes or "")
    if match is None:
        raise ValueError("Eval sample notes do not contain source_image provenance")
    return match.group(1)


def source_class_from_notes(notes: str | None) -> str | None:
    """Return the original dataset class for a positive crop, when present."""

    match = SOURCE_CLASS_PATTERN.search(notes or "")
    return match.group(1) if match else None


def bbox_from_notes(notes: str | None) -> Box:
    """Return the original or sampled absolute crop box from notes."""

    match = BBOX_PATTERN.search(notes or "")
    if match is None:
        raise ValueError("Eval sample notes do not contain bbox provenance")
    value = ast.literal_eval(match.group(1))
    if not isinstance(value, dict):
        raise ValueError("Invalid bbox provenance")
    return Box.model_validate(value)

