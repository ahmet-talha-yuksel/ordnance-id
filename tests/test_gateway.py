import httpx
import pytest
from pydantic import BaseModel, ValidationError

from ordnance_id.gateway.base import Message
from ordnance_id.gateway.providers.anthropic import AnthropicProvider


class Result(BaseModel):
    family: str
    confidence: float


async def test_anthropic_structured_response_retries_then_validates() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        assert request.url.path == "/v1/messages"
        payload = {
            "family": "projectile",
            "confidence": "invalid" if attempts == 1 else 0.82,
        }
        return httpx.Response(
            200,
            json={"content": [{"type": "tool_use", "input": payload}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://test")
    provider = AnthropicProvider("secret", "test-model", client=client)
    messages: list[Message] = [{"role": "user", "content": "Classify observations."}]

    result = await provider.complete_structured(messages, Result)

    assert result == Result(family="projectile", confidence=0.82)
    assert attempts == 2
    await client.aclose()


async def test_anthropic_structured_response_raises_after_two_retries() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            json={"content": [{"type": "tool_use", "input": {"confidence": "invalid"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://test")
    provider = AnthropicProvider("secret", "test-model", client=client)
    messages: list[Message] = [{"role": "user", "content": "Classify observations."}]

    with pytest.raises(ValidationError):
        await provider.complete_structured(messages, Result)

    assert attempts == 3
    await client.aclose()
