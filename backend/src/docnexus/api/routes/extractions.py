"""Information extraction history and task submission."""

import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.api.routes.tasks import enqueue, serialize_task
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db
from docnexus.repositories.extractions import ExtractionRepository
from docnexus.repositories.tasks import TaskRepository
from docnexus.services.upload_security import save_upload_safely

router = APIRouter(tags=["信息提取"])
settings = get_settings()


@router.get("/doc-extract/search")
def search_extractions(
    keyword: str = Query(..., min_length=2, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"items": ExtractionRepository.search_extractions(db, keyword, user.id)}


@router.get("/doc-extract")
def list_extractions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    records = ExtractionRepository.list_extractions(db, user.id, limit, offset)
    return {"items": records, "limit": limit, "offset": offset}


@router.get("/doc-extract/{record_id}")
def get_extraction(record_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = ExtractionRepository.get_extraction(db, record_id, user.id)
    if record is None:
        raise HTTPException(404, "记录不存在")
    return record


@router.delete("/doc-extract/{record_id}", status_code=204)
def delete_extraction(record_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not ExtractionRepository.delete_extraction(db, record_id, user.id):
        raise HTTPException(404, "记录不存在")


@router.post("/doc-extract/upload", status_code=status.HTTP_202_ACCEPTED)
async def submit_extraction(
    file: UploadFile = File(...),
    fields: str = Form(..., min_length=1, max_length=2000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    field_list = list(dict.fromkeys(value.strip() for value in fields.replace("，", ",").split(",") if value.strip()))
    if not field_list or len(field_list) > 100:
        raise HTTPException(400, "字段数量必须在 1 到 100 之间")
    task = TaskRepository.create(db, user.id, "document_extract", {})
    workspace = settings.data_dir / "tasks" / task.id
    try:
        path, _ = await save_upload_safely(file, workspace / "input", {".docx", ".xlsx", ".txt", ".md"})
        task.payload = {"file_path": str(path), "filename": path.name, "fields": field_list, "user_id": user.id}
        db.commit()
        enqueue(task)
        return serialize_task(task)
    except Exception:
        db.delete(task)
        db.commit()
        shutil.rmtree(workspace, ignore_errors=True)
        raise
