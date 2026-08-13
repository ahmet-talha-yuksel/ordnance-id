from pathlib import Path

from ordnance_id.gateway.cache import CachedStructuredResult, StructuredDiskCache
from ordnance_id.gateway.metrics import CallMetrics


def test_cache_key_changes_with_image_and_round_trips(tmp_path: Path) -> None:
    cache = StructuredDiskCache(tmp_path)
    first = cache.key(
        provider="one", model="m", prompt="p", schema_json="s", image_bytes=b"one"
    )
    second = cache.key(
        provider="one", model="m", prompt="p", schema_json="s", image_bytes=b"two"
    )
    assert first != second
    other_provider = cache.key(
        provider="two", model="m", prompt="p", schema_json="s", image_bytes=b"one"
    )
    assert first != other_provider
    value = CachedStructuredResult(
        value={"body_shape": "unclear"},
        metrics=CallMetrics(provider="test", model="m", input_tokens=10),
    )
    cache.put(first, value)
    assert cache.get(first) == value
