"""企业组织、协作、集成、知识库、计费和运维接口。"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import redis
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from docnexus.ai.knowledge_graph.builder import KnowledgeGraphBuilder
from docnexus.api.dependencies import get_current_user
from docnexus.core.settings import get_settings
from docnexus.db import (
    ApiCredential,
    AuditLog,
    AutomationSchedule,
    BackupRecord,
    CollaborationComment,
    DocumentRecord,
    DocumentVersion,
    ExtractionRecord,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeItem,
    Notification,
    Organization,
    OrganizationMember,
    ReviewRecord,
    TaskRecord,
    User,
    WebhookDelivery,
    WebhookEndpoint,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowVersion,
    engine,
    get_db,
)
from docnexus.schemas.enterprise import (
    ApiKeyCreate,
    CommentCreate,
    KnowledgeCreate,
    KnowledgeItemCreate,
    MemberCreate,
    MemberUpdate,
    OrganizationUpdate,
    PlanUpdate,
    ScheduleCreate,
    WebhookCreate,
)
from docnexus.services.enterprise import PLAN_LIMITS, audit, ensure_context, subscription_for
from docnexus.services.knowledge import hybrid_search, index_document
from docnexus.services.scheduling import next_cron_time
from docnexus.services.webhooks import publish_event
from docnexus.worker.celery_app import celery_app

router = APIRouter(prefix="/enterprise", tags=["企业平台"])
settings = get_settings()


def _encrypt_webhook_secret(secret: str) -> str:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.require_secret_key().encode()).digest())
    return Fernet(key).encrypt(secret.encode()).decode()


def _member_data(db: Session, member: OrganizationMember) -> dict:
    user = db.query(User).filter_by(id=member.user_id).first()
    return {
        "id": member.id,
        "user_id": member.user_id,
        "username": user.username if user else "已注销用户",
        "email": user.email if user else "",
        "role": member.role,
        "status": member.status,
        "joined_at": member.joined_at,
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    org_id = context.organization.id
    subscription = subscription_for(db, context)
    storage = (
        db.query(func.coalesce(func.sum(DocumentRecord.size_bytes), 0)).filter_by(organization_id=org_id).scalar() or 0
    )
    run_counts: dict[str, int] = {
        str(run_status): int(count)
        for run_status, count in db.query(WorkflowRun.status, func.count(WorkflowRun.id))
        .filter_by(organization_id=org_id)
        .group_by(WorkflowRun.status)
        .all()
    }
    return {
        "organization": {
            "id": org_id,
            "name": context.organization.name,
            "slug": context.organization.slug,
            "plan": context.organization.plan,
            "role": context.membership.role,
        },
        "metrics": {
            "members": db.query(func.count(OrganizationMember.id))
            .filter_by(organization_id=org_id, status="active")
            .scalar()
            or 0,
            "documents": db.query(func.count(DocumentRecord.id)).filter_by(organization_id=org_id).scalar() or 0,
            "storage_bytes": int(storage),
            "workflow_runs": sum(run_counts.values()),
            "run_counts": run_counts,
            "pending_reviews": db.query(func.count(ReviewRecord.id))
            .filter_by(organization_id=org_id, status="pending")
            .scalar()
            or 0,
            "unread_notifications": db.query(func.count(Notification.id))
            .filter(Notification.user_id == user.id, Notification.read_at.is_(None))
            .scalar()
            or 0,
        },
        "subscription": {
            "plan": subscription.plan,
            "status": subscription.status,
            "limits": subscription.limits,
            "usage": subscription.usage,
        },
    }


@router.get("/organization")
def get_organization(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    members = (
        db.query(OrganizationMember)
        .filter_by(organization_id=context.organization.id)
        .order_by(OrganizationMember.joined_at)
        .all()
    )
    return {
        "id": context.organization.id,
        "name": context.organization.name,
        "slug": context.organization.slug,
        "plan": context.organization.plan,
        "role": context.membership.role,
        "members": [_member_data(db, item) for item in members],
    }


@router.get("/organizations")
def list_organizations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_context(db, user)
    rows = (
        db.query(OrganizationMember)
        .filter_by(user_id=user.id, status="active")
        .order_by(OrganizationMember.joined_at)
        .all()
    )
    result = []
    for membership in rows:
        organization = db.query(Organization).filter_by(id=membership.organization_id, status="active").first()
        if organization:
            result.append(
                {
                    "id": organization.id,
                    "name": organization.name,
                    "slug": organization.slug,
                    "plan": organization.plan,
                    "role": membership.role,
                    "active": organization.id == user.active_organization_id,
                }
            )
    return {"items": result}


@router.post("/organizations/{organization_id}/activate")
def activate_organization(
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = (
        db.query(OrganizationMember)
        .filter_by(organization_id=organization_id, user_id=user.id, status="active")
        .first()
    )
    if membership is None:
        raise HTTPException(404, "组织空间不存在或无权访问")
    user.active_organization_id = organization_id
    db.commit()
    return {"organization_id": organization_id, "active": True}


@router.put("/organization")
def update_organization(
    payload: OrganizationUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    context = ensure_context(db, user)
    context.require("admin")
    before = context.organization.name
    context.organization.name = payload.name
    audit(
        db,
        context,
        user,
        "organization.update",
        "organization",
        context.organization.id,
        {"before": before, "after": payload.name},
        request.client.host if request.client else None,
    )
    db.commit()
    return {"id": context.organization.id, "name": context.organization.name}


@router.post("/members", status_code=status.HTTP_201_CREATED)
def add_member(payload: MemberCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    target = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if target is None:
        raise HTTPException(404, "该邮箱尚未注册，请先邀请对方完成注册")
    if db.query(OrganizationMember).filter_by(organization_id=context.organization.id, user_id=target.id).first():
        raise HTTPException(409, "该用户已在当前组织中")
    subscription = subscription_for(db, context)
    count = (
        db.query(func.count(OrganizationMember.id))
        .filter_by(organization_id=context.organization.id, status="active")
        .scalar()
        or 0
    )
    if count >= int(subscription.limits.get("members", 3)):
        raise HTTPException(409, "当前套餐的成员数量已达上限")
    member = OrganizationMember(
        id=uuid.uuid4().hex, organization_id=context.organization.id, user_id=target.id, role=payload.role
    )
    db.add(member)
    db.add(
        Notification(
            id=uuid.uuid4().hex,
            user_id=target.id,
            kind="organization",
            title="你已加入新的团队",
            content=f"{user.username} 将你加入了 {context.organization.name}",
            link="/workspace/enterprise",
        )
    )
    audit(db, context, user, "member.add", "member", target.id, {"role": payload.role})
    db.commit()
    db.refresh(member)
    return _member_data(db, member)


@router.put("/members/{member_id}")
def update_member(
    member_id: str, payload: MemberUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    context = ensure_context(db, user)
    context.require("admin")
    member = db.query(OrganizationMember).filter_by(id=member_id, organization_id=context.organization.id).first()
    if member is None:
        raise HTTPException(404, "成员不存在")
    if member.role == "owner":
        raise HTTPException(409, "不能修改组织所有者角色")
    member.role = payload.role
    audit(db, context, user, "member.role.update", "member", member.user_id, {"role": payload.role})
    db.commit()
    return _member_data(db, member)


@router.delete("/members/{member_id}", status_code=204)
def remove_member(member_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    member = db.query(OrganizationMember).filter_by(id=member_id, organization_id=context.organization.id).first()
    if member is None:
        raise HTTPException(404, "成员不存在")
    if member.role == "owner":
        raise HTTPException(409, "不能移除组织所有者")
    member.status = "removed"
    audit(db, context, user, "member.remove", "member", member.user_id)
    db.commit()


@router.get("/audit-logs")
def audit_logs(
    action: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    context = ensure_context(db, user)
    context.require("admin")
    query = db.query(AuditLog).filter_by(organization_id=context.organization.id)
    if action:
        query = query.filter(AuditLog.action == action)
    records = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "action": item.action,
                "resource_type": item.resource_type,
                "resource_id": item.resource_id,
                "detail": item.detail,
                "ip_address": item.ip_address,
                "created_at": item.created_at,
            }
            for item in records
        ]
    }


@router.post("/comments", status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("member")
    comment = CollaborationComment(
        id=uuid.uuid4().hex, organization_id=context.organization.id, user_id=user.id, **payload.model_dump()
    )
    db.add(comment)
    member_ids = {
        row[0]
        for row in db.query(OrganizationMember.user_id)
        .filter_by(organization_id=context.organization.id, status="active")
        .all()
    }
    for mentioned_id in set(payload.mentions) & member_ids - {user.id}:
        db.add(
            Notification(
                id=uuid.uuid4().hex,
                user_id=mentioned_id,
                kind="mention",
                title="你在协作评论中被提及",
                content=payload.content[:300],
                link=f"/workspace/{payload.resource_type}s",
            )
        )
    audit(db, context, user, "comment.create", payload.resource_type, payload.resource_id)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "content": comment.content,
        "resolved": comment.resolved,
        "created_at": comment.created_at,
    }


@router.get("/comments")
def list_comments(
    resource_type: str, resource_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    context = ensure_context(db, user)
    records = (
        db.query(CollaborationComment)
        .filter_by(organization_id=context.organization.id, resource_type=resource_type, resource_id=resource_id)
        .order_by(CollaborationComment.created_at)
        .all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "content": item.content,
                "mentions": item.mentions,
                "resolved": item.resolved,
                "created_at": item.created_at,
            }
            for item in records
        ]
    }


@router.patch("/comments/{comment_id}/resolve")
def resolve_comment(comment_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("reviewer")
    comment = db.query(CollaborationComment).filter_by(id=comment_id, organization_id=context.organization.id).first()
    if comment is None:
        raise HTTPException(404, "评论不存在")
    comment.resolved = not comment.resolved
    audit(db, context, user, "comment.resolve", comment.resource_type, comment.resource_id)
    db.commit()
    return {"id": comment.id, "resolved": comment.resolved}


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    records = (
        db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(100).all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "kind": item.kind,
                "title": item.title,
                "content": item.content,
                "link": item.link,
                "read": item.read_at is not None,
                "created_at": item.created_at,
            }
            for item in records
        ]
    }


@router.post("/notifications/read-all", status_code=204)
def read_all_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.read_at.is_(None)).update(
        {"read_at": datetime.now()}
    )
    db.commit()


@router.post("/documents/{document_id}/versions", status_code=201)
def create_document_version(
    document_id: str, note: str = "", db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    context = ensure_context(db, user)
    context.require("member")
    document = db.query(DocumentRecord).filter_by(id=document_id, organization_id=context.organization.id).first()
    if document is None or not Path(document.storage_path).is_file():
        raise HTTPException(404, "文档不存在")
    version = (db.query(func.max(DocumentVersion.version)).filter_by(document_id=document.id).scalar() or 0) + 1
    source = Path(document.storage_path)
    target_dir = settings.data_dir / "versions" / context.organization.id / document.id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"v{version}-{source.name}"
    target.write_bytes(source.read_bytes())
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    record = DocumentVersion(
        id=uuid.uuid4().hex,
        document_id=document.id,
        user_id=user.id,
        version=version,
        storage_path=str(target),
        size_bytes=target.stat().st_size,
        checksum=checksum,
        note=note[:500],
    )
    db.add(record)
    audit(db, context, user, "document.version.create", "document", document.id, {"version": version})
    db.commit()
    return {
        "id": record.id,
        "version": version,
        "checksum": checksum,
        "note": record.note,
        "created_at": record.created_at,
    }


@router.get("/documents/{document_id}/versions")
def list_document_versions(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    if db.query(DocumentRecord).filter_by(id=document_id, organization_id=context.organization.id).first() is None:
        raise HTTPException(404, "文档不存在")
    records = (
        db.query(DocumentVersion).filter_by(document_id=document_id).order_by(DocumentVersion.version.desc()).all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "version": item.version,
                "size_bytes": item.size_bytes,
                "checksum": item.checksum,
                "note": item.note,
                "created_at": item.created_at,
            }
            for item in records
        ]
    }


@router.get("/api-keys")
def list_api_keys(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    rows = (
        db.query(ApiCredential)
        .filter_by(organization_id=context.organization.id)
        .order_by(ApiCredential.created_at.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "prefix": row.prefix,
                "scopes": row.scopes,
                "expires_at": row.expires_at,
                "last_used_at": row.last_used_at,
                "revoked": row.revoked_at is not None,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.post("/api-keys", status_code=201)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    token = f"qn_{secrets.token_urlsafe(32)}"
    prefix = token[:11]
    record = ApiCredential(
        id=uuid.uuid4().hex,
        organization_id=context.organization.id,
        user_id=user.id,
        name=payload.name,
        prefix=prefix,
        key_hash=hashlib.sha256(token.encode()).hexdigest(),
        scopes=payload.scopes,
        expires_at=datetime.now() + timedelta(days=payload.expires_in_days) if payload.expires_in_days else None,
    )
    db.add(record)
    audit(db, context, user, "api_key.create", "api_key", record.id, {"name": payload.name, "scopes": payload.scopes})
    db.commit()
    return {
        "id": record.id,
        "name": record.name,
        "key": token,
        "prefix": prefix,
        "warning": "密钥仅显示一次，请立即保存",
    }


@router.delete("/api-keys/{key_id}", status_code=204)
def revoke_api_key(key_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    record = db.query(ApiCredential).filter_by(id=key_id, organization_id=context.organization.id).first()
    if record is None:
        raise HTTPException(404, "密钥不存在")
    record.revoked_at = datetime.now()
    audit(db, context, user, "api_key.revoke", "api_key", record.id)
    db.commit()


@router.get("/webhooks")
def list_webhooks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    rows = db.query(WebhookEndpoint).filter_by(organization_id=context.organization.id).all()
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "url": row.url,
                "events": row.events,
                "active": row.active,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.post("/webhooks", status_code=201)
def create_webhook(payload: WebhookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    secret = secrets.token_urlsafe(32)
    row = WebhookEndpoint(
        id=uuid.uuid4().hex,
        organization_id=context.organization.id,
        name=payload.name,
        url=str(payload.url),
        events=payload.events,
        secret_hash=hashlib.sha256(secret.encode()).hexdigest(),
        secret_ciphertext=_encrypt_webhook_secret(secret),
    )
    db.add(row)
    audit(db, context, user, "webhook.create", "webhook", row.id, {"events": payload.events})
    db.commit()
    return {
        "id": row.id,
        "name": row.name,
        "url": row.url,
        "events": row.events,
        "signing_secret": secret,
        "warning": "签名密钥仅显示一次；投递器启用后将使用 HMAC-SHA256 签名",
    }


@router.delete("/webhooks/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    row = db.query(WebhookEndpoint).filter_by(id=webhook_id, organization_id=context.organization.id).first()
    if row is None:
        raise HTTPException(404, "Webhook 不存在")
    db.delete(row)
    audit(db, context, user, "webhook.delete", "webhook", webhook_id)
    db.commit()


@router.post("/webhooks/{webhook_id}/test", status_code=202)
def test_webhook(webhook_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    endpoint = db.query(WebhookEndpoint).filter_by(id=webhook_id, organization_id=context.organization.id).first()
    if endpoint is None:
        raise HTTPException(404, "Webhook 不存在")
    event_name = (endpoint.events or ["webhook.test"])[0]
    delivery_ids = publish_event(context.organization.id, event_name, {"message": "慧文融通 Webhook 测试事件"})
    return {"queued": len(delivery_ids), "delivery_ids": delivery_ids}


@router.get("/webhook-deliveries")
def webhook_deliveries(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    context = ensure_context(db, user)
    context.require("admin")
    rows = (
        db.query(WebhookDelivery)
        .filter_by(organization_id=context.organization.id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"items": [
        {
            "id": row.id,
            "event": row.event,
            "status": row.status,
            "attempts": row.attempts,
            "response_status": row.response_status,
            "error_message": row.error_message,
            "created_at": row.created_at,
            "delivered_at": row.delivered_at,
        }
        for row in rows
    ]}


@router.get("/knowledge")
def list_knowledge(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    rows = (
        db.query(KnowledgeCollection)
        .filter_by(organization_id=context.organization.id)
        .order_by(KnowledgeCollection.updated_at.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "retrieval_mode": row.retrieval_mode,
                "documents": db.query(func.count(KnowledgeItem.id)).filter_by(collection_id=row.id).scalar() or 0,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]
    }


@router.post("/knowledge", status_code=201)
def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("member")
    row = KnowledgeCollection(
        id=uuid.uuid4().hex, organization_id=context.organization.id, owner_id=user.id, **payload.model_dump()
    )
    db.add(row)
    audit(db, context, user, "knowledge.create", "knowledge", row.id)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "description": row.description, "retrieval_mode": row.retrieval_mode}


@router.post("/knowledge/{collection_id}/documents", status_code=201)
def add_knowledge_document(
    collection_id: str,
    payload: KnowledgeItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    context = ensure_context(db, user)
    context.require("member")
    collection = (
        db.query(KnowledgeCollection).filter_by(id=collection_id, organization_id=context.organization.id).first()
    )
    document = (
        db.query(DocumentRecord).filter_by(id=payload.document_id, organization_id=context.organization.id).first()
    )
    if collection is None or document is None:
        raise HTTPException(404, "知识库或文档不存在")
    if db.query(KnowledgeItem).filter_by(collection_id=collection.id, document_id=document.id).first():
        raise HTTPException(409, "文档已在知识库中")
    chunks = index_document(db, collection.id, document)
    row = KnowledgeItem(id=uuid.uuid4().hex, collection_id=collection.id, document_id=document.id, chunk_count=chunks)
    db.add(row)
    audit(db, context, user, "knowledge.document.add", "knowledge", collection.id, {"document_id": document.id})
    db.commit()
    return {"id": row.id, "document_id": document.id, "status": row.status, "chunk_count": chunks}


@router.get("/knowledge/{collection_id}/search")
def search_knowledge(
    collection_id: str,
    query: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    context = ensure_context(db, user)
    collection = (
        db.query(KnowledgeCollection).filter_by(id=collection_id, organization_id=context.organization.id).first()
    )
    if collection is None:
        raise HTTPException(404, "知识库不存在")
    results = hybrid_search(db, collection.id, query, collection.retrieval_mode, limit)
    return {
        "query": query,
        "mode": collection.retrieval_mode,
        "provider": "local_hybrid_vector",
        "items": results,
    }


@router.get("/knowledge/{collection_id}/documents")
def list_knowledge_documents(
    collection_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    context = ensure_context(db, user)
    collection = db.query(KnowledgeCollection).filter_by(id=collection_id, organization_id=context.organization.id).first()
    if collection is None:
        raise HTTPException(404, "知识库不存在")
    rows = db.query(KnowledgeItem).filter_by(collection_id=collection_id).all()
    documents = {item.id: item for item in db.query(DocumentRecord).filter(DocumentRecord.id.in_([row.document_id for row in rows])).all()} if rows else {}
    return {
        "items": [
            {
                "id": row.id,
                "document_id": row.document_id,
                "filename": documents[row.document_id].filename if row.document_id in documents else "未知文档",
                "status": row.status,
                "chunk_count": row.chunk_count,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.get("/knowledge/{collection_id}/graph")
def knowledge_graph(
    collection_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    context = ensure_context(db, user)
    collection = (
        db.query(KnowledgeCollection).filter_by(id=collection_id, organization_id=context.organization.id).first()
    )
    if collection is None:
        raise HTTPException(404, "知识库不存在")
    document_ids = [row[0] for row in db.query(KnowledgeItem.document_id).filter_by(collection_id=collection.id).all()]
    extractions = (
        db.query(ExtractionRecord).filter(ExtractionRecord.document_id.in_(document_ids)).all() if document_ids else []
    )
    builder = KnowledgeGraphBuilder()
    entities: dict[str, dict] = {}
    relations: dict[str, dict] = {}
    documents = db.query(DocumentRecord).filter(DocumentRecord.id.in_(document_ids)).all() if document_ids else []
    for document in documents:
        entity_id = f"document:{document.id}"
        entities[entity_id] = {
            "entity_id": entity_id,
            "entity_type": "文档",
            "name": document.filename,
            "attributes": {"file_type": document.file_type, "category": document.category},
            "source_ids": [document.id],
            "source_document_id": document.id,
            "source_filename": document.filename,
        }
    chunks = db.query(KnowledgeChunk).filter_by(collection_id=collection.id).all()
    for chunk in chunks:
        entity_id = f"chunk:{chunk.id}"
        source_document = next((item for item in documents if item.id == chunk.document_id), None)
        entities[entity_id] = {
            "entity_id": entity_id,
            "entity_type": "片段",
            "name": f"片段 {chunk.chunk_index + 1}",
            "attributes": {"preview": chunk.content[:160], **(chunk.location or {})},
            "source_ids": [chunk.document_id],
            "source_document_id": chunk.document_id,
            "source_filename": source_document.filename if source_document else "未知文档",
        }
        relation_id = f"contains:{chunk.document_id}:{chunk.id}"
        relations[relation_id] = {
            "relation_id": relation_id,
            "source_entity_id": f"document:{chunk.document_id}",
            "target_entity_id": entity_id,
            "relation_type": "包含",
            "attributes": {},
            "source_document_id": chunk.document_id,
        }
    for extraction in extractions:
        graph = builder.from_extraction_result(
            extraction.extracted_data or {}, graph_id=f"document:{extraction.document_id}"
        )
        for entity in graph.entities:
            item = entity.to_dict()
            item["source_document_id"] = extraction.document_id
            source_document = next((row for row in documents if row.id == extraction.document_id), None)
            item["source_filename"] = source_document.filename if source_document else "未知文档"
            if entity.entity_type == "文档":
                item["name"] = item["source_filename"]
            entities[entity.entity_id] = item
        for relation in graph.relations:
            item = relation.to_dict()
            item["source_document_id"] = extraction.document_id
            relations[relation.relation_id] = item
    return {
        "collection_id": collection.id,
        "entities": list(entities.values()),
        "relations": list(relations.values()),
        "metadata": {
            "connected_to_main_pipeline": True,
            "entity_count": len(entities),
            "relation_count": len(relations),
        },
    }


@router.get("/schedules")
def list_schedules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    rows = (
        db.query(AutomationSchedule)
        .filter_by(organization_id=context.organization.id)
        .order_by(AutomationSchedule.created_at.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "workflow_id": row.workflow_id,
                "document_id": row.document_id,
                "name": row.name,
                "cron_expression": row.cron_expression,
                "timezone": row.timezone,
                "status": row.status,
                "retry_limit": row.retry_limit,
                "last_run_at": row.last_run_at,
                "next_run_at": row.next_run_at,
                "last_status": row.last_status,
            }
            for row in rows
        ]
    }


@router.post("/schedules", status_code=201)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("member")
    if db.query(WorkflowDefinition).filter_by(id=payload.workflow_id, organization_id=context.organization.id).first() is None:
        raise HTTPException(404, "工作流不存在")
    if db.query(DocumentRecord).filter_by(id=payload.document_id, organization_id=context.organization.id).first() is None:
        raise HTTPException(404, "计划任务使用的文档不存在")
    try:
        next_run_at = next_cron_time(payload.cron_expression, payload.timezone)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    row = AutomationSchedule(
        id=uuid.uuid4().hex,
        organization_id=context.organization.id,
        user_id=user.id,
        next_run_at=next_run_at,
        **payload.model_dump(),
    )
    db.add(row)
    audit(db, context, user, "schedule.create", "schedule", row.id)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "cron_expression": row.cron_expression, "status": row.status, "next_run_at": row.next_run_at}


@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("member")
    row = db.query(AutomationSchedule).filter_by(id=schedule_id, organization_id=context.organization.id).first()
    if row is None:
        raise HTTPException(404, "计划不存在")
    db.delete(row)
    audit(db, context, user, "schedule.delete", "schedule", schedule_id)
    db.commit()


@router.put("/subscription")
def change_plan(payload: PlanUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("owner")
    subscription = subscription_for(db, context)
    subscription.plan = payload.plan
    subscription.limits = PLAN_LIMITS[payload.plan]
    context.organization.plan = payload.plan
    audit(
        db,
        context,
        user,
        "subscription.plan.change",
        "subscription",
        subscription.id,
        {"plan": payload.plan, "provider": "manual"},
    )
    db.commit()
    return {
        "plan": subscription.plan,
        "status": subscription.status,
        "limits": subscription.limits,
        "billing_provider": "manual",
        "message": "已更新本地套餐；生产收款需配置支付适配器",
    }


@router.get("/operations")
def operations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    tasks: dict[str, int] = {
        str(task_status): int(count)
        for task_status, count in db.query(TaskRecord.status, func.count(TaskRecord.id))
        .filter_by(organization_id=context.organization.id)
        .group_by(TaskRecord.status)
        .all()
    }
    recent_errors = (
        db.query(TaskRecord)
        .filter_by(organization_id=context.organization.id, status="failed")
        .order_by(TaskRecord.updated_at.desc())
        .limit(10)
        .all()
    )
    services: dict[str, dict] = {}
    started = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        services["database"] = {"status": "healthy", "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except Exception as exc:
        services["database"] = {"status": "unavailable", "message": str(exc)[:120]}
    started = time.perf_counter()
    try:
        with redis.from_url(settings.redis_url, socket_timeout=1) as client:
            client.ping()
        services["redis"] = {"status": "healthy", "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except Exception as exc:
        services["redis"] = {"status": "unavailable", "message": str(exc)[:120]}
    try:
        replies = celery_app.control.inspect(timeout=0.8).ping() or {}
        services["queue"] = {"status": "healthy" if replies else "unavailable", "workers": len(replies)}
    except Exception as exc:
        services["queue"] = {"status": "unavailable", "message": str(exc)[:120]}
    provider = os.getenv("LLM_PROVIDER", "openai")
    key_name = "DASHSCOPE_API_KEY" if provider == "aliyun" else "OPENAI_API_KEY"
    services["model"] = {"status": "configured" if os.getenv(key_name) else "unconfigured", "provider": provider}
    services["api"] = {"status": "healthy"}
    return {
        "task_counts": tasks,
        "recent_errors": [
            {
                "id": row.id,
                "kind": row.kind,
                "error_code": row.error_code,
                "error_message": row.error_message,
                "updated_at": row.updated_at,
            }
            for row in recent_errors
        ],
        "services": services,
    }


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    org_id = context.organization.id
    reviews = db.query(ReviewRecord).filter_by(organization_id=org_id).all()
    confidences = [
        float(field.get("confidence", 0))
        for review in reviews
        for field in (review.fields or [])
        if isinstance(field, dict)
    ]
    runs = db.query(WorkflowRun).filter_by(organization_id=org_id).all()
    succeeded = sum(1 for run in runs if run.status == "succeeded")
    corrected = sum(
        1 for review in reviews for field in (review.fields or []) if isinstance(field, dict) and field.get("corrected")
    )
    daily: dict[str, dict[str, int]] = {}
    for run in runs:
        day = run.created_at.date().isoformat()
        bucket = daily.setdefault(day, {"runs": 0, "succeeded": 0, "failed": 0})
        bucket["runs"] += 1
        if run.status in bucket:
            bucket[run.status] += 1
    return {
        "quality": {
            "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0,
            "corrected_fields": corrected,
            "reviewed": sum(1 for review in reviews if review.status == "approved"),
        },
        "execution": {
            "total": len(runs),
            "success_rate": round(succeeded / len(runs), 4) if runs else 0,
            "daily": [{"date": day, **values} for day, values in sorted(daily.items())[-30:]],
        },
    }


@router.get("/backups")
def list_backups(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    rows = (
        db.query(BackupRecord)
        .filter_by(organization_id=context.organization.id)
        .order_by(BackupRecord.created_at.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "status": row.status,
                "size_bytes": row.size_bytes,
                "checksum": row.checksum,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.post("/backups", status_code=201)
def create_backup(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    context.require("admin")
    backup_id = uuid.uuid4().hex
    backup_dir = settings.data_dir / "backups" / context.organization.id
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{backup_id}.zip"
    documents = db.query(DocumentRecord).filter_by(organization_id=context.organization.id).all()
    manifest = {
        "version": 1,
        "organization_id": context.organization.id,
        "created_at": datetime.now().isoformat(),
        "documents": [
            {"id": row.id, "filename": row.filename, "category": row.category, "tags": row.tags} for row in documents
        ],
    }
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for row in documents:
            source = Path(row.storage_path)
            if source.is_file():
                archive.write(source, f"documents/{row.id}/{source.name}")
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    record = BackupRecord(
        id=backup_id,
        organization_id=context.organization.id,
        user_id=user.id,
        storage_path=str(target),
        size_bytes=target.stat().st_size,
        checksum=checksum,
    )
    db.add(record)
    audit(db, context, user, "backup.create", "backup", backup_id, {"documents": len(documents)})
    db.commit()
    return {
        "id": backup_id,
        "status": "completed",
        "size_bytes": record.size_bytes,
        "checksum": checksum,
        "message": "备份包含清单和原始文档；数据库灾备仍应由 PostgreSQL 基础设施负责",
    }


@router.get("/workflow-versions/{workflow_id}")
def workflow_versions(workflow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = ensure_context(db, user)
    if db.query(WorkflowDefinition).filter_by(id=workflow_id, organization_id=context.organization.id).first() is None:
        raise HTTPException(404, "工作流不存在")
    rows = db.query(WorkflowVersion).filter_by(workflow_id=workflow_id).order_by(WorkflowVersion.version.desc()).all()
    return {
        "items": [
            {
                "id": row.id,
                "version": row.version,
                "snapshot": row.snapshot,
                "note": row.note,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }
