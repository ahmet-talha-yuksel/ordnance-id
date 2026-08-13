# ADR-001: Provider abstraction

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Early research benefits from capable hosted multimodal models, while humanitarian deployments may
require offline or air-gapped operation. Coupling workflow code to one vendor would make that
transition expensive and could spread credential handling throughout the system.

## Decision

All model access crosses the asynchronous `LLMProvider` protocol. Provider SDK imports and HTTP
calls are permitted only in `gateway/providers/`. The protocol supports text, schema-validated
responses, and base64 images with explicit media types from the outset. Phase 0 implements
Anthropic and Ollama adapters; the OpenAI setting is reserved for a future adapter.

## Consequences

The project can begin with a cloud provider while preserving a route to local, offline, or
air-gapped inference. Provider capabilities must be normalised by adapters, and contract tests
must protect the boundary.

