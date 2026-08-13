"""Compare v1 and v2 pilot completeness without migrating stored v1 records."""

import json
import re
from pathlib import Path
from typing import Any

import typer
from inspect_observations import PROHIBITED_PATTERNS

EXCLUDED_COMPLETION_FIELDS = {"estimated_length_cm"}


def _load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _violations(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        observation = row.get("observation") or {}
        strings = [value for value in observation.values() if isinstance(value, str)]
        strings.extend(
            item
            for value in observation.values()
            if isinstance(value, list)
            for item in value
            if isinstance(item, str)
        )
        count += sum(
            bool(pattern.search(text))
            for text in strings
            for pattern in PROHIBITED_PATTERNS.values()
        )
    return count


def _completion(rows: list[dict[str, Any]]) -> dict[str, float]:
    observations = [row["observation"] for row in rows if row.get("observation")]
    fields = sorted({field for value in observations for field in value})
    return {
        field: sum(value.get(field) is not None for value in observations) / len(observations)
        for field in fields
        if field not in EXCLUDED_COMPLETION_FIELDS
        and field not in {"unclear_features", "observation_notes"}
    }


def _unclear_format(rows: list[dict[str, Any]]) -> tuple[int, int]:
    values = [
        item
        for row in rows
        for item in (row.get("observation") or {}).get("unclear_features", [])
    ]
    valid = sum(bool(re.fullmatch(r"[a-z_]+:\s*\S.+", item)) for item in values)
    return valid, len(values)


def compare(v1: list[dict[str, Any]], v2: list[dict[str, Any]]) -> str:
    """Render requested prompt comparison metrics."""

    v1_completion = _completion(v1)
    v2_completion = _completion(v2)
    fields = sorted(set(v1_completion) | set(v2_completion))
    lines = [
        "# Prompt comparison: observe_v1 vs observe_v2",
        "",
        "`estimated_length_cm` is not applicable in this eval set (no scale references present) "
        "and is excluded from completion averages.",
        "",
        "| Field | v1 filled | v2 filled |",
        "|---|---:|---:|",
    ]
    for field in fields:
        v1_text = f"{v1_completion[field]:.1%}" if field in v1_completion else "n/a"
        v2_text = f"{v2_completion[field]:.1%}" if field in v2_completion else "n/a"
        lines.append(f"| {field} | {v1_text} | {v2_text} |")
    v1_format = _unclear_format(v1)
    v2_format = _unclear_format(v2)
    v1_output_tokens = sum(row["metrics"]["output_tokens"] for row in v1) / len(v1)
    v2_output_tokens = sum(row["metrics"]["output_tokens"] for row in v2) / len(v2)
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Rule violations — v1: {_violations(v1)}, v2: {_violations(v2)}",
            f"- Average output tokens — v1: {v1_output_tokens:.1f}, "
            f"v2: {v2_output_tokens:.1f}",
            f"- Average duration — v1: {sum(row['duration_ms'] for row in v1) / len(v1):.1f} ms, "
            f"v2: {sum(row['duration_ms'] for row in v2) / len(v2):.1f} ms",
            f"- unclear_features format compliance — v1: {v1_format[0]}/{v1_format[1]}, "
            f"v2: {v2_format[0]}/{v2_format[1]}",
            "",
        ]
    )
    return "\n".join(lines)


def main(
    v1_path: Path = Path(
        "evals/results/observations_v1_gemini_gemini-2.5-flash_pilot.jsonl"
    ),
    v2_path: Path = Path(
        "evals/results/observations_v2_gemini_gemini-2.5-flash_pilot.jsonl"
    ),
    output: Path = Path("docs/prompt_comparison_v1_v2.md"),
) -> None:
    """Write the v1/v2 pilot comparison."""

    report = compare(_load(v1_path), _load(v2_path))
    output.write_text(report + "\n", encoding="utf-8")
    typer.echo(report)


if __name__ == "__main__":
    typer.run(main)
