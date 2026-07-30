"""企业租户、权限、审计与 API 密钥的确定性测试。"""

import asyncio
import hashlib
import uuid

import pytest
from docnexus.api.dependencies import get_current_user
from docnexus.api.routes.enterprise import create_template, delete_template, list_templates, update_template
from docnexus.db import ApiCredential, AuditLog, Base, User
from docnexus.schemas.enterprise import TemplateUpsert
from docnexus.services.enterprise import audit, ensure_context, reserve_monthly_run, subscription_for
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def enterprise_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _user(identifier: str = "enterprise-user") -> User:
    return User(
        id=identifier,
        username=identifier,
        email=f"{identifier}@example.com",
        password_hash="not-used",
        account_status="正常",
        role="普通用户",
    )


def _request(path: str = "/api/tasks") -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""})


def test_personal_organization_is_created_once(enterprise_db) -> None:
    user = _user()
    enterprise_db.add(user)
    enterprise_db.commit()

    first = ensure_context(enterprise_db, user)
    second = ensure_context(enterprise_db, user)
    subscription = subscription_for(enterprise_db, first)

    assert first.organization.id == second.organization.id
    assert first.membership.role == "owner"
    assert user.active_organization_id == first.organization.id
    assert subscription.limits["members"] == 3


def test_role_guard_and_audit_log_are_enforced(enterprise_db) -> None:
    user = _user("audit-user")
    enterprise_db.add(user)
    enterprise_db.commit()
    context = ensure_context(enterprise_db, user)
    context.membership.role = "viewer"

    with pytest.raises(HTTPException) as error:
        context.require("member")
    assert error.value.status_code == 403

    audit(enterprise_db, context, user, "document.read", "document", "doc-1", {"source": "test"})
    enterprise_db.commit()
    record = enterprise_db.query(AuditLog).one()
    assert record.organization_id == context.organization.id
    assert record.detail == {"source": "test"}


def test_api_key_authenticates_without_storing_plaintext(enterprise_db) -> None:
    user = _user("api-user")
    enterprise_db.add(user)
    enterprise_db.commit()
    context = ensure_context(enterprise_db, user)
    token = f"qn_{uuid.uuid4().hex}"
    credential = ApiCredential(
        id=uuid.uuid4().hex,
        organization_id=context.organization.id,
        user_id=user.id,
        name="test key",
        prefix=token[:11],
        key_hash=hashlib.sha256(token.encode()).hexdigest(),
        scopes=["workspace:read"],
    )
    enterprise_db.add(credential)
    enterprise_db.commit()

    authenticated = asyncio.run(
        get_current_user(_request(), HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), enterprise_db)
    )

    assert authenticated.id == user.id
    assert credential.key_hash != token
    assert credential.last_used_at is not None


def test_custom_templates_are_shared_through_persistence(enterprise_db) -> None:
    user = _user("template-user")
    enterprise_db.add(user)
    enterprise_db.commit()
    payload = TemplateUpsert(
        name="项目验收表",
        category="项目管理",
        scene="项目验收",
        fields=["项目名称", "验收结论"],
    )

    created = create_template(payload, enterprise_db, user)
    assert created["source"] == "custom"
    assert len(list_templates(enterprise_db, user)["items"]) > 1

    updated = update_template(
        str(created["id"]),
        payload.model_copy(update={"description": "团队统一验收模板"}),
        enterprise_db,
        user,
    )
    assert updated["description"] == "团队统一验收模板"

    delete_template(str(created["id"]), enterprise_db, user)
    assert all(item["id"] != created["id"] for item in list_templates(enterprise_db, user)["items"])


def test_monthly_run_quota_is_reserved_for_every_task_entry(enterprise_db) -> None:
    user = _user("quota-user")
    enterprise_db.add(user)
    enterprise_db.commit()
    context = ensure_context(enterprise_db, user)
    subscription = subscription_for(enterprise_db, context)
    subscription.limits = {**subscription.limits, "monthly_runs": 1}
    subscription.usage = {"monthly_runs": 0}

    reserve_monthly_run(enterprise_db, context)

    assert subscription.usage["monthly_runs"] == 1
    with pytest.raises(HTTPException) as error:
        reserve_monthly_run(enterprise_db, context)
    assert error.value.status_code == 409
