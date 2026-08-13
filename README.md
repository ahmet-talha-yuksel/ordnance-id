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

## Status

**Phase 0 — project scaffolding and architectural boundaries.** No identification workflow is
implemented or operationally validated.

## Documentation

- [Scope and safety limits](docs/SCOPE_LIMITS.md)
- [Architecture](docs/architecture.md)
- [Data sources and provenance](docs/DATA_SOURCES.md)
- [ADR-001: Provider abstraction](docs/decisions/ADR-001-provider-abstraction.md)
- [ADR-002: No GPU model execution in Docker](docs/decisions/ADR-002-no-gpu-in-docker.md)
- [ADR-003: Fixed safety templates](docs/decisions/ADR-003-fixed-safety-templates.md)
