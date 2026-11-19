import math
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Literal, ParamSpec, Protocol, TypeVar

from fastapi import HTTPException, Request, Response, status
from redis.asyncio import Redis

P = ParamSpec("P")
R = TypeVar("R")
RateLimitKey = Literal["ip", "session"]

_RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    limit: int
    window_seconds: int


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int | None = None

    def as_headers(self) -> dict[str, str]:
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_at),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class RateLimiter(Protocol):
    def policy(self, name: str) -> RateLimitPolicy: ...

    async def consume(self, name: str, key: str) -> RateLimitDecision: ...


class RedisRateLimiter:
    """Apply atomic fixed-window policies through Redis."""

    def __init__(
        self,
        client: Redis,
        namespace: str,
        policies: dict[str, RateLimitPolicy],
    ) -> None:
        self._client = client
        self._prefix = f"{namespace}:rate-limit"
        self._policies = policies

    def policy(self, name: str) -> RateLimitPolicy:
        return self._policies[name]

    async def consume(self, name: str, key: str) -> RateLimitDecision:
        policy = self.policy(name)
        redis_key = f"{self._prefix}:{name}:{key}"
        count, ttl = await self._client.eval(
            _RATE_LIMIT_SCRIPT,
            1,
            redis_key,
            policy.window_seconds,
        )
        ttl = max(1, int(ttl))
        count = int(count)
        allowed = count <= policy.limit
        return RateLimitDecision(
            allowed=allowed,
            limit=policy.limit,
            remaining=max(0, policy.limit - count),
            reset_at=int(time.time()) + ttl,
            retry_after=ttl if not allowed else None,
        )


@dataclass(slots=True)
class _WindowCounter:
    window_number: int
    requests: int


class InMemoryRateLimiter:
    """Provide deterministic fixed-window policies for isolated tests."""

    def __init__(
        self,
        policies: dict[str, RateLimitPolicy],
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._policies = policies
        self._clock = clock
        self._counters: dict[tuple[str, str], _WindowCounter] = {}

    def policy(self, name: str) -> RateLimitPolicy:
        return self._policies[name]

    async def consume(self, name: str, key: str) -> RateLimitDecision:
        policy = self.policy(name)
        now = self._clock()
        window_number = int(now // policy.window_seconds)
        reset_at = (window_number + 1) * policy.window_seconds
        counter_key = (name, key)
        counter = self._counters.get(counter_key)
        if counter is None or counter.window_number != window_number:
            counter = _WindowCounter(window_number=window_number, requests=0)
            self._counters[counter_key] = counter

        if counter.requests >= policy.limit:
            return RateLimitDecision(
                allowed=False,
                limit=policy.limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=max(1, math.ceil(reset_at - now)),
            )

        counter.requests += 1
        return RateLimitDecision(
            allowed=True,
            limit=policy.limit,
            remaining=policy.limit - counter.requests,
            reset_at=reset_at,
        )


def rate_limited(
    policy_name: str,
    *,
    key: RateLimitKey,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Enforce a named policy after FastAPI resolves endpoint dependencies."""

    def decorate(endpoint: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(endpoint)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            context = kwargs["context"]
            request = kwargs["http_request"]
            if not isinstance(request, Request):
                raise RuntimeError("Rate-limited endpoints require http_request")

            if key == "session":
                current_session = kwargs["session"]
                identity = current_session.user.user_id
            else:
                identity = request.client.host if request.client else "unknown"

            decision = await context.rate_limiter.consume(policy_name, identity)
            if not decision.allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers=decision.as_headers(),
                )

            response = kwargs.get("response")
            if isinstance(response, Response):
                response.headers.update(decision.as_headers())
            return await endpoint(*args, **kwargs)

        return wrapped

    return decorate
