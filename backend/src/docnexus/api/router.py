"""Aggregate all public API routers while preserving legacy paths."""

from fastapi import APIRouter

from docnexus.api.routes import admin, auth, documents, extractions, system, tables

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(extractions.router)
api_router.include_router(tables.router)
api_router.include_router(admin.router)
