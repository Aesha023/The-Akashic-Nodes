"""Spatial regridding and raster alignment for multi-tier comparison (Phase 5)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

from pravahx.errors import RasterAlignmentError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def regrid_raster_to_target(
    source_path: Path,
    target_path: Path,
    output_path: Path,
    resampling: Resampling = Resampling.bilinear,
    nodata_val: float = -9999.0,
) -> Path:
    """Reproject and resample a source raster to match the geometry of a target raster.

    Args:
        source_path: Path to the input source GeoTIFF raster.
        target_path: Path to the reference/target GeoTIFF raster.
        output_path: Destination path for the regridded GeoTIFF raster.
        resampling: Rasterio Resampling method (default: bilinear).
        nodata_val: Nodata value to set in the destination raster.

    Returns:
        Path to the newly created regridded GeoTIFF raster.

    Raises:
        RasterAlignmentError: If CRS or spatial bounds do not overlap.
    """
    if not source_path.exists():
        raise RasterAlignmentError(
            f"Source raster does not exist: {source_path}",
            detail={"source_path": str(source_path)},
        )
    if not target_path.exists():
        raise RasterAlignmentError(
            f"Target reference raster does not exist: {target_path}",
            detail={"target_path": str(target_path)},
        )

    with rasterio.open(target_path) as tgt, rasterio.open(source_path) as src:
        dst_crs = tgt.crs
        dst_transform = tgt.transform
        dst_width = tgt.width
        dst_height = tgt.height
        dst_bounds = tgt.bounds

        # Check for non-empty bounding box overlap
        src_bounds = src.bounds
        # Simple overlap check in native coordinates if CRSs match
        if src.crs == tgt.crs:
            x_overlap = max(
                0.0,
                min(src_bounds.right, dst_bounds.right) - max(src_bounds.left, dst_bounds.left),
            )
            y_overlap = max(
                0.0,
                min(src_bounds.top, dst_bounds.top) - max(src_bounds.bottom, dst_bounds.bottom),
            )
            if x_overlap <= 0 or y_overlap <= 0:
                raise RasterAlignmentError(
                    f"Rasters do not spatially overlap: {source_path.name} vs {target_path.name}",
                    detail={
                        "source_bounds": [
                            src_bounds.left,
                            src_bounds.bottom,
                            src_bounds.right,
                            src_bounds.top,
                        ],
                        "target_bounds": [
                            dst_bounds.left,
                            dst_bounds.bottom,
                            dst_bounds.right,
                            dst_bounds.top,
                        ],
                    },
                )

        src_data = src.read(1)
        src_nodata = src.nodata

        destination = np.full((dst_height, dst_width), nodata_val, dtype=np.float32)

        reproject(
            source=src_data,
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            src_nodata=src_nodata,
            dst_nodata=nodata_val,
            resampling=resampling,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        profile = tgt.profile.copy()
        profile.update(
            {
                "driver": "GTiff",
                "dtype": rasterio.float32,
                "count": 1,
                "nodata": nodata_val,
                "compress": "lzw",
            }
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(destination, 1)

    logger.info(
        "Successfully regridded %s to match %s -> %s",
        source_path.name,
        target_path.name,
        output_path.name,
    )
    return output_path


def align_rasters_to_common_grid(
    raster_paths: list[Path],
    output_dir: Path,
    target_resolution_m: float | None = None,
    extent_mode: Literal["intersection", "union"] = "intersection",
    resampling: Resampling = Resampling.bilinear,
    nodata_val: float = -9999.0,
) -> list[Path]:
    """Align multiple rasters to a single unified spatial bounding box and grid resolution.

    Args:
        raster_paths: List of input raster paths to align.
        output_dir: Directory where aligned GeoTIFFs will be saved.
        target_resolution_m: Target pixel size in meters (default: finest among inputs).
        extent_mode: Spatial extent computation ('intersection' or 'union').
        resampling: Resampling method.
        nodata_val: Nodata value.

    Returns:
        List of paths to newly aligned rasters in output_dir.

    Raises:
        RasterAlignmentError: If input raster list is empty or extents do not intersect.
    """
    if not raster_paths:
        raise RasterAlignmentError("No raster paths provided for grid alignment.")

    output_dir.mkdir(parents=True, exist_ok=True)

    crs_set = set()
    bounds_list = []
    resolutions = []

    for rp in raster_paths:
        if not rp.exists():
            raise RasterAlignmentError(f"Raster file not found: {rp}")
        with rasterio.open(rp) as src:
            crs_set.add(src.crs.to_string())
            bounds_list.append(src.bounds)
            resolutions.append(abs(src.transform.a))

    if len(crs_set) > 1:
        logger.warning("Input rasters have differing CRSs: %s. Using first CRS.", crs_set)

    with rasterio.open(raster_paths[0]) as first_src:
        base_crs = first_src.crs

    if extent_mode == "intersection":
        min_x = max(b.left for b in bounds_list)
        max_x = min(b.right for b in bounds_list)
        min_y = max(b.bottom for b in bounds_list)
        max_y = min(b.top for b in bounds_list)

        if min_x >= max_x or min_y >= max_y:
            raise RasterAlignmentError(
                "Input rasters do not share a common intersecting bounding box.",
                detail={"extent_mode": extent_mode, "bounds_list": [list(b) for b in bounds_list]},
            )
    else:  # union
        min_x = min(b.left for b in bounds_list)
        max_x = max(b.right for b in bounds_list)
        min_y = min(b.bottom for b in bounds_list)
        max_y = max(b.top for b in bounds_list)

    pixel_size = target_resolution_m if target_resolution_m is not None else min(resolutions)
    width = max(1, int(np.ceil((max_x - min_x) / pixel_size)))
    height = max(1, int(np.ceil((max_y - min_y) / pixel_size)))

    dst_transform = from_bounds(min_x, min_y, max_x, max_y, width, height)

    aligned_paths: list[Path] = []

    for rp in raster_paths:
        out_p = output_dir / f"aligned_{rp.name}"
        with rasterio.open(rp) as src:
            src_data = src.read(1)
            destination = np.full((height, width), nodata_val, dtype=np.float32)

            reproject(
                source=src_data,
                destination=destination,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=base_crs,
                src_nodata=src.nodata,
                dst_nodata=nodata_val,
                resampling=resampling,
            )

            profile = {
                "driver": "GTiff",
                "dtype": rasterio.float32,
                "count": 1,
                "crs": base_crs,
                "transform": dst_transform,
                "width": width,
                "height": height,
                "nodata": nodata_val,
                "compress": "lzw",
            }

            with rasterio.open(out_p, "w", **profile) as dst:
                dst.write(destination, 1)

        aligned_paths.append(out_p)

    return aligned_paths
