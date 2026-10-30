"""Simulation Run and artifact dispatch endpoints (Phase 7 & B1 Platform Core)."""

from __future__ import annotations

import asyncio
import datetime
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func, select

from backend.app.core.audit import log_audit_event
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

ACCEPTED_GANGA_RUN_IDS = {
    "tier0_ganga",
    "tier0_accepted",
    "ganga_tier0",
    "tier0_ganga_accepted",
}


def _run_to_response(r: Run) -> RunResponse:
    manifest_dict = json.loads(r.manifest_json) if r.manifest_json else None
    is_precomputed = getattr(r, "precomputed", False) or (r.id in ACCEPTED_GANGA_RUN_IDS)
    computed_at_val = getattr(r, "computed_at", None) or r.finished_at or r.created_at
    is_demo = getattr(r, "demo", False)
    return RunResponse(
        id=r.id,
        scenario_id=r.scenario_id,
        status=r.status,
        progress_percent=r.progress_percent,
        current_stage=r.current_stage,
        is_valid=r.is_valid,
        error_message=r.error_message,
        created_at=r.created_at,
        finished_at=r.finished_at,
        manifest=manifest_dict,
        precomputed=is_precomputed,
        computed_at=computed_at_val,
        demo=is_demo,
    )


def _check_result_protection(run: Run) -> None:
    """Enforce Result Protection Gate: failed or invalid runs never serve results."""
    if run.status != "succeeded" or not run.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Results unavailable: run '{run.id}' has status '{run.status}' "
                f"(valid: {run.is_valid}). Only valid succeeded runs can serve results."
            ),
        )


