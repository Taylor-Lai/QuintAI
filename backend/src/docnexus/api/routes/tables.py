"""Multi-source table filling task submission."""

import shutil

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.api.routes.tasks import enqueue, serialize_task
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db
from docnexus.repositories.tasks import TaskRepository
from docnexus.services.upload_security import save_upload_safely, validate_file_count

router = APIRouter(tags=["表格处理"])
settings = get_settings()


@router.post("/table-fill/upload", status_code=status.HTTP_202_ACCEPTED)
async def submit_table_fill(
    template: UploadFile = File(...),
    documents: list[UploadFile] = File(...),
    user_request: str = Form("", max_length=4000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    validate_file_count(len(documents))
    task = TaskRepository.create(db, user.id, "table_fill", {})
    workspace = settings.data_dir / "tasks" / task.id
    try:
        template_path, _ = await save_upload_safely(template, workspace, {".xlsx", ".docx"})
        template_path.rename(workspace / f"模板_{template_path.name}")
        source_names: list[str] = []
        for index, document in enumerate(documents):
            source_path, _ = await save_upload_safely(
                document,
                workspace / "source_uploads",
                {".docx", ".xlsx", ".txt", ".md"},
            )
            final_path = workspace / f"source_{index:03d}_{source_path.name}"
            source_path.rename(final_path)
            source_names.append(source_path.name)
        shutil.rmtree(workspace / "source_uploads", ignore_errors=True)
        task.payload = {
            "workspace_dir": str(workspace),
            "user_request": user_request.strip(),
            "output_name": f"filled_{template_path.name}",
            "source_names": source_names,
        }
        db.commit()
        enqueue(task)
        return serialize_task(task)
    except Exception:
        db.delete(task)
        db.commit()
        shutil.rmtree(workspace, ignore_errors=True)
        raise
