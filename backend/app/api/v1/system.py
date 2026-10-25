"""System health, readiness, and runtime information endpoints (Phase 7)."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text

import pravahx
from backend.app.core.config import Settings
from backend.app.db.session import get_db

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["system"])
settings = Settings()


@router.get("/health/live")
async def health_live() -> dict[str, str]:
    """Liveness probe: confirms the process is responsive."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Readiness probe: validates database and core service connectivity."""
    db_ok = False
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = res.scalar() == 1
    except Exception:
        db_ok = False

    return {
        "status": "ready" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "deployment_mode": settings.pravahx_deployment_mode.value,
        "secure_mode": settings.pravahx_secure_mode.value,
    }


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Comprehensive system health probe reporting database, broker, and storage status."""
    db_ok = False
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = res.scalar() == 1
    except Exception:
        db_ok = False

    # Check broker connectivity safely
    broker_ok = False
    try:
        import redis

        r = redis.from_url(settings.redis_url, socket_timeout=0.5)  # type: ignore[no-untyped-call]
        broker_ok = bool(r.ping())
    except Exception:
        broker_ok = False

    # Check storage adapter availability safely
    storage_ok = False
    try:
        from backend.app.core.storage import ObjectStorageAdapter

        storage = ObjectStorageAdapter()
        storage_ok = storage.is_available()
    except Exception:
        storage_ok = False

    status = "healthy" if db_ok else "unhealthy"

    return {
        "status": status,
        "database": "connected" if db_ok else "disconnected",
        "broker": "connected" if broker_ok else "disconnected",
        "storage": "connected" if storage_ok else "disconnected",
        "version": pravahx.__version__,
        "deployment_mode": settings.pravahx_deployment_mode.value,
        "secure_mode": settings.pravahx_secure_mode.value,
    }


@router.get("/system/info")
async def system_info() -> dict[str, Any]:
    """Provides system versions, deployment mode, and capability metadata."""
    return {
        "version": pravahx.__version__,
        "python_version": sys.version.split()[0],
        "deployment_mode": settings.pravahx_deployment_mode.value,
        "secure_mode": settings.pravahx_secure_mode.value,
        "is_showcase": settings.is_showcase,
        "is_secure": settings.is_secure,
    }
