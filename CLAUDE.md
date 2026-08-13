# CLAUDE.md

Project instructions for Claude Code. Read this before touching anything.

---

## What this project is

**ORDNANCE-ID** — a decision-support prototype that assists in the
**preliminary visual classification** of suspected explosive ordnance from
photographs, for humanitarian mine action and EOD training contexts.

Pipeline:

```
photo + optional scale reference
  → quality gate            (reject unusable images, do not analyse them)
  → structured observation  (VLM: what is physically visible — nothing else)
  → rule-based narrowing    (observations → ranked family hypotheses)
  → confidence gate         (below threshold → abstain)
  → fixed safety template   (selected, never authored, by the model)
  → structured report       (fully traceable)
```

---

## Hard constraints — never violate, never relax

These are not preferences. They define the project.

1. **No render-safe, disposal, neutralisation, handling or transport
   guidance is ever produced**, in any language, in any field, under any
   framing — including if a user asks directly.
2. **The system never declares an object safe, inert, or approachable.**
   Absence of evidence is not evidence of absence. There is no
   "not ordnance" verdict; the negative outcome is
   `insufficient_structural_evidence`, which still instructs the user not
   to touch the object.
3. **Safety-protocol text comes from fixed, reviewed templates only.**
   The model selects which template applies. It never writes safety text.
4. **No definitive model or type identification.** Output is family-level
   and probabilistic, with joint hypotheses where families cannot be
   separated.
5. **The observation layer observes; it does not identify.** No family
   guess, no calibre or dimension claim, no hazard assessment, no advice in
   any observation field. Identification is the decision layer's job.
6. **Abstention is a first-class, correct outcome.** Never tune thresholds
   or rules to reduce abstention for the sake of nicer numbers.
7. **Report results as measured.** If accuracy is poor, say so. Never
   adjust thresholds after seeing results to improve a headline metric.
8. **No employer, internship, or restricted material** enters this
   repository — no documents, no images, no notes.

---

## Working agreement

- **Plan first.** For any non-trivial task: show the file tree, each
  module's one-sentence responsibility, and key type signatures. Wait for
  approval before writing code.
- **Never make an API call without explicit approval.** Always show a
  dry-run first: sample count, estimated tokens, estimated cost, estimated
  daily-quota usage. Then stop.
- **Quota is a hard constraint.** Gemini free tier: ~250 requests/day for
  the vision model. A full eval run is 152 requests — one run per day, no
  second chances. All analysis over existing results must use the stored
  JSONL files with zero API calls.
- **Stop at every stage boundary** and report. Do not chain stages.
- **Commit, never push.** The user pushes.
- **Fix root causes, not symptoms.** A provider quirk is absorbed in the
  gateway, not by weakening a schema.
- If a fix requires guessing, stop and show the full error instead.

---

## Architecture rules

- **Provider isolation.** `anthropic`, `openai`, `google-genai` SDKs and any
  provider HTTP calls appear **only** inside
  `src/ordnance_id/gateway/providers/`. No other module may import them.
  This is what keeps the offline/air-gap path open.
