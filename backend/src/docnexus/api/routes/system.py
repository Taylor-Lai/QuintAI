"""System and basic upload HTTP endpoints."""

import logging

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse

from docnexus.core.settings import get_settings
from docnexus.services.document_parser import DocumentParser

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.get("/")
async def root():
    index_path = settings.static_dir / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)
    return {
        "message": "[START] 文档理解系统运行中",
        "version": "1.0.0",
        "docs": "/docs",
        "features": ["文档解析", "AI 提取", "自动填表", "历史记录"],
    }


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "docnexus"}


@router.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """仅上传并解析（不提取）"""
    try:
        result = await DocumentParser.parse_file(file)
        return {
            "status": "success",
            "data": {
                "filename": result["filename"],
                "file_type": result["file_type"],
                "char_count": result["char_count"],
                "preview": (
                    result["content"][:500] + "..."
                    if len(result["content"]) > 500
                    else result["content"]
                ),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"上传失败：{str(e)}")
