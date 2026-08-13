"""Implement Anthropic access behind the provider-neutral gateway."""

from collections.abc import Sequence
from typing import Any, cast

import httpx
from pydantic import ValidationError

from ordnance_id.gateway.base import ImageInput, Message, SchemaT
from ordnance_id.gateway.metrics import CallMetrics


class AnthropicProvider:
    """Call Anthropic's Messages API using schema-enforced tool use."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._last_metrics: CallMetrics | None = None
        self._client = client or httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=60.0,
        )

    @property
    def last_metrics(self) -> CallMetrics | None:
        return self._last_metrics

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system is not None:
            payload["system"] = system
        response = await self._client.post("/v1/messages", json=payload)
        response.raise_for_status()
        blocks = cast(list[dict[str, Any]], response.json()["content"])
        return "".join(str(block["text"]) for block in blocks if block.get("type") == "text")

    async def complete_structured(
        self,
        messages: Sequence[Message],
        schema: type[SchemaT],
        *,
        images: Sequence[ImageInput] | None = None,
    ) -> SchemaT:
        payload_messages = self._with_images(messages, images)
        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 2048,
            "messages": payload_messages,
            "tools": [
                {
                    "name": "submit_result",
                    "description": "Submit the response in the required schema.",
                    "input_schema": schema.model_json_schema(),
                }
            ],
            "tool_choice": {"type": "tool", "name": "submit_result"},
        }
        last_error: ValidationError | None = None
        input_tokens = 0
        output_tokens = 0
        for attempt in range(3):
            response = await self._client.post("/v1/messages", json=payload)
            response.raise_for_status()
            response_data = cast(dict[str, Any], response.json())
            usage = cast(dict[str, Any], response_data.get("usage", {}))
            input_tokens += int(usage.get("input_tokens", 0))
            output_tokens += int(usage.get("output_tokens", 0))
            blocks = cast(list[dict[str, Any]], response_data["content"])
            tool_input: Any = next(
                (block.get("input") for block in blocks if block.get("type") == "tool_use"),
                {},
            )
            try:
                result = schema.model_validate(tool_input)
                self._last_metrics = CallMetrics(
                    provider="anthropic",
                    model=self._model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    retries=attempt,
                )
                return result
            except ValidationError as error:
                last_error = error
        self._last_metrics = CallMetrics(
            provider="anthropic",
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retries=2,
        )
        assert last_error is not None
        raise last_error

    @staticmethod
    def _with_images(
        messages: Sequence[Message], images: Sequence[ImageInput] | None
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = [dict(message) for message in messages]
        if not images:
            return result
        image_blocks: list[dict[str, Any]] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image["media_type"],
                    "data": image["data"],
                },
            }
            for image in images
        ]
        image_blocks.append({"type": "text", "text": "Analyze the attached image(s)."})
        result.append({"role": "user", "content": image_blocks})
        return result
