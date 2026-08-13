import httpx

from ordnance_id.api.main import app
from ordnance_id.config import get_settings
from tests.ingest_helpers import image_bytes, settings


async def post_image(content: bytes, media_type: str) -> httpx.Response:
    app.dependency_overrides[get_settings] = lambda: settings()
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/ingest",
                files={"image": ("fixture.jpg", content, media_type)},
            )
    finally:
        app.dependency_overrides.clear()


async def test_ingest_accepts_valid_image_without_returning_bytes() -> None:
    response = await post_image(image_bytes(), "image/jpeg")
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["ingest_id"].startswith("ingest_")
    assert "sanitized_image" not in response.json()


async def test_ingest_returns_200_for_quality_rejection() -> None:
    response = await post_image(image_bytes("dark"), "image/jpeg")
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert response.json()["quality"]["rejection_reasons"]


async def test_ingest_rejects_unsupported_media_type() -> None:
    response = await post_image(b"plain text", "text/plain")
    assert response.status_code == 415
