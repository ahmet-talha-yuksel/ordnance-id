from io import BytesIO

import piexif
from PIL import Image

from ordnance_id.ingest.exif import extract_metadata, strip_metadata
from ordnance_id.ingest.pipeline import ingest_image
from tests.ingest_helpers import image_bytes, settings


def gps_image() -> bytes:
    exif = {
        "0th": {
            piexif.ImageIFD.Make: "Test Camera",
            piexif.ImageIFD.Model: "Fixture",
        },
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: "N",
            piexif.GPSIFD.GPSLatitude: ((41, 1), (1, 1), (0, 1)),
            piexif.GPSIFD.GPSLongitudeRef: "E",
            piexif.GPSIFD.GPSLongitude: ((29, 1), (2, 1), (0, 1)),
        },
    }
    source = Image.open(BytesIO(image_bytes()))
    output = BytesIO()
    source.save(output, format="JPEG", exif=piexif.dump(exif))
    return output.getvalue()


def test_gps_never_leaks_when_disabled() -> None:
    result = ingest_image(gps_image(), settings=settings(KEEP_EXIF_GPS=False))
    assert result.metadata.gps is None
    assert result.sanitized_image is not None


def test_gps_is_read_only_when_explicitly_enabled() -> None:
    metadata = extract_metadata(gps_image(), settings=settings(KEEP_EXIF_GPS=True))
    assert metadata.gps is not None
    assert round(metadata.gps.latitude, 3) == 41.017


def test_strip_metadata_removes_all_exif() -> None:
    sanitized = strip_metadata(gps_image())
    with Image.open(BytesIO(sanitized)) as image:
        assert len(image.getexif()) == 0

