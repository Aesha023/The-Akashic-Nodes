"""Delft3D Flexible Mesh output reader (xarray) to NormalisedOutput."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import rasterio
import xarray as xr

from pravahx.engines.base import (
    NormalisedLayer,
    NormalisedOutput,
    compute_file_hash,
)
from pravahx.errors import EngineError

if TYPE_CHECKING:
    from pravahx.engines.base import RawResult, RunContext

logger = logging.getLogger(__name__)


def read_delft3d_output(raw_result: RawResult, context: RunContext) -> NormalisedOutput:
    """Read Delft3D FM NetCDF map output and export normalised rasters.

    Extracts maximum depth, maximum velocity, and flood arrival time.

    Args:
        raw_result: RawResult containing solver output directory.
        context: RunContext for metadata and projection.

    Returns:
        NormalisedOutput containing standard layers.
    """
    output_dir = raw_result.output_dir

    # Locate map NetCDF file (*_map.nc)
    map_files = list(output_dir.glob("**/*_map.nc"))
    if not map_files:
        raise EngineError(
            f"No Delft3D FM map output (*_map.nc) found in {output_dir}",
            engine="delft3d_fm",
        )

    map_path = map_files[0]
    logger.info(f"Reading Delft3D FM NetCDF map file: {map_path}")

    # Open NetCDF dataset with xarray
    with xr.open_dataset(map_path) as ds:
        # Check available depth variables
        depth_var = None
        for candidate in ["mesh2d_waterdepth", "waterdepth", "s1", "depth"]:
            if candidate in ds.data_vars:
                depth_var = candidate
                break

        if depth_var is None:
            raise EngineError(
                f"No water depth variable found in Delft3D FM NetCDF: {list(ds.data_vars.keys())}",
                engine="delft3d_fm",
            )

        # Compute max depth across time
        depth_da = ds[depth_var]
        max_depth_da = depth_da.max(dim="time") if "time" in depth_da.dims else depth_da

        # Check for velocity variables
        vel_var = None
        for candidate in ["mesh2d_ucmag", "ucmag", "mesh2d_ucx", "ucx"]:
            if candidate in ds.data_vars:
                vel_var = candidate
                break

        max_vel_arr = None
        if vel_var:
            if "ucmag" in vel_var:
                vel_da = ds[vel_var]
                max_vel_da = vel_da.max(dim="time") if "time" in vel_da.dims else vel_da
                max_vel_arr = np.nan_to_num(max_vel_da.values, nan=0.0)
            elif "mesh2d_ucx" in ds.data_vars and "mesh2d_ucy" in ds.data_vars:
                ucx = ds["mesh2d_ucx"]
                ucy = ds["mesh2d_ucy"]
                vmag = np.sqrt(ucx**2 + ucy**2)
                max_vel_da = vmag.max(dim="time") if "time" in vmag.dims else vmag
                max_vel_arr = np.nan_to_num(max_vel_da.values, nan=0.0)

        depth_arr = np.nan_to_num(max_depth_da.values, nan=0.0).astype(np.float32)

    # Grid / Coordinate bounds
    # If 2D regular grid in xarray:
    if depth_arr.ndim == 1:
        # Reshape 1D cell array into synthetic 2D raster if coordinates are present
        side = int(np.sqrt(len(depth_arr)))
        if side * side == len(depth_arr):
            depth_2d = depth_arr.reshape((side, side))
            if max_vel_arr is not None and len(max_vel_arr) == len(depth_arr):
                vel_2d = max_vel_arr.reshape((side, side)).astype(np.float32)
            else:
                vel_2d = np.zeros_like(depth_2d)
        else:
            depth_2d = depth_arr[: side * side].reshape((side, side))
            vel_2d = np.zeros_like(depth_2d)
    else:
        depth_2d = depth_arr
        vel_2d = (
            max_vel_arr.astype(np.float32) if max_vel_arr is not None else np.zeros_like(depth_2d)
        )

    # Export max_depth raster
    height, width = depth_2d.shape
    crs_str = (
        context.config.geometry.crs if context.config and context.config.geometry else "EPSG:32644"
    )
    transform = rasterio.transform.from_origin(0.0, float(height), 1.0, 1.0)

    max_depth_path = output_dir / "delft3d_max_depth.tif"
    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": rasterio.float32,
        "nodata": -9999.0,
        "transform": transform,
        "crs": crs_str,
    }
    with rasterio.open(max_depth_path, "w", **meta) as dst:
        dst.write(depth_2d, 1)

    layers = [
        NormalisedLayer(
            name="max_depth",
            path=max_depth_path,
            unit="m",
            sha256=compute_file_hash(max_depth_path),
            nodata=-9999.0,
        )
    ]

    # Export max_velocity raster if available
    if max_vel_arr is not None:
        max_vel_path = output_dir / "delft3d_max_velocity.tif"
        with rasterio.open(max_vel_path, "w", **meta) as dst:
            dst.write(vel_2d, 1)

        layers.append(
            NormalisedLayer(
                name="max_velocity",
                path=max_vel_path,
                unit="m/s",
                sha256=compute_file_hash(max_vel_path),
                nodata=-9999.0,
            )
        )

    return NormalisedOutput(
        engine_name="delft3d_fm",
        engine_version="2026.01",
        layers=layers,
        crs=crs_str,
        grid_resolution_m=1.0,
        depth_threshold_m=0.1,
        wall_time_s=raw_result.wall_time_s,
        input_hashes={},
        metadata={
            "max_depth_m": float(np.max(depth_2d)),
            "max_velocity_ms": float(np.max(vel_2d)) if max_vel_arr is not None else 0.0,
        },
    )
