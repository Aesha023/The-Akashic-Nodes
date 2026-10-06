"""Flood hazard rating and severity classification (Phase 7 / Section 9).

Primary Sources:
1. Defra and Environment Agency (2006) 'The Flood Risks to People Methodology',
   Flood Risks to People Phase 2, FD2321 Technical Report 1, HR Wallingford et al.
2. Defra and Environment Agency (2005) 'Framework and Guidance for Assessing and
   Managing Flood Risk for New Development', FD2320 Technical Report 2, HR Wallingford et al.
3. Environment Agency / HR Wallingford (May 2008) 'Supplementary Note on Flood Hazard Ratings
   and Thresholds for Development Planning and Control Purpose - Clarification of Table 13.1
   of FD2320/TR2 and Figure 3.2 of FD2321/TR1'.
   URL: https://assets.publishing.service.gov.uk/media/602bbdcfe90e070561b31432/Explanatory_note_for_FD2320_and_FD2321_project_record.pdf

Formulas:
Flood Hazard Rating (HR):
    HR = d * (v + 0.5) + DF
where:
    d = water depth (m)
    v = flow velocity (m/s)
    DF = debris factor (dimensionless)

Verified Source Quote (FD2321/TR1 Table 3.1 / Supplementary Note Table 1):
"Table 1: Guidance on debris factors for different flood depths, velocities and dominant land
uses. (Source FD2321 Table 3.1):
Depths (d)          Pasture/Arable   Woodland   Urban
0 to 0.25 m         0                0          0
0.25 to 0.75 m      0                0.5        1
d>0.75 m and/or v>2 0.5              1          1"

Conservative Planning Approach (FD2320/TR2 Table 13.1 / Supplementary Note):
"In the Table 13.1 of FD2320/TR2 a debris factor of 0.5 has been applied for depths less than
and equal to 0.25m and a debris factor of 1.0 has been used for depths greater than 0.25m."

Hazard Class Categories (FD2320 Table 4 / FD2321 Table 3.2):
    Low (< 0.75): Caution - "Flood zone with shallow flowing water or deep standing water"
    Moderate (0.75 - 1.25): Dangerous for some (children, elderly) -
        "Danger: Flood zone with deep or fast flowing water"
    High / Significant (1.25 - 2.0): Dangerous for most people -
        "Danger: flood zone with deep fast flowing water"
    Extreme (> 2.0 in FD2320, > 2.5 in FD2321): Dangerous for all -
        "Extreme danger: flood zone with deep fast flowing water"
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
    land_use: str = "conservative",
) -> np.ndarray[Any, Any] | float:
    """Calculate Flood Hazard Rating HR = d * (v + 0.5) + DF.

    Args:
        depth: Water depth in meters (>= 0).
        velocity: Flow velocity in m/s (>= 0).
        debris_factor: Optional explicit custom debris factor. If provided, overrides land_use.
        land_use: Land use mode matching Defra Table 3.1 / Table 13.1:
            - 'conservative': DF = 0.5 for d <= 0.25m, DF = 1.0 for d > 0.25m (FD2320 default).
            - 'pasture': DF = 0.0 for d <= 0.75m; 0.5 for d > 0.75m or v > 2.0m/s.
            - 'woodland': DF = 0.0 for d <= 0.25m; 0.5 for 0.25 < d <= 0.75m; 1.0 for deep/fast.
            - 'urban': DF = 0.0 for d <= 0.25m; 1.0 for d > 0.25m or v > 2.0m/s.

    Returns:
        Hazard rating value or array.
    """
    d = np.maximum(0.0, np.asarray(depth, dtype=np.float64))
    v = np.maximum(0.0, np.asarray(velocity, dtype=np.float64))

    df: float | np.ndarray[Any, Any]
    if debris_factor is not None:
        df = float(debris_factor)
    elif land_use == "pasture":
        high_debris = (d > 0.75) | (v > 2.0)
        df_arr = np.where(high_debris, 0.5, 0.0)
        df = np.where(d > 0.0, df_arr, 0.0)
    elif land_use == "woodland":
        high_debris = (d > 0.75) | (v > 2.0)
        mid_debris = (d > 0.25) & (d <= 0.75) & (v <= 2.0)
        df_arr = np.where(high_debris, 1.0, np.where(mid_debris, 0.5, 0.0))
        df = np.where(d > 0.0, df_arr, 0.0)
    elif land_use == "urban":
        debris_trigger = (d > 0.25) | (v > 2.0)
        df_arr = np.where(debris_trigger, 1.0, 0.0)
        df = np.where(d > 0.0, df_arr, 0.0)
    else:
        # Default 'conservative' (FD2320 Table 13.1): 0.5 for shallow, 1.0 for deep
        df_arr = np.where(d > 0.25, 1.0, 0.5)
        df = np.where(d > 0.0, df_arr, 0.0)

    hr = d * (v + 0.5) + df

    if isinstance(depth, (float, int)) and isinstance(velocity, (float, int)):
        return float(hr.item())
    return hr


def classify_hazard(
    depth: np.ndarray[Any, Any] | float,
    velocity: np.ndarray[Any, Any] | float,
    debris_factor: float | None = None,
    land_use: str = "conservative",
) -> np.ndarray[Any, Any] | HazardClass:
    """Classify water depth and velocity into HazardClass categories (1 to 4).

    Returns:
        Categorical array (0: Dry, 1: Low, 2: Moderate, 3: High, 4: Extreme)
        or single HazardClass if scalar.
    """
    hr = calculate_hazard_rating(depth, velocity, debris_factor=debris_factor, land_use=land_use)

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
    land_use: str = "conservative",
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

        hazard_arr = classify_hazard(
            depth, velocity, debris_factor=debris_factor, land_use=land_use
        )
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
