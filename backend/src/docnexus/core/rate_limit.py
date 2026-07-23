"""进程内滑动窗口限流。

单实例部署不依赖额外基础设施；横向扩容时可用 Redis 实现替换该中间件。
"""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request
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
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _rule(self, path: str) -> tuple[str, int] | None:
        if path in {"/auth/login", "/auth/register"}:
            return "auth", self.auth_limit
        if path.startswith(("/doc-extract/upload", "/table-fill", "/doc-chat/upload")):
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

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rule = self._rule(request.url.path)
        if rule is not None:
            bucket, limit = rule
            client_host = request.client.host if request.client else "unknown"
            allowed, retry_after = self._allowed(f"{bucket}:{client_host}", limit)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后重试"},
                    headers={"Retry-After": str(retry_after)},
                )
        return await call_next(request)
