"""Information extraction and history HTTP endpoints."""

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from docnexus.ai.contracts import Mod2_ExtractInput
from docnexus.ai.workflows import (
    handle_module_2_extract,
)
from docnexus.api.dependencies import get_current_user
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db
from docnexus.repositories.extractions import ExtractionRepository

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.get("/doc-extract/search")
async def search_extractions(keyword: str, db: Session = Depends(get_db)):
    """搜索提取记录"""
    if not keyword or len(keyword) < 2:
        raise HTTPException(400, "关键词至少 2 个字符")

    records = ExtractionRepository.search_extractions(db, keyword)

    return {
        "keyword": keyword,
        "total": len(records),
        "records": [
            {
                "id": r.id,
                "filename": r.filename,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "preview": r.content_preview[:200] + "..." if r.content_preview else "",
            }
            for r in records
        ],
    }


@router.get("/doc-extract")
async def list_extractions(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # 此接口只有登录后才能访问
):
    """获取提取历史记录列表"""
    records = ExtractionRepository.list_extractions(db, limit=limit, offset=offset)

    return {
        "total": len(records),
        "limit": limit,
        "offset": offset,
        "records": [
            {
                "id": r.id,
                "filename": r.filename,
                "file_type": r.file_type,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ],
    }


@router.get("/doc-extract/{record_id}")
async def get_extraction_record(record_id: str, db: Session = Depends(get_db)):
    """查询提取记录（从数据库）"""
    record = ExtractionRepository.get_extraction(db, record_id)

    if not record:
        raise HTTPException(404, "记录不存在")

    return {
        "id": record.id,
        "filename": record.filename,
        "file_type": record.file_type,
        "fields_requested": record.fields_requested,
        "extracted_data": record.extracted_data,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@router.delete("/doc-extract/{record_id}")
async def delete_extraction_record(record_id: str, db: Session = Depends(get_db)):
    """删除提取记录"""
    success = ExtractionRepository.delete_extraction(db, record_id)

    if not success:
        raise HTTPException(404, "记录不存在")

    return {"message": "删除成功", "record_id": record_id}


@router.post("/doc-extract/upload")
async def doc_extract_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="源文档 (.docx, .txt, .md, .xlsx 等)"),
    fields: str = Form(..., description="需要提取的字段，用逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    【模块二】非结构化文档信息提取

    从文档中提取指定的字段信息
    """
    try:
        # 1. 保存上传的文件到临时目录
        temp_dir = Path(tempfile.gettempdir()) / f"doc_extract_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = Path(file.filename).name
        file_path = temp_dir / safe_filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 2. 处理字段列表（支持中英文逗号）
        fields_list = [
            f.strip() for f in fields.replace("，", ",").split(",") if f.strip()
        ]

        if not fields_list:
            raise HTTPException(400, "请至少指定一个提取字段")

        # 3. 调用 ai_core engine 的模块二处理函数
        input_data = Mod2_ExtractInput(
            file_path=str(file_path),
            target_entities=fields_list
        )

        result = await run_in_threadpool(handle_module_2_extract, input_data)

        # 4. 后台任务删除临时目录
        def cleanup_temp():
            import shutil
            try:
                shutil.rmtree(temp_dir)
                logger.debug("Cleaned temporary directory: %s", temp_dir)
            except Exception as e:
                logger.warning("Failed to clean temporary directory %s: %s", temp_dir, e)

        background_tasks.add_task(cleanup_temp)

        # 5. 保存记录到数据库
        if result.status == "success":
            record = ExtractionRepository.save_extraction(
                db=db,
                filename=safe_filename,
                file_type=Path(safe_filename).suffix.lstrip(".") or "unknown",
                fields_requested=fields_list,
                extracted_data=result.extracted_data,
                content_preview=str(result.extracted_data)[:500],
                status="success",
            )

            return {
                "status": "success",
                "task_id": record.id,
                "filename": safe_filename,
                "fields_requested": fields_list,
                "extracted_data": result.extracted_data,
                "created_at": record.created_at.isoformat(),
            }
        else:
            raise HTTPException(500, f"信息提取失败：{result.message}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"信息提取失败：{str(e)}")
