# ADR-009: Axis-specific feature selection

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

The observation pipeline supports two different prediction axes: an `is_ordnance` gate and
positive-family narrowing. A feature can correlate with dataset construction on the first axis yet
encode physically meaningful variation on the second. A single global shortcut label would discard
useful family evidence or admit unsafe object/background evidence.

In eval set v1, `body_shape` has positive/negative TVD 0.692 and negatives concentrate at
`unclear` (26/35), making it suspect for the `is_ordnance` gate. Among positives, however, it has
family MI 0.4920 nats and physically structured concentrations: projectile is 68.4% cylindrical,
mortar is 68.4% ogive, grenade is 42.1% irregular, and fuze is 57.1% irregular.

## Decision

Feature selection is performed independently for each prediction axis.

- Stage A (`is_ordnance`) rejects `body_shape`, `surface_condition`, and `looks_manufactured` as
  shortcut-suspect. It accepts only positive structural-component cues and otherwise abstains.
- Stage B (family narrowing) accepts `body_shape` because its positive-family distribution has a
  physically defensible geometric interpretation. It continues to reject `surface_condition` as a
  suspected family-axis dataset effect.
- Every feature table and decision node records the axis, metric, sample size, and abstention rule.
- A feature rejected on one axis is not implicitly rejected on another; reuse requires separate
  evidence and an explicit decision.

## Consequences

The decision tree cannot use one global feature allowlist. Stage-specific configuration and tests
must prevent Stage B-only features from leaking into the `is_ordnance` gate. The object gate remains
deliberately incomplete and confidence/abstention-based. Family narrowing gains geometric signal:
adding `body_shape` resolves 5 of 9 previously unresolved reportable/limited family pairs at the
descriptive TVD ≥ 0.50 threshold, while the remaining 4 still abstain.

These results describe this eval set; they are not identification-accuracy or causal claims.
