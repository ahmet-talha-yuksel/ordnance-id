"""Stop rejected images before sanitization and downstream analysis."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from ordnance_id.config import Settings, get_settings
from ordnance_id.ingest.exif import ImageMetadata, extract_metadata, strip_metadata
from ordnance_id.ingest.quality import ImageQualityReport, assess_quality
from ordnance_id.ingest.scale import ScaleReference


class IngestResult(BaseModel):
    """Return a quality decision and sanitized bytes only for accepted images."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ingest_id: str
    accepted: bool
    quality: ImageQualityReport
    metadata: ImageMetadata
    scale_reference: ScaleReference
    sanitized_image: bytes | None = None


def ingest_image(
    image_bytes: bytes,
    scale_ref: ScaleReference | None = None,
    *,
    settings: Settings | None = None,
) -> IngestResult:
    """Apply metadata and quality policy, stopping immediately on rejection."""

    active_settings = settings or get_settings()
    metadata = extract_metadata(image_bytes, settings=active_settings)
    quality = assess_quality(image_bytes, settings=active_settings)
    scale = scale_ref or ScaleReference()
    ingest_id = f"ingest_{uuid4().hex}"
    if not quality.is_acceptable:
        return IngestResult(
            ingest_id=ingest_id,
            accepted=False,
            quality=quality,
            metadata=metadata,
            scale_reference=scale,
            sanitized_image=None,
        )
    return IngestResult(
        ingest_id=ingest_id,
        accepted=True,
        quality=quality,
        metadata=metadata,
        scale_reference=scale,
        sanitized_image=strip_metadata(image_bytes),
    )

