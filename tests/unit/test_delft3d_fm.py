"""Unit tests for Delft3D Flexible Mesh adapter (prepare, postprocess, blocked run)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
import rasterio
import xarray as xr

from pravahx.engines.base import EngineStatus, RawResult, RunContext
from pravahx.engines.delft3d_fm.adapter import Delft3DFMAdapter
from pravahx.errors import EngineError

if TYPE_CHECKING:
    from pathlib import Path


def _create_sample_delft3d_netcdf(nc_path: Path) -> None:
    """Create a synthetic Delft3D FM map output NetCDF dataset for testing."""
    times = np.array([0, 3600, 7200], dtype=np.int32)
    # 2D grid: 5x5 nodes
    ny, nx = 5, 5
    depth_data = np.zeros((3, ny, nx), dtype=np.float32)
    # Flood develops over time
    depth_data[1, 1:4, 1:4] = 2.5
    depth_data[2, 1:4, 1:4] = 4.2
    depth_data[2, 2, 2] = 6.8

    ucx_data = np.zeros((3, ny, nx), dtype=np.float32)
    ucy_data = np.zeros((3, ny, nx), dtype=np.float32)
    ucx_data[2, 1:4, 1:4] = 1.5
    ucy_data[2, 1:4, 1:4] = 0.8

    ds = xr.Dataset(
        data_vars={
            "mesh2d_waterdepth": (("time", "y", "x"), depth_data),
            "mesh2d_ucx": (("time", "y", "x"), ucx_data),
            "mesh2d_ucy": (("time", "y", "x"), ucy_data),
        },
        coords={
            "time": times,
            "y": np.arange(ny),
            "x": np.arange(nx),
        },
    )
    ds.to_netcdf(nc_path)


def test_delft3d_fm_prepare(tmp_path: Path) -> None:
    """Test that Delft3D FM adapter prepare() creates valid HYDROLIB-core files."""
    adapter = Delft3DFMAdapter()
    assert adapter.name == "delft3d_fm"

    ctx = RunContext(
        run_id="delft3d_test_01",
        config=None,  # type: ignore[arg-type]
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=None,
    )

    prepared = adapter.prepare(ctx)
    assert prepared.engine_name == "delft3d_fm"
    assert prepared.case_dir.exists()

    # Check generated files
    assert (prepared.case_dir / "flow2d3d.mdu").exists()
    assert (prepared.case_dir / "boundary_conditions.ext").exists()
    assert (prepared.case_dir / "hydrograph.bc").exists()
    assert (prepared.case_dir / "inflow_boundary.pli").exists()

    assert "flow2d3d.mdu" in prepared.input_file_hashes
    assert "hydrograph.bc" in prepared.input_file_hashes


def test_delft3d_fm_run_blocked(tmp_path: Path) -> None:
    """Test that Delft3D FM run() raises EngineError while container runner is blocked."""
    adapter = Delft3DFMAdapter()

    ctx = RunContext(
        run_id="delft3d_test_02",
        config=None,  # type: ignore[arg-type]
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=None,
    )
    prepared = adapter.prepare(ctx)

    with pytest.raises(EngineError, match="Delft3D FM solver execution is blocked"):
        adapter.run(prepared)


def test_delft3d_fm_postprocess(tmp_path: Path) -> None:
    """Test that Delft3D FM postprocess() parses NetCDF and outputs NormalisedOutput."""
    adapter = Delft3DFMAdapter()

    output_dir = tmp_path / "delft3d_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    nc_path = output_dir / "flow2d3d_map.nc"
    _create_sample_delft3d_netcdf(nc_path)

    ctx = RunContext(
        run_id="delft3d_test_03",
        config=None,  # type: ignore[arg-type]
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=None,
    )

    raw_result = RawResult(
        engine_name="delft3d_fm",
        status=EngineStatus.SUCCESS,
        output_dir=output_dir,
        log_path=output_dir / "delft3d.log",
        wall_time_s=12.5,
        exit_code=0,
    )

    norm_output = adapter.postprocess(raw_result, ctx)
    assert norm_output.engine_name == "delft3d_fm"
    assert len(norm_output.layers) >= 1

    # Check max depth layer
    depth_layer = next(lyr for lyr in norm_output.layers if lyr.name == "max_depth")
    assert depth_layer.path.exists()

    # Check that GeoTIFF is readable
    with rasterio.open(depth_layer.path) as src:
        arr = src.read(1)
        assert arr.shape == (5, 5)
        assert abs(float(np.max(arr)) - 6.8) < 1e-3

    # Check metadata
    assert norm_output.metadata["max_depth_m"] == pytest.approx(6.8, rel=1e-3)
