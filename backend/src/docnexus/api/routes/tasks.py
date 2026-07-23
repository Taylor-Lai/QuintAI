from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.db import TaskRecord, User, get_db
from docnexus.repositories.tasks import TaskRepository
from docnexus.worker.celery_app import celery_app
from docnexus.worker.tasks import process_task

router = APIRouter(prefix="/tasks", tags=["任务"])


def serialize_task(task: TaskRecord) -> dict[str, object]:
    return {
        "id": task.id,
        "kind": task.kind,
        "status": task.status,
        "progress": task.progress,
        "stage": task.stage,
        "result": task.result_data,
        "has_file": bool(task.output_path),
        "filename": task.output_name,
        "error": {"code": task.error_code, "message": task.error_message} if task.error_message else None,
        "attempts": task.attempts,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


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
    return serialize_task(task)


@router.get("/{task_id}/download")
def download_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = TaskRepository.get_owned(db, task_id, user.id)
    if task is None or task.status != "succeeded" or not task.output_path:
        raise HTTPException(404, "任务结果文件不存在")
    path = Path(task.output_path)
    if not path.is_file():
        raise HTTPException(410, "任务结果文件已过期")
    return FileResponse(path, filename=task.output_name)


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
    db.commit()
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
    db.commit()
    enqueue(task)
    return serialize_task(task)
