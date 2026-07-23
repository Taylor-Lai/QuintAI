"""Document editing task submission."""

import shutil

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.api.routes.tasks import enqueue, serialize_task
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db
from docnexus.repositories.tasks import TaskRepository
from docnexus.services.upload_security import save_upload_safely

router = APIRouter(tags=["文档处理"])
settings = get_settings()


@router.post("/doc-chat/upload", status_code=status.HTTP_202_ACCEPTED)
async def submit_document_edit(
    command: str = Form(..., min_length=2, max_length=2000),
    document: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = TaskRepository.create(db, user.id, "document_edit", {})
    workspace = settings.data_dir / "tasks" / task.id
    try:
        file_path, _ = await save_upload_safely(document, workspace / "input", {".docx"})
        task.payload = {
            "file_path": str(file_path),
            "command": command.strip(),
            "output_name": f"formatted_{file_path.name}",
        }
        db.commit()
        enqueue(task)
        return serialize_task(task)
    except Exception:
        db.delete(task)
        db.commit()
        shutil.rmtree(workspace, ignore_errors=True)
        raise
