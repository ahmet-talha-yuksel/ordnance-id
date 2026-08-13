"""Implement local Ollama access behind the provider-neutral gateway."""

from collections.abc import Sequence
from typing import Any, cast

import httpx
from pydantic import ValidationError

from ordnance_id.gateway.base import ImageInput, Message, SchemaT


class OllamaProvider:
    """Call Ollama's chat API for text and JSON-schema responses."""

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        request_messages: list[dict[str, Any]] = [dict(message) for message in messages]
        if system is not None:
            request_messages.insert(0, {"role": "system", "content": system})
        response = await self._client.post(
            "/api/chat",
            json={
                "model": self._model,
                "messages": request_messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        response.raise_for_status()
        return str(response.json()["message"]["content"])

    async def complete_structured(
        self,
        messages: Sequence[Message],
        schema: type[SchemaT],
        *,
        images: Sequence[ImageInput] | None = None,
    ) -> SchemaT:
        request_messages: list[dict[str, Any]] = [dict(message) for message in messages]
        if images:
            if not request_messages:
                request_messages.append({"role": "user", "content": "Analyze the image(s)."})
            request_messages[-1]["images"] = [image["data"] for image in images]
        last_error: ValidationError | None = None
        for _attempt in range(3):
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self._model,
                    "messages": request_messages,
                    "stream": False,
                    "format": schema.model_json_schema(),
                    "options": {"temperature": 0},
                },
            )
            response.raise_for_status()
            content = cast(str, response.json()["message"]["content"])
            try:
                return schema.model_validate_json(content)
            except ValidationError as error:
                last_error = error
        assert last_error is not None
        raise last_error

