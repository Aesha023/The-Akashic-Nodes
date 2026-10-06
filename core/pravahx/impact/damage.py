"""Economic flood damage and loss estimation (Phase 7 / Section 9).

Calculates direct losses in INR using depth-damage vulnerability curves for:
1. Residential housing and contents (per household / capita).
2. Agricultural crop losses (per hectare inundated).
3. Public and critical infrastructure (per affected asset / km of road).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pravahx.impact.exposure import CriticalAssetExposure, VillageExposure


# Standard unit costs in INR (Indian Rupees)
COST_PER_HOUSEHOLD_ASSET_INR: float = 250_000.0  # Mean household replacement value
PERSONS_PER_HOUSEHOLD: float = 4.5
COST_PER_CROPLAND_HA_INR: float = 65_000.0  # Mean seasonal crop value per hectare
COST_PER_ASSET_REPAIR_INR: dict[str, float] = {
    "Hospital": 15_000_000.0,
    "School": 4_000_000.0,
    "Substation": 25_000_000.0,
    "Water Treatment": 18_000_000.0,
    "Bridge": 30_000_000.0,
    "Road": 2_000_000.0,
}


def residential_damage_factor(depth_m: float) -> float:
    """Depth-damage curve for residential structures and household contents.

    Returns damage ratio in [0.0, 1.0].
    """
    if depth_m <= 0.05:
        return 0.0
    if depth_m <= 0.3:
        return 0.15
    if depth_m <= 0.6:
        return 0.30
    if depth_m <= 1.0:
        return 0.50
    if depth_m <= 2.0:
        return 0.75
    if depth_m <= 3.0:
        return 0.90
    return 1.00


def agricultural_damage_factor(depth_m: float) -> float:
    """Depth-damage curve for seasonal agricultural standing crops.

    Returns damage ratio in [0.0, 1.0].
    """
    if depth_m <= 0.1:
        return 0.0
    if depth_m <= 0.3:
        return 0.40
    if depth_m <= 0.6:
        return 0.75
    return 1.00


def infrastructure_damage_factor(depth_m: float) -> float:
    """Depth-damage factor for infrastructure repairs."""
    if depth_m <= 0.1:
        return 0.0
    if depth_m <= 0.5:
        return 0.25
    if depth_m <= 1.5:
        return 0.60
    return 1.00


class VillageDamage(BaseModel):
    """Detailed damage valuation for a single village."""

    village_name: str
    district: str
    residential_loss_inr: float
    agricultural_loss_inr: float
    total_loss_inr: float


class DamageEstimate(BaseModel):
    """Comprehensive economic loss evaluation summary."""

    total_residential_loss_inr: float
    total_agricultural_loss_inr: float
    total_infrastructure_loss_inr: float
    grand_total_loss_inr: float
    village_breakdown: list[VillageDamage] = Field(default_factory=list)
    asset_breakdown: list[dict[str, Any]] = Field(default_factory=list)


def estimate_flood_damage(
    village_exposures: list[VillageExposure],
    asset_exposures: list[CriticalAssetExposure] | None = None,
) -> DamageEstimate:
    """Estimate total economic damages in INR from village and asset exposures."""
    tot_res = 0.0
    tot_agri = 0.0
    tot_infra = 0.0
    v_details: list[VillageDamage] = []
    a_details: list[dict[str, Any]] = []

    for v in village_exposures:
        if not v.is_inundated or v.max_depth_m <= 0.05:
            continue

        res_ratio = residential_damage_factor(v.max_depth_m)
        num_households = v.affected_population / PERSONS_PER_HOUSEHOLD
        res_loss = num_households * COST_PER_HOUSEHOLD_ASSET_INR * res_ratio

        agri_ratio = agricultural_damage_factor(v.max_depth_m)
        agri_loss = v.inundated_cropland_ha * COST_PER_CROPLAND_HA_INR * agri_ratio

        tot_res += res_loss
        tot_agri += agri_loss

        v_details.append(
            VillageDamage(
                village_name=v.village_name,
                district=v.district,
                residential_loss_inr=round(res_loss, 2),
                agricultural_loss_inr=round(agri_loss, 2),
                total_loss_inr=round(res_loss + agri_loss, 2),
            )
        )

    if asset_exposures:
        for a in asset_exposures:
            if not a.is_inundated:
                continue

            base_cost = COST_PER_ASSET_REPAIR_INR.get(a.asset_type, 5_000_000.0)
            infra_ratio = infrastructure_damage_factor(a.max_depth_m)
            loss = base_cost * infra_ratio
            tot_infra += loss

            a_details.append(
                {
                    "asset_name": a.asset_name,
                    "asset_type": a.asset_type,
                    "max_depth_m": a.max_depth_m,
                    "damage_factor": infra_ratio,
                    "estimated_loss_inr": round(loss, 2),
                }
            )

    grand_total = tot_res + tot_agri + tot_infra

    return DamageEstimate(
        total_residential_loss_inr=round(tot_res, 2),
        total_agricultural_loss_inr=round(tot_agri, 2),
        total_infrastructure_loss_inr=round(tot_infra, 2),
        grand_total_loss_inr=round(grand_total, 2),
        village_breakdown=v_details,
        asset_breakdown=a_details,
    )
