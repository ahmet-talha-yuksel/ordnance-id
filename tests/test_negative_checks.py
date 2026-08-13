from ordnance_id.evals.builder import Box
from scripts.check_negatives import intersection_area


def test_intersection_detects_partial_and_contained_boxes() -> None:
    annotation = Box(x=10, y=10, width=20, height=20)
    assert intersection_area(Box(x=0, y=0, width=15, height=15), annotation) == 25
    assert intersection_area(Box(x=0, y=0, width=100, height=100), annotation) == 400
    assert intersection_area(Box(x=40, y=40, width=10, height=10), annotation) == 0

