"""API v1 router aggregator (Phase 7)."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.batches import router as batches_router
from backend.app.api.v1.cascade import router as cascade_router
from backend.app.api.v1.data_catalog import router as data_catalog_router
from backend.app.api.v1.gee import router as gee_router
from backend.app.api.v1.impact import router as impact_router
from backend.app.api.v1.lake_watch import router as lake_watch_router
from backend.app.api.v1.runs import router as runs_router
from backend.app.api.v1.scenarios import router as scenarios_router
from backend.app.api.v1.share import router as share_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.tiles import router as tiles_router
from backend.app.api.v1.validation import router as validation_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(runs_router)
api_v1_router.include_router(batches_router)
api_v1_router.include_router(cascade_router)
api_v1_router.include_router(lake_watch_router)
api_v1_router.include_router(data_catalog_router)
api_v1_router.include_router(tiles_router)
api_v1_router.include_router(impact_router)
api_v1_router.include_router(gee_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(validation_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(share_router)

__all__ = ["api_v1_router"]
