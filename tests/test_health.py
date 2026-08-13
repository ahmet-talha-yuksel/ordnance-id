import httpx

from ordnance_id.api.main import app
from ordnance_id.config import Settings, get_settings


async def test_health_returns_only_safe_configuration() -> None:
    settings = Settings(
        VISION_MODEL="vision-test",
        TEXT_MODEL="text-test",
        FAST_MODEL="fast-test",
        DATABASE_URL="postgresql://localhost/test",
        QDRANT_URL="http://localhost:6333",
        ANTHROPIC_API_KEY="must-not-leak",
        _env_file=None,
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "provider": "anthropic",
        "config": {"valid": True, "provider_ready": True},
    }
    assert "must-not-leak" not in response.text
