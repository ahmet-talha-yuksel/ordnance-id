"""Apply deterministic image-quality gates before any identification analysis."""

import cv2
import numpy as np
from pydantic import BaseModel, Field

from ordnance_id.config import Settings, get_settings


class ImageQualityReport(BaseModel):
    """Explain whether an image clears every configured analysis-quality gate."""

    is_acceptable: bool
    overall_score: float = Field(ge=0.0, le=1.0)
    blur_score: float = Field(ge=0.0, le=1.0)
    brightness_score: float = Field(ge=0.0, le=1.0)
    resolution_ok: bool
    rejection_reasons: list[str]
    recommendations: list[str]


def assess_quality(
    image_bytes: bytes, *, settings: Settings | None = None
) -> ImageQualityReport:
    """Score decoded pixels and reject clearly when any configured gate fails."""

    active_settings = settings or get_settings()
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Image bytes cannot be decoded")
    height, width = image.shape
    resolution_ok = (
        width >= active_settings.MIN_IMAGE_WIDTH and height >= active_settings.MIN_IMAGE_HEIGHT
    )
    laplacian_variance = float(cv2.Laplacian(image, cv2.CV_64F).var())
    blur_score = min(1.0, laplacian_variance / active_settings.BLUR_VARIANCE_REFERENCE)
    mean_brightness = float(image.mean())
    brightness_score = max(0.0, 1.0 - abs(mean_brightness - 127.5) / 127.5)
    overall_score = (blur_score + brightness_score + float(resolution_ok)) / 3.0

    reasons: list[str] = []
    recommendations: list[str] = []
    if not resolution_ok:
        reasons.append("Resolution is too low / Çözünürlük çok düşük")
        recommendations.append(
            "Provide a higher-resolution image / Daha yüksek çözünürlüklü görüntü sağlayın"
        )
    if blur_score < active_settings.MIN_BLUR_SCORE:
        reasons.append("Image is too blurred / Görüntü fazla bulanık")
        recommendations.append(
            "Retake from a stable position without approaching / "
            "Yaklaşmadan sabit konumdan yeniden çekin"
        )
    if brightness_score < active_settings.MIN_BRIGHTNESS_SCORE:
        reasons.append("Lighting is inadequate / Aydınlatma yetersiz")
        recommendations.append(
            "Provide an evenly lit image if safely available / "
            "Güvenli biçimde mümkünse eşit aydınlatılmış görüntü sağlayın"
        )
    if overall_score < active_settings.MIN_IMAGE_QUALITY_SCORE:
        reasons.append("Overall quality score is below threshold / Genel kalite puanı eşik altında")
        recommendations.append(
            "Submit a clearer image; analysis will not continue / "
            "Daha net görüntü gönderin; analiz devam etmeyecek"
        )
    is_acceptable = not reasons
    return ImageQualityReport(
        is_acceptable=is_acceptable,
        overall_score=round(overall_score, 4),
        blur_score=round(blur_score, 4),
        brightness_score=round(brightness_score, 4),
        resolution_ok=resolution_ok,
        rejection_reasons=reasons,
        recommendations=recommendations,
    )
