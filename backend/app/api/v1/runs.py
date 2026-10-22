"""Simulation Run and artifact dispatch endpoints (Phase 7)."""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from backend.app.core.auth import get_current_user, get_optional_current_user, require_analyst
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
    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        manifest_path = Path("data/ganga_inputs/manifest.json")
        manifest_dict = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else None
        )
        return RunResponse(
            id=run_id,
            scenario_id="ganga_tier0_accepted",
            status="succeeded",
            progress_percent=100.0,
            current_stage="completed",
            error_message=None,
            created_at=datetime.datetime(2026, 10, 22, 12, 0, tzinfo=datetime.UTC),
            finished_at=datetime.datetime(2026, 10, 22, 12, 5, tzinfo=datetime.UTC),
            manifest=manifest_dict,
        )

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
    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        manifest_path = Path("data/ganga_inputs/manifest.json")
        if manifest_path.exists():
            data: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
            return data

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

    data = json.loads(run.manifest_json)
    return data


@router.get("/runs/{run_id}/artifacts/{artifact_name:path}")
async def get_run_artifact(
    run_id: str,
    artifact_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download a generated artifact file from the run directory."""
    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        for cand in [Path("artifacts") / artifact_name, Path("data/ganga_inputs") / artifact_name]:
            if cand.exists() and cand.is_file():
                return FileResponse(path=cand, filename=cand.name)

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


@router.get("/runs/{run_id}/extent", response_class=Response)
@router.get("/runs/{run_id}/extent.geojson", response_class=Response)
async def get_run_extent(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> Response:
    """Retrieve the inundation extent envelope as GeoJSON (EPSG:4326)."""
    # Check special Tier-0 Ganga benchmark run
    geojson_candidates: list[Path] = []
    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        geojson_candidates = [
            Path("data/ganga_inputs/tier0_envelope.geojson"),
            Path("data/ganga_inputs/tier0_envelope.shp"),
        ]
    else:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is not None:
            work_dir = Path(run.work_dir)
            geojson_candidates = list(work_dir.glob("*envelope*.geojson")) + list(
                work_dir.glob("*envelope*.shp")
            )

    for p in geojson_candidates:
        if p.exists() and p.suffix == ".geojson":
            return Response(
                content=p.read_text(encoding="utf-8"), media_type="application/geo+json"
            )
        if p.exists() and p.suffix == ".shp":
            import geopandas as gpd

            gdf = gpd.read_file(p)
            if gdf.crs and gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            geojson_str = gdf.to_json()
            return Response(content=geojson_str, media_type="application/geo+json")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Inundation extent not found for run '{run_id}'.",
    )


@router.get("/runs/{run_id}/point-query")
async def query_run_point(
    run_id: str,
    lon: float = Query(
        ..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (EPSG:4326)"
    ),
    lat: float = Query(
        ..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (EPSG:4326)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    """Query inundation water depth at a specific lon/lat point.

    Tier-0 screening is static: arrival time is null with an explicit explanatory notice.
    """
    import numpy as np
    import rasterio
    from pyproj import Transformer

    # Locate depth raster
    raster_path: Path | None = None
    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        for cand in [
            Path("data/ganga_inputs/tier0_max_depth_cog.tif"),
            Path("data/ganga_inputs/tier0_max_depth.tif"),
        ]:
            if cand.exists():
                raster_path = cand
                break
    else:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is not None:
            work_dir = Path(run.work_dir)
            matches = list(work_dir.glob("*depth*.tif"))
            if matches:
                raster_path = matches[0]

    if raster_path is None or not raster_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Depth raster not found for run '{run_id}'.",
        )

    with rasterio.open(raster_path) as src:
        src_crs = src.crs.to_string() if src.crs else "EPSG:32644"
        transformer = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
        x_proj, y_proj = transformer.transform(lon, lat)

        row, col = src.index(x_proj, y_proj)
        depth_m = 0.0
        is_flooded = False

        if 0 <= row < src.height and 0 <= col < src.width:
            val = src.read(1, window=((row, row + 1), (col, col + 1)))[0, 0]
            nodata = src.nodata
            if (nodata is not None and val == nodata) or np.isnan(val) or val <= 0:
                depth_m = 0.0
            else:
                depth_m = round(float(val), 3)
                is_flooded = True

    return {
        "run_id": run_id,
        "scenario_type": "hypothetical scenario, Tier-0 screening",
        "lon": lon,
        "lat": lat,
        "x_proj": round(x_proj, 2),
        "y_proj": round(y_proj, 2),
        "crs": src_crs,
        "is_flooded": is_flooded,
        "depth_m": depth_m,
        "arrival_time_s": None,
        "notice": (
            "Tier-0 screening is static: arrival time is not simulated in this tier. "
            "Use Tier-1 (Delft3D FM) for dynamic flood wave arrival times."
        ),
    }
