"""Read and write evaluation-set YAML with deterministic serialization."""

from pathlib import Path

import yaml

from ordnance_id.evals.schema import EvalSet


def load_eval_set(path: Path) -> EvalSet:
    """Load and validate an evaluation-set YAML document."""

    return EvalSet.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def write_eval_set(eval_set: EvalSet, path: Path) -> None:
    """Serialize a validated evaluation set deterministically."""

    value = eval_set.model_dump(mode="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
