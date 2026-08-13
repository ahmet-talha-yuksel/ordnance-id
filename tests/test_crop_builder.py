import pytest

from ordnance_id.evals.builder import Box, intersection_over_union, padded_bounds


def test_padding_clamps_to_image_boundaries() -> None:
    result = padded_bounds(Box(x=0, y=5, width=100, height=100), (120, 120))
    assert result.x == 0
    assert result.y == 0
    assert result.width == pytest.approx(115)
    assert result.height == pytest.approx(120)


def test_iou_rejects_overlap_and_accepts_separation() -> None:
    annotation = Box(x=10, y=10, width=100, height=100)
    assert intersection_over_union(annotation, Box(x=20, y=20, width=100, height=100)) > 0.02
    assert intersection_over_union(annotation, Box(x=200, y=200, width=20, height=20)) == 0
