"""组织租户、权限、审计与用量服务。"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from docnexus.db import AuditLog, DocumentRecord, Organization, OrganizationMember, Subscription, User

PLAN_LIMITS = {
    "starter": {"members": 3, "documents": 500, "monthly_runs": 200, "storage_bytes": 2 * 1024**3},
    "team": {"members": 20, "documents": 10000, "monthly_runs": 5000, "storage_bytes": 50 * 1024**3},
    "enterprise": {"members": 9999, "documents": 999999, "monthly_runs": 999999, "storage_bytes": 1024**4},
}
ROLE_LEVEL = {"viewer": 10, "member": 20, "reviewer": 30, "admin": 40, "owner": 50}


@dataclass(slots=True)
class EnterpriseContext:
    organization: Organization
    membership: OrganizationMember

    def require(self, role: str) -> None:
        if ROLE_LEVEL.get(self.membership.role, 0) < ROLE_LEVEL[role]:
            raise HTTPException(403, "当前成员角色无权执行此操作")


def _slug(value: str, user_id: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:45] or "workspace"
    return f"{normalized}-{user_id[:8]}"


def ensure_context(db: Session, user: User) -> EnterpriseContext:
    organization: Organization | None
    membership = None
    if user.active_organization_id:
        membership = (
            db.query(OrganizationMember)
            .filter_by(organization_id=user.active_organization_id, user_id=user.id, status="active")
            .first()
        )
    if membership is None:
        membership = db.query(OrganizationMember).filter_by(user_id=user.id, status="active").first()
    if membership is None:
        organization = Organization(
            id=uuid.uuid4().hex,
            owner_id=user.id,
            name=f"{user.nickname or user.username}的团队",
            slug=_slug(user.username, user.id),
            plan="starter",
        )
        membership = OrganizationMember(
            id=uuid.uuid4().hex, organization_id=organization.id, user_id=user.id, role="owner"
        )
        subscription = Subscription(
            id=uuid.uuid4().hex,
            organization_id=organization.id,
            plan="starter",
            limits=PLAN_LIMITS["starter"],
            usage={"monthly_runs": 0},
            period_end=datetime.now() + timedelta(days=30),
        )
        db.add_all([organization, membership, subscription])
        user.active_organization_id = organization.id
        try:
            db.flush()
            for relation in (
                user.documents,
                user.reviews,
                user.workflows,
                user.workflow_runs,
                user.tasks,
                user.extractions,
            ):
                for record in relation:
                    if record.organization_id is None:
                        record.organization_id = organization.id
            db.commit()
        except IntegrityError:
            # 首次打开工作台时多个并发请求可能同时初始化个人组织。
            db.rollback()
            membership = db.query(OrganizationMember).filter_by(user_id=user.id, status="active").first()
            if membership is None:
                raise
            organization = db.query(Organization).filter_by(id=membership.organization_id, status="active").first()
            if organization is None:
                raise
    else:
        organization = db.query(Organization).filter_by(id=membership.organization_id, status="active").first()
        if organization is None:
            raise HTTPException(403, "组织空间已停用")
        if user.active_organization_id != organization.id:
            user.active_organization_id = organization.id
            db.commit()
    assert organization is not None and membership is not None
    return EnterpriseContext(organization=organization, membership=membership)


def audit(
    db: Session,
    context: EnterpriseContext,
    user: User,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            id=uuid.uuid4().hex,
            organization_id=context.organization.id,
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail or {},
            ip_address=ip_address,
        )
    )


def subscription_for(db: Session, context: EnterpriseContext) -> Subscription:
    subscription = db.query(Subscription).filter_by(organization_id=context.organization.id).first()
    if subscription is None:
        subscription = Subscription(
            id=uuid.uuid4().hex,
            organization_id=context.organization.id,
            plan=context.organization.plan,
            limits=PLAN_LIMITS.get(context.organization.plan, PLAN_LIMITS["starter"]),
            usage={"monthly_runs": 0},
        )
        db.add(subscription)
        db.flush()
    return subscription


def reserve_monthly_run(db: Session, context: EnterpriseContext) -> Subscription:
    """Reserve one AI/workflow run inside the caller's transaction."""
    subscription = (
        db.query(Subscription)
        .filter_by(organization_id=context.organization.id)
        .with_for_update()
        .first()
    )
    if subscription is None:
        subscription = subscription_for(db, context)
    now = datetime.now()
    if subscription.period_end is None or subscription.period_end <= now:
        subscription.period_start = now
        subscription.period_end = now + timedelta(days=30)
        subscription.usage = {**(subscription.usage or {}), "monthly_runs": 0}
    usage = dict(subscription.usage or {})
    used = int(usage.get("monthly_runs", 0))
    limit = int(subscription.limits.get("monthly_runs", PLAN_LIMITS["starter"]["monthly_runs"]))
    if used >= limit:
        raise HTTPException(409, "当前套餐的本周期任务运行次数已达上限")
    usage["monthly_runs"] = used + 1
    subscription.usage = usage
    return subscription


def ensure_document_capacity(
    db: Session,
    context: EnterpriseContext,
    *,
    additional_documents: int,
    additional_bytes: int,
) -> None:
    """Validate organization document and storage quotas in the current transaction."""
    subscription = subscription_for(db, context)
    current_documents = (
        db.query(func.count(DocumentRecord.id))
        .filter(DocumentRecord.organization_id == context.organization.id)
        .scalar()
        or 0
    )
    current_storage = (
        db.query(func.coalesce(func.sum(DocumentRecord.size_bytes), 0))
        .filter(DocumentRecord.organization_id == context.organization.id)
        .scalar()
        or 0
    )
    if current_documents + additional_documents > int(subscription.limits.get("documents", 500)):
        raise HTTPException(409, "当前套餐的文档数量已达上限")
    if current_storage + additional_bytes > int(subscription.limits.get("storage_bytes", 2 * 1024**3)):
        raise HTTPException(409, "当前套餐的文档存储空间已达上限")
