# Architecture

## Target flow

```text
Photograph + metadata
         |
         v
      Ingest ---------> quality failure ---------> abstain
         |
         v
       Vision -------- observable evidence
         |
         +-----------> RAG <---------- verified references / Qdrant
         |              |
         v              v
       Decision <---- LLMProvider ---- cloud or host-local model
         |
         v
      Confidence ------ below threshold ----------> abstain
         |
         v
      Reporting ------- fixed safety template
         |
         v
 API response + trace record (Postgres)
```

## Layer responsibilities

- **API:** Validates transport-level requests and exposes results without leaking secrets.
- **Agent:** Coordinates the workflow; it does not contain provider-specific code.
- **Ingest:** Validates input formats, strips GPS by default, and applies initial quality checks.
- **Vision:** Extracts observable attributes without asserting an exact ordnance identity.
- **RAG:** Retrieves traceable evidence only from reviewed sources.
- **Decision:** Produces probabilistic family-level candidates from evidence and context.
- **Confidence:** Enforces quality and confidence gates and owns abstention decisions.
- **Reporting:** Combines results with reviewed, fixed safety text.
- **Gateway:** Isolates all provider SDK and HTTP details behind `LLMProvider`.
- **Postgres/Qdrant:** Store trace records and searchable references respectively; neither runs a
  model.

The application and all model execution run on the host during macOS development. Docker Compose
contains only Postgres and Qdrant.

