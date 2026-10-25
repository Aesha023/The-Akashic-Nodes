"""Lake watch monitoring and alert notification endpoints (B4 Features F16/F17)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.app.core.alerts import AlertDispatcher
from backend.app.core.auth import require_analyst
from pravahx.gee.lake_watch import LakeObservation, analyze_lake_time_series

if TYPE_CHECKING:
    from backend.app.models.user import User

router = APIRouter(tags=["lake-watch"])


class LakeWatchEvaluateRequest(BaseModel):
    """Payload for evaluating lake surface area time-series and anomaly risk."""

    lake_id: str
    lake_name: str
    lake_type: str = "glacial"  # "glacial", "landslide", "reservoir"
    observations: list[LakeObservation] = Field(default_factory=list)
    expansion_threshold_percent: float = 10.0
    drainage_threshold_percent: float = -20.0
    dispatch_alerts: bool = True
    webhook_url: str | None = None
    email_to: str | None = None


class AlertTestRequest(BaseModel):
    """Payload for verifying alert dispatch channels."""

    title: str = "PravahX Test Notification"
    details: dict[str, Any] = Field(default_factory=dict)
    webhook_url: str | None = None
    email_to: str | None = None


@router.post("/lake-watch/evaluate", response_model=dict[str, Any])
async def evaluate_lake_watch(
    payload: LakeWatchEvaluateRequest,
    current_user: User = Depends(require_analyst),
) -> dict[str, Any]:
    """Evaluate satellite time series for a monitored lake and dispatch alerts on anomaly."""
    summary = analyze_lake_time_series(
        lake_id=payload.lake_id,
        lake_name=payload.lake_name,
        lake_type=payload.lake_type,
        observations=payload.observations,
        expansion_threshold_percent=payload.expansion_threshold_percent,
        drainage_threshold_percent=payload.drainage_threshold_percent,
    )

    alert_dispatch_result: dict[str, Any] | None = None
    if payload.dispatch_alerts and summary.status in {
        "RAPID_EXPANSION_WARNING",
        "SUDDEN_DRAINAGE_OUTBURST",
    }:
        dispatcher = AlertDispatcher(
            webhook_url=payload.webhook_url,
            email_to=payload.email_to,
        )
        alert_dispatch_result = await dispatcher.dispatch(
            event_type=f"LAKE_{summary.status}",
            title=f"Lake Outburst Risk Alert: {summary.lake_name} ({summary.status})",
            details={
                "lake_id": summary.lake_id,
                "lake_name": summary.lake_name,
                "status": summary.status,
                "current_area_km2": summary.current_area_km2,
                "baseline_area_km2": summary.baseline_area_km2,
                "area_change_percent": summary.area_change_percent,
                "expansion_rate_m2_per_day": summary.expansion_rate_m2_per_day,
                "risk_notes": summary.risk_notes,
            },
        )

    return {
        "summary": summary.model_dump(),
        "alert_dispatched": alert_dispatch_result is not None,
        "alert_details": alert_dispatch_result,
    }


@router.post("/alerts/test", response_model=dict[str, Any])
async def test_alert_dispatch(
    payload: AlertTestRequest,
    current_user: User = Depends(require_analyst),
) -> dict[str, Any]:
    """Test webhook and email alert delivery channels."""
    dispatcher = AlertDispatcher(
        webhook_url=payload.webhook_url,
        email_to=payload.email_to,
    )
    result = await dispatcher.dispatch(
        event_type="SYSTEM_TEST_ALERT",
        title=payload.title,
        details=payload.details or {"sender": current_user.email, "mode": "test"},
    )
    return result
