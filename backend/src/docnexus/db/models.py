"""SQLAlchemy persistence models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docnexus.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(80))
    gender: Mapped[str | None] = mapped_column(String(10))
    phone: Mapped[str | None] = mapped_column(String(20))
    account_status: Mapped[str] = mapped_column(String(20), default="正常", index=True)
    role: Mapped[str] = mapped_column(String(20), default="普通用户", index=True)
    token_version: Mapped[int] = mapped_column(default=0)
    last_login_at: Mapped[datetime | None]
    last_login_ip: Mapped[str | None] = mapped_column(String(64))
    last_activity_at: Mapped[datetime | None]
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    extractions: Mapped[list[ExtractionRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list[TaskRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[list[DocumentRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[list[ReviewRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
    workflows: Mapped[list[WorkflowDefinition]] = relationship(back_populates="user", cascade="all, delete-orphan")
    workflow_runs: Mapped[list[WorkflowRun]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ExtractionRecord(Base):
    __tablename__ = "extraction_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("task_records.id", ondelete="SET NULL"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("document_records.id", ondelete="SET NULL"), index=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    file_type: Mapped[str] = mapped_column(String(20))
    fields_requested: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    content_preview: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="success", index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="extractions")
    document: Mapped[DocumentRecord | None] = relationship(back_populates="extractions")
    review: Mapped[ReviewRecord | None] = relationship(back_populates="extraction", uselist=False)


class TaskRecord(Base):
    __tablename__ = "task_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    celery_task_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    progress: Mapped[int] = mapped_column(default=0)
    stage: Mapped[str] = mapped_column(String(100), default="等待执行")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_path: Mapped[str | None] = mapped_column(Text)
    output_name: Mapped[str | None] = mapped_column(String(255))
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=2)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="tasks")


class DocumentRecord(Base):
    """A durable document asset in the user's workspace."""

    __tablename__ = "document_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    file_type: Mapped[str] = mapped_column(String(30), index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_path: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="upload", index=True)
    category: Mapped[str] = mapped_column(String(80), default="未分类", index=True)
    status: Mapped[str] = mapped_column(String(30), default="ready", index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    content_preview: Mapped[str] = mapped_column(Text, default="")
    metadata_data: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="documents")
    extractions: Mapped[list[ExtractionRecord]] = relationship(back_populates="document")
    reviews: Mapped[list[ReviewRecord]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ReviewRecord(Base):
    """Human review state for evidence-backed extracted fields."""

    __tablename__ = "review_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("document_records.id", ondelete="CASCADE"), index=True)
    extraction_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("extraction_records.id", ondelete="SET NULL"), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", index=True)
    fields: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    validation_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    validation_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="reviews")
    document: Mapped[DocumentRecord | None] = relationship(back_populates="reviews")
    extraction: Mapped[ExtractionRecord | None] = relationship(back_populates="review")


class WorkflowDefinition(Base):
    """Versioned, user-owned document workflow definition."""

    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    version: Mapped[int] = mapped_column(default=1)
    nodes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    rules: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    runs_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="workflows")
    runs: Mapped[list[WorkflowRun]] = relationship(back_populates="workflow", cascade="all, delete-orphan")


class WorkflowRun(Base):
    """Execution record connecting a workflow, document and async task."""

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workflow_id: Mapped[str] = mapped_column(String(32), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(String(32), ForeignKey("document_records.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("task_records.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    current_node: Mapped[str] = mapped_column(String(80), default="文档接收")
    progress: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="workflow_runs")
    workflow: Mapped[WorkflowDefinition] = relationship(back_populates="runs")
    document: Mapped[DocumentRecord] = relationship()
    task: Mapped[TaskRecord | None] = relationship()
