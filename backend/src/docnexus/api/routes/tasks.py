import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.core.settings import get_settings
from docnexus.db import DocumentRecord, TaskRecord, User, WorkflowRun, get_db
from docnexus.repositories.tasks import TaskRepository
from docnexus.services.task_progress import report_step, reset_progress, serialize_events
from docnexus.worker.celery_app import celery_app
from docnexus.worker.tasks import process_task

router = APIRouter(prefix="/tasks", tags=["任务"])
logger = logging.getLogger(__name__)


def serialize_task(task: TaskRecord, include_events: bool = False) -> dict[str, object]:
    payload = {
        "id": task.id,
        "kind": task.kind,
        "status": task.status,
        "progress": task.progress,
        "completed_steps": task.completed_steps,
        "total_steps": task.total_steps,
        "progress_source": "pipeline_steps",
        "stage": task.stage,
        "result": task.result_data,
        "has_file": bool(task.output_path),
        "filename": task.output_name,
        "error": {"code": task.error_code, "message": task.error_message} if task.error_message else None,
        "attempts": task.attempts,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "quality_report": task.quality_report,
        "evidence_summary": task.evidence_summary,
    }
    if include_events:
        payload["events"] = serialize_events(task.id)
    return payload


def enqueue(task: TaskRecord) -> None:
    process_task.apply_async(args=[task.id], task_id=task.celery_task_id)


@router.get("")
def list_tasks(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": [serialize_task(item) for item in TaskRepository.list_owned(db, user.id, limit)]}


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    return serialize_task(task, include_events=True)


@router.get("/{task_id}/report")
def get_task_report(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    return {
        "task_id": task.id,
        "kind": task.kind,
        "status": task.status,
        "quality": task.quality_report,
        "evidence": task.evidence_summary,
        "events": serialize_events(task.id),
    }


@router.get("/{task_id}/download")
def download_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None or task.status != "succeeded" or not task.output_path:
        raise HTTPException(404, "任务结果文件不存在")
    path = Path(task.output_path)
    if not path.is_file():
        raise HTTPException(410, "任务结果文件已过期")
    return FileResponse(path, filename=task.output_name)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    if task.status not in {"succeeded", "failed", "cancelled"}:
        raise HTTPException(409, "运行中的任务不能删除，请先取消任务")

    output_path = Path(task.output_path).resolve() if task.output_path else None
    data_root = get_settings().data_dir.resolve()
    task_root = (data_root / "tasks" / task.id).resolve()
    retained_document = (
        db.query(DocumentRecord)
        .filter(DocumentRecord.storage_path.startswith(str(task_root)))
        .first()
    )
    db.delete(task)
    db.commit()

    if retained_document is None and task_root.is_relative_to(data_root) and task_root.is_dir():
        try:
            shutil.rmtree(task_root)
        except OSError:
            logger.warning("Unable to remove task workspace after deleting task %s", task_id, exc_info=True)
    elif output_path and output_path.is_relative_to(data_root) and output_path.is_file():
        try:
            output_path.unlink()
        except OSError:
            logger.warning("Unable to remove task output after deleting task %s", task_id, exc_info=True)


@router.post("/{task_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    if task.status in {"succeeded", "failed", "cancelled"}:
        raise HTTPException(409, "任务已经结束")
    task.cancel_requested = True
    task.status = "cancelled"
    task.stage = "已取消"
    workflow_run = db.query(WorkflowRun).filter(WorkflowRun.task_id == task.id).first()
    if workflow_run is not None:
        workflow_run.status = "cancelled"
        workflow_run.current_node = "已取消"
    db.commit()
    report_step(task.id, "cancelled", "任务已由用户取消", "failed", task.completed_steps, task.total_steps)
    celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")
    return serialize_task(task)


@router.post("/{task_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    if task.status not in {"failed", "cancelled"}:
        raise HTTPException(409, "只有失败或取消的任务可以重试")
    import uuid
    task.celery_task_id = str(uuid.uuid4())
    task.status = "queued"
    task.progress = 0
    task.stage = "等待重试"
    task.cancel_requested = False
    task.error_code = None
    task.error_message = None
    workflow_run = db.query(WorkflowRun).filter(WorkflowRun.task_id == task.id).first()
    if workflow_run is not None:
        workflow_run.status = "queued"
        workflow_run.progress = 0
        workflow_run.current_node = "等待重试"
        workflow_run.error_message = None
        workflow_run.completed_at = None
    db.commit()
    reset_progress(task.id)
    enqueue(task)
    return serialize_task(task)
