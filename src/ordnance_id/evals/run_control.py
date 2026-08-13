"""Small durable-run primitives for long observation jobs."""

import json
from pathlib import Path

from ordnance_id.evals.observations import ObservationRecord


class ObservationLedger:
    """Append complete JSONL records and expose IDs available for resume."""

    def __init__(self, path: Path, *, resume: bool) -> None:
        self.path = path
        if path.exists() and not resume:
            raise FileExistsError(f"output already exists; pass --resume: {path}")
        self.completed_ids = self._load_ids() if resume else set()

    def _load_ids(self) -> set[str]:
        return {
            json.loads(line)["sample_id"]
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    def append(self, record: ObservationRecord) -> None:
        """Durably append one completed sample before moving to the next."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
            handle.flush()
        self.completed_ids.add(record.sample_id)


class RequestBudget:
    """Track provider HTTP requests against a conservative per-run RPD budget."""

    def __init__(self, limit: int) -> None:
        if limit <= 0:
            raise ValueError("request budget must be positive")
        self.limit = limit
        self.used = 0

    @property
    def available(self) -> bool:
        return self.used < self.limit

    def add(self, request_count: int) -> None:
        self.used += max(0, request_count)

