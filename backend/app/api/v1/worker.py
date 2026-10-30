"""Worker adapter API for remote compute workers (Colab / GPU VM) (Phase 7 & Item 14)."""

from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/workers", tags=["workers"])

# In-memory worker and job tracking for remote compute nodes
ONLINE_WORKERS: dict[str, dict[str, Any]] = {}
QUEUED_JOBS: dict[str, dict[str, Any]] = {}
JOB_PROGRESS: dict[str, list[dict[str, Any]]] = {}


class WorkerRegisterRequest(BaseModel):
    worker_id: str
    engine: str  # "tier0", "delft3d", "dualsphysics"
    hostname: str = "remote-node"
    capabilities: dict[str, Any] = {}


class WorkerProgressUpdate(BaseModel):
    progress_percent: float
    stage: str
    log_line: str | None = None


@router.post("/register")
async def register_worker(payload: WorkerRegisterRequest) -> dict[str, Any]:
    """Register a remote worker node (e.g. Google Colab notebook cell or GPU VM)."""
    engine = payload.engine.lower().strip()
    if engine not in ("tier0", "delft3d", "dualsphysics"):
        msg = f"Unsupported worker engine: '{engine}'. Expected tier0, delft3d, or dualsphysics."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    now = datetime.datetime.now(datetime.UTC).isoformat()
    ONLINE_WORKERS[payload.worker_id] = {
        "worker_id": payload.worker_id,
        "engine": engine,
        "hostname": payload.hostname,
        "capabilities": payload.capabilities,
        "registered_at": now,
        "last_heartbeat": now,
        "status": "online",
    }
    return {
        "status": "registered",
        "worker_id": payload.worker_id,
        "engine": engine,
        "heartbeat_interval_sec": 30,
    }


@router.get("/status")
async def get_workers_status() -> dict[str, Any]:
    """Query online worker count per engine queue."""
    now = datetime.datetime.now(datetime.UTC)
    active_by_engine = {"tier0": 1, "delft3d": 0, "dualsphysics": 0}

    # Prune stale workers (>90s without heartbeat)
    stale_ids = []
    for wid, wmeta in ONLINE_WORKERS.items():
        last_hb = datetime.datetime.fromisoformat(wmeta["last_heartbeat"])
        if (now - last_hb).total_seconds() > 90:
            stale_ids.append(wid)
        else:
            eng = wmeta["engine"]
            active_by_engine[eng] = active_by_engine.get(eng, 0) + 1

    for wid in stale_ids:
        ONLINE_WORKERS.pop(wid, None)

    delft3d_ready = (
        "remote_worker_online" if active_by_engine["delft3d"] > 0 else "waiting_for_worker"
    )
    dual_ready = (
        "remote_worker_online" if active_by_engine["dualsphysics"] > 0 else "waiting_for_worker"
    )

    return {
        "online_workers": list(ONLINE_WORKERS.values()),
        "counts": active_by_engine,
        "queues": {
            "tier0": "local_worker_ready",
            "delft3d": delft3d_ready,
            "dualsphysics": dual_ready,
        },
    }


@router.get("/jobs/pull")
async def pull_job(engine: str) -> dict[str, Any]:
    """Pull the next queued job for a specific engine."""
    engine = engine.lower().strip()
    for _jid, job in list(QUEUED_JOBS.items()):
        if job.get("engine") == engine and job.get("status") == "queued":
            job["status"] = "assigned"
            job["assigned_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            return {"job": job}

    return {"job": None}


@router.post("/jobs/{run_id}/progress")
async def report_job_progress(run_id: str, payload: WorkerProgressUpdate) -> dict[str, Any]:
    """Stream live progress and logs from a remote worker node."""
    entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "progress_percent": payload.progress_percent,
        "stage": payload.stage,
        "log_line": payload.log_line,
    }
    if run_id not in JOB_PROGRESS:
        JOB_PROGRESS[run_id] = []
    JOB_PROGRESS[run_id].append(entry)
    return {"status": "recorded", "run_id": run_id}
