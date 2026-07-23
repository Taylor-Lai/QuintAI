"""Contract tests for the public HTTP surface."""

from docnexus.main import app
from fastapi.routing import APIRoute

EXPECTED_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("POST", "/api/upload"),
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/doc-extract/search"),
    ("GET", "/doc-extract"),
    ("GET", "/doc-extract/{record_id}"),
    ("DELETE", "/doc-extract/{record_id}"),
    ("POST", "/auth/register"),
    ("POST", "/auth/login"),
    ("POST", "/auth/logout"),
    ("POST", "/auth/heartbeat"),
    ("GET", "/user/profile"),
    ("PUT", "/user/profile"),
    ("POST", "/doc-chat/upload"),
    ("POST", "/doc-extract/upload"),
    ("POST", "/table-fill/upload"),
    ("GET", "/tasks"),
    ("GET", "/tasks/{task_id}"),
    ("GET", "/tasks/{task_id}/download"),
    ("POST", "/tasks/{task_id}/cancel"),
    ("POST", "/tasks/{task_id}/retry"),
    ("GET", "/admin/users"),
    ("GET", "/admin/users/{user_id}"),
    ("PUT", "/admin/users/{user_id}/status"),
    ("PUT", "/admin/users/{user_id}/role"),
    ("DELETE", "/admin/users/{user_id}"),
    ("GET", "/admin/statistics"),
}


def test_public_route_contract_is_preserved() -> None:
    actual = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
        if method not in {"HEAD", "OPTIONS"}
    }
    assert EXPECTED_ROUTES <= actual
