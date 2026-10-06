"""Village and critical asset flood exposure analysis (Phase 7 / Section 9)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import rasterio
from pydantic import BaseModel, Field

from pravahx.impact.hazard import HazardClass, classify_hazard

if TYPE_CHECKING:
    from pathlib import Path


class VillageExposure(BaseModel):
    """Detailed flood exposure statistics for a single village settlement."""

    village_name: str
    district: str
    population: int
    cropland_ha: float
    is_inundated: bool = False
    max_depth_m: float = 0.0
    arrival_time_min: float = float("inf")
    time_to_peak_min: float = float("inf")
    hazard_class: str = "none"
    affected_population: int = 0
    inundated_cropland_ha: float = 0.0
    geom: dict[str, Any] | None = None


class CriticalAssetExposure(BaseModel):
    """Flood exposure evaluation for a critical infrastructure asset."""

    asset_name: str
    asset_type: str  # Hospital, School, Substation, Water Treatment, Bridge, Road
    is_inundated: bool = False
    max_depth_m: float = 0.0
    arrival_time_min: float = float("inf")
    hazard_class: str = "none"
    geom: dict[str, Any] | None = None


class ExposureSummary(BaseModel):
    """Aggregated population, agricultural, and asset exposure summary."""

    total_villages: int
    inundated_villages: int
    total_population_exposed: int
    total_cropland_inundated_ha: float
    critical_assets_at_risk: int
    villages: list[VillageExposure] = Field(default_factory=list)
    critical_assets: list[CriticalAssetExposure] = Field(default_factory=list)


def _sample_raster_at_point(
    src: rasterio.io.DatasetReader,
    x: float,
    y: float,
) -> float:
    """Sample continuous raster value at coordinates (x, y)."""
    try:
        row, col = src.index(x, y)
        if 0 <= row < src.height and 0 <= col < src.width:
            val = src.read(1)[row, col]
            if src.nodata is not None and np.isclose(val, src.nodata):
                return 0.0
            return float(val)
    except Exception:
        return 0.0
    return 0.0


def compute_village_exposure(
    villages_data: list[dict[str, Any]],
    depth_raster_path: str | Path,
    arrival_raster_path: str | Path | None = None,
    velocity_raster_path: str | Path | None = None,
    depth_threshold_m: float = 0.15,
) -> list[VillageExposure]:
    """Compute flood exposure for settlements from hydrodynamic rasters.

    Args:
        villages_data: List of dicts containing name, district, population, cropland_ha, x, y.
        depth_raster_path: Path to max water depth GeoTIFF raster.
        arrival_raster_path: Optional path to arrival time GeoTIFF raster.
        velocity_raster_path: Optional path to max velocity GeoTIFF raster.
        depth_threshold_m: Inundation threshold depth (default 0.15 m).

    Returns:
        List of VillageExposure records.
    """
    results: list[VillageExposure] = []

    with rasterio.open(depth_raster_path) as d_src:
        arr_src = rasterio.open(arrival_raster_path) if arrival_raster_path else None
        v_src = rasterio.open(velocity_raster_path) if velocity_raster_path else None

        try:
            for v in villages_data:
                name = v.get("name", "Unknown")
                dist = v.get("district", "Unknown")
                pop = int(v.get("population", 0))
                cropland = float(v.get("cropland_ha", 0.0))
                x = float(v.get("x", 0.0))
                y = float(v.get("y", 0.0))

                depth = _sample_raster_at_point(d_src, x, y)
                arr_time = _sample_raster_at_point(arr_src, x, y) if arr_src else float("inf")
                vel = _sample_raster_at_point(v_src, x, y) if v_src else 0.0

                is_inundated = depth >= depth_threshold_m

                if is_inundated:
                    hazard_obj = classify_hazard(depth, vel)
                    hazard = (
                        hazard_obj.value if isinstance(hazard_obj, HazardClass) else str(hazard_obj)
                    )
                    # Fractional impact scaling with depth
                    pop_fraction = min(1.0, depth / 1.5) if depth < 1.5 else 1.0
                    crop_fraction = min(1.0, depth / 0.5) if depth < 0.5 else 1.0

                    affected_pop = int(pop * pop_fraction)
                    inundated_crop = cropland * crop_fraction
                else:
                    hazard = "none"
                    affected_pop = 0
                    inundated_crop = 0.0
                    arr_time = float("inf")

                results.append(
                    VillageExposure(
                        village_name=name,
                        district=dist,
                        population=pop,
                        cropland_ha=cropland,
                        is_inundated=is_inundated,
                        max_depth_m=round(depth, 3),
                        arrival_time_min=round(arr_time, 1)
                        if arr_time != float("inf")
                        else float("inf"),
                        hazard_class=hazard,
                        affected_population=affected_pop,
                        inundated_cropland_ha=round(inundated_crop, 2),
                        geom={"type": "Point", "coordinates": [x, y]},
                    )
                )
        finally:
            if arr_src:
                arr_src.close()
            if v_src:
                v_src.close()

    return results


def compute_asset_exposure(
    assets_data: list[dict[str, Any]],
    depth_raster_path: str | Path,
    arrival_raster_path: str | Path | None = None,
    velocity_raster_path: str | Path | None = None,
    depth_threshold_m: float = 0.15,
) -> list[CriticalAssetExposure]:
    """Evaluate flood impact on critical infrastructure assets."""
    results: list[CriticalAssetExposure] = []

    with rasterio.open(depth_raster_path) as d_src:
        arr_src = rasterio.open(arrival_raster_path) if arrival_raster_path else None
        v_src = rasterio.open(velocity_raster_path) if velocity_raster_path else None

        try:
            for a in assets_data:
                name = a.get("name", "Asset")
                atype = a.get("type", "Infrastructure")
                x = float(a.get("x", 0.0))
                y = float(a.get("y", 0.0))

                depth = _sample_raster_at_point(d_src, x, y)
                arr_time = _sample_raster_at_point(arr_src, x, y) if arr_src else float("inf")
                vel = _sample_raster_at_point(v_src, x, y) if v_src else 0.0

                is_inundated = depth >= depth_threshold_m
                if is_inundated:
                    hazard_obj = classify_hazard(depth, vel)
                    hazard = (
                        hazard_obj.value if isinstance(hazard_obj, HazardClass) else str(hazard_obj)
                    )
                else:
                    hazard = "none"

                results.append(
                    CriticalAssetExposure(
                        asset_name=name,
                        asset_type=atype,
                        is_inundated=is_inundated,
                        max_depth_m=round(depth, 3),
                        arrival_time_min=round(arr_time, 1)
                        if arr_time != float("inf")
                        else float("inf"),
                        hazard_class=hazard,
                        geom={"type": "Point", "coordinates": [x, y]},
                    )
                )
        finally:
            if arr_src:
                arr_src.close()
            if v_src:
                v_src.close()

    return results
