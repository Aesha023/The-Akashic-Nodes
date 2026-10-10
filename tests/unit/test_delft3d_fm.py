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


def test_delft3d_fm_mdu_writer(tmp_path: Path) -> None:
    """Test that Delft3D FM MDU writer sets the correct simulation time rules."""
    adapter = Delft3DFMAdapter()
    ctx = RunContext(
        run_id="delft3d_test_mdu",
        config=None,  # type: ignore[arg-type]
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=None,
    )
    prepared = adapter.prepare(ctx)
    mdu_path = prepared.case_dir / "flow2d3d.mdu"
    assert mdu_path.exists()

    # Read the text of the MDU to verify Hydrolib-core wrote it correctly
    mdu_text = mdu_path.read_text(encoding="utf-8")
    assert "RefDate" in mdu_text or "refdate" in mdu_text.lower()
    assert "20260101" in mdu_text
    assert "Tstart" in mdu_text or "tstart" in mdu_text.lower()
    assert "Tstop" in mdu_text or "tstop" in mdu_text.lower()
    assert "14400" in mdu_text

    # Verify MDU writer rules
    obsolete_keys = [
        "TransportMethod",
        "Qhrelax",
        "Jaorgsethu",
        "EffectSpiral",
        "Gapres",
        "WaveNikuradse",
        "Writebalancefile",
    ]
    lines = [line.strip() for line in mdu_text.splitlines() if line.strip()]
    for key in obsolete_keys:
        for line in lines:
            if line.lower().startswith(key.lower() + "=") or line.lower().startswith(
                key.lower() + " "
            ):
                raise AssertionError(f"Obsolete key {key} found active in MDU")

    mapformat_found = False
    mapinterval_found = False
    obsfile_empty = True
    for line in lines:
        if line.lower().startswith("mapformat"):
            assert "4" in line
            mapformat_found = True
        if line.lower().startswith("mapinterval"):
            # Should be > 0
            val_str = line.split("=")[1].split()[0].strip()
            val = float(val_str)
            assert val > 0
            mapinterval_found = True
        if line.lower().startswith("obsfile"):
            val = line.split("=", 1)[1].strip()
            if val:
                obsfile_empty = False

    assert mapformat_found
    assert mapinterval_found
    assert obsfile_empty


def test_delft3d_fm_mdu_writer_keeps_obsfile(tmp_path: Path) -> None:
    """Test that Delft3D FM MDU writer preserves ObsFile if the file actually exists."""
    adapter = Delft3DFMAdapter()
    ctx = RunContext(
        run_id="delft3d_test_mdu_obs",
        config=None,  # type: ignore[arg-type]
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=None,
    )

    # Create the case dir early and touch the dummy obsfile
    case_dir = tmp_path / "delft3d_fm"
    case_dir.mkdir(parents=True, exist_ok=True)
    obs_file = case_dir / "my_obs_file.obs"
    obs_file.touch()

    # We must patch the hydrolib mdu model saving to insert this obsfile
    # Wait, the easiest way is to mock builder.build_delft3d_case or let the real adapter run
    # and we modify the mdu file before the post-processing? Actually, the builder code creates
    # the mdu from scratch and does not set ObsFile. Wait!
    # Hydrolib-core by default writes `ObsFile =` (empty) or doesn't write it.
    # Let's just create a dummy mdu, pass it to the post-processing logic directly, or
    # inject it. Since builder.py rewrites the MDU from Hydrolib-core, and Hydrolib-core
    # doesn't write an ObsFile by default in our current setup (as verified),
    # let's just test the post-processing logic directly or patch the FMModel.

    # But wait, to make it simple, let's just write the mdu text and run the post-processing code
    # directly as it's written in builder.py. Or I can monkeypatch FMModel.save to write an ObsFile.
    import pravahx.engines.delft3d_fm.builder as builder

    original_save = builder.FMModel.save

    def mock_save(self, filepath, *args, **kwargs):
        # Let it save normally
        original_save(self, filepath, *args, **kwargs)
        # Then inject an ObsFile line
        text = filepath.read_text(encoding="utf-8")
        text += "\nObsFile = my_obs_file.obs\n"
        filepath.write_text(text, encoding="utf-8")

    builder.FMModel.save = mock_save
    try:
        prepared = adapter.prepare(ctx)
    finally:
        builder.FMModel.save = original_save

    mdu_path = prepared.case_dir / "flow2d3d.mdu"
    mdu_text = mdu_path.read_text(encoding="utf-8")

    obsfile_kept = False
    for line in mdu_text.splitlines():
        if line.lower().startswith("obsfile"):
            val = line.split("=", 1)[1].strip()
            if val == "my_obs_file.obs":
                obsfile_kept = True
    assert obsfile_kept


def test_delft3d_fm_run_missing_binary(tmp_path: Path) -> None:
    """Test that Delft3D FM run() raises EngineError when CPU binary is missing."""
    adapter = Delft3DFMAdapter()

    ctx = RunContext(
        run_id="delft3d_test_02",
        config=None,  # type: ignore[arg-type]
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=None,
    )
    prepared = adapter.prepare(ctx)
    prepared.metadata["mode"] = "cpu"

    with pytest.raises(EngineError, match="Delft3D FM CPU binary not found"):
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
