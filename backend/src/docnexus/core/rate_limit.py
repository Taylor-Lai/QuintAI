"""API rate limiting with a shared Redis backend in production.

Development keeps an in-process sliding window so the service and test suite do
not require infrastructure. Production deliberately fails closed when Redis is
unavailable: silently disabling an authentication/AI abuse control would be a
security failure, not graceful degradation.
"""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from docnexus.core.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.window = settings.rate_limit_window_seconds
        self.auth_limit = settings.auth_rate_limit
        self.ai_limit = settings.ai_rate_limit
        self._production = getattr(settings, "app_env", "development").lower() == "production"
        self._redis = (
            Redis.from_url(getattr(settings, "redis_url", "redis://localhost:6379/0"))
            if self._production
            else None
        )
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _rule(self, path: str) -> tuple[str, int] | None:
        if path in {"/api/auth/login", "/api/auth/register", "/auth/login", "/auth/register"}:
            return "auth", self.auth_limit
        if path.startswith(
            (
                "/api/doc-extract/upload",
                "/api/table-fill",
                "/api/doc-chat/upload",
                "/doc-extract/upload",
                "/table-fill",
                "/doc-chat/upload",
            )
        ):
            return "ai", self.ai_limit
        return None

    def _allowed(self, key: str, limit: int) -> tuple[bool, int]:
        now = monotonic()
        cutoff = now - self.window
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(self.window - (now - events[0])))
                return False, retry_after
            events.append(now)
        return True, 0

    async def _allowed_shared(self, key: str, limit: int) -> tuple[bool, int]:
        """Apply a shared fixed-window counter atomically in Redis."""
        assert self._redis is not None
        redis_key = f"huiwen:rate-limit:{key}"
        try:
            count = await self._redis.incr(redis_key)
            if count == 1:
                await self._redis.expire(redis_key, self.window)
            ttl = await self._redis.ttl(redis_key)
        except RedisError as exc:
            raise RuntimeError("Rate-limit storage is unavailable") from exc
        return count <= limit, max(1, ttl if ttl > 0 else self.window)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rule = self._rule(request.url.path)
        if rule is not None:
            bucket, limit = rule
            client_host = request.client.host if request.client else "unknown"
            key = f"{bucket}:{client_host}"
            try:
                allowed, retry_after = (
                    await self._allowed_shared(key, limit) if self._production else self._allowed(key, limit)
                )
            except RuntimeError:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "请求保护服务暂不可用，请稍后重试"},
                    headers={"Retry-After": "5"},
                )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后重试"},
                    headers={"Retry-After": str(retry_after)},
                )
        return await call_next(request)
