"""SQLAlchemy persistence models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
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


class ExtractionRecord(Base):
    __tablename__ = "extraction_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("task_records.id", ondelete="SET NULL"), index=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    file_type: Mapped[str] = mapped_column(String(20))
    fields_requested: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    content_preview: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="success", index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="extractions")


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
