"""Generate a non-accuracy observation quality report from JSONL results."""

import json
from pathlib import Path

import typer

from ordnance_id.evals.observations import ObservationRecord, write_observation_report


def main(
    results: Path = Path("evals/results/observations_observe_v1.jsonl"),
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    output: Path = Path("docs/observation_report_v1.md"),
) -> None:
    """Summarize schema completion, uncertainty, timing, token use, and cost."""

    records = [
        ObservationRecord.model_validate(json.loads(line))
        for line in results.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    write_observation_report(records, eval_path, output)
    typer.echo(f"Wrote observation quality report to {output}")


if __name__ == "__main__":
    typer.run(main)

