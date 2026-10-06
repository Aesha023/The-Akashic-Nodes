"""DualSPHysics output reader and raster/hydrograph extractor (Phase 3)."""

from __future__ import annotations

import csv
import logging
import math
from typing import Any

import numpy as np
import rasterio
from rasterio.transform import from_bounds

from pravahx.engines.base import (
    NormalisedLayer,
    NormalisedOutput,
    RawResult,
    RunContext,
    compute_file_hash,
)
from pravahx.errors import EngineError

logger = logging.getLogger(__name__)


def read_dualsphysics_output(raw: RawResult, context: RunContext) -> NormalisedOutput:
    """Post-process DualSPHysics outputs into NormalisedOutput rasters and downstream hydrograph.

    Args:
        raw: RawResult from DualSPHysicsRunner.
        context: RunContext containing scenario config, grid bounds, and paths.

    Returns:
        NormalisedOutput containing 5 GeoTIFF layers, hydrograph metadata, and hashes.
    """
    output_dir = raw.output_dir
    if not output_dir.exists():
        raise EngineError(
            f"DualSPHysics output directory does not exist: {output_dir}",
            engine="dualsphysics",
        )

    # 1. Locate particle CSV files
    csv_files = sorted(output_dir.glob("PartFluid_*.csv"))
    if not csv_files:
        # Check in 'data' subfolder
        csv_files = sorted((output_dir / "data").glob("PartFluid_*.csv"))

    if not csv_files:
        raise EngineError(
            f"No PartFluid_*.csv particle output files found in {output_dir}",
            engine="dualsphysics",
        )

    logger.info("Parsing %d DualSPHysics particle output files...", len(csv_files))

    # Grid definition from context or default UTM bounds
    grid_res_m = 10.0
    depth_thresh_m = 0.1

    # Find bounding box across all particles
    all_x: list[float] = []
    all_y: list[float] = []
    all_z: list[float] = []

    # Read first file to get initial spatial extent
    with open(csv_files[0], encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_x.append(float(row["x"]))
            all_y.append(float(row["y"]))
            all_z.append(float(row["z"]))

    x_min = min(all_x) if all_x else 0.0
    x_max = max(all_x) + 50.0 if all_x else 100.0
    y_min = min(all_y) if all_y else 0.0
    y_max = max(all_y) if all_y else 20.0

    # Expand bounds slightly
    nx = max(5, int(np.ceil((x_max - x_min) / grid_res_m)))
    ny = max(5, int(np.ceil((y_max - y_min) / grid_res_m)))

    max_depth = np.zeros((ny, nx), dtype=np.float32)
    max_velocity = np.zeros((ny, nx), dtype=np.float32)
    arrival_time = np.full((ny, nx), fill_value=np.nan, dtype=np.float32)
    time_to_peak = np.zeros((ny, nx), dtype=np.float32)

    # Read time series and track maximums
    for step_idx, cp in enumerate(csv_files):
        time_min = step_idx * 0.5 / 60.0  # Convert seconds to minutes

        with open(cp, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                px = float(row["x"])
                py = float(row["y"])
                pz = float(row["z"])
                vx = float(row.get("vx", 0.0))
                vy = float(row.get("vy", 0.0))
                vz = float(row.get("vz", 0.0))
                vel = math.sqrt(vx**2 + vy**2 + vz**2)

                ix = int((px - x_min) / grid_res_m)
                iy = int((py - y_min) / grid_res_m)

                if 0 <= ix < nx and 0 <= iy < ny:
                    if pz > max_depth[iy, ix]:
                        max_depth[iy, ix] = pz
                        time_to_peak[iy, ix] = time_min

                    if vel > max_velocity[iy, ix]:
                        max_velocity[iy, ix] = vel

                    if pz >= depth_thresh_m and np.isnan(arrival_time[iy, ix]):
                        arrival_time[iy, ix] = time_min

    # Replace nan arrival times with 0.0
    arrival_time = np.nan_to_num(arrival_time, nan=0.0)

    # Compute binary extent raster
    extent = (max_depth >= depth_thresh_m).astype(np.float32)

    # 2. Extract downstream outflow hydrograph from MeasureTool
    hydrograph_points: list[dict[str, float]] = []
    measure_csv = output_dir / "MeasureTool_Gauges.csv"
    if not measure_csv.exists():
        measure_csv = output_dir / "data" / "MeasureTool_Gauges.csv"

    if measure_csv.exists():
        with open(measure_csv, encoding="utf-8") as f:
            m_reader = csv.DictReader(f)
            for row in m_reader:
                hydrograph_points.append(
                    {
                        "time_s": float(row["time_s"]),
                        "discharge_m3s": float(row.get("discharge_m3s", 0.0)),
                        "water_level_m": float(row.get("water_level_m", 0.0)),
                        "velocity_m_s": float(row.get("velocity_m_s", 0.0)),
                    }
                )

    # 3. Export 5 standard GeoTIFF layers
    raster_dir = context.work_dir / "dualsphysics_rasters"
    raster_dir.mkdir(parents=True, exist_ok=True)

    crs_str = "EPSG:32644"  # Default local UTM zone
    transform = from_bounds(x_min, y_min, x_max, y_max, nx, ny)

    layers_data: dict[str, tuple[np.ndarray, str, float | None]] = {
        "max_depth": (max_depth, "m", -9999.0),
        "max_velocity": (max_velocity, "m/s", -9999.0),
        "arrival_time": (arrival_time, "minutes", -9999.0),
        "time_to_peak": (time_to_peak, "minutes", -9999.0),
        "extent": (extent, "0/1", 0.0),
    }

    norm_layers: list[NormalisedLayer] = []
    out_hashes: dict[str, str] = {}

    for name, (arr, unit, nodata_val) in layers_data.items():
        tif_path = raster_dir / f"{name}.tif"
        with rasterio.open(
            tif_path,
            "w",
            driver="GTiff",
            height=ny,
            width=nx,
            count=1,
            dtype=rasterio.float32,
            crs=crs_str,
            transform=transform,
            nodata=nodata_val,
        ) as dst:
            dst.write(arr, 1)

        h_val = compute_file_hash(tif_path)
        out_hashes[f"{name}.tif"] = h_val
        norm_layers.append(
            NormalisedLayer(
                name=name,
                path=tif_path,
                unit=unit,
                sha256=h_val,
                nodata=nodata_val,
            )
        )

    # 4. Save downstream hydrograph CSV
    hydrograph_out = raster_dir / "dualsphysics_outflow_hydrograph.csv"
    with open(hydrograph_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "discharge_m3s", "water_level_m", "velocity_m_s"])
        for hp in hydrograph_points:
            writer.writerow(
                [hp["time_s"], hp["discharge_m3s"], hp["water_level_m"], hp["velocity_m_s"]]
            )

    metadata: dict[str, Any] = {
        "total_particle_dumps": len(csv_files),
        "grid_resolution_m": grid_res_m,
        "grid_shape": [ny, nx],
        "hydrograph_path": str(hydrograph_out),
        "peak_discharge_m3s": max((hp["discharge_m3s"] for hp in hydrograph_points), default=0.0),
        "is_imported": raw.status == "success",
    }

    return NormalisedOutput(
        engine_name="dualsphysics",
        engine_version="5.0/5.2",
        layers=norm_layers,
        crs=crs_str,
        grid_resolution_m=grid_res_m,
        depth_threshold_m=depth_thresh_m,
        wall_time_s=raw.wall_time_s,
        input_hashes=out_hashes,
        metadata=metadata,
        is_precomputed=(raw.status == "success"),
    )
