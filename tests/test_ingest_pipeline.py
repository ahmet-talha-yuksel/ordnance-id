from ordnance_id.ingest.pipeline import ingest_image
from tests.ingest_helpers import image_bytes, settings


def test_rejection_stops_before_sanitized_output() -> None:
    result = ingest_image(image_bytes("dark"), settings=settings())
    assert result.accepted is False
    assert result.sanitized_image is None


def test_accepted_image_is_sanitized() -> None:
    result = ingest_image(image_bytes(), settings=settings())
    assert result.accepted is True
    assert result.sanitized_image is not None
    assert result.ingest_id.startswith("ingest_")

