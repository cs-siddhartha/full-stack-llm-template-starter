import asyncio
import math
import time
from collections.abc import Callable
from dataclasses import dataclass

type Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Carry one limit decision and its client-visible response metadata."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int | None = None

    def as_headers(self) -> dict[str, str]:
        """Serialize standard rate metadata for success and error responses."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_at),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        return headers


@dataclass(slots=True)
class _WindowCounter:
    window_number: int
    requests: int


class InMemoryFixedWindowRateLimiter:
    """Limit one process safely; use shared storage for multi-worker deployments."""

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        clock: Clock = time.time,
    ) -> None:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("Rate limit and window must be positive")

        self._limit = limit
        self._window_seconds = window_seconds
        self._clock = clock
        self._counters: dict[str, _WindowCounter] = {}
        self._lock = asyncio.Lock()

    async def consume(self, key: str) -> RateLimitDecision:
        """Atomically consume capacity for a key in the current fixed window."""
        now = self._clock()
        window_number = int(now // self._window_seconds)
        reset_at = (window_number + 1) * self._window_seconds

        async with self._lock:
            counter = self._counters.get(key)
            if counter is None or counter.window_number != window_number:
                counter = _WindowCounter(window_number=window_number, requests=0)
                self._counters[key] = counter

            if counter.requests >= self._limit:
                return RateLimitDecision(
                    allowed=False,
                    limit=self._limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=max(1, math.ceil(reset_at - now)),
                )

            counter.requests += 1
            return RateLimitDecision(
                allowed=True,
                limit=self._limit,
                remaining=self._limit - counter.requests,
                reset_at=reset_at,
            )