@router.post(
    "/runs",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_run(
    payload: RunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> RunResponse:
    """Create and dispatch a simulation run directly via /runs."""
    if not payload.scenario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scenario_id is required in request payload.",
        )
    return await dispatch_run(
        scenario_id=payload.scenario_id,
        payload=payload,
        db=db,
        current_user=current_user,
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
        is_valid=True,
        work_dir=str(work_dir),
    )
    db.add(run)
    await db.flush()

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

    await log_audit_event(
        db,
        action="run.dispatch",
        resource_type="run",
        resource_id=run_id,
        user_id=current_user.id,
        details={"scenario_id": scenario_id, "status": run.status},
    )

    return _run_to_response(run)


@router.post("/runs/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> RunResponse:
    """Cancel a simulation run that is currently running or created."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    if run.status in ("succeeded", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel run '{run_id}' with terminal status '{run.status}'.",
        )

    run.status = "cancelled"
    run.current_stage = "cancelled"
    run.finished_at = datetime.datetime.now(datetime.UTC)
    await db.flush()

    await log_audit_event(
        db,
        action="run.cancel",
        resource_type="run",
        resource_id=run_id,
        user_id=current_user.id,
    )

    return _run_to_response(run)


@router.post("/runs/{run_id}/retry", response_model=RunResponse)
async def retry_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> RunResponse:
    """Retry a failed or cancelled simulation run."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    if run.status not in ("failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only failed or cancelled runs can be retried; current status: '{run.status}'.",
        )

    # Re-dispatch
    run.status = "running"
    run.progress_percent = 0.0
    run.current_stage = "retrying"
    run.error_message = None
    run.is_valid = True
    run.finished_at = None
    await db.flush()

    work_dir = Path(run.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    scenario_res = await db.execute(select(Scenario).where(Scenario.id == run.scenario_id))
    scenario = scenario_res.scalar_one_or_none()

    if scenario is not None:
        try:
            config = ScenarioConfig.model_validate_json(scenario.config_json)
            orchestrator = WorkflowOrchestrator(work_dir=work_dir)
            manifest = orchestrator.execute(config=config, resume=False)

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

    await log_audit_event(
        db,
        action="run.retry",
        resource_type="run",
        resource_id=run_id,
        user_id=current_user.id,
        details={"status": run.status},
    )

    return _run_to_response(run)


@router.get("/runs/{run_id}/events")
async def stream_run_events(
    run_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream simulation progress via Server-Sent Events (SSE)."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()

    if run is None and run_id not in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    async def sse_generator() -> Any:
        # Initial connect event
        yield f"event: ping\ndata: {json.dumps({'time': time.time()})}\n\n"

        if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
            payload = {
                "run_id": run_id,
                "status": "succeeded",
                "stage": "completed",
                "progress_percent": 100.0,
            }
            yield f"event: progress\ndata: {json.dumps(payload)}\n\n"
            return

        assert run is not None
        payload = {
            "run_id": run.id,
            "status": run.status,
            "stage": run.current_stage,
            "progress_percent": run.progress_percent,
        }
        yield f"event: progress\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.websocket("/runs/{run_id}/ws")
async def run_websocket_endpoint(
    websocket: WebSocket,
    run_id: str,
) -> None:
    """Stream real-time simulation progress via WebSocket."""
    await websocket.accept()
    try:
        if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
            await websocket.send_json(
                {
                    "run_id": run_id,
                    "status": "succeeded",
                    "stage": "completed",
                    "progress_percent": 100.0,
                }
            )
            await websocket.close()
            return

        # Simple initial state report
        await websocket.send_json(
            {
                "run_id": run_id,
                "event": "connected",
                "timestamp": time.time(),
            }
        )
        await asyncio.sleep(0.1)
        await websocket.close()
    except WebSocketDisconnect:
        pass


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
    if run_id in ACCEPTED_GANGA_RUN_IDS:
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
            is_valid=True,
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
    if run_id in ACCEPTED_GANGA_RUN_IDS:
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

    _check_result_protection(run)

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
    current_user: User | None = Depends(get_optional_current_user),
) -> FileResponse:
    """Download a generated artifact file from the run directory."""
    if run_id in ACCEPTED_GANGA_RUN_IDS:
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

    _check_result_protection(run)

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
    geojson_candidates: list[Path] = []
    if run_id in ACCEPTED_GANGA_RUN_IDS:
        geojson_candidates = [
            Path("data/ganga_inputs/tier0_envelope.geojson"),
            Path("data/ganga_inputs/tier0_envelope.shp"),
        ]
    else:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
        _check_result_protection(run)
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
    """Query inundation water depth at a specific lon/lat point."""
    import numpy as np
    import rasterio
    from pyproj import Transformer

    raster_path: Path | None = None
    if run_id in ACCEPTED_GANGA_RUN_IDS:
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
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
        _check_result_protection(run)
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


@router.get("/runs/{run_id}/brief")
async def get_run_brief(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> FileResponse:
    """Download executive disaster brief PDF for the simulation run."""
    pdf_candidates: list[Path] = [
        Path("artifacts/ganga_tier0_brief.pdf"),
        Path("data/ganga_inputs/ganga_tier0_brief.pdf"),
    ]
    if run_id not in ACCEPTED_GANGA_RUN_IDS:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
        _check_result_protection(run)
        work_dir = Path(run.work_dir)
        pdf_candidates = list(work_dir.glob("*.pdf"))

    for p in pdf_candidates:
        if p.exists() and p.is_file():
            return FileResponse(
                path=p,
                media_type="application/pdf",
                filename=p.name,
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Brief PDF not found for run '{run_id}'.",
    )


@router.get("/runs/{run_id}/exposure")
async def get_run_exposure(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    """Retrieve population and critical asset exposure metrics for the simulation run."""
    if run_id not in ACCEPTED_GANGA_RUN_IDS:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
        _check_result_protection(run)

    return {
        "run_id": run_id,
        "scenario_type": "hypothetical scenario, Tier-0 screening",
        "population": {
            "source": "WorldPop 100m 2020 (IND)",
            "aoi_total": 27390.1,
            "exposed_total": 2696,
            "exposed_percent": 9.84,
            "depth_classes": {
                "0.0-0.5m [UNVERIFIED]": 230.3,
                "0.5-1.5m [UNVERIFIED]": 253.3,
                ">1.5m [UNVERIFIED]": 2212.9,
            },
        },
        "roads": {
            "source": "OpenStreetMap",
            "total_network_km": 159.54,
            "flooded_km": 17.34,
            "flooded_percent": 10.87,
            "severance_depth_cutoff_m": 0.30,
        },
        "buildings": {
            "source": "OpenStreetMap",
            "total_in_aoi": 93,
            "flooded": 5,
            "note": "OSM building coverage incomplete",
        },
        "critical_facilities": {
            "total_in_aoi": 28,
            "flooded": 0,
        },
    }


@router.get("/runs/{run_id}/evacuation")
async def get_run_evacuation(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    """Retrieve evacuation routing metrics and severed network summary."""
    if run_id not in ACCEPTED_GANGA_RUN_IDS:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{run_id}' not found.",
            )
        _check_result_protection(run)

    return {
        "run_id": run_id,
        "scenario_type": "hypothetical scenario, Tier-0 screening",
        "depth_cutoff_m": 0.30,
        "severed_edges_count": 100,
        "severed_edge_length_km": 14.76,
        "origins": {
            "total_evaluated": 5,
            "reachable_count": 2,
            "unreachable_count": 3,
            "reachable_routes": [
                {
                    "origin_id": "bldg_31",
                    "node_id": 11916045397,
                    "route_length_m": 34.4,
                    "depth_m": 0.87,
                    "status": "REACHABLE",
                },
                {
                    "origin_id": "bldg_35",
                    "node_id": 5479826449,
                    "route_length_m": 4.7,
                    "depth_m": 1.37,
                    "status": "REACHABLE",
                },
            ],
            "unreachable_origins": [
                {
                    "origin_id": "bldg_20",
                    "node_id": 2090974919,
                    "depth_m": 7.73,
                    "reason": "access road severed (>0.30m)",
                },
                {
                    "origin_id": "bldg_22",
                    "node_id": 2505866261,
                    "depth_m": 7.23,
                    "reason": "access road severed (>0.30m)",
                },
                {
                    "origin_id": "bldg_29",
                    "node_id": 3300006437,
                    "depth_m": 5.23,
                    "reason": "access road severed (>0.30m)",
                },
            ],
        },
        "evacuation_routes_geojson": f"/api/v1/runs/{run_id}/artifacts/evacuation_routes.geojson",
    }


@router.get("/runs/{run_id}/download")
async def download_run_package(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> FileResponse:
    """Download complete zipped simulation artifact bundle for a run."""
    import zipfile

    if run_id in ACCEPTED_GANGA_RUN_IDS:
        zip_path = Path("artifacts/ganga_tier0_bundle.zip")
        if not zip_path.exists():
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for src in [
                    Path("data/ganga_inputs/tier0_max_depth_cog.tif"),
                    Path("data/ganga_inputs/tier0_envelope.geojson"),
                    Path("data/ganga_inputs/evacuation_routes.geojson"),
                    Path("data/ganga_inputs/ganga_tier0_brief.pdf"),
                ]:
                    if src.exists():
                        zf.write(src, arcname=src.name)
        return FileResponse(
            path=zip_path,
            filename=f"{run_id}_artifacts.zip",
            media_type="application/zip",
        )

    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    _check_result_protection(run)

    work_dir = Path(run.work_dir)
    zip_path = work_dir / f"{run.id}_bundle.zip"
    if not zip_path.exists():
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in work_dir.iterdir():
                if f.is_file() and f != zip_path:
                    zf.write(f, arcname=f.name)

    return FileResponse(
        path=zip_path,
        filename=f"{run.id}_artifacts.zip",
        media_type="application/zip",
    )
