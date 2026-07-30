"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    application = FastAPI(
        title="慧文融通",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(OperationalMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix="/api")

    return application


app = create_app()
