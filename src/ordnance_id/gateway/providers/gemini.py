"""Implement Gemini native structured output behind the neutral gateway."""

import base64
from collections.abc import Sequence
from time import perf_counter
from typing import Any, cast

from google import genai
from google.genai import types
from pydantic import ValidationError

from ordnance_id.gateway.base import ImageInput, Message, SchemaT
from ordnance_id.gateway.metrics import CallMetrics
from ordnance_id.gateway.rate_limit import TokenBucket, call_with_backoff


class GeminiProvider:
    """Call Google Gen AI with native JSON-schema constrained responses."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        requests_per_minute: int = 10,
        client: genai.Client | None = None,
        limiter: TokenBucket | None = None,
    ) -> None:
        self._model = model
        self._client = client or genai.Client(api_key=api_key)
        self._limiter = limiter or TokenBucket(requests_per_minute)
        self._last_metrics: CallMetrics | None = None

    @property
    def last_metrics(self) -> CallMetrics | None:
        return self._last_metrics

    @staticmethod
    def _text(messages: Sequence[Message]) -> str:
        return "\n\n".join(f"{message['role']}: {message['content']}" for message in messages)

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        started = perf_counter()

        async def operation() -> Any:
            return await self._client.aio.models.generate_content(
                model=self._model,
                contents=self._text(messages),
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

        response, stats = await call_with_backoff(operation, limiter=self._limiter)
        usage = response.usage_metadata
        self._last_metrics = CallMetrics(
            provider="gemini",
            model=self._model,
            input_tokens=int(getattr(usage, "prompt_token_count", 0) or 0),
            output_tokens=int(getattr(usage, "candidates_token_count", 0) or 0),
            retries=stats.request_count - 1,
            request_count=stats.request_count,
            duration_ms=(perf_counter() - started) * 1000,
            rate_limit_429s=stats.rate_limit_429s,
        )
        return str(response.text)

    async def complete_structured(
        self,
        messages: Sequence[Message],
        schema: type[SchemaT],
        *,
        images: Sequence[ImageInput] | None = None,
    ) -> SchemaT:
        started = perf_counter()
        parts: list[types.Part] = [types.Part.from_text(text=self._text(messages))]
        parts.extend(
            types.Part.from_bytes(
                data=base64.b64decode(image["data"], validate=True),
                mime_type=image["media_type"],
            )
            for image in images or []
        )
        total_requests = 0
        total_429s = 0
        input_tokens = 0
        output_tokens = 0
        last_error: ValidationError | None = None
        for _schema_attempt in range(3):

            async def operation() -> Any:
                return await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=types.Content(role="user", parts=parts),
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=schema.model_json_schema(),
                    ),
                )

            response, stats = await call_with_backoff(operation, limiter=self._limiter)
            total_requests += stats.request_count
            total_429s += stats.rate_limit_429s
            usage = response.usage_metadata
            input_tokens += int(getattr(usage, "prompt_token_count", 0) or 0)
            output_tokens += int(getattr(usage, "candidates_token_count", 0) or 0)
            try:
                result = schema.model_validate_json(cast(str, response.text))
                self._last_metrics = CallMetrics(
                    provider="gemini",
                    model=self._model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    retries=total_requests - 1,
                    request_count=total_requests,
                    duration_ms=(perf_counter() - started) * 1000,
                    rate_limit_429s=total_429s,
                )
                return result
            except ValidationError as error:
                last_error = error
        self._last_metrics = CallMetrics(
            provider="gemini",
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retries=max(0, total_requests - 1),
            request_count=total_requests,
            duration_ms=(perf_counter() - started) * 1000,
            rate_limit_429s=total_429s,
        )
        assert last_error is not None
        raise last_error
