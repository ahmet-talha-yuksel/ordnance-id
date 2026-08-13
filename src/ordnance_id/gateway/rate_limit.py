"""Provide reusable async token-bucket limiting and transient-error backoff."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from time import monotonic, time
from typing import TypeVar

T = TypeVar("T")


class TokenBucket:
    """Limit starts to a configurable requests-per-minute rate."""

    def __init__(
        self,
        requests_per_minute: int,
        *,
        clock: Callable[[], float] = monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        self._capacity = 1.0
        self._tokens = 1.0
        self._refill_per_second = requests_per_minute / 60.0
        self._clock = clock
        self._sleep = sleep
        self._updated_at = clock()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until one request token is available and consume it."""

        while True:
            async with self._lock:
                now = self._clock()
                elapsed = max(0.0, now - self._updated_at)
                self._tokens = min(
                    self._capacity, self._tokens + elapsed * self._refill_per_second
                )
                self._updated_at = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait_seconds = (1.0 - self._tokens) / self._refill_per_second
            await self._sleep(wait_seconds)


@dataclass(frozen=True)
class RetryStats:
    """Count requests and rate-limit responses consumed by one operation."""

    request_count: int
    rate_limit_429s: int


def _status_code(error: Exception) -> int | None:
    for attribute in ("status_code", "code"):
        value = getattr(error, attribute, None)
        if isinstance(value, int):
            return value
    response = getattr(error, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _retry_after(error: Exception) -> float | None:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {})
    raw = headers.get("retry-after") if hasattr(headers, "get") else None
    if raw is None:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        try:
            return max(0.0, parsedate_to_datetime(raw).timestamp() - time())
        except (TypeError, ValueError):
            return None


async def call_with_backoff(
    operation: Callable[[], Awaitable[T]],
    *,
    limiter: TokenBucket,
    max_attempts: int = 5,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    random_value: Callable[[], float] = random.random,
) -> tuple[T, RetryStats]:
    """Retry 429/5xx responses with Retry-After or jittered exponential backoff."""

    rate_limits = 0
    for attempt in range(max_attempts):
        await limiter.acquire()
        try:
            return await operation(), RetryStats(attempt + 1, rate_limits)
        except Exception as error:
            status = _status_code(error)
            if status == 429:
                rate_limits += 1
            if status != 429 and (status is None or status < 500 or status >= 600):
                raise
            if attempt + 1 == max_attempts:
                raise
            delay = _retry_after(error)
            if delay is None:
                delay = min(30.0, 2.0**attempt) * (0.5 + random_value())
            await sleep(delay)
    raise RuntimeError("unreachable retry state")
