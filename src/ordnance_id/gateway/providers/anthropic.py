"""Implement Anthropic access behind the provider-neutral gateway."""

from collections.abc import Sequence
from typing import Any, cast

import httpx
from pydantic import ValidationError

from ordnance_id.gateway.base import ImageInput, Message, SchemaT


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
        self._client = client or httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=60.0,
        )

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
        for _attempt in range(3):
            response = await self._client.post("/v1/messages", json=payload)
            response.raise_for_status()
            blocks = cast(list[dict[str, Any]], response.json()["content"])
            tool_input: Any = next(
                (block.get("input") for block in blocks if block.get("type") == "tool_use"),
                {},
            )
            try:
                return schema.model_validate(tool_input)
            except ValidationError as error:
                last_error = error
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
