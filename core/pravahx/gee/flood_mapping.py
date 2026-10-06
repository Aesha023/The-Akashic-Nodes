"""Satellite SAR and optical flood extent extraction (Phase 6 / Section 6).

Methods:
1. UN-SPIDER Recommended Practice (Default SAR Method):
   - Linear ratio change detection: Ratio = sigma0_pre_linear / sigma0_post_linear >= 1.25
     (or in dB: sigma0_pre_dB - sigma0_post_dB >= 10 * log10(1.25) ~= +0.9691 dB).
   - Topographic slope / HAND filter: excludes terrain with slope > 5% or HAND > 15m
     to eliminate mountain radar shadow false positives.
   - Permanent water subtraction: excludes permanent rivers/lakes (e.g. JRC surface water).
   Source URL: https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping/step-by-step

2. Alternative SAR Backscatter Thresholding (Labelled Alternative):
   - Absolute backscatter threshold: sigma0_post < threshold_db (typically -15.0 dB in VV/VH).

3. Optical Water Index (Sentinel-2 / Landsat):
   - MNDWI = (Green - SWIR) / (Green + SWIR)
   - NDWI = (Green - NIR) / (Green + NIR)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pydantic import BaseModel


class FloodExtractionResult(BaseModel):
    """Satellite-derived flood inundation mapping results."""

    sensor_type: str  # "UN_SPIDER_SAR_Sentinel1", "Absolute_SAR_Sentinel1", "Optical_Sentinel2"
    total_flooded_area_km2: float
    total_permanent_water_km2: float
    flood_mask_path: str
    metadata: dict[str, Any] = {}


def extract_unspider_sar_flood(
    post_event_backscatter_db: np.ndarray[Any, Any],
    pre_event_backscatter_db: np.ndarray[Any, Any],
    ratio_threshold: float = 1.25,
    slope_array_deg: np.ndarray[Any, Any] | None = None,
    max_slope_deg: float = 5.0,
    hand_array_m: np.ndarray[Any, Any] | None = None,
    max_hand_m: float = 15.0,
) -> np.ndarray[Any, Any]:
    """Extract flood water mask following the UN-SPIDER recommended practice.

    Computes linear power change ratio:
        Ratio = 10^(pre_dB / 10) / 10^(post_dB / 10) = 10^((pre_dB - post_dB) / 10)
    Flooded where Ratio >= ratio_threshold (default: 1.25), conditioned on slope <= 5 deg
    and HAND <= 15 m.

    Source:
        https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping/step-by-step
    """
    post_db = np.asarray(post_event_backscatter_db, dtype=np.float64)
    pre_db = np.asarray(pre_event_backscatter_db, dtype=np.float64)

    # In linear power scale, water appears darker (lower backscatter), so pre / post >= 1.25
    # Mathematically: pre_dB - post_dB >= 10 * log10(ratio_threshold)
    db_drop_threshold = 10.0 * math.log10(ratio_threshold)
    db_drop = pre_db - post_db

    # Candidate flooded pixels based on UN-SPIDER ratio
    flood_candidate = (db_drop >= db_drop_threshold) & (post_db < -12.0)

    # Topographic slope filter (mask out steep slopes > 5 deg to remove radar shadow)
    if slope_array_deg is not None:
        slope_mask = np.asarray(slope_array_deg, dtype=np.float64) <= max_slope_deg
        flood_candidate = flood_candidate & slope_mask

    # HAND filter (mask out high elevation above nearest drainage)
    if hand_array_m is not None:
        hand_mask = np.asarray(hand_array_m, dtype=np.float64) <= max_hand_m
        flood_candidate = flood_candidate & hand_mask

    return flood_candidate.astype(np.uint8)


def extract_sar_flood_extent_alternative(
    post_event_backscatter_db: np.ndarray[Any, Any],
    pre_event_backscatter_db: np.ndarray[Any, Any] | None = None,
    threshold_db: float = -15.0,
    diff_threshold_db: float = -3.0,
) -> np.ndarray[Any, Any]:
    """Alternative absolute/difference SAR backscatter thresholding method."""
    post = np.asarray(post_event_backscatter_db, dtype=np.float64)
    water_abs = post < threshold_db

    if pre_event_backscatter_db is not None:
        pre = np.asarray(pre_event_backscatter_db, dtype=np.float64)
        diff = post - pre
        water_diff = diff <= diff_threshold_db
        flood_mask = (water_abs | water_diff) & (post < -12.0)
    else:
        flood_mask = water_abs

    return flood_mask.astype(np.uint8)


# Alias for backward compatibility
extract_sar_flood_extent = extract_sar_flood_extent_alternative


def extract_optical_water_extent(
    green_band: np.ndarray[Any, Any],
    swir_band: np.ndarray[Any, Any] | None = None,
    nir_band: np.ndarray[Any, Any] | None = None,
    threshold: float = 0.0,
) -> np.ndarray[Any, Any]:
    """Extract water mask from optical bands using MNDWI or NDWI."""
    g = np.asarray(green_band, dtype=np.float64)

    if swir_band is not None:
        swir = np.asarray(swir_band, dtype=np.float64)
        mndwi = (g - swir) / np.maximum(1e-6, g + swir)
        water = mndwi > threshold
    elif nir_band is not None:
        nir = np.asarray(nir_band, dtype=np.float64)
        ndwi = (g - nir) / np.maximum(1e-6, g + nir)
        water = ndwi > threshold
    else:
        raise ValueError("Either swir_band or nir_band must be provided.")

    res: np.ndarray[Any, Any] = water.astype(np.uint8)
    return res


def process_satellite_flood_raster(
    post_event_raster_path: str | Path,
    output_mask_path: str | Path,
    sensor_type: str = "UN_SPIDER_SAR_Sentinel1",
    pre_event_raster_path: str | Path | None = None,
    slope_raster_path: str | Path | None = None,
    hand_raster_path: str | Path | None = None,
    permanent_water_mask_path: str | Path | None = None,
    ratio_threshold: float = 1.25,
) -> FloodExtractionResult:
    """Generate satellite flood inundation GeoTIFF following UN-SPIDER change detection."""
    out_p = Path(output_mask_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(post_event_raster_path) as src:
        post_data = src.read(1)

        slope_data = None
        if slope_raster_path:
            with rasterio.open(slope_raster_path) as slp_src:
                slope_data = slp_src.read(1)

        hand_data = None
        if hand_raster_path:
            with rasterio.open(hand_raster_path) as hnd_src:
                hand_data = hnd_src.read(1)

        if sensor_type in ("UN_SPIDER_SAR_Sentinel1", "SAR_Sentinel1") and pre_event_raster_path:
            with rasterio.open(pre_event_raster_path) as pre_src:
                pre_data = pre_src.read(1)
            raw_water = extract_unspider_sar_flood(
                post_event_backscatter_db=post_data,
                pre_event_backscatter_db=pre_data,
                ratio_threshold=ratio_threshold,
                slope_array_deg=slope_data,
                hand_array_m=hand_data,
            )
        elif sensor_type in ("Absolute_SAR_Sentinel1", "SAR_Sentinel1", "UN_SPIDER_SAR_Sentinel1"):
            pre_data = None
            if pre_event_raster_path:
                with rasterio.open(pre_event_raster_path) as pre_src:
                    pre_data = pre_src.read(1)
            raw_water = extract_sar_flood_extent_alternative(
                post_event_backscatter_db=post_data,
                pre_event_backscatter_db=pre_data,
            )
        else:
            raw_water = (post_data > 0).astype(np.uint8)

        # Subtract permanent water if provided
        perm_water_km2 = 0.0
        if permanent_water_mask_path:
            with rasterio.open(permanent_water_mask_path) as perm_src:
                perm_data = perm_src.read(1)
                perm_mask = perm_data > 0
                cell_area_km2 = (abs(src.res[0]) * abs(src.res[1])) / 1e6
                perm_water_km2 = float(np.sum(perm_mask) * cell_area_km2)
                raw_water = np.where(perm_mask, 0, raw_water)

        cell_area_km2 = (abs(src.res[0]) * abs(src.res[1])) / 1e6
        flooded_km2 = float(np.sum(raw_water > 0) * cell_area_km2)

        profile = src.profile.copy()
        profile.update(
            dtype=rasterio.uint8,
            count=1,
            nodata=0,
            compress="deflate",
        )

        with rasterio.open(out_p, "w", **profile) as dst:
            dst.write(raw_water.astype(np.uint8), 1)

    return FloodExtractionResult(
        sensor_type=sensor_type,
        total_flooded_area_km2=round(flooded_km2, 6),
        total_permanent_water_km2=round(perm_water_km2, 6),
        flood_mask_path=str(out_p),
        metadata={
            "resolution_m": float(abs(src.res[0])),
            "crs": str(src.crs),
            "ratio_threshold": ratio_threshold,
            "method": "UN-SPIDER Recommended Practice (change detection)",
        },
    )
