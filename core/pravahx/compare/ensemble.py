"""Ensemble and uncertainty raster aggregation for multi-scenario flood modeling (Phase 5)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pydantic import BaseModel, Field

from pravahx.compare.regrid import align_rasters_to_common_grid
from pravahx.errors import ComparisonError

logger = logging.getLogger(__name__)


class EnsembleRasterResults(BaseModel):
    """Paths and summary metadata for aggregated ensemble rasters."""

    probability_raster: Path
    depth_min_raster: Path
    depth_median_raster: Path
    depth_max_raster: Path
    depth_std_raster: Path
    scenario_count: int
    percentiles: tuple[float, float, float]
    depth_threshold_m: float
    max_inundation_area_km2: float = Field(
        ...,
        description="Surface area where probability of inundation > 0 in square kilometres",
    )
    median_inundation_area_km2: float = Field(
        ...,
        description="Surface area where median depth >= threshold in square kilometres",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


def aggregate_ensemble_rasters(
    raster_paths: list[Path],
    output_dir: Path,
    depth_threshold_m: float = 0.05,
    percentiles: tuple[float, float, float] = (10.0, 50.0, 90.0),
    nodata_val: float = -9999.0,
) -> EnsembleRasterResults:
    """Aggregate multiple depth raster realizations into probability and percentile rasters.

    Args:
        raster_paths: List of file paths to scenario depth GeoTIFFs.
        output_dir: Output directory for aggregated GeoTIFFs.
        depth_threshold_m: Minimum depth in metres to consider a cell inundated (default: 0.05 m).
        percentiles: Tuple of three percentiles to compute (default: (10.0, 50.0, 90.0)).
        nodata_val: Nodata value for output rasters.

    Returns:
        EnsembleRasterResults containing paths to generated rasters and summary statistics.

    Raises:
        ComparisonError: If raster_paths has fewer than 2 realizations or files are missing.
    """
    if len(raster_paths) < 2:
        raise ComparisonError(
            f"Ensemble aggregation requires at least 2 raster realizations, got {len(raster_paths)}"
        )

    for rp in raster_paths:
        if not rp.exists():
            raise ComparisonError(f"Scenario raster not found: {rp}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Check if alignment is needed
    with rasterio.open(raster_paths[0]) as ref:
        ref_shape = (ref.height, ref.width)
        ref_transform = ref.transform
        ref_crs = ref.crs

    needs_align = False
    for rp in raster_paths[1:]:
        with rasterio.open(rp) as src:
            if (
                (src.height, src.width) != ref_shape
                or src.transform != ref_transform
                or src.crs != ref_crs
            ):
                needs_align = True
                break

    aligned_paths = raster_paths
    if needs_align:
        temp_dir = output_dir / "_align_temp"
        aligned_paths = align_rasters_to_common_grid(
            raster_paths=raster_paths,
            output_dir=temp_dir,
            extent_mode="intersection",
        )

    # 2. Read all aligned depth rasters into a 3D numpy stack (N, H, W)
    arrays: list[np.ndarray] = []
    with rasterio.open(aligned_paths[0]) as first_src:
        profile = first_src.profile.copy()
        pixel_area_m2 = abs(first_src.transform.a) * abs(first_src.transform.e)

    for ap in aligned_paths:
        with rasterio.open(ap) as src:
            arr = src.read(1).astype(np.float64)
            if src.nodata is not None:
                arr[arr == src.nodata] = 0.0
            arr = np.nan_to_num(arr, nan=0.0)
            # Clip negative depths if any
            arr = np.maximum(arr, 0.0)
            arrays.append(arr)

    stack = np.stack(arrays, axis=0)  # shape (N, H, W)
    num_scenarios = stack.shape[0]

    # 3. Compute probability of inundation P(depth >= threshold)
    wet_flags = (stack >= depth_threshold_m).astype(np.float64)
    prob_inundation = np.mean(wet_flags, axis=0).astype(np.float32)

    # 4. Compute percentiles (e.g. p10, p50, p90)
    p_low, p_med, p_high = percentiles
    depth_min = np.percentile(stack, p_low, axis=0).astype(np.float32)
    depth_median = np.percentile(stack, p_med, axis=0).astype(np.float32)
    depth_max = np.percentile(stack, p_high, axis=0).astype(np.float32)
    depth_std = np.std(stack, axis=0).astype(np.float32)

    # 5. Write GeoTIFF outputs
    profile.update(
        {
            "driver": "GTiff",
            "dtype": rasterio.float32,
            "count": 1,
            "nodata": nodata_val,
            "compress": "lzw",
        }
    )

    prob_path = output_dir / "inundation_probability.tif"
    min_path = output_dir / f"depth_p{int(p_low)}.tif"
    med_path = output_dir / f"depth_p{int(p_med)}.tif"
    max_path = output_dir / f"depth_p{int(p_high)}.tif"
    std_path = output_dir / "depth_std.tif"

    outputs_map = {
        prob_path: prob_inundation,
        min_path: depth_min,
        med_path: depth_median,
        max_path: depth_max,
        std_path: depth_std,
    }

    for path, data in outputs_map.items():
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(data, 1)

    # 6. Calculate summary areas
    sq_km_factor = pixel_area_m2 / 1.0e6
    max_inun_cells = int(np.count_nonzero(prob_inundation > 0.0))
    med_inun_cells = int(np.count_nonzero(depth_median >= depth_threshold_m))

    max_inun_km2 = max_inun_cells * sq_km_factor
    med_inun_km2 = med_inun_cells * sq_km_factor

    logger.info(
        "Aggregated %d scenario rasters: Max area = %.2f km2, Median area = %.2f km2",
        num_scenarios,
        max_inun_km2,
        med_inun_km2,
    )

    return EnsembleRasterResults(
        probability_raster=prob_path,
        depth_min_raster=min_path,
        depth_median_raster=med_path,
        depth_max_raster=max_path,
        depth_std_raster=std_path,
        scenario_count=num_scenarios,
        percentiles=percentiles,
        depth_threshold_m=depth_threshold_m,
        max_inundation_area_km2=round(max_inun_km2, 4),
        median_inundation_area_km2=round(med_inun_km2, 4),
        metadata={
            "input_rasters": [p.name for p in raster_paths],
            "pixel_area_m2": pixel_area_m2,
        },
    )
