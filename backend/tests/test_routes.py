"""Contract tests for the public HTTP surface."""

from docnexus.main import app
from fastapi.testclient import TestClient

UNPREFIXED_API_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/metrics"),
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
    ("GET", "/tasks/{task_id}/report"),
    ("DELETE", "/tasks/{task_id}"),
    ("POST", "/tasks/{task_id}/cancel"),
    ("POST", "/tasks/{task_id}/retry"),
    ("GET", "/admin/users"),
    ("GET", "/admin/users/{user_id}"),
    ("PUT", "/admin/users/{user_id}/status"),
    ("PUT", "/admin/users/{user_id}/role"),
    ("DELETE", "/admin/users/{user_id}"),
    ("GET", "/admin/statistics"),
    ("GET", "/workspace/overview"),
    ("POST", "/workspace/demo"),
    ("POST", "/workspace/documents"),
    ("GET", "/workspace/documents"),
    ("GET", "/workspace/documents/export"),
    ("PATCH", "/workspace/documents/{document_id}"),
    ("GET", "/workspace/documents/{document_id}/download"),
    ("DELETE", "/workspace/documents/{document_id}"),
    ("GET", "/workspace/reviews"),
    ("GET", "/workspace/reviews/{review_id}"),
    ("POST", "/workspace/reviews/bulk"),
    ("PUT", "/workspace/reviews/{review_id}"),
    ("POST", "/workspace/reviews/{review_id}/auto-fix"),
    ("GET", "/workspace/workflows"),
    ("POST", "/workspace/workflows"),
    ("PUT", "/workspace/workflows/{workflow_id}"),
    ("DELETE", "/workspace/workflows/{workflow_id}"),
    ("POST", "/workspace/workflows/{workflow_id}/runs"),
    ("GET", "/workspace/workflow-runs"),
    ("GET", "/enterprise/dashboard"),
    ("GET", "/enterprise/organization"),
    ("GET", "/enterprise/organizations"),
    ("POST", "/enterprise/organizations/{organization_id}/activate"),
    ("PUT", "/enterprise/organization"),
    ("POST", "/enterprise/members"),
    ("PUT", "/enterprise/members/{member_id}"),
    ("DELETE", "/enterprise/members/{member_id}"),
    ("GET", "/enterprise/audit-logs"),
    ("POST", "/enterprise/comments"),
    ("GET", "/enterprise/comments"),
    ("PATCH", "/enterprise/comments/{comment_id}/resolve"),
    ("GET", "/enterprise/notifications"),
    ("POST", "/enterprise/notifications/read-all"),
    ("POST", "/enterprise/documents/{document_id}/versions"),
    ("GET", "/enterprise/documents/{document_id}/versions"),
    ("GET", "/enterprise/api-keys"),
    ("POST", "/enterprise/api-keys"),
    ("DELETE", "/enterprise/api-keys/{key_id}"),
    ("GET", "/enterprise/webhooks"),
    ("POST", "/enterprise/webhooks"),
    ("DELETE", "/enterprise/webhooks/{webhook_id}"),
    ("POST", "/enterprise/webhooks/{webhook_id}/test"),
    ("GET", "/enterprise/webhook-deliveries"),
    ("GET", "/enterprise/templates"),
    ("POST", "/enterprise/templates"),
    ("PUT", "/enterprise/templates/{template_id}"),
    ("DELETE", "/enterprise/templates/{template_id}"),
    ("GET", "/enterprise/knowledge"),
    ("POST", "/enterprise/knowledge"),
    ("POST", "/enterprise/knowledge/{collection_id}/documents"),
    ("GET", "/enterprise/knowledge/{collection_id}/documents"),
    ("GET", "/enterprise/knowledge/{collection_id}/search"),
    ("GET", "/enterprise/knowledge/{collection_id}/graph"),
    ("POST", "/enterprise/knowledge/{collection_id}/graph/rebuild"),
    ("PATCH", "/enterprise/knowledge/{collection_id}/graph/entities/{entity_id}"),
    ("GET", "/enterprise/schedules"),
    ("POST", "/enterprise/schedules"),
    ("DELETE", "/enterprise/schedules/{schedule_id}"),
    ("PUT", "/enterprise/subscription"),
    ("GET", "/enterprise/operations"),
    ("GET", "/enterprise/analytics"),
    ("GET", "/enterprise/backups"),
    ("POST", "/enterprise/backups"),
    ("GET", "/enterprise/backups/{backup_id}/download"),
    ("GET", "/enterprise/workflow-versions/{workflow_id}"),
}

EXPECTED_ROUTES = {(method, f"/api{path}") for method, path in UNPREFIXED_API_ROUTES}


def test_public_route_contract_is_exact() -> None:
    schema = app.openapi()
    actual = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.upper() not in {"HEAD", "OPTIONS", "PARAMETERS"}
    }
    assert actual == EXPECTED_ROUTES


def test_api_prefix_is_owned_by_fastapi() -> None:
    client = TestClient(app)

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/docs").status_code == 200
    assert client.get("/health").status_code == 404
