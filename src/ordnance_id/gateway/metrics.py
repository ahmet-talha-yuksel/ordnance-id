"""Expose provider-neutral token, retry, latency, and cache telemetry."""

from pydantic import BaseModel, Field


class CallMetrics(BaseModel):
    """Describe one structured provider call without retaining prompts or images."""

    provider: str
    model: str
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    retries: int = Field(default=0, ge=0)
    request_count: int = Field(default=1, ge=0)
    duration_ms: float = Field(default=0.0, ge=0)
    rate_limit_429s: int = Field(default=0, ge=0)
    cache_hit: bool = False
