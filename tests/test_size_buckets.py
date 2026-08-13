import pytest

from ordnance_id.evals.size_buckets import size_bucket


@pytest.mark.parametrize(
    ("short_edge", "expected"),
    [(149, "small"), (150, "medium"), (600, "medium"), (601, "large")],
)
def test_size_bucket_boundaries(short_edge: int, expected: str) -> None:
    assert size_bucket(short_edge) == expected
