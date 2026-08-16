"""Real task progress derived from persisted pipeline step events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func

from docnexus.db import SessionLocal, TaskEvent, TaskRecord, WorkflowRun

TASK_STEP_TOTALS = {
    "document_edit": 4,
    "document_extract": 5,
    "table_fill": 8,
}


def _percent(completed: int, total: int) -> int:
    return round(max(0, min(completed, total)) / max(1, total) * 100)


def report_step(
    task_id: str,
    node_code: str,
    label: str,
    status: str,
    completed_steps: int,
    total_steps: int,
    detail: dict | None = None,
) -> None:
    """Create/update one event and synchronize task/workflow progress."""
    now = datetime.now()
    with SessionLocal() as db:
        task = db.get(TaskRecord, task_id)
        if task is None:
            return
        event = (
            db.query(TaskEvent)
            .filter(TaskEvent.task_id == task_id, TaskEvent.node_code == node_code, TaskEvent.status == "running")
            .order_by(TaskEvent.sequence.desc())
            .first()
        )
        if status == "running" or event is None:
            sequence = int(db.query(func.max(TaskEvent.sequence)).filter(TaskEvent.task_id == task_id).scalar() or 0) + 1
            event = TaskEvent(
                id=uuid.uuid4().hex,
                task_id=task_id,
                sequence=sequence,
                node_code=node_code,
                label=label,
                status=status,
                progress=_percent(completed_steps, total_steps),
                detail=detail or {},
                started_at=now,
                completed_at=now if status in {"completed", "failed", "skipped"} else None,
            )
            db.add(event)
        else:
            event.label = label
            event.status = status
            event.progress = _percent(completed_steps, total_steps)
            event.detail = detail or event.detail
            event.completed_at = now

        task.completed_steps = max(0, min(completed_steps, total_steps))
        task.total_steps = max(1, total_steps)
        task.progress = _percent(task.completed_steps, task.total_steps)
        task.stage = label[:100]
        run = db.query(WorkflowRun).filter(WorkflowRun.task_id == task_id).first()
        if run is not None:
            run.progress = task.progress
            run.current_node = task.stage[:80]
        db.commit()


def reset_progress(task_id: str) -> None:
    with SessionLocal() as db:
        task = db.get(TaskRecord, task_id)
        if task is None:
            return
        db.query(TaskEvent).filter(TaskEvent.task_id == task_id).delete()
        task.completed_steps = 0
        task.total_steps = TASK_STEP_TOTALS.get(task.kind, 1)
        task.progress = 0
        db.commit()


def serialize_events(task_id: str) -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(TaskEvent).filter(TaskEvent.task_id == task_id).order_by(TaskEvent.sequence).all()
        return [
            {
                "id": row.id,
                "sequence": row.sequence,
                "node_code": row.node_code,
                "label": row.label,
                "status": row.status,
                "progress": row.progress,
                "detail": row.detail,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "duration_ms": round((row.completed_at - row.started_at).total_seconds() * 1000)
                if row.started_at and row.completed_at
                else None,
            }
            for row in rows
        ]
