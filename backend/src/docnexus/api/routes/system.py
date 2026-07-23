"""System health and static application endpoints."""

import logging

import redis
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text

from docnexus.core.settings import get_settings
from docnexus.db import engine

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
