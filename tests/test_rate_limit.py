import httpx
import pytest

from ordnance_id.gateway.rate_limit import TokenBucket, call_with_backoff


class FakeTime:
    def __init__(self) -> None:
        self.value = 0.0

    def clock(self) -> float:
        return self.value

    async def sleep(self, seconds: float) -> None:
        self.value += seconds


async def test_token_bucket_spaces_requests_at_configured_rpm() -> None:
    fake = FakeTime()
    limiter = TokenBucket(10, clock=fake.clock, sleep=fake.sleep)
    starts: list[float] = []
    for _index in range(4):
        await limiter.acquire()
        starts.append(fake.clock())
    assert starts == pytest.approx([0.0, 6.0, 12.0, 18.0])


async def test_429_honors_retry_after_with_httpx_mock() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "2"}, request=request)
        return httpx.Response(200, text="ok", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    fake = FakeTime()
    limiter = TokenBucket(60, clock=fake.clock, sleep=fake.sleep)

    async def operation() -> str:
        response = await client.get("https://example.test")
        response.raise_for_status()
        return response.text

    result, stats = await call_with_backoff(
        operation,
        limiter=limiter,
        sleep=fake.sleep,
        random_value=lambda: 0.0,
    )
    assert result == "ok"
    assert stats.request_count == 2
    assert stats.rate_limit_429s == 1
    assert fake.value >= 2.0
    await client.aclose()
