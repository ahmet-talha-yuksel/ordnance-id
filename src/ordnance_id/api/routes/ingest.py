"""Expose bounded image ingestion without returning image content."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from ordnance_id.config import Settings, get_settings
from ordnance_id.ingest.exif import ImageMetadata
from ordnance_id.ingest.pipeline import ingest_image
from ordnance_id.ingest.quality import ImageQualityReport
from ordnance_id.ingest.scale import ScaleReference

router = APIRouter(tags=["ingest"])
ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp"}


class IngestResponse(BaseModel):
    """Expose an ingest decision without leaking sanitized image bytes."""

    ingest_id: str
    accepted: bool
    quality: ImageQualityReport
    metadata: ImageMetadata


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    image: Annotated[UploadFile, File(description="JPEG, PNG, or WebP image")],
    settings: Annotated[Settings, Depends(get_settings)],
    reference_type: Annotated[
        Literal["ruler", "coin", "hand", "none"], Form()
    ] = "none",
    known_dimension_mm: Annotated[float | None, Form(gt=0)] = None,
    pixels_per_mm: Annotated[float | None, Form(gt=0)] = None,
) -> IngestResponse:
    """Validate media constraints and return acceptance or explicit quality rejection."""

    if image.content_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, and WebP images are supported.",
        )
    image_bytes = await image.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image exceeds the configured upload limit.",
        )
    try:
        scale = ScaleReference(
            reference_type=reference_type,
            known_dimension_mm=known_dimension_mm,
            pixels_per_mm=pixels_per_mm,
        )
        result = ingest_image(image_bytes, scale, settings=settings)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    return IngestResponse(
        ingest_id=result.ingest_id,
        accepted=result.accepted,
        quality=result.quality,
        metadata=result.metadata,
    )
