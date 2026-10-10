"""Unit tests for Tier-1 Delft3D FM Ganga real-terrain case builder and intercomparison."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

from pravahx.engines.delft3d_fm.ganga_tier1 import (
    build_ganga_tier1_case,
    compare_tier0_and_tier1,
    compute_hypothetical_breach_scenario,
    compute_manning_normal_depth,
    generate_hypothetical_inflow_series,
)


def test_hypothetical_breach_scenario() -> None:
    """Verify hypothetical breach parameters and peak discharge match Froehlich (2008)."""
    scenario = compute_hypothetical_breach_scenario()
    assert 58.0 < scenario.average_breach_width_m < 59.0
    assert 1850.0 < scenario.formation_time_s < 1890.0
    assert scenario.failure_mode == "overtopping"
    assert scenario.side_slope_z == 1.0
    assert scenario.base_flow_m3s == 100.0
    # Peak total discharge must match Tier-0 accepted 5000 m3/s within 1%
    assert abs(scenario.total_peak_discharge_m3s - 5000.0) < 50.0


def test_inflow_series_generation() -> None:
    """Verify generated hydrograph has proper start, peak, and duration."""
    scenario = compute_hypothetical_breach_scenario()
    series = generate_hypothetical_inflow_series(
        scenario=scenario,
        total_duration_s=7200.0,
        dt_s=30.0,
    )
    assert len(series) > 100
    times = [p[0] for p in series]
    flows = [p[1] for p in series]
    assert times[0] == 0.0
    assert flows[0] == 100.0  # Base flow
    assert max(flows) > 4950.0  # Peaks near 5000 m3/s
    assert times[-1] == 7200.0


def test_manning_normal_depth() -> None:
    """Verify normal flow depth calculation from Manning's equation."""
    d0 = compute_manning_normal_depth(0.0)
    assert d0 == 0.0

    d100 = compute_manning_normal_depth(100.0)
    d5000 = compute_manning_normal_depth(5000.0)
    assert 0.3 < d100 < 1.0
    assert 4.0 < d5000 < 7.0
    assert d5000 > d100


def test_build_ganga_tier1_case(tmp_path: Path) -> None:
    """Verify complete case build with real Ganga inputs."""
    data_dir = Path("data/ganga_inputs")
    dem_path = data_dir / "dem_ganga_32644.tif"
    tier0_env = data_dir / "tier0_envelope.shp"
    lc_path = data_dir / "worldcover_ganga_32644.tif"

    if not dem_path.exists() or not tier0_env.exists():
        return

    case_dir = tmp_path / "case"
    res = build_ganga_tier1_case(
        case_dir=case_dir,
        dem_path=dem_path,
        tier0_envelope_path=tier0_env,
        worldcover_path=lc_path,
        buffer_m=300.0,
        dx=50.0,
        tstop_s=7200.0,
    )

    mesh_info = res["mesh_info"]
    # Free Colab CPU constraint: cell count must be well under 100k
    assert mesh_info["n_faces"] < 100000
    assert mesh_info["n_faces"] > 1000  # Reasonable resolution on ~7.5 km reach

    # Verify key files created
    assert (case_dir / "grid_net.nc").exists()
    assert (case_dir / "flow2d3d.mdu").exists()
    assert (case_dir / "boundary_conditions.ext").exists()
    assert (case_dir / "inflow.bc").exists()
    assert (case_dir / "downstream.bc").exists()
    assert (case_dir / "initialFields.ini").exists()
    assert (case_dir / "roughness.xyz").exists()

    # Verify MDU contents
    mdu_text = (case_dir / "flow2d3d.mdu").read_text(encoding="utf-8")
    assert "mapFormat" in mdu_text and "4" in mdu_text
    assert "iniFieldFile" in mdu_text and "initialFields.ini" in mdu_text
    assert "obsFile" in mdu_text
    assert "TransportMethod" not in mdu_text or "# OBSOLETE" in mdu_text
    assert "wrishp_enc" not in mdu_text or "# OBSOLETE" in mdu_text


def test_compare_tier0_and_tier1(tmp_path: Path) -> None:
    """Verify Model Intercomparison metrics computation and raster generation."""
    t0_path = Path("data/ganga_inputs/tier0_max_depth.tif")
    if not t0_path.exists():
        return

    # Create mock tier1 depth raster
    t1_path = tmp_path / "mock_tier1_depth.tif"
    with rasterio.open(t0_path) as src:
        d0 = src.read(1)
        meta = src.meta.copy()

    d1 = np.where(d0 > 0.05, d0 + 0.25, -9999.0).astype(np.float32)
    with rasterio.open(t1_path, "w", **meta) as dst:
        dst.write(d1, 1)

    out_dir = tmp_path / "comp_out"
    res = compare_tier0_and_tier1(
        tier0_depth_path=t0_path,
        tier1_depth_path=t1_path,
        out_dir=out_dir,
        depth_threshold_m=0.05,
    )

    assert res["area_tier0_km2"] > 0.0
    assert res["area_tier1_km2"] > 0.0
    assert res["iou"] == 1.0
    assert res["f_score"] == 1.0
    assert abs(res["diff_stats"]["mean_diff_m"] - 0.25) < 0.01
    assert (out_dir / "intercomparison_agreement_map.tif").exists()
    assert (out_dir / "intercomparison_metrics.csv").exists()
