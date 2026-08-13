# ADR-005: No project-specific model training

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

CTX-UXO has serious class imbalance: common projectile, mortar, and grenade instances greatly
outnumber rare classes. It also combines real objects and replicas from one institutional and
geographic source. Training a project-specific classifier on that evidence could encode dataset
bias while presenting unjustified precision in a safety-critical context.

## Decision

ORDNANCE-ID does not train a model. The target approach combines a provider-neutral multimodal VLM
for structured observable evidence, retrieval from verified references, a rule-based decision tree,
and explicit confidence/abstention gates. Evaluation uses a bounded test-split subset plus licensed
distractor samples; it does not turn the test split into training data.

## Consequences

The system prioritizes traceable evidence, explainable rules, provider portability, and measured
abstention over benchmark optimization. VLM limitations and domain shift still require evaluation.
Future training would require a new ADR, representative licensed data, leakage controls, and a
separate safety-validation case.

