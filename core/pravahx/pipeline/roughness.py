"""Roughness coefficient generation (Phase 1).

Maps land cover classes (e.g., ESA WorldCover) to Manning's n values.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import rasterio

logger = logging.getLogger(__name__)

# ESA WorldCover 10m v200/v210 classes to Manning's n
# 10: Trees, 20: Shrubland, 30: Grassland, 40: Cropland, 50: Built-up,
# 60: Bare / sparse vegetation, 70: Snow and ice, 80: Permanent water bodies,
# 90: Herbaceous wetland, 95: Mangroves, 100: Moss and lichen
WORLDCOVER_TO_MANNINGS = {
    10: 0.100,  # Trees (dense brush/forest)
    20: 0.070,  # Shrubland
    30: 0.035,  # Grassland
    40: 0.040,  # Cropland
    50: 0.015,  # Built-up (smooth surfaces, though buildings obstruct)
    60: 0.025,  # Bare
    70: 0.020,  # Snow/ice
    80: 0.030,  # Water
    90: 0.050,  # Wetland
    95: 0.080,  # Mangroves
    100: 0.030, # Moss/lichen
}

DEFAULT_MANNINGS_N = 0.035


def create_roughness_raster(
    landcover_path: Path | None,
    out_path: Path,
    reference_path: Path,
    default_n: float = DEFAULT_MANNINGS_N,
) -> Path:
    """Create a Manning's n roughness raster.
    
    If landcover_path is provided, maps WorldCover classes to n values.
    Otherwise, creates a uniform raster with default_n.
    
    Args:
        landcover_path: Optional path to land cover raster.
        out_path: Output path for the roughness raster.
        reference_path: Reference raster (e.g., DEM) to match extent/resolution.
        default_n: Default value if no landcover is provided or for unknown classes.
        
    Returns:
        Path to the generated roughness raster.
    """
    logger.info(f"Generating roughness raster at {out_path}")
    
    with rasterio.open(reference_path) as ref:
        meta = ref.meta.copy()
        shape = (ref.height, ref.width)
        
    meta.update(dtype=rasterio.float32, nodata=-9999.0)
    
    if not landcover_path or not landcover_path.exists():
        logger.info(f"No landcover provided, using uniform n={default_n}")
        n_array = np.full(shape, default_n, dtype=np.float32)
    else:
        # In a full implementation, we'd resample/reproject landcover to match reference.
        # For Phase 1, we assume it's pre-aligned or we just use default if mismatch.
        try:
            with rasterio.open(landcover_path) as lc:
                lc_data = lc.read(1)
                
            # Map classes
            n_array = np.full_like(lc_data, default_n, dtype=np.float32)
            for lc_class, n_val in WORLDCOVER_TO_MANNINGS.items():
                n_array[lc_data == lc_class] = n_val
                
        except Exception as exc:
            logger.warning(f"Failed to process landcover: {exc}. Using uniform n={default_n}")
            n_array = np.full(shape, default_n, dtype=np.float32)

    with rasterio.open(out_path, "w", **meta) as dest:
        dest.write(n_array, 1)
        
    return out_path
