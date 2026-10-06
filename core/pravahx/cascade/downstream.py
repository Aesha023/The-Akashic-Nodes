"""Cascade analysis and downstream dam-break chain evaluation (Phase 4).

Evaluates flood wave propagation along a downstream river reach containing multiple
reservoirs/barrages in series. Assesses reservoir surcharge, spillway capacity,
overtopping risk, and automatically triggers chained breach scenarios when an
upstream dam break causes downstream dam failure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

import numpy as np

from pravahx.breach.froehlich import (
    FroehlichParams,
    compute_froehlich_2008,
)
from pravahx.breach.hydrograph import route_hydrograph

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChannelHydrographPoint:
    """Hydrograph time series point along river channel."""

    time_seconds: float
    discharge_m3s: float
    reservoir_head_m: float = 0.0
    breach_width_m: float = 0.0
    volume_remaining_m3: float = 0.0


class CascadeVerdict(StrEnum):
    """Verdict of cascade dam assessment."""

    SAFE = "safe"
    SPILLED_NO_BREACH = "spilled_no_breach"
    OVERTOPPED = "overtopped"


@dataclass(frozen=True)
class DamStructure:
    """Metadata and hydraulic attributes of a dam along the reach."""

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
    location: tuple[float, float] | None = None  # (longitude, latitude)


@dataclass(frozen=True)
class RiverProfilePoint:
    """Longitudinal elevation point along the cascade river reach."""

    chainage_km: float
    bed_elevation_m: float
    peak_water_elevation_m: float
    dam_id: str | None = None
    crest_elevation_m: float | None = None


@dataclass(frozen=True)
class CascadeLink:
    """Evaluation result for one dam link in the cascade chain."""

    order: int
    dam_id: str
    dam_name: str
    chainage_km: float
    peak_inflow_m3s: float
    flood_volume_m3: float
    arrival_time_min: float
    initial_storage_m3: float
    available_surcharge_m3: float
    peak_water_elevation_m: float
    crest_elevation_m: float
    freeboard_m: float
    overtopped: bool
    verdict: CascadeVerdict
    chained_scenario_id: str | None = None
    chained_peak_outflow_m3s: float | None = None
    chained_breach_width_m: float | None = None
    chained_formation_time_h: float | None = None


@dataclass(frozen=True)
class CascadeSummary:
    """Complete summary of cascade analysis across all downstream dams."""

    scenario_id: str
    links: list[CascadeLink]
    total_dams_evaluated: int
    total_dams_overtopped: int
    cascade_triggered: bool
    max_peak_flow_m3s: float
    profile: list[RiverProfilePoint]
    metadata: dict[str, Any] = field(default_factory=dict)


class CascadeAnalyzer:
    """Orchestrates multi-dam cascade analysis and chained breach progression."""

    def __init__(
        self,
        celerity_m_s: float = 4.5,
        attenuation_rate_per_km: float = 0.005,
    ) -> None:
        """Initialize cascade analyzer.

        Args:
            celerity_m_s: Average flood wave celerity in metres/second (default: 4.5 m/s).
            attenuation_rate_per_km: Peak flow attenuation fraction per km of channel.
        """
        self.celerity_m_s = celerity_m_s
        self.attenuation_rate_per_km = attenuation_rate_per_km

    def route_channel_flood_wave(
        self,
        inflow_hydrograph: list[ChannelHydrographPoint],
        distance_km: float,
    ) -> tuple[list[ChannelHydrographPoint], float]:
        """Route flood hydrograph downstream along open river channel.

        Args:
            inflow_hydrograph: Upstream hydrograph time series.
            distance_km: Reach distance in km.

        Returns:
            Tuple of (attenuated & lagged hydrograph, lag_time_minutes).
        """
        if distance_km <= 0 or not inflow_hydrograph:
            return inflow_hydrograph, 0.0

        lag_seconds = (distance_km * 1000.0) / self.celerity_m_s
        lag_minutes = lag_seconds / 60.0

        # Attenuation factor decreases peak discharge with distance
        atten_factor = max(0.35, 1.0 - (self.attenuation_rate_per_km * distance_km))

        routed: list[ChannelHydrographPoint] = []
        for pt in inflow_hydrograph:
            routed.append(
                ChannelHydrographPoint(
                    time_seconds=pt.time_seconds + lag_seconds,
                    discharge_m3s=pt.discharge_m3s * atten_factor,
                    reservoir_head_m=pt.reservoir_head_m,
                    breach_width_m=pt.breach_width_m,
                    volume_remaining_m3=pt.volume_remaining_m3,
                )
            )

        return routed, lag_minutes

    def evaluate_dam_surcharge_and_overtopping(
        self,
        dam: DamStructure,
        inflow_hydrograph: list[ChannelHydrographPoint],
    ) -> tuple[bool, float, float, CascadeVerdict]:
        """Assess whether arriving flood wave overtop the dam.

        Args:
            dam: Downstream DamStructure specifications.
            inflow_hydrograph: Arriving hydrograph at dam axis.

        Returns:
            Tuple of (overtopped_bool, peak_water_elevation_m, freeboard_m, verdict).
        """
        if not inflow_hydrograph:
            return False, dam.bed_elevation_m, dam.dam_height_m, CascadeVerdict.SAFE

        # Compute arriving flood volume
        times = np.array([pt.time_seconds for pt in inflow_hydrograph], dtype=np.float64)
        flows = np.array([pt.discharge_m3s for pt in inflow_hydrograph], dtype=np.float64)
        flood_vol_m3 = float(np.trapezoid(flows, times)) if len(times) > 1 else 0.0

        peak_inflow = max(pt.discharge_m3s for pt in inflow_hydrograph)

        initial_storage = dam.storage_m3 * dam.initial_storage_fraction

        # Uncontrolled flood volume after spillway discharge
        uncontrolled_volume_m3 = max(0.0, flood_vol_m3 - (dam.spillway_capacity_m3s * 3600.0 * 2.0))

        # Hypsometric reservoir level rise
        # V = K_v * h^m  => h = h_dam * (V / V_full)^(1/m)
        total_retained_volume = initial_storage + uncontrolled_volume_m3
        vol_ratio = total_retained_volume / max(1.0, dam.storage_m3)
        h_pool_m = dam.dam_height_m * (vol_ratio ** (1.0 / dam.hypsometric_m))

        peak_water_elevation = dam.bed_elevation_m + h_pool_m
        freeboard_m = dam.crest_elevation_m - peak_water_elevation

        if peak_water_elevation > dam.crest_elevation_m:
            overtopped = True
            verdict = CascadeVerdict.OVERTOPPED
        elif peak_inflow > dam.spillway_capacity_m3s:
            overtopped = False
            verdict = CascadeVerdict.SPILLED_NO_BREACH
        else:
            overtopped = False
            verdict = CascadeVerdict.SAFE

        return overtopped, peak_water_elevation, freeboard_m, verdict

    def evaluate_cascade(
        self,
        scenario_id: str,
        initial_dam: DamStructure,
        initial_hydrograph: list[ChannelHydrographPoint],
        downstream_dams: list[DamStructure],
    ) -> CascadeSummary:
        """Execute full multi-dam cascade analysis along the downstream chain.

        Args:
            scenario_id: Parent scenario ID.
            initial_dam: Upstream triggering dam.
            initial_hydrograph: Upstream breach hydrograph.
            downstream_dams: Ordered list of downstream dams by chainage.

        Returns:
            CascadeSummary containing all links, verdicts, and longitudinal profile.
        """
        # Sort downstream dams by chainage
        sorted_dams = sorted(downstream_dams, key=lambda d: d.chainage_km)

        links: list[CascadeLink] = []
        profile_pts: list[RiverProfilePoint] = []

        # Add initial triggering dam to profile
        profile_pts.append(
            RiverProfilePoint(
                chainage_km=initial_dam.chainage_km,
                bed_elevation_m=initial_dam.bed_elevation_m,
                peak_water_elevation_m=initial_dam.crest_elevation_m,
                dam_id=initial_dam.id,
                crest_elevation_m=initial_dam.crest_elevation_m,
            )
        )

        current_hydrograph = initial_hydrograph
        current_chainage = initial_dam.chainage_km
        cascade_triggered = False
        overtopped_count = 0
        global_max_peak = max((pt.discharge_m3s for pt in initial_hydrograph), default=0.0)

        for order, dam in enumerate(sorted_dams, start=1):
            dist_km = max(0.0, dam.chainage_km - current_chainage)

            # 1. Route channel flood wave to this dam
            arriving_hg, _lag_min = self.route_channel_flood_wave(current_hydrograph, dist_km)

            peak_inflow = max((pt.discharge_m3s for pt in arriving_hg), default=0.0)
            times = np.array([pt.time_seconds for pt in arriving_hg], dtype=np.float64)
            flows = np.array([pt.discharge_m3s for pt in arriving_hg], dtype=np.float64)
            flood_vol = float(np.trapezoid(flows, times)) if len(times) > 1 else 0.0

            arrival_time = min((pt.time_seconds / 60.0 for pt in arriving_hg), default=0.0)

            # 2. Check overtopping
            overtopped, peak_wse, freeboard, verdict = self.evaluate_dam_surcharge_and_overtopping(
                dam, arriving_hg
            )

            chained_id = None
            chained_peak = None
            chained_b = None
            chained_tf = None

            if overtopped:
                overtopped_count += 1
                cascade_triggered = True
                chained_id = f"{scenario_id}_cascade_{dam.id}"

                # 3. Compute chained breach parameters using Froehlich (2008)
                total_release_volume = dam.storage_m3 + flood_vol
                f_mode: Literal["overtopping", "piping"] = (
                    "piping" if dam.failure_mode == "piping" else "overtopping"
                )
                breach_params: FroehlichParams = compute_froehlich_2008(
                    volume_m3=total_release_volume,
                    height_m=dam.dam_height_m,
                    mode=f_mode,
                )

                # Route downstream combined breach hydrograph
                chained_routed = route_hydrograph(
                    initial_volume_m3=total_release_volume,
                    dam_height_m=dam.dam_height_m,
                    b_avg_m=breach_params.average_width_m,
                    t_f_hr=breach_params.formation_time_hr,
                    reservoir_exponent=dam.hypsometric_m,
                    side_slope_z=breach_params.side_slope_z,
                    progression_mode="vertical_and_horizontal",
                )

                chained_peak = chained_routed.peak_discharge_m3s
                chained_b = breach_params.average_width_m
                chained_tf = breach_params.formation_time_hr

                # Convert points to ChannelHydrographPoint
                current_hydrograph = [
                    ChannelHydrographPoint(
                        time_seconds=pt["time_hr"] * 3600.0,
                        discharge_m3s=pt["discharge_m3s"],
                        reservoir_head_m=pt["head_m"],
                        volume_remaining_m3=pt["volume_remaining_m3"],
                    )
                    for pt in chained_routed.points
                ]
                global_max_peak = max(global_max_peak, chained_peak)
            else:
                # Hydrograph continues through spillway/overflow
                current_hydrograph = arriving_hg

            current_chainage = dam.chainage_km

            links.append(
                CascadeLink(
                    order=order,
                    dam_id=dam.id,
                    dam_name=dam.name,
                    chainage_km=dam.chainage_km,
                    peak_inflow_m3s=peak_inflow,
                    flood_volume_m3=flood_vol,
                    arrival_time_min=arrival_time,
                    initial_storage_m3=dam.storage_m3 * dam.initial_storage_fraction,
                    available_surcharge_m3=dam.storage_m3 * (1.0 - dam.initial_storage_fraction),
                    peak_water_elevation_m=peak_wse,
                    crest_elevation_m=dam.crest_elevation_m,
                    freeboard_m=freeboard,
                    overtopped=overtopped,
                    verdict=verdict,
                    chained_scenario_id=chained_id,
                    chained_peak_outflow_m3s=chained_peak,
                    chained_breach_width_m=chained_b,
                    chained_formation_time_h=chained_tf,
                )
            )

            # Record profile at dam
            profile_pts.append(
                RiverProfilePoint(
                    chainage_km=dam.chainage_km,
                    bed_elevation_m=dam.bed_elevation_m,
                    peak_water_elevation_m=peak_wse,
                    dam_id=dam.id,
                    crest_elevation_m=dam.crest_elevation_m,
                )
            )

        metadata: dict[str, Any] = {
            "initial_dam_id": initial_dam.id,
            "total_chainage_km": (
                sorted_dams[-1].chainage_km if sorted_dams else initial_dam.chainage_km
            ),
            "celerity_m_s": self.celerity_m_s,
            "attenuation_rate": self.attenuation_rate_per_km,
        }

        return CascadeSummary(
            scenario_id=scenario_id,
            links=links,
            total_dams_evaluated=len(sorted_dams),
            total_dams_overtopped=overtopped_count,
            cascade_triggered=cascade_triggered,
            max_peak_flow_m3s=global_max_peak,
            profile=profile_pts,
            metadata=metadata,
        )
