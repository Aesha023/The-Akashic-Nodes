"""Unit tests for Delft3D FM Tier-1 job pipeline and validity gating."""

from __future__ import annotations

import json
from pathlib import Path

from pravahx.engines.delft3d_fm.ganga_tier1 import stub_ganga_tier1_output
from pravahx.engines.delft3d_fm.job import (
    ARRIVAL_TIME_THRESHOLD_NOTE,
    EXPECTED_ENGINE_SHA256,
    run_delft3d_fm_tier1_job,
)


def test_delft3d_tier1_job_valid(tmp_path: Path) -> None:
    """Test unified Tier-1 job execution when validity gates pass."""
    data_dir = Path("data/ganga_inputs").resolve()
    dem_path = data_dir / "dem_ganga_32644.tif"
    tier0_env = data_dir / "tier0_envelope.shp"

    if not dem_path.exists() or not tier0_env.exists():
        return

    case_dir = tmp_path / "case_job_valid"
    out_dir = tmp_path / "case_job_valid_outputs"

    # Pre-generate valid case files and stub simulation outputs
    # Run job with stubbed output
    # First build and stub
    case_dir.mkdir(parents=True, exist_ok=True)
    stub_ganga_tier1_output(case_dir, spinup_s=5400.0)

    result = run_delft3d_fm_tier1_job(
        case_dir=case_dir,
        dem_path=dem_path,
        aoi_path=tier0_env,
        out_dir=out_dir,
        dx=50.0,
        spinup_s=5400.0,
        breach_duration_s=10800.0,
        engine_bin=None,
        allow_invalid=False,
    )

    # Re-apply stub output after case rebuild so gates pass
    stub_ganga_tier1_output(case_dir, spinup_s=5400.0)
    result = run_delft3d_fm_tier1_job(
        case_dir=case_dir,
        dem_path=dem_path,
        aoi_path=tier0_env,
        out_dir=out_dir,
        dx=50.0,
        spinup_s=5400.0,
        breach_duration_s=10800.0,
        engine_bin=None,
        allow_invalid=False,
    )

    assert result.status == "VALID"
    assert result.gate_results["all_passed"] is True
    assert result.output_layers is not None
    assert "max_depth_tif" in result.output_layers
    assert "max_velocity_tif" in result.output_layers
    assert "arrival_time_0_05_tif" in result.output_layers
    assert "arrival_time_0_30_tif" in result.output_layers
    assert "extent_shp" in result.output_layers
    assert "extent_kml" in result.output_layers

    # Check report JSON contents
    assert result.report_json_path.exists()
    report = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert report["status"] == "VALID"
    assert report["engine_sha256"] == EXPECTED_ENGINE_SHA256
    assert report["parameters"]["arrival_time_note"] == ARRIVAL_TIME_THRESHOLD_NOTE
    assert "mass_balance" in report


def test_delft3d_tier1_job_invalid_gate_withheld(tmp_path: Path) -> None:
    """Verify that if validity gates fail, run is marked INVALID and results withheld."""
    data_dir = Path("data/ganga_inputs").resolve()
    dem_path = data_dir / "dem_ganga_32644.tif"
    tier0_env = data_dir / "tier0_envelope.shp"

    if not dem_path.exists() or not tier0_env.exists():
        return

    case_dir = tmp_path / "case_job_invalid"
    out_dir = tmp_path / "case_job_invalid_outputs"

    # Job without engine binary and without simulation output -> gate failure
    result = run_delft3d_fm_tier1_job(
        case_dir=case_dir,
        dem_path=dem_path,
        aoi_path=tier0_env,
        out_dir=out_dir,
        dx=50.0,
        engine_bin=None,
        allow_invalid=True,
    )

    assert result.status == "INVALID"
    assert result.gate_results["all_passed"] is False
    # INVALID runs are never returned as valid result layers
    assert result.output_layers is None
    assert result.report_json_path.exists()
    report = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert report["status"] == "INVALID"
