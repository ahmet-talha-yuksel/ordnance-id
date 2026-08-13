"""Adapt canonical Pydantic schemas to provider-specific accepted dialects."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)

GEMINI_SCHEMA_KEYS = frozenset(
    {
        "type",
        "format",
        "description",
        "nullable",
        "enum",
        "items",
        "properties",
        "required",
        "minItems",
        "maxItems",
        "minimum",
        "maximum",
        "propertyOrdering",
    }
)


def to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert Pydantic JSON Schema to Gemini's supported OpenAPI-style subset."""

    source = model.model_json_schema()
    definitions = source.get("$defs", {})
    if not isinstance(definitions, dict):
        raise ValueError("Pydantic $defs must be an object")

    def resolve_reference(reference: str, reference_stack: tuple[str, ...]) -> dict[str, Any]:
        prefix = "#/$defs/"
        if not reference.startswith(prefix):
            raise ValueError(f"Unsupported schema reference: {reference}")
        name = reference.removeprefix(prefix)
        if name in reference_stack:
            chain = " -> ".join((*reference_stack, name))
            raise ValueError(f"Cyclic schema reference detected: {chain}")
        target = definitions.get(name)
        if not isinstance(target, dict):
            raise ValueError(f"Unresolved schema reference: {reference}")
        return adapt(target, ("$defs", name), (*reference_stack, name))

    def adapt(
        node: dict[str, Any], path: tuple[str, ...], reference_stack: tuple[str, ...]
    ) -> dict[str, Any]:
        if "$ref" in node:
            reference = node["$ref"]
            if not isinstance(reference, str):
                raise ValueError(f"Schema reference at {'.'.join(path)} must be a string")
            resolved = resolve_reference(reference, reference_stack)
            siblings = {key: value for key, value in node.items() if key != "$ref"}
            if siblings:
                resolved.update(adapt(siblings, path, reference_stack))
            return resolved

        if "anyOf" in node:
            variants = node["anyOf"]
            if not isinstance(variants, list) or len(variants) != 2:
                raise ValueError(f"Unsupported anyOf at {'.'.join(path)}: expected nullable pair")
            null_variants = [
                item for item in variants if isinstance(item, dict) and item.get("type") == "null"
            ]
            non_null = [item for item in variants if item not in null_variants]
            if len(null_variants) != 1 or len(non_null) != 1 or not isinstance(non_null[0], dict):
                raise ValueError(f"Unsupported anyOf at {'.'.join(path)}: expected X | null")
            combined = dict(non_null[0])
            combined.update({key: value for key, value in node.items() if key != "anyOf"})
            nullable_result = adapt(combined, path, reference_stack)
            nullable_result["nullable"] = True
            return nullable_result

        result: dict[str, Any] = {}
        for key, value in node.items():
            if key not in GEMINI_SCHEMA_KEYS:
                LOGGER.debug("Dropping unsupported Gemini schema key %s at %s", key, ".".join(path))
                continue
            if key == "properties":
                if not isinstance(value, dict):
                    raise ValueError(f"properties at {'.'.join(path)} must be an object")
                result[key] = {
                    field_name: adapt(
                        field_schema, (*path, "properties", field_name), reference_stack
                    )
                    for field_name, field_schema in value.items()
                    if isinstance(field_schema, dict)
                }
                result["propertyOrdering"] = list(value.keys())
            elif key == "items":
                if not isinstance(value, dict):
                    raise ValueError(f"items at {'.'.join(path)} must be an object")
                result[key] = adapt(value, (*path, "items"), reference_stack)
            else:
                result[key] = value
        return result

    return adapt(source, (model.__name__,), ())
