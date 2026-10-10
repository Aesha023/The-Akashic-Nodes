"""Impact assessment, hazard rating, damage valuation, and evacuation API endpoints (Phase 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.app.core.auth import get_current_user
from pravahx.impact.brief import generate_impact_brief_markdown
from pravahx.impact.damage import estimate_flood_damage
from pravahx.impact.evacuation import EvacuationShelter, plan_evacuation_routes
from pravahx.impact.exposure import compute_asset_exposure, compute_village_exposure
from pravahx.impact.hazard import calculate_hazard_rating, classify_hazard

if TYPE_CHECKING:
    from backend.app.models.user import User

router = APIRouter(prefix="/impact", tags=["impact"])


class HazardRequest(BaseModel):
    depth_m: float = Field(..., ge=0.0, description="Inundation water depth in metres")
    velocity_m_s: float = Field(..., ge=0.0, description="Flow velocity in metres per second")
    debris_factor: float | None = Field(
        None, ge=0.0, le=1.0, description="Optional debris factor DF"
    )


class HazardResponse(BaseModel):
    hazard_rating: float
    hazard_class: str
    danger_description: str


class ExposureRequest(BaseModel):
    villages: list[dict[str, Any]]
    assets: list[dict[str, Any]] | None = None


class EvacuationRequest(BaseModel):
    villages: list[dict[str, Any]]
    shelters: list[dict[str, Any]]


class DamageRequest(BaseModel):
    villages: list[dict[str, Any]]
    depth_unit_cost_inr: float = 120_000.0


class BriefRequest(BaseModel):
    scenario_id: str
    exposure: dict[str, Any]
    damage: dict[str, Any]
    evacuation: dict[str, Any]


@router.post("/hazard", response_model=HazardResponse)
async def evaluate_hazard(
    req: HazardRequest, current_user: User = Depends(get_current_user)
) -> HazardResponse:
    """Evaluate UK Defra / Environment Agency FD2321 Flood Hazard Rating."""
    hr = calculate_hazard_rating(
        depth=req.depth_m,
        velocity=req.velocity_m_s,
        debris_factor=req.debris_factor,
    )
    h_class = classify_hazard(
        depth=req.depth_m,
        velocity=req.velocity_m_s,
        debris_factor=req.debris_factor,
    )
    descriptions = {
        "Low": "Caution - Shallow or slow-moving water",
        "Moderate": "Danger for some - Children, elderly, infirm",
        "Significant": "Danger for most - General public in danger",
        "Extreme": "Danger for all - Severe structural collapse and risk to life",
    }
    return HazardResponse(
        hazard_rating=round(float(hr), 3),
        hazard_class=h_class.value,
        danger_description=descriptions.get(h_class.value, "Unknown"),
    )


@router.post("/exposure")
async def evaluate_exposure(
    req: ExposureRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Calculate village population, buildings, and critical infrastructure exposure."""
    v_exposures = compute_village_exposure(req.villages)
    a_exposures = compute_asset_exposure(req.assets or [])
    return {
        "villages": [
            {
                "village_id": v.village_name,
                "name": v.village_name,
                "population_exposed": v.affected_population,
                "buildings_flooded": int(v.affected_population / 4.5),
                "max_depth_m": v.max_depth_m,
                "arrival_time_hr": round(v.arrival_time_min / 60.0, 2)
                if v.arrival_time_min != float("inf")
                else 0.0,
                "hazard_class": v.hazard_class,
            }
            for v in v_exposures
        ],
        "critical_assets": [
            {
                "asset_id": a.asset_name,
                "name": a.asset_name,
                "asset_type": a.asset_type,
                "depth_m": a.max_depth_m,
                "is_operational": not a.is_inundated,
                "hazard_class": a.hazard_class,
            }
            for a in a_exposures
        ],
        "total_population_exposed": sum(v.affected_population for v in v_exposures),
        "total_buildings_flooded": sum(int(v.affected_population / 4.5) for v in v_exposures),
    }


