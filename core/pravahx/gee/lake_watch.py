"""Glacial and landslide-dammed lake monitoring and anomaly detection (Phase 6 / Section 6)."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class LakeObservation(BaseModel):
    """Single satellite observation of a monitored lake water body."""

    observed_at: datetime.datetime
    water_area_m2: float
    water_area_km2: float
    sensor_platform: str  # "Sentinel-2", "Sentinel-1", "Landsat-8"
    cloud_cover_percent: float = 0.0
    quality_flag: str = "good"  # "good", "cloudy", "shadowed"


class LakeWatchSummary(BaseModel):
    """Time-series analysis and outburst anomaly risk report for a monitored lake."""

    lake_id: str
    lake_name: str
    lake_type: str  # "glacial", "landslide", "reservoir"
    current_area_km2: float
    baseline_area_km2: float
    area_change_percent: float
    expansion_rate_m2_per_day: float
    status: (
        str  # "STABLE", "RAPID_EXPANSION_WARNING", "SUDDEN_DRAINAGE_OUTBURST", "INSUFFICIENT_DATA"
    )
    observations: list[LakeObservation] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


def analyze_lake_time_series(
    lake_id: str,
    lake_name: str,
    lake_type: str,
    observations: list[LakeObservation],
    expansion_threshold_percent: float = 10.0,
    drainage_threshold_percent: float = -20.0,
) -> LakeWatchSummary:
    """Analyze time-series water area observations to detect GLOF / outburst anomalies.

    Args:
        lake_id: Unique identifier for the lake.
        lake_name: Human-readable lake name.
        lake_type: "glacial", "landslide", or "reservoir".
        observations: Chronological list of satellite lake observations.
        expansion_threshold_percent: Percent expansion triggering warning (default 10%).
        drainage_threshold_percent: Percent drop triggering drainage alert (default -20%).

    Returns:
        LakeWatchSummary with status verdict and rate metrics.
    """
    if not observations:
        return LakeWatchSummary(
            lake_id=lake_id,
            lake_name=lake_name,
            lake_type=lake_type,
            current_area_km2=0.0,
            baseline_area_km2=0.0,
            area_change_percent=0.0,
            expansion_rate_m2_per_day=0.0,
            status="INSUFFICIENT_DATA",
            risk_notes=["No satellite observations available."],
        )

    # Sort observations by date
    sorted_obs = sorted(observations, key=lambda o: o.observed_at)
    baseline_obs = sorted_obs[0]
    latest_obs = sorted_obs[-1]

    dt_days = max(
        1.0, (latest_obs.observed_at - baseline_obs.observed_at).total_seconds() / 86400.0
    )

    area_change_m2 = latest_obs.water_area_m2 - baseline_obs.water_area_m2
    area_change_pct = (area_change_m2 / max(1.0, baseline_obs.water_area_m2)) * 100.0
    rate_m2_per_day = area_change_m2 / dt_days

    notes: list[str] = []
    status = "STABLE"

    if area_change_pct >= expansion_threshold_percent:
        status = "RAPID_EXPANSION_WARNING"
        exp_km2 = area_change_m2 / 1e6
        notes.append(
            f"Lake surface area expanded by {area_change_pct:+.1f}% "
            f"(+{exp_km2:.2f} km²) over {dt_days:.0f} days."
        )
        notes.append(
            "Increased hydrostatic pressure on moraine dam; potential GLOF trigger condition."
        )
    elif area_change_pct <= drainage_threshold_percent:
        status = "SUDDEN_DRAINAGE_OUTBURST"
        drn_km2 = abs(area_change_m2) / 1e6
        notes.append(
            f"Lake surface area contracted rapidly by {area_change_pct:.1f}% "
            f"(-{drn_km2:.2f} km²) over {dt_days:.0f} days."
        )
        notes.append(
            "CRITICAL: Sudden lake drainage detected! Breach or subglacial outburst may be active."
        )
    else:
        status = "STABLE"
        notes.append(f"Lake area within normal bounds ({area_change_pct:+.1f}% change).")

    return LakeWatchSummary(
        lake_id=lake_id,
        lake_name=lake_name,
        lake_type=lake_type,
        current_area_km2=round(latest_obs.water_area_km2, 4),
        baseline_area_km2=round(baseline_obs.water_area_km2, 4),
        area_change_percent=round(area_change_pct, 2),
        expansion_rate_m2_per_day=round(rate_m2_per_day, 1),
        status=status,
        observations=sorted_obs,
        risk_notes=notes,
    )
