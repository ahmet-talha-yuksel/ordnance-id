import base64
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from ordnance_id.gateway.base import Message
from ordnance_id.gateway.providers.gemini import GeminiProvider
from ordnance_id.gateway.rate_limit import TokenBucket


class StructuredResult(BaseModel):
    visible: bool


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        text = '{"visible":"invalid"}' if len(self.calls) == 1 else '{"visible":true}'
        return SimpleNamespace(
            text=text,
            usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=4),
        )


async def test_gemini_native_schema_images_and_validation_retry() -> None:
    models = FakeModels()
    client = SimpleNamespace(aio=SimpleNamespace(models=models))
    provider = GeminiProvider(
        "secret",
        "gemini-test",
        client=client,
        limiter=TokenBucket(100_000),
    )
    messages: list[Message] = [{"role": "user", "content": "Observe visible properties."}]
    result = await provider.complete_structured(
        messages,
        StructuredResult,
        images=[
            {
                "data": base64.b64encode(b"image bytes").decode("ascii"),
                "media_type": "image/jpeg",
            }
        ],
    )
    assert result == StructuredResult(visible=True)
    assert len(models.calls) == 2
    config = models.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == StructuredResult.model_json_schema()
    parts = models.calls[0]["contents"].parts
    assert parts[1].inline_data.mime_type == "image/jpeg"
    assert parts[1].inline_data.data == b"image bytes"
    assert provider.last_metrics is not None
    assert provider.last_metrics.request_count == 2
    assert provider.last_metrics.input_tokens == 24
