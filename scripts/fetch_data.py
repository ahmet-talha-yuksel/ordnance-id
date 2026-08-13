"""Download, verify, extract, and list configured datasets."""

import asyncio
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn
from rich.table import Table

from ordnance_id.data_sources import (
    download_archive,
    extract_zip_safely,
    load_catalog,
    local_status,
    manifest_entry,
    write_manifest,
)

app = typer.Typer(no_args_is_help=True)
console = Console()
CATALOG_PATH = Path("config/data_sources.yaml")
RAW_ROOT = Path("data/raw")


@app.command("list")
def list_sources() -> None:
    """List configured sources and their verified local status."""

    table = Table("Name", "Licence", "Size (bytes)", "Local status")
    for source in load_catalog(CATALOG_PATH).sources:
        table.add_row(
            source.name,
            source.license,
            str(source.size_bytes),
            local_status(source, RAW_ROOT),
        )
    console.print(table)


async def _download(name: str) -> None:
    source = load_catalog(CATALOG_PATH).by_name(name)
    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    with progress:
        async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
            archive = await download_archive(source, RAW_ROOT, client=client, progress=progress)
    extract_zip_safely(archive, source.target_dir)
    write_manifest(RAW_ROOT / "manifest.json", manifest_entry(source, archive))
    console.print(f"[green]Verified and extracted[/green] {source.name} to {source.target_dir}")


@app.command()
def download(name: Annotated[str, typer.Argument(help="Configured source name")]) -> None:
    """Download one source, verify its MD5, and extract it safely."""

    try:
        asyncio.run(_download(name))
    except (httpx.HTTPError, OSError, ValueError) as error:
        console.print(f"[red]Data acquisition failed:[/red] {error}", err=True)
        raise typer.Exit(code=1) from error


if __name__ == "__main__":
    app()
