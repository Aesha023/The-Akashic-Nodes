"""Flood hazard rating and severity classification (Phase 7 / Section 9).

Formulas:
Flood Hazard Rating (HR):
    HR = d * (v + 0.5) + DF
where:
    d = water depth (m)
    v = flow velocity (m/s)
    DF = debris factor (dimensionless):
        DF = 0.5 for shallow flow (d <= 0.25 m)
        DF = 1.0 for deep / high-velocity flow (d > 0.25 m) or urban / forest terrain.

Hazard Class Categories:
    1 - Low (HR < 0.75): Caution. Shallow flowing water, safe for most adults.
    2 - Moderate (0.75 <= HR < 1.25): Dangerous for children, elderly, and frail.
    3 - High (1.25 <= HR < 2.0): Dangerous for most people; vehicles unstable.
    4 - Extreme (HR >= 2.0): Dangerous for all; structural damage to buildings.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np
import rasterio


class HazardClass(StrEnum):
    """Flood hazard severity categories."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


def calculate_hazard_rating(
    depth: np.ndarray[Any, Any] | float,
    velocity: np.ndarray[Any, Any] | float,
    debris_factor: float | None = None,
) -> np.ndarray[Any, Any] | float:
    """Calculate Flood Hazard Rating HR = d * (v + 0.5) + DF.

    Args:
        depth: Water depth in meters (>= 0).
        velocity: Flow velocity in m/s (>= 0).
        debris_factor: Optional custom debris factor. If None, uses depth-dependent DF.

    Returns:
        Hazard rating value or array.
    """
    d = np.maximum(0.0, np.asarray(depth, dtype=np.float64))
    v = np.maximum(0.0, np.asarray(velocity, dtype=np.float64))

    df: float | np.ndarray[Any, Any]
    if debris_factor is not None:
        df = float(debris_factor)
    else:
        # Dynamic debris factor: 0.5 for shallow water, 1.0 for deeper flow
        df_arr = np.where(d > 0.25, 1.0, 0.5)
        # For dry cells (d == 0), debris factor is 0
        df = np.where(d > 0.0, df_arr, 0.0)

    hr = d * (v + 0.5) + df

    if isinstance(depth, (float, int)) and isinstance(velocity, (float, int)):
        return float(hr.item())
    return hr


def classify_hazard(
    depth: np.ndarray[Any, Any] | float,
    velocity: np.ndarray[Any, Any] | float,
    debris_factor: float | None = None,
) -> np.ndarray[Any, Any] | HazardClass:
    """Classify water depth and velocity into HazardClass categories (1 to 4).

    Returns:
        Categorical array (0: Dry, 1: Low, 2: Moderate, 3: High, 4: Extreme)
        or single HazardClass if scalar.
    """
    hr = calculate_hazard_rating(depth, velocity, debris_factor=debris_factor)

    if isinstance(hr, (float, int)):
        if float(depth) <= 0.01:
            return HazardClass.LOW
        if hr < 0.75:
            return HazardClass.LOW
        if hr < 1.25:
            return HazardClass.MODERATE
        if hr < 2.0:
            return HazardClass.HIGH
        return HazardClass.EXTREME

    hr_arr = np.asarray(hr, dtype=np.float64)
    d_arr = np.asarray(depth, dtype=np.float64)

    # Classification integer codes:
    # 0 = Dry (depth <= 0.01 m)
    # 1 = Low
    # 2 = Moderate
    # 3 = High
    # 4 = Extreme
    classes = np.zeros_like(hr_arr, dtype=np.uint8)

    wet = d_arr > 0.01
    classes[wet & (hr_arr < 0.75)] = 1
    classes[wet & (hr_arr >= 0.75) & (hr_arr < 1.25)] = 2
    classes[wet & (hr_arr >= 1.25) & (hr_arr < 2.0)] = 3
    classes[wet & (hr_arr >= 2.0)] = 4

    return classes


def generate_hazard_raster(
    depth_raster_path: str | Path,
    velocity_raster_path: str | Path,
    output_raster_path: str | Path,
    debris_factor: float | None = None,
) -> Path:
    """Generate a classified 8-bit GeoTIFF raster of flood hazard classes (0 to 4)."""
    out_p = Path(output_raster_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(depth_raster_path) as d_src, rasterio.open(velocity_raster_path) as v_src:
        depth = d_src.read(1)
        velocity = v_src.read(1)

        # Handle nodata
        if d_src.nodata is not None:
            depth = np.where(depth == d_src.nodata, 0.0, depth)
        if v_src.nodata is not None:
            velocity = np.where(velocity == v_src.nodata, 0.0, velocity)

        hazard_arr = classify_hazard(depth, velocity, debris_factor=debris_factor)
        assert isinstance(hazard_arr, np.ndarray)

        profile = d_src.profile.copy()
        profile.update(
            dtype=rasterio.uint8,
            count=1,
            nodata=0,
            compress="deflate",
        )

        with rasterio.open(out_p, "w", **profile) as dst:
            dst.write(hazard_arr.astype(np.uint8), 1)
            # Colormap: 0: Transparent, 1: Yellow (Low), 2: Orange (Moderate),
            # 3: Red (High), 4: Purple (Extreme)
            colormap = {
                0: (0, 0, 0, 0),
                1: (255, 255, 0, 255),
                2: (255, 140, 0, 255),
                3: (255, 0, 0, 255),
                4: (128, 0, 128, 255),
            }
            dst.write_colormap(1, colormap)

    return out_p
