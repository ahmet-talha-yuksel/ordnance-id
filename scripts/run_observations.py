"""Run cost-gated, cached structured observations over an evaluation set."""

import asyncio
import json
from pathlib import Path
from time import perf_counter
from typing import Annotated

import typer
from PIL import Image

from ordnance_id.config import get_settings
from ordnance_id.data_analysis.tiers import load_class_tiers
from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.observations import ObservationRecord
from ordnance_id.evals.pilot import select_pilot
from ordnance_id.evals.size_buckets import size_bucket
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
    pilot: bool,
    dry_run: bool,
    yes: bool,
    input_cost_per_million: float,
    output_cost_per_million: float,
) -> None:
    settings = get_settings()
    active_model = (
        settings.GEMINI_VISION_MODEL
        if settings.LLM_PROVIDER == "gemini"
        else settings.VISION_MODEL
    )
    if output is None:
        safe_model = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in active_model
        )
        output = Path(
            f"evals/results/observations_observe_v1_{settings.LLM_PROVIDER}_{safe_model}.jsonl"
        )
    eval_set = load_eval_set(eval_path)
    if pilot:
        tiers = load_class_tiers(Path("config/class_tiers.yaml")).mapping()
        samples = [
            item.sample for item in select_pilot(eval_set.samples, image_dir, tiers, seed=0)
        ]
    else:
        samples = eval_set.samples[:limit] if limit is not None else eval_set.samples
    prompt_chars = len(Path("prompts/observe_v1.md").read_text(encoding="utf-8"))
    estimated_text_tokens = len(samples) * (prompt_chars // 4 + 100)
    estimated_image_tokens = 0
    for sample in samples:
        with Image.open(image_dir / sample.filename) as image:
            width, height = image.size
            scale = min(1.0, settings.VISION_MAX_EDGE_PX / max(width, height))
            estimated_image_tokens += round(width * scale * height * scale / 750)
    estimated_input = estimated_text_tokens + estimated_image_tokens
    estimated_output = len(samples) * 400
    estimate = (
        estimated_input / 1_000_000 * input_cost_per_million
        + estimated_output / 1_000_000 * output_cost_per_million
    )
    typer.echo(
        f"Provider={settings.LLM_PROVIDER} model={active_model} samples={len(samples)} "
        f"prompt=observe_v1 samples={len(samples)} image_tokens≈{estimated_image_tokens} "
        f"text_tokens≈{estimated_text_tokens} output_tokens≤{estimated_output}; "
        + (
            f"maliyet: $0 (free tier); günlük kota≈{len(samples)}/{settings.GEMINI_RPD} istek"
            if settings.LLM_PROVIDER == "gemini"
            else f"estimated cost=${estimate:.4f}"
        )
    )
    if dry_run:
        typer.echo("Dry run: no provider calls were made.")
        return
    if settings.LLM_PROVIDER not in {"ollama", "gemini"} and input_cost_per_million <= 0:
        raise typer.BadParameter("Cloud runs require an explicit positive input token price")
    if not yes and not typer.confirm("Proceed with provider calls?"):
        raise typer.Abort()
    provider = get_provider(settings)
    analyzer = VisionAnalyzer(provider, max_edge_px=settings.VISION_MAX_EDGE_PX)
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
            with Image.open(image_dir / sample.filename) as image:
                bucket = size_bucket(min(image.size))
            key = cache.key(
                provider=settings.LLM_PROVIDER,
                model=active_model,
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
            metrics = CallMetrics(provider=settings.LLM_PROVIDER, model=active_model)
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
                family=sample.ground_truth.family,
                size_bucket=bucket,
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
    pilot: bool = False,
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
            pilot,
            dry_run,
            yes,
            input_cost_per_million,
            output_cost_per_million,
        )
    )


if __name__ == "__main__":
    app()
