"""Agreement map classification and raster generation for flood models (Phase 5)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np
import rasterio
from pydantic import BaseModel, Field

from pravahx.compare.regrid import regrid_raster_to_target
from pravahx.errors import ComparisonError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class AgreementCategoryStats(BaseModel):
    """Statistics for an individual agreement class."""

    class_id: int
    label: str
    cell_count: int
    percentage: float
    area_km2: float


class AgreementSummary(BaseModel):
    """Overall summary of the spatial agreement between two hydrodynamic models."""

    categories: list[AgreementCategoryStats]
    total_cells: int
    total_area_km2: float
    wet_agreement_ratio: float = Field(
        ...,
        description=(
            "Agreed wet area divided by total mutually wet area: Class 3 / (Class 3 + Class 4)"
        ),
    )
    overall_extent_agreement_ratio: float = Field(
        ...,
        description="(Both Dry + Both Wet Agreed) / Total Domain",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


def generate_agreement_raster(
    raster_a_path: Path,
    raster_b_path: Path,
    output_path: Path,
    depth_diff_threshold_m: float = 0.5,
    wet_threshold_m: float = 0.05,
    temp_dir: Path | None = None,
) -> tuple[Path, AgreementSummary]:
    """Generate a classified agreement GeoTIFF map and statistical breakdown.

    Classification Scheme:
      - 0: Both Dry (Neither model floods)
      - 1: Model A Only (Flooded in A, Dry in B)
      - 2: Model B Only (Dry in A, Flooded in B)
      - 3: Both Flooded — Agreed (Depth difference <= threshold)
      - 4: Both Flooded — Disagreed (Depth difference > threshold)

    Args:
        raster_a_path: Path to Model A maximum depth raster.
        raster_b_path: Path to Model B maximum depth raster.
        output_path: Destination path for the agreement GeoTIFF.
        depth_diff_threshold_m: Max depth difference to classify as 'agreed' (default: 0.5 m).
        wet_threshold_m: Minimum depth in metres to consider a cell wet (default: 0.05 m).
        temp_dir: Scratch directory for intermediate regridding if needed.

    Returns:
        Tuple of (output GeoTIFF path, AgreementSummary).
    """
    if not raster_a_path.exists():
        raise ComparisonError(f"Model A depth raster not found: {raster_a_path}")
    if not raster_b_path.exists():
        raise ComparisonError(f"Model B depth raster not found: {raster_b_path}")

    # Inspect geometries
    with rasterio.open(raster_a_path) as src_a, rasterio.open(raster_b_path) as src_b:
        needs_regrid = (
            (src_a.height != src_b.height)
            or (src_a.width != src_b.width)
            or (src_a.transform != src_b.transform)
            or (src_a.crs != src_b.crs)
        )

    work_a_path = raster_a_path
    if needs_regrid:
        if temp_dir is None:
            temp_dir = output_path.parent / "_regrid_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        work_a_path = temp_dir / f"regridded_{raster_a_path.name}"
        regrid_raster_to_target(raster_a_path, raster_b_path, work_a_path)

    with rasterio.open(work_a_path) as src_a, rasterio.open(raster_b_path) as src_b:
        arr_a = src_a.read(1).astype(np.float64)
        arr_b = src_b.read(1).astype(np.float64)
        nodata_a = src_a.nodata
        nodata_b = src_b.nodata
        dst_profile = src_b.profile.copy()
        transform = src_b.transform
        pixel_area_m2 = abs(transform.a) * abs(transform.e)

    if nodata_a is not None:
        arr_a[arr_a == nodata_a] = 0.0
    if nodata_b is not None:
        arr_b[arr_b == nodata_b] = 0.0
    arr_a = np.nan_to_num(arr_a, nan=0.0)
    arr_b = np.nan_to_num(arr_b, nan=0.0)

    wet_a = arr_a >= wet_threshold_m
    wet_b = arr_b >= wet_threshold_m

    # Classification matrix (0..4)
    height, width = arr_b.shape
    agreement_grid = np.zeros((height, width), dtype=np.uint8)

    # 1: A only
    agreement_grid[wet_a & (~wet_b)] = 1
    # 2: B only
    agreement_grid[(~wet_a) & wet_b] = 2

    # Mutually wet cells
    mutually_wet = wet_a & wet_b
    depth_diff = np.abs(arr_a - arr_b)
    agreed_wet = mutually_wet & (depth_diff <= depth_diff_threshold_m)
    disagreed_wet = mutually_wet & (depth_diff > depth_diff_threshold_m)

    # 3: Both agreed
    agreement_grid[agreed_wet] = 3
    # 4: Both disagreed
    agreement_grid[disagreed_wet] = 4

    # Write output GeoTIFF with colormap
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dst_profile.update(
        {
            "driver": "GTiff",
            "dtype": rasterio.uint8,
            "count": 1,
            "nodata": None,
            "compress": "lzw",
        }
    )

    with rasterio.open(output_path, "w", **dst_profile) as dst:
        dst.write(agreement_grid, 1)
        colormap = {
            0: (240, 240, 240, 0),
            1: (230, 57, 70, 255),
            2: (69, 123, 157, 255),
            3: (42, 157, 143, 255),
            4: (244, 162, 97, 255),
        }
        dst.write_colormap(1, colormap)

    # Calculate statistics
    total_cells = height * width
    sq_km_factor = pixel_area_m2 / 1.0e6
    labels = {
        0: "Both Dry",
        1: "Model A Only",
        2: "Model B Only",
        3: "Both Flooded (Agreed)",
        4: "Both Flooded (Disagreed)",
    }

    cat_stats: list[AgreementCategoryStats] = []
    for cid in range(5):
        cnt = int(np.count_nonzero(agreement_grid == cid))
        pct = (cnt / total_cells) * 100.0 if total_cells > 0 else 0.0
        area_km2 = cnt * sq_km_factor
        cat_stats.append(
            AgreementCategoryStats(
                class_id=cid,
                label=labels[cid],
                cell_count=cnt,
                percentage=round(pct, 2),
                area_km2=round(area_km2, 4),
            )
        )

    cnt_both_wet = int(np.count_nonzero(mutually_wet))
    cnt_agreed_wet = int(np.count_nonzero(agreed_wet))
    cnt_both_dry = int(np.count_nonzero(agreement_grid == 0))

    wet_agree_ratio = (cnt_agreed_wet / cnt_both_wet) if cnt_both_wet > 0 else 1.0
    overall_agree_ratio = (cnt_both_dry + cnt_agreed_wet) / total_cells if total_cells > 0 else 1.0

    summary = AgreementSummary(
        categories=cat_stats,
        total_cells=total_cells,
        total_area_km2=round(total_cells * sq_km_factor, 4),
        wet_agreement_ratio=round(wet_agree_ratio, 4),
        overall_extent_agreement_ratio=round(overall_agree_ratio, 4),
        metadata={
            "depth_diff_threshold_m": depth_diff_threshold_m,
            "wet_threshold_m": wet_threshold_m,
            "raster_a": str(raster_a_path.name),
            "raster_b": str(raster_b_path.name),
        },
    )

    logger.info(
        "Agreement raster generated: %s (Agreed Wet Ratio: %.2f%%, Overall: %.2f%%)",
        output_path.name,
        wet_agree_ratio * 100.0,
        overall_agree_ratio * 100.0,
    )

    return output_path, summary
