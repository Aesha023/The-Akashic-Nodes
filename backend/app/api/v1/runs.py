"""Simulation Run and artifact dispatch endpoints (Phase 7)."""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from backend.app.core.auth import get_current_user, require_analyst
from backend.app.core.config import Settings
from backend.app.db.session import get_db
from backend.app.models.run import Run
from backend.app.models.scenario import Scenario
from backend.app.schemas.run import (
    RunCreate,
    RunListResponse,
    RunResponse,
)
from pravahx.config.schema import ScenarioConfig
from pravahx.pipeline.workflow import WorkflowOrchestrator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.app.models.user import User

router = APIRouter(tags=["runs"])
settings = Settings()


def _run_to_response(r: Run) -> RunResponse:
    manifest_dict = json.loads(r.manifest_json) if r.manifest_json else None
    return RunResponse(
        id=r.id,
        scenario_id=r.scenario_id,
        status=r.status,
        progress_percent=r.progress_percent,
        current_stage=r.current_stage,
        error_message=r.error_message,
        created_at=r.created_at,
        finished_at=r.finished_at,
        manifest=manifest_dict,
    )


@router.post(
    "/scenarios/{scenario_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_run(
    scenario_id: str,
    payload: RunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> RunResponse:
    """Dispatch a simulation run for the specified scenario."""
    if settings.is_showcase:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System is in read-only showcase mode (constraint C). New runs are disabled.",
        )

    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found.",
        )

    run_id = f"run_{scenario_id}_{int(time.time())}"
    work_dir = Path("./runs") / run_id
    work_dir.mkdir(parents=True, exist_ok=True)

    run = Run(
        id=run_id,
        scenario_id=scenario_id,
        status="running",
        progress_percent=0.0,
        current_stage="initializing",
        work_dir=str(work_dir),
    )
    db.add(run)
    await db.flush()

    # In local execution / tests, execute synchronously via orchestrator
    try:
        config = ScenarioConfig.model_validate_json(scenario.config_json)
        orchestrator = WorkflowOrchestrator(work_dir=work_dir)
        manifest = orchestrator.execute(config=config, resume=payload.resume)

        run.status = manifest.status
        run.progress_percent = 100.0
        run.current_stage = "completed"
        run.manifest_json = json.dumps(manifest.to_dict())
        run.finished_at = datetime.datetime.now(datetime.UTC)
    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        run.finished_at = datetime.datetime.now(datetime.UTC)

    await db.flush()
    return _run_to_response(run)


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    scenario_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunListResponse:
    """List simulation runs with optional scenario filter."""
    base_q = select(Run)
    if scenario_id:
        base_q = base_q.where(Run.scenario_id == scenario_id)

    total_q = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = total_q.scalar_one() or 0

    q = base_q.order_by(Run.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    runs = result.scalars().all()

    return RunListResponse(
        total=total,
        items=[_run_to_response(r) for r in runs],
    )


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunResponse:
    """Get status and details of a specific simulation run."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    return _run_to_response(run)


@router.get("/runs/{run_id}/manifest")
async def get_run_manifest(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve full provenance manifest JSON for a completed run."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    if not run.manifest_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manifest not yet generated for run '{run_id}'.",
        )

    data: dict[str, Any] = json.loads(run.manifest_json)
    return data


@router.get("/runs/{run_id}/artifacts/{artifact_name:path}")
async def get_run_artifact(
    run_id: str,
    artifact_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download a generated artifact file from the run directory."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    art_path = Path(run.work_dir) / artifact_name
    if not art_path.exists() or not art_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_name}' not found for run '{run_id}'.",
        )

    return FileResponse(path=art_path, filename=art_path.name)
