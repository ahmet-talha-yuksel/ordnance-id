import pytest
from pydantic import ValidationError

from ordnance_id.ingest.scale import ScaleReference, estimate_dimensions


def test_no_scale_returns_none_without_guessing() -> None:
    assert estimate_dimensions((100, 50), ScaleReference()) is None


def test_manual_scale_returns_uncertainty_interval() -> None:
    scale = ScaleReference(reference_type="ruler", known_dimension_mm=100, pixels_per_mm=2)
    estimate = estimate_dimensions((200, 100), scale)
    assert estimate is not None
    assert estimate.width_mm_min == 95
    assert estimate.width_mm_max == 105


def test_none_reference_rejects_scale_values() -> None:
    with pytest.raises(ValidationError):
        ScaleReference(reference_type="none", pixels_per_mm=2)

