"""Derive evaluation size slices from crop short-edge dimensions."""

from typing import Literal

SizeBucket = Literal["small", "medium", "large"]


def size_bucket(short_edge_px: int) -> SizeBucket:
    """Map a crop short edge to the shared reporting bucket definition."""

    if short_edge_px < 150:
        return "small"
    if short_edge_px <= 600:
        return "medium"
    return "large"

