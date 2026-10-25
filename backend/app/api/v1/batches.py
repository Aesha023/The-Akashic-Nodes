"""Batch simulation queue and dam list management endpoints (B4 Feature F15)."""

from __future__ import annotations

import csv
import datetime
import io
import json
import uuid
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.app.core.audit import log_audit_event
from backend.app.core.auth import require_analyst
from backend.app.core.config import Settings
from backend.app.db.session import get_db
from backend.app.models.run import Run
from backend.app.models.scenario import Scenario

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.app.models.user import User

router = APIRouter(prefix="/batches", tags=["batches"])
settings = Settings()

# In-memory batch directory for rapid status aggregation
_BATCH_REGISTRY: dict[str, dict[str, Any]] = {}


class BatchDamItem(BaseModel):
    """Specification of a single dam within a batch execution list."""

    name: str
    height_m: float = Field(..., gt=0.0)
    volume_m3: float = Field(..., gt=0.0)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    river: str = "Tributary"


class BatchCreateRequest(BaseModel):
    """Request payload to initiate a batch of simulation runs."""

    name: str = "Batch Dam Simulation"
    dams: list[BatchDamItem] | None = None
    csv_data: str | None = None
    template_tier: str = "tier0"
    breach_equation: str = "froehlich_2008"
    manning_n: float = 0.035


class BatchQueuedRunItem(BaseModel):
    """Reference to an enqueued simulation run within a batch."""

    run_id: str
    scenario_id: str
    dam_name: str
    status: str


class BatchResponse(BaseModel):
    """Summary of created batch simulation job."""

    batch_id: str
    name: str
    total_dams: int
    queued_runs: list[BatchQueuedRunItem]
    status: str
    created_at: datetime.datetime


class BatchStatusResponse(BaseModel):
    """Detailed execution progress of an active or completed batch."""

    batch_id: str
    name: str
    total_dams: int
    completed_runs: int
    failed_runs: int
    progress_percent: float
    status: str
    runs: list[dict[str, Any]]
    created_at: datetime.datetime


def _parse_csv_dams(csv_text: str) -> list[BatchDamItem]:
    """Parse CSV text with flexible column name headers."""
    f = io.StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    items: list[BatchDamItem] = []

    for row in reader:
        # Normalize header keys
        norm = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}
        name = norm.get("name") or norm.get("dam_name") or norm.get("dam") or "Dam"
        height = float(norm.get("height_m") or norm.get("dam_height_m") or norm.get("height", 30.0))
        volume = float(
            norm.get("volume_m3")
            or norm.get("reservoir_volume_m3")
            or norm.get("volume", 5000000.0)
        )
        lat = float(norm.get("lat") or norm.get("latitude", 30.0))
        lon = float(norm.get("lon") or norm.get("longitude", 78.0))
        river = norm.get("river", "Tributary")

        items.append(
            BatchDamItem(
                name=name,
                height_m=height,
                volume_m3=volume,
                lat=lat,
                lon=lon,
                river=river,
            )
        )
    return items


