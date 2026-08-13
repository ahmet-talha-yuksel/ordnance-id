# ADR-007: Provider schema dialect adaptation

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Model providers accept different structured-output schema dialects. Anthropic tool input accepts the
project's full Pydantic-generated JSON Schema, while Gemini accepts an OpenAPI 3.0-style subset and
rejects valid JSON Schema keywords such as `exclusiveMinimum`.

## Decision

Pydantic models remain the single validation contract. The Gemini gateway adapter converts that
canonical schema through an explicit allowlist, inlines references, converts nullable `anyOf`
pairs, preserves property order, and rejects unsupported union shapes. Keywords omitted for Gemini
are logged at debug level. Returned JSON is always validated again with the original Pydantic model,
so constraints omitted from the provider schema remain enforced locally.

Anthropic continues to receive the complete schema and does not use the Gemini adapter.

## Consequences

Provider dialect differences remain inside `gateway/` and do not weaken domain models. A provider
may receive a less expressive generation hint, but invalid output still fails canonical validation
and triggers the configured retry policy. This is a concrete benefit of the `LLMProvider`
abstraction: application and safety layers retain one contract while adapters absorb vendor
differences.

