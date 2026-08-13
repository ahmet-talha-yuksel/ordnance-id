"""Create the FastAPI application and its operational endpoints."""

from typing import Annotated, Any

from fastapi import Depends, FastAPI

from ordnance_id import __version__
from ordnance_id.api.routes.ingest import router as ingest_router
from ordnance_id.config import Settings, get_settings

app = FastAPI(title="ORDNANCE-ID", version=__version__)
app.include_router(ingest_router)


@app.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    """Report service and non-secret configuration health."""

    provider_ready = (
        settings.LLM_PROVIDER == "ollama"
        or settings.LLM_PROVIDER == "anthropic"
        and settings.ANTHROPIC_API_KEY is not None
        or settings.LLM_PROVIDER == "openai"
        and settings.OPENAI_API_KEY is not None
        or settings.LLM_PROVIDER == "gemini"
        and settings.GEMINI_API_KEY is not None
    )
    return {
        "status": "ok" if provider_ready else "degraded",
        "version": __version__,
        "provider": settings.LLM_PROVIDER,
        "config": {"valid": True, "provider_ready": provider_ready},
    }
