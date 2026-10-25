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


@router.get("/system/health/detailed")
async def system_health_detailed(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Detailed operational health report.

    Includes queue depth, worker status, disk usage, and last backup timestamp (F20).
    """
    import datetime
    import shutil
    from pathlib import Path

    # 1. Database check
    db_ok = False
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = res.scalar() == 1
    except Exception:
        db_ok = False

    # 2. Celery / Redis queue depth
    queue_depth = 0
    broker_ok = False
    try:
        import redis

        r = redis.from_url(settings.redis_url, socket_timeout=0.5)  # type: ignore[no-untyped-call]
        broker_ok = bool(r.ping())
        queue_depth = int(r.llen("celery"))
    except Exception:
        broker_ok = False
        queue_depth = 0

    # 3. Worker status inspection
    workers_online = 0
    worker_status = "offline"
    if broker_ok:
        try:
            from backend.app.core.celery_app import celery_app

            insp = celery_app.control.inspect(timeout=0.5)
            pings = insp.ping()
            if pings:
                workers_online = len(pings)
                worker_status = f"{workers_online} worker(s) online"
            else:
                worker_status = "standby / idle"
        except Exception:
            worker_status = "unavailable"
    else:
        worker_status = "broker_disconnected"

    # 4. Storage check
    storage_ok = False
    try:
        from backend.app.core.storage import ObjectStorageAdapter

        storage = ObjectStorageAdapter()
        storage_ok = storage.is_available()
    except Exception:
        storage_ok = False

    # 5. Disk usage
    disk_info: dict[str, Any] = {}
    try:
        usage = shutil.disk_usage(".")
        disk_info = {
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent_used": round((usage.used / usage.total) * 100, 1),
        }
    except Exception as exc:
        disk_info = {"error": str(exc)}

    # 6. Last backup timestamp
    last_backup_time: str | None = None
    backup_dir = Path("backups")
    if backup_dir.exists():
        backup_files = sorted(
            [f for f in backup_dir.iterdir() if f.is_file()],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if backup_files:
            latest_mtime = backup_files[0].stat().st_mtime
            last_backup_time = datetime.datetime.fromtimestamp(
                latest_mtime, tz=datetime.UTC
            ).isoformat()

    return {
        "status": "healthy" if db_ok and broker_ok else "degraded",
        "database": {"connected": db_ok},
        "broker": {"connected": broker_ok, "queue_depth": queue_depth},
        "workers": {"status": worker_status, "count": workers_online},
        "storage": {"connected": storage_ok},
        "disk": disk_info,
        "last_backup": last_backup_time,
        "checked_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "version": pravahx.__version__,
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
