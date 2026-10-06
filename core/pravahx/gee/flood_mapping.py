"""Satellite SAR and optical flood extent extraction (Phase 6 / Section 6).

Methods:
1. SAR Backscatter Thresholding (Sentinel-1 GRD):
   - Water surfaces act as specular reflectors, resulting in low backscatter
     (< -14 to -17 dB in VV/VH).
   - Difference method: Delta_sigma0 = sigma0_post - sigma0_pre (drop in backscatter <= -3.0 dB).
2. Optical Water Index (Sentinel-2 / Landsat):
   - MNDWI = (Green - SWIR) / (Green + SWIR)
   - NDWI = (Green - NIR) / (Green + NIR)
   - Water threshold: MNDWI > 0.0 or NDWI > 0.0 with Cloud SCL masking.
3. Permanent Water Masking:
   - Excludes pre-existing lakes/rivers to isolate newly flooded floodplains.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pydantic import BaseModel


class FloodExtractionResult(BaseModel):
    """Satellite-derived flood inundation mapping results."""

    sensor_type: str  # "SAR_Sentinel1", "Optical_Sentinel2", "Synthetic"
    total_flooded_area_km2: float
    total_permanent_water_km2: float
    flood_mask_path: str
    metadata: dict[str, Any] = {}


def extract_sar_flood_extent(
    post_event_backscatter_db: np.ndarray[Any, Any],
    pre_event_backscatter_db: np.ndarray[Any, Any] | None = None,
    threshold_db: float = -15.0,
    diff_threshold_db: float = -3.0,
) -> np.ndarray[Any, Any]:
    """Extract flood water mask from Sentinel-1 SAR backscatter array (in dB).

    Args:
        post_event_backscatter_db: Post-flood SAR backscatter image in dB.
        pre_event_backscatter_db: Optional pre-flood baseline SAR image in dB.
        threshold_db: Absolute backscatter threshold for open water (default -15.0 dB).
        diff_threshold_db: Relative drop threshold (post - pre <= diff_threshold_db).

    Returns:
        Binary uint8 mask (1: Flooded, 0: Non-flooded).
    """
    post = np.asarray(post_event_backscatter_db, dtype=np.float64)

    # Absolute thresholding: open calm water is typically < -15 dB
    water_abs = post < threshold_db

    if pre_event_backscatter_db is not None:
        pre = np.asarray(pre_event_backscatter_db, dtype=np.float64)
        # Relative drop in backscatter due to specular reflection
        diff = post - pre
        water_diff = diff <= diff_threshold_db
        # Flood water is both low backscatter and significantly darker than pre-event baseline
        flood_mask = (water_abs | water_diff) & (post < -12.0)
    else:
        flood_mask = water_abs

    return flood_mask.astype(np.uint8)


def extract_optical_water_extent(
    green_band: np.ndarray[Any, Any],
    swir_band: np.ndarray[Any, Any] | None = None,
    nir_band: np.ndarray[Any, Any] | None = None,
    threshold: float = 0.0,
) -> np.ndarray[Any, Any]:
    """Extract water mask from optical bands using MNDWI or NDWI.

    MNDWI = (Green - SWIR) / (Green + SWIR + 1e-6)
    NDWI = (Green - NIR) / (Green + NIR + 1e-6)

    Returns:
        Binary uint8 mask (1: Water, 0: Non-water).
    """
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
    sensor_type: str = "SAR_Sentinel1",
    pre_event_raster_path: str | Path | None = None,
    permanent_water_mask_path: str | Path | None = None,
) -> FloodExtractionResult:
    """Generate satellite flood inundation GeoTIFF from raw satellite raster bands."""
    out_p = Path(output_mask_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(post_event_raster_path) as src:
        post_data = src.read(1)

        if sensor_type == "SAR_Sentinel1":
            pre_data = None
            if pre_event_raster_path:
                with rasterio.open(pre_event_raster_path) as pre_src:
                    pre_data = pre_src.read(1)
            raw_water = extract_sar_flood_extent(
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
        },
    )
