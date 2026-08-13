"""Read minimal image metadata while suppressing location by default."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, cast

from PIL import ExifTags, Image
from pydantic import BaseModel

from ordnance_id.config import Settings, get_settings


class GpsCoordinates(BaseModel):
    """Represent optional decimal coordinates retained only by explicit policy."""

    latitude: float
    longitude: float


class ImageMetadata(BaseModel):
    """Contain non-sensitive image properties and policy-controlled coordinates."""

    captured_at: datetime | None
    camera_make: str | None
    camera_model: str | None
    width: int
    height: int
    orientation: int | None
    gps: GpsCoordinates | None = None


def _rational(value: Any) -> float:
    return float(value)


def _coordinate(values: object, reference: object) -> float | None:
    if not isinstance(values, (tuple, list)) or len(values) != 3:
        return None
    degrees, minutes, seconds = (_rational(item) for item in values)
    coordinate = degrees + minutes / 60.0 + seconds / 3600.0
    if str(reference).upper() in {"S", "W"}:
        coordinate *= -1
    return coordinate


def _gps(gps_value: object) -> GpsCoordinates | None:
    if not isinstance(gps_value, dict):
        return None
    gps = cast(dict[int, Any], gps_value)
    latitude = _coordinate(gps.get(2), gps.get(1))
    longitude = _coordinate(gps.get(4), gps.get(3))
    if latitude is None or longitude is None:
        return None
    return GpsCoordinates(latitude=latitude, longitude=longitude)


def extract_metadata(
    image_bytes: bytes, *, settings: Settings | None = None
) -> ImageMetadata:
    """Read metadata and omit GPS unless the privacy setting explicitly permits it."""

    active_settings = settings or get_settings()
    with Image.open(BytesIO(image_bytes)) as image:
        exif_object = image.getexif()
        exif = dict(exif_object)
        captured_raw = exif.get(ExifTags.Base.DateTimeOriginal) or exif.get(ExifTags.Base.DateTime)
        captured_at = None
        if captured_raw:
            try:
                captured_at = datetime.strptime(str(captured_raw), "%Y:%m:%d %H:%M:%S")
            except ValueError:
                captured_at = None
        return ImageMetadata(
            captured_at=captured_at,
            camera_make=str(exif[ExifTags.Base.Make]).strip()
            if ExifTags.Base.Make in exif
            else None,
            camera_model=str(exif[ExifTags.Base.Model]).strip()
            if ExifTags.Base.Model in exif
            else None,
            width=image.width,
            height=image.height,
            orientation=int(exif[ExifTags.Base.Orientation])
            if ExifTags.Base.Orientation in exif
            else None,
            gps=_gps(exif_object.get_ifd(ExifTags.Base.GPSInfo))
            if active_settings.KEEP_EXIF_GPS and ExifTags.Base.GPSInfo in exif
            else None,
        )


def strip_metadata(image_bytes: bytes) -> bytes:
    """Re-encode pixels without EXIF before storage or model access."""

    source = BytesIO(image_bytes)
    output = BytesIO()
    with Image.open(source) as image:
        image.load()
        image_format = image.format or "PNG"
        clean = Image.new(image.mode, image.size)
        clean.paste(image)
        if image_format.upper() == "JPEG" and clean.mode not in {"L", "RGB", "CMYK"}:
            clean = clean.convert("RGB")
        clean.save(output, format=image_format)
    return output.getvalue()
