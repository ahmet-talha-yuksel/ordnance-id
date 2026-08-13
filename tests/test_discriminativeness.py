from collections import Counter

import pytest

from ordnance_id.evals.discriminativeness import (
    interval_overlap,
    mutual_information,
    total_variation,
)


def test_mutual_information_zero_for_constant_feature() -> None:
    assert mutual_information(["x", "x", "x", "x"], ["a", "a", "b", "b"]) == 0


def test_mutual_information_positive_for_perfect_partition() -> None:
    assert mutual_information(["x", "x", "y", "y"], ["a", "a", "b", "b"]) == pytest.approx(
        0.693147, rel=1e-5
    )


def test_mutual_information_treats_none_as_a_category() -> None:
    assert mutual_information([None, None, "seen", "seen"], ["a", "a", "b", "b"]) > 0


def test_total_variation_and_iqr_overlap_bounds() -> None:
    assert total_variation(Counter({"x": 2}), Counter({"y": 3})) == 1
    assert interval_overlap((1, 3), (2, 4)) == pytest.approx(1 / 3)
    assert interval_overlap((1, 2), (3, 4)) == 0