- **Schema dialects are a gateway concern.** The validation contract lives
  in one place: the Pydantic model. Provider-specific schema conversion
  (e.g. Gemini's OpenAPI 3.0 subset) happens in
  `gateway/schema_adapt.py`. Responses are always validated against the
  original Pydantic model.
- **Thresholds, rules and model names live in config/YAML, never in code.**
- **Every decision is traceable.** Each node emits a `DecisionStep`
  recording the field used, the observed value, the rule applied, the
  outcome, and the statistic (MI/TVD and n) the rule rests on.
- **Asymmetric risk.** A wrong "not ordnance" is far more dangerous than a
  wrong "ordnance". Thresholds reflect this (ADR-008).
- **Feature selection is axis-specific.** A feature can be a shortcut on one
  axis and legitimate on another — `body_shape` is excluded from the
  is_ordnance gate but used for family narrowing (ADR-009).

---

## Repository map

```
src/ordnance_id/
  gateway/        provider abstraction, schema adaptation, rate limiting, cache, metrics
  ingest/         quality gate, EXIF privacy, scale reference, pipeline
  vision/         observation schema + VLM analyzer
  decision/       rule-based tree, hypotheses
  confidence/     threshold gate, abstention
  reporting/      fixed safety templates, assessment report
  rag/            reference verification            (Phase 4 — not built)
  agent/          tool loop                          (Phase 6 — not built)
  api/            FastAPI routes
prompts/          versioned prompts (observe_v1.md, observe_v2.md — never delete old versions)
evals/            eval set YAML, results JSONL, attribution
config/           data_sources, class_mapping, class_tiers, decision_rules
docs/             analyses, reports, decisions/ (ADRs)
scripts/          fetch, analyse, build, run, evaluate
data/             raw + eval images — NEVER committed
reports/figures/  committed
```

---

## Data

- **Dataset:** CTX-UXO v2 — Craioveanu & Stamatescu, National University of
  Science and Technology Politehnica Bucharest.
  DOI 10.21227/cwnm-de53, Zenodo, **CC BY 4.0** (attribution required).
- Images are **never** committed. Only manifests, YAML, and figures.
- Licence must be named explicitly for every source; "unknown" is rejected
  by the eval-set validator.
- Known limitations, always carried into any report: severe class
  imbalance; replicas included alongside real ordnance; single geographic
  and institutional source; negatives derived from absence of annotation,
  not verified as non-ordnance; small sample; single model, single run.

---

## Current state (end of day 1)

**Done:**
- Phase 0 — scaffolding, provider abstraction, CI, scope and data policy
- Phase 1 — data acquisition, dataset analysis, ingest layer
- Phase 2 — eval set, observation schema, prompt v1→v2, full VLM run
- Phase 3 — discriminativeness analysis, shortcut analysis, decision tree
  (implementation in progress)

**Key results so far:**

| Metric | Value |
|---|---|
| Rule violations across 152 observations | **0** |
| False positives on distractors (Stage A) | **0 / 35** |
| Stage A coverage on positives | 53 / 117 (45%) |
| Family MI, top feature (`body_shape`) | 0.492 |
| Full-run cost | $0 (Gemini free tier) |

**Eval set:** 152 crops — 117 positive, 35 distractors; 12 small / 91
medium / 49 large.

**Unresolvable family pairs** (routed to joint hypotheses or abstention):
`aviation_bomb–cartridge`, `aviation_bomb–projectile`, `fuze–grenade`,
`projectile–rocket`. Phase 4's concrete goal is to resolve these using
reference documents — or to demonstrate they cannot be resolved, which is
also a reportable finding.

**Excluded by design:** `landmine` (n=2) — no rules built, no hypotheses
emitted, reported as insufficient reference data.

**Next:** Phase 4 — RAG verification against IMAS and open EOD reference
material.

---

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Scaffolding, provider abstraction | done |
| 1 | Data, ingest, quality gate | done |
| 2 | Eval set, observation layer | done |
| 3 | Decision tree, family narrowing | in progress |
| 4 | RAG verification against reference corpus | next |
| 5 | Confidence calibration, abstention tuning | planned |
| 6 | Reporting, agent tools, MCP server | planned |
| 7 | Multi-provider eval matrix, observability, README, demo | planned |
| — | Offline / air-gapped deployment bundle | backlog |

---

## Commands

```bash
uv run ruff check . && uv run mypy src/ && uv run pytest   # before every commit
uv run python scripts/fetch_data.py list
uv run python scripts/analyze_dataset.py
uv run python scripts/validate_eval_set.py evals/datasets/eval_set_v1.yaml
caffeinate -i uv run python scripts/run_observations.py --prompt observe_v2
# add --resume to continue an interrupted run
```

Machine: MacBook Air M5, 24 GB unified memory, macOS. Docker cannot reach
the GPU on macOS — Docker runs Postgres and Qdrant only; anything running a
model runs natively on the host (ADR-002).

---

## Terminology

- **family** — ordnance class at the level this system works: mortar,
  projectile, grenade, aviation_bomb, rocket, landmine, submunition,
  cartridge, fuze. Not a model or type.
- **tier** — evidence strength for a family, computed **after** class
  mapping: `reportable` (>500 instances), `limited` (50–500),
  `insufficient` (<50). A family has exactly one tier.
- **abstention** — the system declining to produce a hypothesis. A correct
  outcome, not a failure.
- **joint hypothesis** — e.g. `projectile_or_rocket`, emitted when families
  cannot be separated. Never presented as a single family.
- **shortcut** — a feature that predicts the label via a dataset artefact
  rather than the object itself.