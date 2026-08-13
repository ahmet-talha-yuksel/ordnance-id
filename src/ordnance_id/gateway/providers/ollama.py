"""Implement local Ollama access behind the provider-neutral gateway."""

from collections.abc import Sequence
from typing import Any, cast

import httpx
from pydantic import ValidationError

from ordnance_id.gateway.base import ImageInput, Message, SchemaT
from ordnance_id.gateway.metrics import CallMetrics


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
        self._last_metrics: CallMetrics | None = None
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=120.0)

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
        for attempt in range(3):
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
            response_data = cast(dict[str, Any], response.json())
            content = cast(str, cast(dict[str, Any], response_data["message"])["content"])
            try:
                result = schema.model_validate_json(content)
                self._last_metrics = CallMetrics(
                    provider="ollama",
                    model=self._model,
                    input_tokens=int(response_data.get("prompt_eval_count", 0)),
                    output_tokens=int(response_data.get("eval_count", 0)),
                    retries=attempt,
                )
                return result
            except ValidationError as error:
                last_error = error
        self._last_metrics = CallMetrics(
            provider="ollama", model=self._model, retries=2
        )
        assert last_error is not None
        raise last_error
