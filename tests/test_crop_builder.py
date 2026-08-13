import pytest

from ordnance_id.evals.builder import (
    Box,
    intersection_over_union,
    is_strictly_disjoint,
    padded_bounds,
)


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


@pytest.mark.parametrize(
    ("dirty_candidate", "annotation"),
    [
        (
            Box(x=2019, y=571, width=303, height=125),
            Box(x=2165.93576, y=154.062036, width=734.06192, height=1395.625464),
        ),
        (
            Box(x=1236, y=293, width=771, height=348),
            Box(x=1785.31192, y=579.99942, width=1585.93808, height=806.56308),
        ),
    ],
    ids=["UXOs_3487", "UXOs_3320"],
)
def test_known_contaminated_negatives_fail_strict_rule(
    dirty_candidate: Box, annotation: Box
) -> None:
    assert is_strictly_disjoint(dirty_candidate, [annotation], margin=8) is False


def test_negative_requires_eight_pixel_clearance() -> None:
    annotation = Box(x=100, y=100, width=50, height=50)
    assert is_strictly_disjoint(Box(x=50, y=100, width=42, height=20), [annotation]) is True
    assert is_strictly_disjoint(Box(x=50, y=100, width=43, height=20), [annotation]) is False
