from collections import Counter

import pytest

from scripts.observation_report import total_variation


def test_total_variation_is_zero_for_identical_distributions() -> None:
    assert total_variation(Counter({True: 3, False: 1}), Counter({True: 6, False: 2})) == 0


def test_total_variation_is_one_for_disjoint_distributions() -> None:
    assert total_variation(Counter({True: 4}), Counter({False: 3})) == pytest.approx(1.0)
