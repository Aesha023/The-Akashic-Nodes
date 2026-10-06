"""Hydrodynamic comparison metrics: spatial extent, depth error, and timing (Phase 5)."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

import numpy as np
import rasterio
from pydantic import BaseModel, Field

from pravahx.compare.regrid import regrid_raster_to_target
from pravahx.errors import ComparisonError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class ComparisonMetrics(BaseModel):
    """Statistical and spatial comparison metrics between two inundation model runs."""

    # Spatial extent metrics
    iou: float = Field(
        ...,
        description="Intersection over Union / Critical Success Index: TP / (TP + FP + FN)",
    )
    f1_score: float = Field(..., description="Dice / F1 score: 2*TP / (2*TP + FP + FN)")
    precision: float = Field(
        ...,
        description="Precision / Positive Predictive Value: TP / (TP + FP)",
    )
    recall: float = Field(..., description="Recall / Hit Rate: TP / (TP + FN)")
    false_alarm_ratio: float = Field(..., description="False Alarm Ratio: FP / (TP + FP)")

    tp_cells: int = Field(..., description="Number of mutually wet cells (True Positives)")
    fp_cells: int = Field(..., description="Wet in A, dry in B (False Positives)")
    fn_cells: int = Field(..., description="Dry in A, wet in B (False Negatives)")
    tn_cells: int = Field(..., description="Dry in both models (True Negatives)")

    wet_area_a_km2: float = Field(
        ...,
        description="Total wet surface area in Model A in square kilometres",
    )
    wet_area_b_km2: float = Field(
        ...,
        description="Total wet surface area in Model B in square kilometres",
    )
    overlap_area_km2: float = Field(
        ...,
        description="Mutually flooded surface area in square kilometres",
    )

    # Depth comparison (evaluated over mutually wet cells)
    depth_rmse_m: float | None = Field(
        None,
        description="Depth RMSE in metres over mutually wet cells",
    )
    depth_mae_m: float | None = Field(
        None,
        description="Depth MAE in metres over mutually wet cells",
    )
    depth_bias_m: float | None = Field(
        None,
        description="Mean depth bias (A - B) in metres over mutually wet cells",
    )
    depth_max_a_m: float = Field(..., description="Maximum depth in Model A in metres")
    depth_max_b_m: float = Field(..., description="Maximum depth in Model B in metres")
    depth_correlation: float | None = Field(
        None,
        description="Pearson correlation coefficient of depth over mutually wet cells",
    )

    # Arrival time comparison (evaluated over mutually wet cells with valid timing)
    arrival_mae_min: float | None = Field(None, description="Arrival time MAE in minutes")
    arrival_rmse_min: float | None = Field(None, description="Arrival time RMSE in minutes")
    arrival_bias_min: float | None = Field(None, description="Arrival time bias (A - B) in minutes")

    # Context
    wet_threshold_m: float = Field(
        ...,
        description="Depth threshold used to classify wet cells (m)",
    )
    pixel_area_m2: float = Field(
        ...,
        description="Surface area of an individual grid cell in square metres",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context or provenance",
    )


def compute_comparison_metrics(
    depth_a_path: Path,
    depth_b_path: Path,
    arrival_a_path: Path | None = None,
    arrival_b_path: Path | None = None,
    wet_threshold_m: float = 0.05,
    temp_dir: Path | None = None,
) -> ComparisonMetrics:
    """Compute comprehensive spatial, depth, and arrival-time comparison metrics.

    Args:
        depth_a_path: GeoTIFF path for Model A maximum depth raster.
        depth_b_path: GeoTIFF path for Model B maximum depth raster.
        arrival_a_path: Optional GeoTIFF path for Model A arrival time raster.
        arrival_b_path: Optional GeoTIFF path for Model B arrival time raster.
        wet_threshold_m: Inundation threshold depth in metres (default 0.05 m).
        temp_dir: Optional scratch directory for regridded temporary rasters.

    Returns:
        ComparisonMetrics instance with all calculated statistics.

    Raises:
        ComparisonError: If raster files cannot be read or processed.
    """
    if not depth_a_path.exists():
        raise ComparisonError(f"Model A depth raster not found: {depth_a_path}")
    if not depth_b_path.exists():
        raise ComparisonError(f"Model B depth raster not found: {depth_b_path}")

    # Inspect raster geometries
    with rasterio.open(depth_a_path) as src_a, rasterio.open(depth_b_path) as src_b:
        shape_a = (src_a.height, src_a.width)
        shape_b = (src_b.height, src_b.width)
        transform_a = src_a.transform
        transform_b = src_b.transform
        crs_a = src_a.crs
        crs_b = src_b.crs
        cell_size_x = abs(transform_a.a)
        cell_size_y = abs(transform_a.e)
        pixel_area_m2 = cell_size_x * cell_size_y

        needs_regrid = (shape_a != shape_b) or (transform_a != transform_b) or (crs_a != crs_b)

    work_a_depth = depth_a_path
    work_a_arrival = arrival_a_path

    if needs_regrid:
        if temp_dir is None:
            temp_dir = depth_a_path.parent / "_regrid_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        work_a_depth = temp_dir / f"regridded_{depth_a_path.name}"
        regrid_raster_to_target(depth_a_path, depth_b_path, work_a_depth)

        if arrival_a_path is not None and arrival_a_path.exists():
            work_a_arrival = temp_dir / f"regridded_{arrival_a_path.name}"
            regrid_raster_to_target(arrival_a_path, depth_b_path, work_a_arrival)

        with rasterio.open(depth_b_path) as src_b:
            pixel_area_m2 = abs(src_b.transform.a) * abs(src_b.transform.e)

    # Read aligned rasters
    with rasterio.open(work_a_depth) as src_a, rasterio.open(depth_b_path) as src_b:
        arr_a = src_a.read(1).astype(np.float64)
        arr_b = src_b.read(1).astype(np.float64)
        nodata_a = src_a.nodata
        nodata_b = src_b.nodata

    # Mask nodata
    if nodata_a is not None:
        arr_a[arr_a == nodata_a] = 0.0
    if nodata_b is not None:
        arr_b[arr_b == nodata_b] = 0.0
    arr_a = np.nan_to_num(arr_a, nan=0.0)
    arr_b = np.nan_to_num(arr_b, nan=0.0)

    # Binary wet masks
    wet_a = arr_a >= wet_threshold_m
    wet_b = arr_b >= wet_threshold_m

    tp = int(np.count_nonzero(wet_a & wet_b))
    fp = int(np.count_nonzero(wet_a & (~wet_b)))
    fn = int(np.count_nonzero((~wet_a) & wet_b))
    tn = int(np.count_nonzero((~wet_a) & (~wet_b)))

    # Spatial extent metrics
    union = tp + fp + fn
    iou = float(tp / union) if union > 0 else (1.0 if (tp == 0 and fp == 0 and fn == 0) else 0.0)
    dice_denom = 2 * tp + fp + fn
    f1_score = float((2 * tp) / dice_denom) if dice_denom > 0 else (1.0 if dice_denom == 0 else 0.0)
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else (1.0 if tp == 0 else 0.0)
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else (1.0 if tp == 0 else 0.0)
    far = float(fp / (tp + fp)) if (tp + fp) > 0 else 0.0

    sq_km_conv = pixel_area_m2 / 1.0e6
    wet_area_a_km2 = float((tp + fp) * sq_km_conv)
    wet_area_b_km2 = float((tp + fn) * sq_km_conv)
    overlap_area_km2 = float(tp * sq_km_conv)

    depth_max_a = float(np.max(arr_a))
    depth_max_b = float(np.max(arr_b))

    # Depth errors over mutually wet cells (TP)
    depth_rmse: float | None = None
    depth_mae: float | None = None
    depth_bias: float | None = None
    depth_corr: float | None = None

    if tp > 0:
        d_a_tp = arr_a[wet_a & wet_b]
        d_b_tp = arr_b[wet_a & wet_b]
        diff = d_a_tp - d_b_tp

        depth_rmse = float(np.sqrt(np.mean(diff**2)))
        depth_mae = float(np.mean(np.abs(diff)))
        depth_bias = float(np.mean(diff))

        # Pearson correlation
        if len(d_a_tp) > 1 and np.std(d_a_tp) > 1e-6 and np.std(d_b_tp) > 1e-6:
            r = np.corrcoef(d_a_tp, d_b_tp)[0, 1]
            depth_corr = float(r) if not math.isnan(r) else None

    # Arrival time metrics
    arrival_mae: float | None = None
    arrival_rmse: float | None = None
    arrival_bias: float | None = None

    has_arr_a = work_a_arrival is not None and work_a_arrival.exists()
    has_arr_b = arrival_b_path is not None and arrival_b_path.exists()
    if has_arr_a and has_arr_b and work_a_arrival is not None and arrival_b_path is not None:
        with rasterio.open(work_a_arrival) as src_t_a, rasterio.open(arrival_b_path) as src_t_b:
            t_a = src_t_a.read(1).astype(np.float64)
            t_b = src_t_b.read(1).astype(np.float64)

        # Mutually wet cells with positive arrival times
        timing_mask = (wet_a & wet_b) & (t_a > 0.0) & (t_b > 0.0)
        if np.count_nonzero(timing_mask) > 0:
            dt = t_a[timing_mask] - t_b[timing_mask]
            arrival_mae = float(np.mean(np.abs(dt)))
            arrival_rmse = float(np.sqrt(np.mean(dt**2)))
            arrival_bias = float(np.mean(dt))

    return ComparisonMetrics(
        iou=round(iou, 4),
        f1_score=round(f1_score, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        false_alarm_ratio=round(far, 4),
        tp_cells=tp,
        fp_cells=fp,
        fn_cells=fn,
        tn_cells=tn,
        wet_area_a_km2=round(wet_area_a_km2, 4),
        wet_area_b_km2=round(wet_area_b_km2, 4),
        overlap_area_km2=round(overlap_area_km2, 4),
        depth_rmse_m=round(depth_rmse, 4) if depth_rmse is not None else None,
        depth_mae_m=round(depth_mae, 4) if depth_mae is not None else None,
        depth_bias_m=round(depth_bias, 4) if depth_bias is not None else None,
        depth_max_a_m=round(depth_max_a, 4),
        depth_max_b_m=round(depth_max_b, 4),
        depth_correlation=round(depth_corr, 4) if depth_corr is not None else None,
        arrival_mae_min=round(arrival_mae, 4) if arrival_mae is not None else None,
        arrival_rmse_min=round(arrival_rmse, 4) if arrival_rmse is not None else None,
        arrival_bias_min=round(arrival_bias, 4) if arrival_bias is not None else None,
        wet_threshold_m=wet_threshold_m,
        pixel_area_m2=pixel_area_m2,
        metadata={
            "source_a": str(depth_a_path.name),
            "source_b": str(depth_b_path.name),
        },
    )
