# ADR-003: Fixed safety-protocol templates

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Generative text can vary, omit warnings, overstate certainty, or produce hazardous instructions.
Safety guidance must remain consistent and reviewable regardless of model or prompt behaviour.

## Decision

Safety-protocol text is selected from fixed, versioned, human-reviewed templates. A model may
produce structured evidence and family-level candidates, but it may not author, rewrite, or extend
the safety protocol. Templates never contain handling, movement, neutralisation, or destruction
instructions and never declare an object safe.

## Consequences

Safety wording is deterministic, testable, and auditable. Template changes require review and a
version change. Model output remains data that reporting renders, not authoritative safety prose.

