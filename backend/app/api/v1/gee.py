"""Google Earth Engine satellite flood mapping and Lake Watch API endpoints (Phase 7)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.app.core.auth import get_current_user
from pravahx.gee.client import GEEClient
from pravahx.gee.lake_watch import LakeObservation, analyze_lake_time_series

if TYPE_CHECKING:
    from backend.app.models.user import User

router = APIRouter(prefix="/gee", tags=["gee"])


class LakeWatchRequest(BaseModel):
    observations: list[dict[str, Any]] = Field(
        ..., description="List of historical lake observations with date and area_km2"
    )
    baseline_window: int = 5


@router.get("/status")
async def get_gee_status(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Check Earth Engine service account authentication and project configuration."""
    service_account = os.environ.get("GEE_SERVICE_ACCOUNT_EMAIL")
    key_path = os.environ.get("GEE_SERVICE_ACCOUNT_KEY_FILE")
    project_id = os.environ.get("GEE_PROJECT_ID")

    client = GEEClient()
    is_ready = client.is_authenticated()

    return {
        "authenticated": is_ready,
        "service_account_configured": bool(service_account),
        "key_file_configured": bool(key_path and os.path.exists(key_path)),
        "project_id": project_id or "Not configured",
        "service_account": service_account or "Not configured",
    }


@router.post("/lake-watch")
async def evaluate_lake_watch(
    req: LakeWatchRequest, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Analyze glacial/high-altitude lake area expansion time series and alert flags."""
    obs_list = [
        LakeObservation(
            observed_at=parse(str(o["date"])),
            water_area_km2=float(o["area_km2"]),
            water_area_m2=float(o["area_km2"]) * 1e6,
            sensor_platform=str(o.get("sensor", "Sentinel-2")),
            cloud_cover_percent=float(o.get("cloud_cover_percent", 0.0)),
        )
        for o in req.observations
    ]

    summary = analyze_lake_time_series(
        lake_id="unknown", lake_name="Unknown", lake_type="glacial", observations=obs_list
    )
    return {
        "lake_id": summary.lake_id,
        "latest_area_km2": summary.current_area_km2,
        "baseline_area_km2": summary.baseline_area_km2,
        "expansion_rate_percent": summary.area_change_percent,
        "growth_status": summary.status,
        "expansion_rate_m2_per_day": summary.expansion_rate_m2_per_day,
    }
