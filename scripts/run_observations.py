"""Run cost-gated, cached structured observations over an evaluation set."""

import asyncio
import json
import signal
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
from ordnance_id.evals.run_control import ObservationLedger, RequestBudget
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
    sample_ids: str | None,
    dry_run: bool,
    yes: bool,
    input_cost_per_million: float,
    output_cost_per_million: float,
    prompt_path: Path,
    resume: bool,
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
            f"evals/results/observations_{prompt_path.stem}_{settings.LLM_PROVIDER}_"
            f"{safe_model}.jsonl"
        )
    eval_set = load_eval_set(eval_path)
    if sample_ids:
        requested_ids = [value.strip() for value in sample_ids.split(",") if value.strip()]
        by_id = {sample.id: sample for sample in eval_set.samples}
        missing = [sample_id for sample_id in requested_ids if sample_id not in by_id]
        if missing:
            raise typer.BadParameter("Unknown sample IDs: " + ", ".join(missing))
        samples = [by_id[sample_id] for sample_id in requested_ids]
    elif pilot:
        tiers = load_class_tiers(Path("config/class_tiers.yaml")).mapping()
        samples = [
            item.sample for item in select_pilot(eval_set.samples, image_dir, tiers, seed=0)
        ]
    else:
        samples = eval_set.samples[:limit] if limit is not None else eval_set.samples
    prompt_chars = len(prompt_path.read_text(encoding="utf-8"))
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
        f"prompt={prompt_path.stem} samples={len(samples)} image_tokens≈{estimated_image_tokens} "
        f"text_tokens≈{estimated_text_tokens} output_tokens≤{estimated_output}; "
        + (
            f"maliyet: $0 (free tier); günlük kota≈{len(samples)}/{settings.GEMINI_RPD} istek; "
            f"koşum bütçesi={settings.GEMINI_RPD_BUDGET}"
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
    analyzer = VisionAnalyzer(
        provider, prompt_path=prompt_path, max_edge_px=settings.VISION_MAX_EDGE_PX
    )
    cache = StructuredDiskCache(cache_dir)
    try:
        ledger = ObservationLedger(output, resume=resume)
    except FileExistsError as error:
        raise typer.BadParameter(str(error)) from error
    pending = [sample for sample in samples if sample.id not in ledger.completed_ids]
    if resume:
        typer.echo(f"Resume: {len(samples) - len(pending)} existing records skipped.")
    budget = RequestBudget(settings.GEMINI_RPD_BUDGET)
    stop_requested = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True
        typer.echo("SIGINT received; stopping after the current sample.")

    previous_sigint = signal.signal(signal.SIGINT, request_stop)
    run_started = perf_counter()
    errors = 0
    processed = 0
    try:
        for sample in pending:
            if not budget.available:
                typer.echo(
                    f"Quota budget reached ({budget.used}/{budget.limit}); "
                    f"stopped before {sample.id}. Resume with --resume."
                )
                break
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
            metrics = CallMetrics(
                provider=settings.LLM_PROVIDER, model=active_model, request_count=0
            )
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
                metrics = provider.last_metrics or metrics
            if not metrics.cache_hit:
                budget.add(metrics.request_count)
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
            ledger.append(record)
            processed += 1
            errors += error is not None
            if processed % 25 == 0:
                elapsed = perf_counter() - run_started
                average = elapsed / processed
                remaining = len(pending) - processed
                typer.echo(
                    f"Progress: completed={processed}/{len(pending)} errors={errors} "
                    f"average={average:.1f}s ETA={average * remaining:.0f}s "
                    f"requests={budget.used}/{budget.limit}"
                )
            if stop_requested:
                typer.echo(f"Clean stop after {sample.id}; resume with --resume.")
                break
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
    typer.echo(
        f"Run summary: completed={processed}/{len(pending)} errors={errors} "
        f"requests={budget.used}/{budget.limit}"
    )


@app.command()
def run(
    eval_path: Path = Path("evals/datasets/eval_set_v1.yaml"),
    image_dir: Path = Path("data/eval_images"),
    output: Path | None = None,
    cache_dir: Path = Path(".cache/observations"),
    limit: Annotated[int | None, typer.Option(min=1)] = None,
    pilot: bool = False,
    sample_ids: str | None = None,
    dry_run: bool = False,
    yes: bool = False,
    input_cost_per_million: Annotated[float, typer.Option(min=0)] = 0.0,
    output_cost_per_million: Annotated[float, typer.Option(min=0)] = 0.0,
    prompt_path: Path = Path("prompts/observe_v1.md"),
    resume: bool = False,
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
            sample_ids,
            dry_run,
            yes,
            input_cost_per_million,
            output_cost_per_million,
            prompt_path,
            resume,
        )
    )


if __name__ == "__main__":
    app()
