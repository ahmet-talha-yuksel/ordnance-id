"""Cache schema-validated observations without storing source image bytes."""

import hashlib
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ordnance_id.gateway.metrics import CallMetrics


class CachedStructuredResult(BaseModel):
    """Store validated output and provider-neutral call metrics."""

    value: dict[str, Any]
    metrics: CallMetrics


class StructuredDiskCache:
    """Persist atomic JSON cache entries addressed by request fingerprints."""

    def __init__(self, root: Path) -> None:
        self.root = root

    @staticmethod
    def key(*, model: str, prompt: str, schema_json: str, image_bytes: bytes) -> str:
        digest = hashlib.sha256()
        for value in (model.encode(), prompt.encode(), schema_json.encode(), image_bytes):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
        return digest.hexdigest()

    def get(self, key: str) -> CachedStructuredResult | None:
        path = self.root / f"{key}.json"
        if not path.exists():
            return None
        return CachedStructuredResult.model_validate_json(path.read_text(encoding="utf-8"))

    def put(self, key: str, result: CachedStructuredResult) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{key}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
