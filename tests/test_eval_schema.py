from datetime import date

import pytest
from pydantic import ValidationError

from ordnance_id.evals.schema import EvalSample, EvalSet, GroundTruth


def valid_sample(**overrides: object) -> EvalSample:
    values: dict[str, object] = {
        "id": "eval_001",
        "filename": "eval_001.jpg",
        "source_url": "https://example.test/source",
        "license": "CC BY 4.0",
        "attribution": "Example Author",
        "retrieved": date(2026, 8, 13),
        "ground_truth": GroundTruth(
            is_ordnance=True,
            family="mortar",
            confidence_of_label="high",
        ),
    }
    values.update(overrides)
    return EvalSample.model_validate(values)


@pytest.mark.parametrize("license_name", ["", "unknown", "UNKNOWN", "n/a", " N/A "])
def test_rejects_unknown_licenses(license_name: str) -> None:
    with pytest.raises(ValidationError, match="verified license"):
        valid_sample(license=license_name)


@pytest.mark.parametrize(
    "values",
    [
        {"is_ordnance": True, "family": "not_ordnance", "confidence_of_label": "high"},
        {"is_ordnance": False, "family": "mortar", "confidence_of_label": "high"},
        {"is_ordnance": True, "family": "mortar", "confidence_of_label": "medium"},
        {"is_ordnance": True, "family": "indeterminate", "confidence_of_label": "high"},
    ],
)
def test_rejects_inconsistent_ground_truth(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        GroundTruth.model_validate(values)


def test_accepts_explained_low_confidence_label() -> None:
    truth = GroundTruth(
        is_ordnance=False,
        family="indeterminate",
        confidence_of_label="low",
        label_rationale="Image does not permit a reliable ordnance decision.",
    )
    assert truth.family == "indeterminate"


@pytest.mark.parametrize("duplicate_field", ["id", "filename"])
def test_eval_set_rejects_duplicate_identifiers(duplicate_field: str) -> None:
    first = valid_sample()
    overrides: dict[str, object] = {"id": "eval_002", "filename": "eval_002.jpg"}
    overrides[duplicate_field] = getattr(first, duplicate_field)
    second = valid_sample(**overrides)

    with pytest.raises(ValidationError, match="must be unique"):
        EvalSet(version="1", description="Fixture", samples=[first, second])


def test_rejects_invalid_eval_id() -> None:
    with pytest.raises(ValidationError):
        valid_sample(id="sample-1")
