import pytest
from pydantic import ValidationError

from ordnance_id.vision.schema import OrdnanceObservation


def observation_values() -> dict[str, object]:
    return {
        "body_shape": "cylindrical",
        "fins_or_tail_visible": None,
        "fuze_visible": False,
        "driving_band_visible": None,
        "markings_visible": False,
        "markings_text": None,
        "color_bands": [],
        "surface_condition": "weathered",
        "embedded_in_ground": False,
        "estimated_length_cm": None,
        "length_to_width_ratio": 3.2,
        "looks_manufactured": True,
        "image_quality_sufficient": True,
        "unclear_features": [],
        "observation_notes": "Elongated weathered metal object.",
    }


def test_unknown_nullable_features_are_explicit() -> None:
    observation = OrdnanceObservation.model_validate(observation_values())
    assert any(item.startswith("fins_or_tail_visible:") for item in observation.unclear_features)
    assert any(item.startswith("driving_band_visible:") for item in observation.unclear_features)


def test_identification_fields_are_forbidden() -> None:
    values = observation_values()
    values["family"] = "projectile"
    with pytest.raises(ValidationError, match="Extra inputs"):
        OrdnanceObservation.model_validate(values)
