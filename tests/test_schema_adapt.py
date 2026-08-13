from typing import Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field

from ordnance_id.gateway.schema_adapt import GEMINI_SCHEMA_KEYS, to_gemini_schema
from ordnance_id.vision.schema import OrdnanceObservation


class NestedDetail(BaseModel):
    label: str


class NestedContainer(BaseModel):
    detail: NestedDetail
    mode: Literal["visible", "unclear"]


def _assert_only_allowed_keys(schema: dict[str, object]) -> None:
    assert set(schema) <= GEMINI_SCHEMA_KEYS
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for value in properties.values():
            assert isinstance(value, dict)
            _assert_only_allowed_keys(value)
    items = schema.get("items")
    if isinstance(items, dict):
        _assert_only_allowed_keys(items)


def test_observation_schema_removes_unsupported_keywords_and_converts_nullable() -> None:
    schema = to_gemini_schema(OrdnanceObservation)
    serialized = repr(schema)
    for forbidden in (
        "exclusiveMinimum",
        "$ref",
        "$defs",
        "anyOf",
        "default",
        "additionalProperties",
    ):
        assert forbidden not in serialized
    length = schema["properties"]["estimated_length_cm"]
    assert length["type"] == "number"
    assert length["nullable"] is True


def test_nested_models_are_inlined_literals_remain_enums_and_order_is_preserved() -> None:
    schema = to_gemini_schema(NestedContainer)
    detail = schema["properties"]["detail"]
    assert detail["properties"]["label"]["type"] == "string"
    assert schema["properties"]["mode"]["enum"] == ["visible", "unclear"]
    assert schema["propertyOrdering"] == ["detail", "mode"]


def test_unexpected_anyof_raises() -> None:
    class UnsupportedUnion(BaseModel):
        value: int | str

    with pytest.raises(ValueError, match="Unsupported anyOf"):
        to_gemini_schema(UnsupportedUnion)


def test_every_nested_schema_key_is_allowlisted() -> None:
    _assert_only_allowed_keys(to_gemini_schema(OrdnanceObservation))


def test_original_pydantic_constraints_remain_strict() -> None:
    class PositiveValue(BaseModel):
        model_config = ConfigDict(extra="forbid")
        value: float = Field(gt=0)

    schema = to_gemini_schema(PositiveValue)
    assert "exclusiveMinimum" not in repr(schema)
    with pytest.raises(ValueError):
        PositiveValue.model_validate({"value": 0})
