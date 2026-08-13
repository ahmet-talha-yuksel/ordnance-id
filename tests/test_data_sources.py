import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from ordnance_id.data_sources import (
    DataSource,
    download_archive,
    extract_zip_safely,
    local_status,
    manifest_entry,
    write_manifest,
)


def source_for(content: bytes, target: Path) -> DataSource:
    return DataSource(
        name="fixture",
        title="Fixture",
        authors=["Test Author"],
        affiliation="Test",
        doi="10.0000/test",
        landing_page="https://example.test/dataset",
        download_url="https://example.test/archive.zip",
        license="CC BY 4.0",
        md5=hashlib.md5(content, usedforsecurity=False).hexdigest(),
        size_bytes=len(content),
        target_dir=target,
        redistribute=False,
    )


async def test_download_resumes_and_writes_manifest(tmp_path: Path) -> None:
    content = b"complete archive bytes"
    source = source_for(content, tmp_path / "extracted")
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    (download_dir / "archive.zip.part").write_bytes(content[:9])

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["range"] == "bytes=9-"
        return httpx.Response(206, content=content[9:])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        archive = await download_archive(source, tmp_path, client=client)

    assert archive.read_bytes() == content
    assert local_status(source, tmp_path) == "downloaded"
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, manifest_entry(source, archive))
    assert json.loads(manifest.read_text())[0]["name"] == "fixture"


async def test_download_rejects_bad_checksum(tmp_path: Path) -> None:
    source = source_for(b"expected", tmp_path / "extracted")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"wrong")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="MD5 mismatch"):
            await download_archive(source, tmp_path, client=client)

    assert (tmp_path / "downloads" / "archive.zip").exists()
    assert local_status(source, tmp_path) == "corrupt"


def test_safe_extraction_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("../escape.txt", "unsafe")

    with pytest.raises(ValueError, match="Unsafe archive member"):
        extract_zip_safely(archive, tmp_path / "target")
