from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from docnexus.core.settings import get_settings
from docnexus.db import TaskRecord


class TaskRepository:
    @staticmethod
    def create(db: Session, user_id: str, kind: str, payload: dict[str, object]) -> TaskRecord:
        record = TaskRecord(
            id=uuid.uuid4().hex,
            celery_task_id=str(uuid.uuid4()),
            user_id=user_id,
            kind=kind,
            payload=payload,
            status="queued",
            progress=0,
            stage="等待执行",
            max_attempts=get_settings().task_max_attempts,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_owned(db: Session, task_id: str, user_id: str) -> TaskRecord | None:
        return db.query(TaskRecord).filter(TaskRecord.id == task_id, TaskRecord.user_id == user_id).first()

    @staticmethod
    def list_owned(db: Session, user_id: str, limit: int = 50) -> list[TaskRecord]:
        return db.query(TaskRecord).filter(TaskRecord.user_id == user_id).order_by(TaskRecord.created_at.desc()).limit(limit).all()
