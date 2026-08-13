import pytest

from ordnance_id.ingest.quality import assess_quality
from tests.ingest_helpers import image_bytes, settings


def test_accepts_clear_well_lit_image() -> None:
    report = assess_quality(image_bytes(), settings=settings())
    assert report.is_acceptable is True
    assert report.rejection_reasons == []


@pytest.mark.parametrize(
    ("kind", "width", "height", "reason"),
    [
        ("blurred", 800, 600, "bulanık"),
        ("dark", 800, 600, "Aydınlatma"),
        ("noise", 320, 240, "Çözünürlük"),
    ],
)
def test_rejects_inadequate_images(kind: str, width: int, height: int, reason: str) -> None:
    report = assess_quality(
        image_bytes(kind, width, height),
        settings=settings(),
    )
    assert report.is_acceptable is False
    assert any(reason in value for value in report.rejection_reasons)
    assert report.recommendations


def test_invalid_bytes_fail_closed() -> None:
    with pytest.raises(ValueError, match="cannot be decoded"):
        assess_quality(b"not an image", settings=settings())