@router.post("/damage")
async def evaluate_damage(
    req: DamageRequest, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Calculate direct structural, contents, and infrastructure economic loss."""
    v_exposures = compute_village_exposure(req.villages)
    estimate = estimate_flood_damage(v_exposures)
    return {
        "total_loss_inr": estimate.grand_total_loss_inr,
        "structural_loss_inr": estimate.total_residential_loss_inr,
        "agricultural_loss_inr": estimate.total_agricultural_loss_inr,
        "infrastructure_loss_inr": estimate.total_infrastructure_loss_inr,
        "villages_affected_count": len(
            [v for v in estimate.village_breakdown if v.total_loss_inr > 0]
        ),
    }


@router.post("/evacuation")
async def evaluate_evacuation(
    req: EvacuationRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Plan emergency evacuation routes, clearance time, and safe staging windows."""
    shelter_objs = [
        EvacuationShelter(
            shelter_id=str(s.get("shelter_id", f"S{i}")),
            name=str(s.get("name", f"Shelter {i}")),
            capacity=int(s.get("capacity", 500)),
            x=float(s.get("x", 0.0)),
            y=float(s.get("y", 0.0)),
            elevation_m=float(s.get("elevation_m", 0.0)),
        )
        for i, s in enumerate(req.shelters)
    ]
    v_exposures = compute_village_exposure(req.villages)
    summary = plan_evacuation_routes(v_exposures, shelter_objs)
    return {
        "total_evacuees": sum(v.affected_population for v in v_exposures),
        "total_shelter_capacity": sum(s.capacity for s in shelter_objs),
        "routes": [
            {
                "village_id": r.village_name,
                "shelter_id": r.shelter_name,
                "clearance_time_hr": round(r.clearance_time_min / 60.0, 2),
                "is_safe": r.is_viable,
                "safety_margin_hr": round(r.safety_margin_min / 60.0, 2),
                "urgency_level": r.urgency_level,
            }
            for r in summary.routes
        ],
    }


@router.post("/brief")
async def generate_brief(
    req: BriefRequest, current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Generate automated executive disaster brief in Markdown."""
    from pravahx.impact.damage import DamageEstimate
    from pravahx.impact.evacuation import EvacuationPlanSummary
    from pravahx.impact.exposure import ExposureSummary

    exp = ExposureSummary(
        total_villages=len(req.exposure.get("villages", [])),
        inundated_villages=len(req.exposure.get("villages", [])),
        total_population_exposed=req.exposure.get("total_population_exposed", 0),
        total_cropland_inundated_ha=float(req.exposure.get("total_cropland_inundated_ha", 0.0)),
        critical_assets_at_risk=req.exposure.get("critical_assets_at_risk", 0),
        villages=[],
        critical_assets=[],
    )
    dmg = DamageEstimate(
        total_residential_loss_inr=float(req.damage.get("structural_loss_inr", 0.0)),
        total_agricultural_loss_inr=float(req.damage.get("agricultural_loss_inr", 0.0)),
        total_infrastructure_loss_inr=float(req.damage.get("infrastructure_loss_inr", 0.0)),
        grand_total_loss_inr=float(req.damage.get("total_loss_inr", 0.0)),
        village_breakdown=[],
        asset_breakdown=[],
    )
    evac = EvacuationPlanSummary(
        total_settlements=len(req.evacuation.get("routes", [])),
        trapped_settlements=0,
        critical_settlements=0,
        viable_settlements=len(req.evacuation.get("routes", [])),
        routes=[],
    )

    md = generate_impact_brief_markdown(
        scenario_id=req.scenario_id,
        scenario_name=f"Scenario {req.scenario_id}",
        exposure=exp,
        damage=dmg,
        evacuation=evac,
    )
    return {"scenario_id": req.scenario_id, "markdown": md}
