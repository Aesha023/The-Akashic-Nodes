"""API v1 router aggregator (Phase 7)."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.runs import router as runs_router
from backend.app.api.v1.scenarios import router as scenarios_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.tiles import router as tiles_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(runs_router)
api_v1_router.include_router(tiles_router)
api_v1_router.include_router(system_router)

__all__ = ["api_v1_router"]
