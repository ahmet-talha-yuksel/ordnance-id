from pathlib import Path

import pytest

from ordnance_id.evals.observations import ObservationRecord
from ordnance_id.evals.run_control import ObservationLedger, RequestBudget
from ordnance_id.gateway.metrics import CallMetrics


def _record(sample_id: str) -> ObservationRecord:
    return ObservationRecord(
        sample_id=sample_id,
        family="not_ordnance",
        size_bucket="small",
        duration_ms=1,
        metrics=CallMetrics(provider="test", model="test"),
    )


def test_ledger_appends_each_record_and_resume_skips_existing(tmp_path: Path) -> None:
    output = tmp_path / "results.jsonl"
    ledger = ObservationLedger(output, resume=False)
    ledger.append(_record("eval_001"))
    ledger.append(_record("eval_002"))

    resumed = ObservationLedger(output, resume=True)

    assert output.read_text(encoding="utf-8").count("\n") == 2
    assert resumed.completed_ids == {"eval_001", "eval_002"}


def test_ledger_refuses_existing_output_without_resume(tmp_path: Path) -> None:
    output = tmp_path / "results.jsonl"
    output.write_text("", encoding="utf-8")

    with pytest.raises(FileExistsError, match="--resume"):
        ObservationLedger(output, resume=False)


def test_request_budget_stops_at_limit() -> None:
    budget = RequestBudget(3)
    budget.add(2)
    assert budget.available
    budget.add(1)
    assert not budget.available
