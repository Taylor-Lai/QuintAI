"""FastAPI application factory and production static-file integration."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from docnexus.api.router import api_router
from docnexus.core.observability import OperationalMiddleware, configure_logging
from docnexus.core.rate_limit import RateLimitMiddleware
from docnexus.core.settings import get_settings
from docnexus.db.bootstrap import create_initial_admin

settings = get_settings()
configure_logging(json_logs=settings.is_production)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_production:
        settings.require_secret_key()
    create_initial_admin()
    logger.info("Service startup completed")
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="文档理解系统", version="1.0.0", lifespan=lifespan)
    application.add_middleware(OperationalMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)

    if settings.static_dir.is_dir():
        assets_dir = settings.static_dir / "assets"
        if assets_dir.is_dir():
            application.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @application.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            requested_path = settings.static_dir / full_path
            if requested_path.is_file():
                return FileResponse(requested_path)
            if "." not in Path(full_path).name:
                return FileResponse(settings.static_dir / "index.html")
            raise HTTPException(status_code=404, detail="Not found")

    return application


app = create_app()
