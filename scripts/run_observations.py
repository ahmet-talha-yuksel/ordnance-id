"""Run cost-gated, cached structured observations over an evaluation set."""

import asyncio
import json
from pathlib import Path
from time import perf_counter
from typing import Annotated

import typer

from ordnance_id.config import get_settings
from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.observations import ObservationRecord
from ordnance_id.gateway.cache import CachedStructuredResult, StructuredDiskCache
from ordnance_id.gateway.metrics import CallMetrics
from ordnance_id.gateway.providers import get_provider
from ordnance_id.vision.analyzer import VisionAnalyzer
from ordnance_id.vision.schema import OrdnanceObservation

app = typer.Typer()


async def _run(
    eval_path: Path,
    image_dir: Path,
    output: Path | None,
    cache_dir: Path,
    limit: int | None,
    dry_run: bool,
    yes: bool,
    input_cost_per_million: float,
    output_cost_per_million: float,
) -> None:
    settings = get_settings()
    if output is None:
        safe_model = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in settings.VISION_MODEL
        )
        output = Path(f"evals/results/observations_observe_v1_{safe_model}.jsonl")
    eval_set = load_eval_set(eval_path)
    samples = eval_set.samples[:limit] if limit is not None else eval_set.samples
    estimated_input = len(samples) * 1600
    estimated_output = len(samples) * 400
    estimate = (
        estimated_input / 1_000_000 * input_cost_per_million
        + estimated_output / 1_000_000 * output_cost_per_million
    )
    typer.echo(
        f"Provider={settings.LLM_PROVIDER} model={settings.VISION_MODEL} samples={len(samples)} "
        f"estimated tokens={estimated_input}+{estimated_output}; estimated cost=${estimate:.4f}"
    )
    if dry_run:
        typer.echo("Dry run: no provider calls were made.")
        return
    if settings.LLM_PROVIDER != "ollama" and input_cost_per_million <= 0:
        raise typer.BadParameter("Cloud runs require an explicit positive input token price")
    if not yes and not typer.confirm("Proceed with provider calls?"):
        raise typer.Abort()
    provider = get_provider(settings)
    analyzer = VisionAnalyzer(provider)
    cache = StructuredDiskCache(cache_dir)
    completed: set[str] = set()
    if output.exists():
        completed = {
            json.loads(line)["sample_id"]
            for line in output.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as handle:
        for sample in samples:
            if sample.id in completed:
                continue
            image_bytes = (image_dir / sample.filename).read_bytes()
            key = cache.key(
                model=settings.VISION_MODEL,
                prompt=analyzer.system_prompt(),
                schema_json=json.dumps(
                    OrdnanceObservation.model_json_schema(), sort_keys=True, separators=(",", ":")
                ),
                image_bytes=image_bytes,
            )
            cached = cache.get(key)
            started = perf_counter()
            error: str | None = None
            observation: OrdnanceObservation | None = None
            metrics = CallMetrics(provider=settings.LLM_PROVIDER, model=settings.VISION_MODEL)
            try:
                if cached:
                    observation = OrdnanceObservation.model_validate(cached.value)
                    metrics = cached.metrics.model_copy(update={"cache_hit": True})
                else:
                    observation = await analyzer.observe(image_bytes)
                    metrics = provider.last_metrics or metrics
                    cache.put(
                        key,
                        CachedStructuredResult(value=observation.model_dump(), metrics=metrics),
                    )
            except Exception as caught:  # noqa: BLE001
                error = f"{type(caught).__name__}: {caught}"
            duration_ms = (perf_counter() - started) * 1000
            cost = (
                metrics.input_tokens / 1_000_000 * input_cost_per_million
                + metrics.output_tokens / 1_000_000 * output_cost_per_million
            )
            record = ObservationRecord(
                sample_id=sample.id,
                observation=observation,
                duration_ms=duration_ms,
                metrics=metrics,
                estimated_cost_usd=cost,
                error=error,
            )
            handle.write(record.model_dump_json() + "\n")
            handle.flush()


@app.command()
def run(
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    image_dir: Path = Path("data/eval_images"),
    output: Path | None = None,
    cache_dir: Path = Path(".cache/observations"),
    limit: Annotated[int | None, typer.Option(min=1)] = None,
    dry_run: bool = False,
    yes: bool = False,
    input_cost_per_million: Annotated[float, typer.Option(min=0)] = 0.0,
    output_cost_per_million: Annotated[float, typer.Option(min=0)] = 0.0,
) -> None:
    """Estimate first, then optionally run cached observations sequentially."""

    asyncio.run(
        _run(
            eval_path,
            image_dir,
            output,
            cache_dir,
            limit,
            dry_run,
            yes,
            input_cost_per_million,
            output_cost_per_million,
        )
    )


if __name__ == "__main__":
    app()
