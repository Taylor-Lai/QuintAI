"""System and basic upload HTTP endpoints."""

import logging

import redis
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import text

from docnexus.api.dependencies import get_current_user
from docnexus.core.settings import get_settings
from docnexus.db import User, engine
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


@router.get("/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    checks: dict[str, str] = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"
    try:
        with redis.from_url(settings.redis_url, socket_timeout=2) as client:
            client.ping()
            checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "failed"
    if "failed" in checks.values():
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@router.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
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
