"""HTTP tracing, structured logs and baseline security headers."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("docnexus.http")
http_requests: dict[tuple[str, str, int], int] = defaultdict(int)
http_duration_seconds: dict[tuple[str, str], float] = defaultdict(float)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(json_logs: bool) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if json_logs else logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class OperationalMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied_id = request.headers.get("X-Request-ID", "")
        request_id = supplied_id if supplied_id.isalnum() and len(supplied_id) <= 64 else uuid.uuid4().hex
        token = request_id_context.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            http_requests[(request.method, route_path, response.status_code)] += 1
            http_duration_seconds[(request.method, route_path)] += duration_ms / 1000
            logger.info("%s %s %s %.2fms", request.method, request.url.path, response.status_code, duration_ms)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            return response
        finally:
            request_id_context.reset(token)


def render_prometheus_metrics() -> str:
    lines = [
        "# HELP huiwenrongtong_http_requests_total Total HTTP requests.",
        "# TYPE huiwenrongtong_http_requests_total counter",
    ]
    for (method, path, status_code), count in sorted(http_requests.items()):
        lines.append(f'huiwenrongtong_http_requests_total{{method="{method}",path="{path}",status="{status_code}"}} {count}')
    lines.extend(
        [
            "# HELP huiwenrongtong_http_request_duration_seconds_sum Cumulative HTTP request duration.",
            "# TYPE huiwenrongtong_http_request_duration_seconds_sum counter",
        ]
    )
    for (method, path), duration in sorted(http_duration_seconds.items()):
        lines.append(f'huiwenrongtong_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {duration:.6f}')
    return "\n".join(lines) + "\n"
