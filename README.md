# ORDNANCE-ID

> **WARNING: This is a research prototype and is not validated for operational use. It does not
> provide handling, movement, disarming, neutralisation, or destruction instructions and never
> declares an object safe. Do not approach or interact with suspected ordnance. Decisions require
> appropriately qualified personnel. Read the [scope and safety limits](docs/SCOPE_LIMITS.md).**

ORDNANCE-ID explores photograph-based decision support for unexploded-ordnance identification in
humanitarian mine-action and EOD training contexts. It is designed to suggest probabilistic
ordnance-family candidates, present traceable evidence, and abstain when image quality or
confidence is inadequate—not to claim an exact model or type.

## Approach

```text
image -> quality gate -> visual evidence -> verified retrieval
      -> family-level decision -> confidence/abstention -> fixed safety template
```

Provider-specific model access is isolated behind one gateway so research can begin with a cloud
model and later move to host-local, offline, or air-gapped inference. During macOS development,
only Postgres and Qdrant run in Docker; model execution stays on the host.

## Setup

Requirements: Python 3.11, [uv](https://docs.astral.sh/uv/), and Docker Compose for optional data
services.

```bash
cp .env.example .env
uv sync
docker compose up -d
uv run uvicorn --app-dir src ordnance_id.api.main:app --reload
```

Fill the required model names, database URLs, and the selected provider's credentials in `.env`.
Ollama defaults to `http://localhost:11434`. Raw data and model weights are intentionally excluded
from Git.

Run the quality checks with:

```bash
uv run ruff check .
uv run mypy src/
uv run pytest
```

## Data and evaluation tooling

CTX-UXO v2 is used only as licensed evaluation data; this project does not train on it. The source
is **CTX-UXO: A Comprehensive Dataset for Detection and Identification of UneXploded Ordnances**,
by Gheorghe Marian Craioveanu and Grigore Stamatescu, DOI
[`10.21227/cwnm-de53`](https://doi.org/10.21227/cwnm-de53), licensed CC BY 4.0. The source contains
real ordnance and replicas, which is a documented limitation.

```bash
PYTHONPATH=src uv run python scripts/fetch_data.py list
PYTHONPATH=src uv run python scripts/fetch_data.py download ctx-uxo-v2
PYTHONPATH=src uv run python scripts/analyze_dataset.py
PYTHONPATH=src uv run python scripts/build_eval_set.py --max-per-class 25
PYTHONPATH=src uv run python scripts/validate_eval_set.py
```

The `/ingest` endpoint accepts bounded JPEG, PNG, or WebP uploads. It returns HTTP 200 with
`accepted=false` when image quality is inadequate; rejected images are not forwarded. GPS is
suppressed by default and accepted images are stripped of EXIF before downstream use.

## Status

**Phase 1 — data & ingest.** Licensed acquisition, descriptive dataset analysis, evaluation-set
validation, and the image-quality gate are implemented. No identification workflow is implemented
or operationally validated.

## Documentation

- [Scope and safety limits](docs/SCOPE_LIMITS.md)
- [Architecture](docs/architecture.md)
- [Data sources and provenance](docs/DATA_SOURCES.md)
- [ADR-001: Provider abstraction](docs/decisions/ADR-001-provider-abstraction.md)
- [ADR-002: No GPU model execution in Docker](docs/decisions/ADR-002-no-gpu-in-docker.md)
- [ADR-003: Fixed safety templates](docs/decisions/ADR-003-fixed-safety-templates.md)
- [ADR-004: EXIF privacy by default](docs/decisions/ADR-004-exif-privacy.md)
- [ADR-005: No project-specific training](docs/decisions/ADR-005-no-training.md)
- [ADR-006: Gemini free tier for initial evaluation](docs/decisions/ADR-006-provider-choice.md)