@router.post("", response_model=BatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_batch(
    payload: BatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> BatchResponse:
    """Queue a batch of dam breach simulations from a structured JSON list or CSV."""
    dams: list[BatchDamItem] = []
    if payload.dams:
        dams.extend(payload.dams)
    if payload.csv_data:
        dams.extend(_parse_csv_dams(payload.csv_data))

    if not dams:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch request must contain at least one dam in 'dams' or valid 'csv_data'.",
        )

    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    queued_runs: list[BatchQueuedRunItem] = []
    run_ids: list[str] = []

    for dam in dams:
        scen_id = f"scen_batch_{uuid.uuid4().hex[:8]}"
        run_id = f"run_batch_{uuid.uuid4().hex[:8]}"
        run_ids.append(run_id)

        config_dict = {
            "name": f"{payload.name} - {dam.name}",
            "tier": payload.template_tier,
            "tier0": {"manning_n": payload.manning_n},
            "source": {
                "latitude": dam.lat,
                "longitude": dam.lon,
                "volume_m3": dam.volume_m3,
                "volume_method": "user",
            },
            "breach": {
                "equation": payload.breach_equation,
                "dam_height_m": dam.height_m,
                "reservoir_volume_m3": dam.volume_m3,
                "width_uncertainty_factor": 1.0,
                "time_uncertainty_factor": 1.0,
            },
        }

        scenario = Scenario(
            id=scen_id,
            name=f"{payload.name} - {dam.name}",
            scenario_type="dam_break",
            failure_mode="overtopping",
            created_by=current_user.id,
            config_json=json.dumps(config_dict),
            version=1,
        )
        db.add(scenario)

        manifest = {
            "batch_id": batch_id,
            "dam_name": dam.name,
            "river": dam.river,
            "height_m": dam.height_m,
            "volume_m3": dam.volume_m3,
        }

        run = Run(
            id=run_id,
            scenario_id=scen_id,
            status="queued",
            progress_percent=0.0,
            current_stage="queued_in_batch",
            work_dir=f"/tmp/pravahx/{run_id}",
            manifest_json=json.dumps(manifest),
        )
        db.add(run)

        queued_runs.append(
            BatchQueuedRunItem(
                run_id=run_id,
                scenario_id=scen_id,
                dam_name=dam.name,
                status="queued",
            )
        )

    await db.commit()

    created_at = datetime.datetime.now(datetime.UTC)
    _BATCH_REGISTRY[batch_id] = {
        "batch_id": batch_id,
        "name": payload.name,
        "total_dams": len(dams),
        "run_ids": run_ids,
        "created_at": created_at,
    }

    await log_audit_event(
        db,
        user_id=current_user.id,
        action="batch_create",
        resource_type="batch",
        resource_id=batch_id,
        details={"total_dams": len(dams), "runs_queued": len(run_ids)},
    )

    return BatchResponse(
        batch_id=batch_id,
        name=payload.name,
        total_dams=len(dams),
        queued_runs=queued_runs,
        status="queued",
        created_at=created_at,
    )


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> BatchStatusResponse:
    """Retrieve execution progress and individual status for all runs in a batch."""
    meta = _BATCH_REGISTRY.get(batch_id)

    # If not in memory registry, locate runs by manifest_json containing batch_id
    if not meta:
        stmt = select(Run).where(Run.manifest_json.contains(batch_id))
        res = await db.execute(stmt)
        runs_list = list(res.scalars().all())
        if not runs_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch '{batch_id}' not found.",
            )
        run_ids = [r.id for r in runs_list]
        name = "Recovered Batch"
        created_at = runs_list[0].created_at
    else:
        run_ids = meta["run_ids"]
        name = meta["name"]
        created_at = meta["created_at"]
        stmt = select(Run).where(Run.id.in_(run_ids))
        res = await db.execute(stmt)
        runs_list = list(res.scalars().all())

    total = len(run_ids)
    completed = sum(1 for r in runs_list if r.status == "succeeded")
    failed = sum(1 for r in runs_list if r.status == "failed")
    progress = (
        round((sum(r.progress_percent for r in runs_list) / (total * 100.0)) * 100.0, 1)
        if total > 0
        else 0.0
    )

    batch_status = "queued"
    if completed == total and total > 0:
        batch_status = "completed"
    elif failed > 0:
        batch_status = "completed_with_failures" if completed > 0 else "failed"
    elif any(r.status == "running" for r in runs_list):
        batch_status = "running"

    run_summaries = [
        {
            "run_id": r.id,
            "scenario_id": r.scenario_id,
            "status": r.status,
            "progress_percent": r.progress_percent,
            "current_stage": r.current_stage,
            "is_valid": r.is_valid,
        }
        for r in runs_list
    ]

    return BatchStatusResponse(
        batch_id=batch_id,
        name=name,
        total_dams=total,
        completed_runs=completed,
        failed_runs=failed,
        progress_percent=progress,
        status=batch_status,
        runs=run_summaries,
        created_at=created_at,
    )
