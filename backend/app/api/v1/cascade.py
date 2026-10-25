"""Downstream dam cascade and overtopping risk evaluation endpoint (B4 Feature F11)."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.app.core.auth import require_analyst
from pravahx.cascade.downstream import (
    CascadeAnalyzer,
    ChannelHydrographPoint,
    DamStructure,
)

if TYPE_CHECKING:
    from backend.app.models.user import User

router = APIRouter(prefix="/cascade", tags=["cascade"])


class ChannelHydrographPointPayload(BaseModel):
    """Time-series point for routed inflow/outflow hydrographs."""

    time_seconds: float
    discharge_m3s: float
    reservoir_head_m: float = 0.0
    breach_width_m: float = 0.0
    volume_remaining_m3: float = 0.0


class DamStructurePayload(BaseModel):
    """Specification of dam geometry and hydraulic properties for cascade evaluation."""

    id: str
    name: str
    river: str
    chainage_km: float
    dam_height_m: float
    storage_m3: float
    crest_elevation_m: float
    bed_elevation_m: float
    spillway_capacity_m3s: float
    initial_storage_fraction: float = 0.85
    hypsometric_m: float = 2.0
    failure_mode: str = "overtopping"
    erodibility: str = "erosion_resistant"
    location: tuple[float, float] | None = None


class CascadeEvaluateRequest(BaseModel):
    """Payload to simulate downstream flood wave propagation and overtopping checks."""

    scenario_id: str = "cascade_eval"
    initial_dam: DamStructurePayload
    initial_hydrograph: list[ChannelHydrographPointPayload]
    downstream_dams: list[DamStructurePayload] = Field(default_factory=list)
    celerity_m_s: float = 4.5
    attenuation_rate_per_km: float = 0.005


@router.post("/evaluate", response_model=dict[str, Any])
async def evaluate_cascade(
    payload: CascadeEvaluateRequest,
    current_user: User = Depends(require_analyst),
) -> dict[str, Any]:
    """Evaluate multi-dam cascade overtopping risk and chained breach triggers."""
    analyzer = CascadeAnalyzer(
        celerity_m_s=payload.celerity_m_s,
        attenuation_rate_per_km=payload.attenuation_rate_per_km,
    )

    init_dam = DamStructure(**payload.initial_dam.model_dump())
    downstream = [DamStructure(**d.model_dump()) for d in payload.downstream_dams]
    inflow = [
        ChannelHydrographPoint(
            time_seconds=pt.time_seconds,
            discharge_m3s=pt.discharge_m3s,
            reservoir_head_m=pt.reservoir_head_m,
            breach_width_m=pt.breach_width_m,
            volume_remaining_m3=pt.volume_remaining_m3,
        )
        for pt in payload.initial_hydrograph
    ]

    summary = analyzer.evaluate_cascade(
        scenario_id=payload.scenario_id,
        initial_dam=init_dam,
        initial_hydrograph=inflow,
        downstream_dams=downstream,
    )

    return {
        "scenario_id": summary.scenario_id,
        "total_dams_evaluated": summary.total_dams_evaluated,
        "total_dams_overtopped": summary.total_dams_overtopped,
        "cascade_triggered": summary.cascade_triggered,
        "max_peak_flow_m3s": summary.max_peak_flow_m3s,
        "links": [dataclasses.asdict(link) for link in summary.links],
        "profile": [dataclasses.asdict(pt) for pt in summary.profile],
        "status_label": "NOT RUN on Ganga (no downstream dam between Tehri and Rishikesh)",
    }
