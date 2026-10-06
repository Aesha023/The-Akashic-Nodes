"""Evacuation planning and clearance time margin analysis (Phase 7 / Section 9)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pravahx.impact.exposure import VillageExposure


class EvacuationShelter(BaseModel):
    """Emergency relief shelter or designated high-ground muster point."""

    shelter_id: str
    name: str
    capacity: int
    x: float
    y: float
    elevation_m: float = 0.0


class EvacuationRoute(BaseModel):
    """Evacuation path and timing clearance margin for a settlement."""

    village_name: str
    shelter_name: str
    route_length_km: float
    walking_time_min: float
    vehicular_time_min: float
    clearance_time_min: float
    arrival_time_min: float
    safety_margin_min: float
    is_viable: bool
    urgency_level: str  # "TRAPPED", "CRITICAL", "HIGH_PRIORITY", "VIABLE"
    geom: dict[str, Any] | None = None


class EvacuationPlanSummary(BaseModel):
    """Comprehensive disaster management evacuation summary."""

    total_settlements: int
    trapped_settlements: int
    critical_settlements: int
    viable_settlements: int
    routes: list[EvacuationRoute] = Field(default_factory=list)


def calculate_euclidean_distance_km(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate projected distance in kilometers assuming planar coordinates (UTM)."""
    dist_m = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return dist_m / 1000.0


def plan_evacuation_routes(
    village_exposures: list[VillageExposure],
    shelters: list[EvacuationShelter],
    walking_speed_kmh: float = 3.5,
    vehicular_speed_kmh: float = 25.0,
    preparation_buffer_min: float = 30.0,
) -> EvacuationPlanSummary:
    """Compute optimal evacuation routing and safety margins to nearest viable shelter.

    Args:
        village_exposures: List of village flood exposure results.
        shelters: Available emergency shelter points.
        walking_speed_kmh: Average pedestrian evacuation speed across rough terrain.
        vehicular_speed_kmh: Convoy vehicular speed.
        preparation_buffer_min: Mobilization and warning dissemination buffer.

    Returns:
        EvacuationPlanSummary with safety margin classifications.
    """
    routes: list[EvacuationRoute] = []
    trapped_count = 0
    critical_count = 0
    viable_count = 0

    for v in village_exposures:
        if not v.is_inundated or not v.geom:
            continue

        vx, vy = v.geom["coordinates"][0], v.geom["coordinates"][1]

        # Find closest shelter
        best_shelter: EvacuationShelter | None = None
        best_dist = float("inf")

        for s in shelters:
            d_km = calculate_euclidean_distance_km(vx, vy, s.x, s.y)
            # Add tortuosity factor of 1.3 for mountain/rural roads
            road_dist_km = d_km * 1.3
            if road_dist_km < best_dist:
                best_dist = road_dist_km
                best_shelter = s

        if best_shelter is None:
            continue

        walk_time = (best_dist / walking_speed_kmh) * 60.0
        veh_time = (best_dist / vehicular_speed_kmh) * 60.0

        # Blended clearance time assuming 60% walking, 40% vehicular + prep buffer
        blended_travel_time = 0.6 * walk_time + 0.4 * veh_time
        total_clearance_time = blended_travel_time + preparation_buffer_min

        arrival_time = v.arrival_time_min
        safety_margin = arrival_time - total_clearance_time

        if safety_margin < 0:
            urgency = "TRAPPED"
            is_viable = False
            trapped_count += 1
        elif safety_margin < 60.0:
            urgency = "CRITICAL"
            is_viable = True
            critical_count += 1
        elif safety_margin < 180.0:
            urgency = "HIGH_PRIORITY"
            is_viable = True
            viable_count += 1
        else:
            urgency = "VIABLE"
            is_viable = True
            viable_count += 1

        route_geom = {
            "type": "LineString",
            "coordinates": [[vx, vy], [best_shelter.x, best_shelter.y]],
        }

        routes.append(
            EvacuationRoute(
                village_name=v.village_name,
                shelter_name=best_shelter.name,
                route_length_km=round(best_dist, 2),
                walking_time_min=round(walk_time, 1),
                vehicular_time_min=round(veh_time, 1),
                clearance_time_min=round(total_clearance_time, 1),
                arrival_time_min=round(arrival_time, 1),
                safety_margin_min=round(safety_margin, 1),
                is_viable=is_viable,
                urgency_level=urgency,
                geom=route_geom,
            )
        )

    return EvacuationPlanSummary(
        total_settlements=len(routes),
        trapped_settlements=trapped_count,
        critical_settlements=critical_count,
        viable_settlements=viable_count,
        routes=routes,
    )
