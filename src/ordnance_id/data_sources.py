"""Validate data-source records and maintain their local acquisition manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse
from zipfile import ZipFile

import httpx
import yaml
from pydantic import BaseModel, Field, HttpUrl
from rich.progress import Progress


class DataSource(BaseModel):
    """Describe one licensed and checksum-pinned external dataset."""

    name: str
    title: str
    authors: list[str]
    affiliation: str
    doi: str
    landing_page: HttpUrl
    download_url: HttpUrl
    license: str = Field(min_length=1)
    md5: str = Field(pattern=r"^[0-9a-fA-F]{32}$")
    size_bytes: int = Field(gt=0)
    target_dir: Path
    redistribute: bool


class DataSourceCatalog(BaseModel):
    """Contain the configured set of external data sources."""

    sources: list[DataSource]

    def by_name(self, name: str) -> DataSource:
        """Return a uniquely named source or raise a useful lookup error."""

        matches = [source for source in self.sources if source.name == name]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one data source named {name!r}")
        return matches[0]


class ManifestEntry(BaseModel):
    """Record a verified local acquisition without embedding raw data."""

    name: str
    url: str
    filename: str
    size: int
    md5: str
    downloaded_at: datetime


LocalStatus = Literal["missing", "partial", "corrupt", "downloaded", "extracted"]


def load_catalog(path: Path) -> DataSourceCatalog:
    """Load and validate a YAML source catalog."""

    with path.open(encoding="utf-8") as handle:
        return DataSourceCatalog.model_validate(yaml.safe_load(handle))


def archive_name(source: DataSource) -> str:
    """Derive a safe local archive name from the source URL."""

    name = Path(unquote(urlparse(str(source.download_url)).path)).name
    if not name or name in {".", ".."}:
        raise ValueError(f"Cannot determine archive filename for {source.name}")
    return name


def file_md5(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calculate a file's MD5 checksum in bounded memory."""

    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_status(source: DataSource, raw_root: Path) -> LocalStatus:
    """Report whether a configured source is absent, partial, corrupt, or ready."""

    archive = raw_root / "downloads" / archive_name(source)
    partial = archive.with_suffix(f"{archive.suffix}.part")
    target = source.target_dir
    if target.exists() and archive.exists() and file_md5(archive) == source.md5.lower():
        return "extracted"
    if partial.exists():
        return "partial"
    if not archive.exists():
        return "missing"
    return "downloaded" if file_md5(archive) == source.md5.lower() else "corrupt"


async def download_archive(
    source: DataSource,
    raw_root: Path,
    *,
    client: httpx.AsyncClient,
    progress: Progress | None = None,
) -> Path:
    """Download with HTTP range resumption and return only a checksum-valid archive."""

    download_dir = raw_root / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    archive = download_dir / archive_name(source)
    if archive.exists():
        if file_md5(archive) == source.md5.lower():
            return archive
        raise ValueError(f"Existing archive has an invalid MD5: {archive}")

    partial = archive.with_suffix(f"{archive.suffix}.part")
    existing = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    async with client.stream("GET", str(source.download_url), headers=headers) as response:
        response.raise_for_status()
        resumed = existing > 0 and response.status_code == httpx.codes.PARTIAL_CONTENT
        mode = "ab" if resumed else "wb"
        if existing and not resumed:
            existing = 0
        task_id = None
        if progress is not None:
            total_header = response.headers.get("content-length")
            total = existing + int(total_header) if total_header else source.size_bytes
            task_id = progress.add_task(source.name, total=total, completed=existing)
        with partial.open(mode) as handle:
            async for chunk in response.aiter_bytes():
                handle.write(chunk)
                if progress is not None and task_id is not None:
                    progress.update(task_id, advance=len(chunk))

    actual_md5 = file_md5(partial)
    if actual_md5 != source.md5.lower():
        partial.replace(archive)
        raise ValueError(
            f"MD5 mismatch for {source.name}: expected {source.md5}, got {actual_md5}"
        )
    partial.replace(archive)
    return archive


def extract_zip_safely(archive: Path, target: Path) -> None:
    """Extract a ZIP while rejecting members that escape the destination."""

    target.mkdir(parents=True, exist_ok=True)
    target_root = target.resolve()
    with ZipFile(archive) as zip_file:
        for member in zip_file.infolist():
            destination = (target / member.filename).resolve()
            if not destination.is_relative_to(target_root):
                raise ValueError(f"Unsafe archive member: {member.filename}")
        zip_file.extractall(target)


def write_manifest(path: Path, entry: ManifestEntry) -> None:
    """Upsert one acquisition record using an atomic file replacement."""

    entries: list[ManifestEntry] = []
    if path.exists():
        entries = [ManifestEntry.model_validate(item) for item in json.loads(path.read_text())]
    entries = [item for item in entries if item.name != entry.name]
    entries.append(entry)
    entries.sort(key=lambda item: item.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in entries], indent=2, ensure_ascii=False
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def manifest_entry(source: DataSource, archive: Path) -> ManifestEntry:
    """Build a manifest entry for a verified archive."""

    return ManifestEntry(
        name=source.name,
        url=str(source.download_url),
        filename=archive.name,
        size=archive.stat().st_size,
        md5=source.md5.lower(),
        downloaded_at=datetime.now(UTC),
    )
