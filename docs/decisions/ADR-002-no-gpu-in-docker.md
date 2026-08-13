# ADR-002: No model execution in Docker on macOS

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

The development machine is an Apple-silicon Mac using Metal. Docker Desktop does not expose the
host Metal GPU to Linux containers as a CUDA-compatible accelerator. A containerised model service
would therefore give misleading performance and complicate local development.

## Decision

Docker Compose contains only Postgres 16 and Qdrant. The application and local model runtime run on
the macOS host. `LLMProvider` is the contract between application code and either host-local or
remote inference.

Development on macOS/Metal and deployment on Linux/CUDA are treated as separate environments.
Future Linux deployment may containerise a CUDA-backed model service without changing application
layers outside the provider adapter.

## Consequences

Local acceleration remains available through native tools such as Ollama. Environment-specific
startup and performance testing are required, while the provider contract limits architectural
divergence.

