"""Aggregate the public API routers."""

from fastapi import APIRouter

from docnexus.api.routes import admin, auth, documents, enterprise, extractions, system, tables, tasks, workspace

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(documents.router)
api_router.include_router(extractions.router)
api_router.include_router(tables.router)
api_router.include_router(admin.router)
api_router.include_router(workspace.router)
api_router.include_router(enterprise.router)
