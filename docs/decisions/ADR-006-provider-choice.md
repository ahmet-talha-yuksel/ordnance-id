# ADR-006: Gemini free tier for initial observation evaluation

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Phase 2 needs an initial measurement of structured visual-observation behavior across the public
evaluation crops. The gateway already isolates provider details, so this measurement does not need
to establish a permanent model dependency. Avoiding API cost makes repeatable pilot and full-set
evaluation practical while the observation prompt is still changing.

Google states that content submitted through unpaid Gemini API services may be used to improve its
products, including machine-learning technologies. Therefore free-tier processing is inappropriate
for sensitive field imagery, private operational records, precise locations, or restricted data.

## Decision

Initial Phase 2 evaluation uses the Gemini API free tier and only the public CTX-UXO material
published under CC BY 4.0. The Gemini adapter uses native structured output and remains behind the
unchanged `LLMProvider` contract. Anthropic remains available for later comparison, and the Ollama
path remains available for host-local processing.

## Consequences

Evaluation requests have zero billed API cost while remaining subject to free-tier RPM and daily
quotas. Request, token, latency, retry, cache, and HTTP 429 metrics are recorded. No sensitive or
new field data may be sent through the free tier. Sensitive-data deployments must use a suitably
contracted service or a local model, which is why provider abstraction and the offline path remain
architectural requirements.

