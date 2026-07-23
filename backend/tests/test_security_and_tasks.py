from __future__ import annotations

import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest
from docnexus.api.dependencies import get_current_user
from docnexus.core.rate_limit import RateLimitMiddleware
from docnexus.core.security import AuthService
from docnexus.db.models import Base, User
from docnexus.repositories.extractions import ExtractionRepository
from docnexus.repositories.tasks import TaskRepository
from docnexus.schemas.auth import LoginRequest, UserCreate
from docnexus.services.document_parser import DocumentParser
from docnexus.services.upload_security import safe_filename, validate_upload_content
from docnexus.worker import tasks as worker_tasks
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import Headers, UploadFile


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _user(user_id: str, email: str) -> User:
    return User(id=user_id, username=user_id, email=email, password_hash="hash")


def test_extraction_records_are_strictly_isolated_by_user(db_session) -> None:
    db_session.add_all([_user("u1", "u1@example.com"), _user("u2", "u2@example.com")])
    db_session.commit()
    record = ExtractionRepository.save_extraction(
        db_session, "a.txt", "txt", ["名称"], {"名称": "A"}, user_id="u1"
    )
    assert ExtractionRepository.get_extraction(db_session, record.id, "u1") is not None
    assert ExtractionRepository.get_extraction(db_session, record.id, "u2") is None
    assert ExtractionRepository.delete_extraction(db_session, record.id, "u2") is False


def test_tasks_are_strictly_isolated_by_user(db_session) -> None:
    db_session.add_all([_user("u1", "u1@example.com"), _user("u2", "u2@example.com")])
    db_session.commit()
    task = TaskRepository.create(db_session, "u1", "document_extract", {})
    assert TaskRepository.get_owned(db_session, task.id, "u1") is not None
    assert TaskRepository.get_owned(db_session, task.id, "u2") is None


def test_incrementing_token_version_revokes_existing_token(db_session, monkeypatch) -> None:
    monkeypatch.setattr(
        "docnexus.core.security.get_settings",
        lambda: SimpleNamespace(
            access_token_expire_minutes=180,
            require_secret_key=lambda: "unit-test-secret-key-with-32-characters",
        ),
    )
    user = _user("u1", "u1@example.com")
    db_session.add(user)
    db_session.commit()
    token = AuthService.create_access_token({"sub": user.id, "ver": 0})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert asyncio.run(get_current_user(credentials, db_session)).id == user.id
    user.token_version = 1
    db_session.commit()
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(credentials, db_session))
    assert exc_info.value.status_code == 401


def test_safe_filename_removes_path_and_unsafe_characters() -> None:
    assert safe_filename("../../含 空格?.docx") == "含_空格_.docx"


def test_office_extension_cannot_hide_arbitrary_content() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_content("fake.docx", b"not-a-zip", {".docx"})
    assert exc_info.value.status_code == 400


def test_document_parser_preserves_client_error_status() -> None:
    upload = UploadFile(BytesIO(b"content"), filename="payload.exe", headers=Headers())
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(DocumentParser.parse_file(upload))
    assert exc_info.value.status_code == 400


def test_rate_limit_returns_retry_after(monkeypatch) -> None:
    monkeypatch.setattr(
        "docnexus.core.rate_limit.get_settings",
        lambda: SimpleNamespace(rate_limit_window_seconds=60, auth_rate_limit=1, ai_rate_limit=1),
    )
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.post("/auth/login")
    async def login():
        return {"ok": True}

    client = TestClient(app)
    assert client.post("/auth/login").status_code == 200
    response = client.post("/auth/login")
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


@pytest.mark.parametrize(
    "schema,payload",
    [
        (UserCreate, {"username": "tester", "email": "test@example.com", "password": "密" * 25}),
        (LoginRequest, {"email": "test@example.com", "password": "密" * 25}),
    ],
)
def test_auth_passwords_reject_more_than_72_utf8_bytes(schema, payload) -> None:
    with pytest.raises(ValidationError):
        schema.model_validate(payload)


def test_cancelled_task_is_not_overwritten_as_succeeded(monkeypatch) -> None:
    updates: list[dict[str, object]] = []
    monkeypatch.setattr(worker_tasks, "_execute", lambda _task_id: None)
    monkeypatch.setattr(worker_tasks, "_is_cancelled", lambda _task_id: True)
    monkeypatch.setattr(worker_tasks, "_update", lambda _task_id, **values: updates.append(values))

    worker_tasks.process_task.run("cancelled-task")

    assert updates == []
