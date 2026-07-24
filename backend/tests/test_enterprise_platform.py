"""企业租户、权限、审计与 API 密钥的确定性测试。"""

import asyncio
import hashlib
import uuid

import pytest
from docnexus.api.dependencies import get_current_user
from docnexus.db import ApiCredential, AuditLog, Base, User
from docnexus.services.enterprise import audit, ensure_context, subscription_for
from fastapi import HTTPException
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
        get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), enterprise_db)
    )

    assert authenticated.id == user.id
    assert credential.key_hash != token
    assert credential.last_used_at is not None
