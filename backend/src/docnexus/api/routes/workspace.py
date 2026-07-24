"""Product workspace APIs for documents, reviews and workflows."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.api.routes.tasks import enqueue
from docnexus.core.settings import get_settings
from docnexus.db import DocumentRecord, ReviewRecord, TaskRecord, User, WorkflowDefinition, WorkflowRun, get_db
from docnexus.repositories.tasks import TaskRepository
from docnexus.schemas.workspace import DocumentUpdate, ReviewUpdate, WorkflowCreate, WorkflowRunCreate, WorkflowUpdate
from docnexus.services.upload_security import save_upload_safely
from docnexus.services.validation import validate_fields

router = APIRouter(prefix="/workspace", tags=["文档工作台"])
settings = get_settings()
ALLOWED_DOCUMENT_TYPES = {".docx", ".xlsx", ".xls", ".txt", ".md", ".pdf", ".csv"}


def _document_data(record: DocumentRecord) -> dict:
    return {
        "id": record.id, "filename": record.filename, "file_type": record.file_type,
        "size_bytes": record.size_bytes, "source": record.source, "category": record.category,
        "status": record.status, "tags": record.tags or [], "content_preview": record.content_preview,
        "metadata": record.metadata_data or {}, "created_at": record.created_at, "updated_at": record.updated_at,
    }


def _review_data(record: ReviewRecord) -> dict:
    return {
        "id": record.id, "document_id": record.document_id, "extraction_id": record.extraction_id,
        "title": record.title, "status": record.status, "priority": record.priority,
        "fields": record.fields or [], "validation_results": record.validation_results or [],
        "note": record.note, "reviewed_at": record.reviewed_at, "created_at": record.created_at,
        "updated_at": record.updated_at,
        "document": _document_data(record.document) if record.document else None,
    }


def _workflow_data(record: WorkflowDefinition) -> dict:
    return {
        "id": record.id, "name": record.name, "description": record.description,
        "status": record.status, "version": record.version, "nodes": record.nodes or [],
        "rules": record.rules or [], "runs_count": record.runs_count,
        "created_at": record.created_at, "updated_at": record.updated_at,
    }


def _workflow_run_data(record: WorkflowRun) -> dict:
    return {
        "id": record.id, "workflow_id": record.workflow_id, "document_id": record.document_id,
        "task_id": record.task_id, "status": record.status, "current_node": record.current_node,
        "progress": record.progress, "error_message": record.error_message,
        "workflow_name": record.workflow.name if record.workflow else "",
        "document_name": record.document.filename if record.document else "",
        "started_at": record.started_at, "completed_at": record.completed_at, "created_at": record.created_at,
    }


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    document_counts = dict(db.query(DocumentRecord.status, func.count(DocumentRecord.id)).filter(DocumentRecord.user_id == user.id).group_by(DocumentRecord.status).all())
    review_counts = dict(db.query(ReviewRecord.status, func.count(ReviewRecord.id)).filter(ReviewRecord.user_id == user.id).group_by(ReviewRecord.status).all())
    active_tasks = db.query(func.count(TaskRecord.id)).filter(TaskRecord.user_id == user.id, TaskRecord.status.in_(["queued", "running", "retrying"])).scalar() or 0
    workflow_count = db.query(func.count(WorkflowDefinition.id)).filter(WorkflowDefinition.user_id == user.id, WorkflowDefinition.status == "active").scalar() or 0
    recent = db.query(DocumentRecord).filter(DocumentRecord.user_id == user.id).order_by(DocumentRecord.created_at.desc()).limit(5).all()
    return {
        "documents_total": sum(document_counts.values()), "document_counts": document_counts,
        "pending_reviews": review_counts.get("pending", 0), "review_counts": review_counts,
        "active_tasks": active_tasks, "active_workflows": workflow_count,
        "recent_documents": [_document_data(item) for item in recent],
    }


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile] = File(...), category: str = Form("未分类"), tags: str = Form(""),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    if len(files) > settings.max_upload_files:
        raise HTTPException(400, f"单次最多上传 {settings.max_upload_files} 个文件")
    tag_list = list(dict.fromkeys(item.strip() for item in tags.replace("，", ",").split(",") if item.strip()))[:20]
    created: list[DocumentRecord] = []
    batch_dir = settings.data_dir / "documents" / user.id / uuid.uuid4().hex
    try:
        for upload in files:
            path, size = await save_upload_safely(upload, batch_dir, ALLOWED_DOCUMENT_TYPES)
            record = DocumentRecord(
                id=uuid.uuid4().hex, user_id=user.id, filename=path.name,
                file_type=path.suffix.lstrip(".").lower(), size_bytes=size, storage_path=str(path),
                category=category.strip()[:80] or "未分类", tags=tag_list,
            )
            db.add(record)
            created.append(record)
        db.commit()
        for record in created:
            db.refresh(record)
        return {"items": [_document_data(item) for item in created]}
    except Exception:
        db.rollback()
        shutil.rmtree(batch_dir, ignore_errors=True)
        raise


@router.get("/documents")
def list_documents(
    keyword: str = Query("", max_length=100), category: str | None = None,
    document_status: str | None = Query(None, alias="status"), limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(DocumentRecord).filter(DocumentRecord.user_id == user.id)
    if keyword:
        query = query.filter(or_(DocumentRecord.filename.contains(keyword), DocumentRecord.content_preview.contains(keyword)))
    if category:
        query = query.filter(DocumentRecord.category == category)
    if document_status:
        query = query.filter(DocumentRecord.status == document_status)
    total = query.count()
    records = query.order_by(DocumentRecord.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": [_document_data(item) for item in records], "total": total, "limit": limit, "offset": offset}


@router.patch("/documents/{document_id}")
def update_document(document_id: str, payload: DocumentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id, DocumentRecord.user_id == user.id).first()
    if record is None:
        raise HTTPException(404, "文档不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return _document_data(record)


@router.get("/documents/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id, DocumentRecord.user_id == user.id).first()
    if record is None or not Path(record.storage_path).is_file():
        raise HTTPException(404, "文档不存在")
    return FileResponse(record.storage_path, filename=record.filename)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id, DocumentRecord.user_id == user.id).first()
    if record is None:
        raise HTTPException(404, "文档不存在")
    path = Path(record.storage_path)
    db.delete(record)
    db.commit()
    path.unlink(missing_ok=True)


@router.get("/reviews")
def list_reviews(
    review_status: str | None = Query(None, alias="status"), limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(ReviewRecord).filter(ReviewRecord.user_id == user.id)
    if review_status:
        query = query.filter(ReviewRecord.status == review_status)
    records = query.order_by(ReviewRecord.created_at.desc()).limit(limit).all()
    return {"items": [_review_data(item) for item in records]}


@router.get("/reviews/{review_id}")
def get_review(review_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(ReviewRecord).filter(ReviewRecord.id == review_id, ReviewRecord.user_id == user.id).first()
    if record is None:
        raise HTTPException(404, "复核任务不存在")
    return _review_data(record)


@router.put("/reviews/{review_id}")
def update_review(review_id: str, payload: ReviewUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(ReviewRecord).filter(ReviewRecord.id == review_id, ReviewRecord.user_id == user.id).first()
    if record is None:
        raise HTTPException(404, "复核任务不存在")
    fields = [item.model_dump() for item in payload.fields]
    record.fields = fields
    record.validation_results = validate_fields(fields, record.validation_rules or [])
    record.note = payload.note
    if payload.action == "approve":
        if any(item["level"] == "error" for item in record.validation_results):
            raise HTTPException(409, "仍有未解决的错误，无法通过复核")
        record.status = "approved"
        record.reviewed_at = datetime.now()
    elif payload.action == "reject":
        record.status = "rejected"
        record.reviewed_at = datetime.now()
    elif payload.action == "reopen":
        record.status = "pending"
        record.reviewed_at = None
    else:
        record.status = "in_review"
    if record.document:
        record.document.status = "completed" if record.status == "approved" else "needs_review"
    db.commit()
    db.refresh(record)
    return _review_data(record)


@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    records = db.query(WorkflowDefinition).filter(WorkflowDefinition.user_id == user.id).order_by(WorkflowDefinition.updated_at.desc()).all()
    return {"items": [_workflow_data(item) for item in records]}


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = WorkflowDefinition(id=uuid.uuid4().hex, user_id=user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _workflow_data(record)


@router.put("/workflows/{workflow_id}")
def update_workflow(workflow_id: str, payload: WorkflowUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == workflow_id, WorkflowDefinition.user_id == user.id).first()
    if record is None:
        raise HTTPException(404, "工作流不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    record.version += 1
    db.commit()
    db.refresh(record)
    return _workflow_data(record)


@router.delete("/workflows/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == workflow_id, WorkflowDefinition.user_id == user.id).first()
    if record is None:
        raise HTTPException(404, "工作流不存在")
    db.delete(record)
    db.commit()


@router.post("/workflows/{workflow_id}/runs", status_code=status.HTTP_202_ACCEPTED)
def run_workflow(
    workflow_id: str, payload: WorkflowRunCreate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    workflow = db.query(WorkflowDefinition).filter(
        WorkflowDefinition.id == workflow_id, WorkflowDefinition.user_id == user.id
    ).first()
    if workflow is None:
        raise HTTPException(404, "工作流不存在")
    if workflow.status != "active":
        raise HTTPException(409, "只有已启用的工作流可以运行")
    document = db.query(DocumentRecord).filter(
        DocumentRecord.id == payload.document_id, DocumentRecord.user_id == user.id
    ).first()
    if document is None:
        raise HTTPException(404, "文档不存在")
    if document.file_type not in {"docx", "xlsx", "txt", "md"}:
        raise HTTPException(400, "当前信息提取节点支持 Word、Excel、TXT 和 Markdown 文档")
    extraction_node = next((node for node in workflow.nodes or [] if node.get("type") == "extract"), None)
    if extraction_node is None:
        raise HTTPException(400, "工作流缺少信息提取节点")
    fields = [str(item).strip() for item in extraction_node.get("fields", []) if str(item).strip()]
    if not fields:
        raise HTTPException(400, "请先在信息提取节点中配置字段")

    task = TaskRepository.create(db, user.id, "document_extract", {})
    run = WorkflowRun(
        id=uuid.uuid4().hex, user_id=user.id, workflow_id=workflow.id,
        document_id=document.id, task_id=task.id,
    )
    task.payload = {
        "file_path": document.storage_path, "filename": document.filename,
        "fields": fields, "user_id": user.id, "document_id": document.id,
        "validation_rules": workflow.rules or [], "workflow_run_id": run.id,
    }
    document.status = "processing"
    db.add(run)
    db.commit()
    db.refresh(run)
    enqueue(task)
    return _workflow_run_data(run)


@router.get("/workflow-runs")
def list_workflow_runs(
    limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    records = db.query(WorkflowRun).filter(WorkflowRun.user_id == user.id).order_by(WorkflowRun.created_at.desc()).limit(limit).all()
    return {"items": [_workflow_run_data(item) for item in records]}
