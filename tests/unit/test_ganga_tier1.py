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
    plot_inflow_hydrograph,
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
    """Verify generated hydrograph has spin-up, breach peak, and total duration."""
    scenario = compute_hypothetical_breach_scenario()
    series = generate_hypothetical_inflow_series(
        scenario=scenario,
        spinup_s=5400.0,
        breach_duration_s=7200.0,
        dt_s=30.0,
    )
    assert len(series) > 100
    times = [p[0] for p in series]
    flows = [p[1] for p in series]
    assert times[0] == 0.0
    assert flows[0] == 100.0  # Base flow during spin-up
    # At t = 5400 s (spin-up end), flow is still base flow
    idx_spin = int(5400.0 / 30.0)
    assert flows[idx_spin] == 100.0
    assert max(flows) > 4950.0  # Peaks near 5000 m3/s
    assert times[-1] == 12600.0


def test_plot_inflow_hydrograph(tmp_path: Path) -> None:
    """Verify inflow hydrograph plot generation and export."""
    scenario = compute_hypothetical_breach_scenario()
    series = generate_hypothetical_inflow_series(
        scenario=scenario,
        spinup_s=5400.0,
        breach_duration_s=7200.0,
        dt_s=60.0,
    )
    plot_path = tmp_path / "inflow_hydrograph.png"
    fig = plot_inflow_hydrograph(series, spinup_s=5400.0, out_path=plot_path)
    assert fig is not None
    assert plot_path.exists()
    assert plot_path.stat().st_size > 10000


def test_manning_normal_depth() -> None:
    """Verify normal flow depth calculation from Manning's equation using DEM params."""
    d0 = compute_manning_normal_depth(0.0)
    assert d0 == 0.0

    d100 = compute_manning_normal_depth(100.0)
    d5000 = compute_manning_normal_depth(5000.0)
    assert 0.5 < d100 < 1.5
    assert 7.0 < d5000 < 11.0
    assert d5000 > d100


def test_build_ganga_tier1_case(tmp_path: Path) -> None:
    """Verify complete case build with real Ganga inputs for uniform and WorldCover variants."""
    data_dir = Path("data/ganga_inputs")
    dem_path = data_dir / "dem_ganga_32644.tif"
    tier0_env = data_dir / "tier0_envelope.shp"
    lc_path = data_dir / "worldcover_ganga_32644.tif"

    if not dem_path.exists() or not tier0_env.exists():
        return

    # 1. Primary uniform roughness case
    case_dir_uni = tmp_path / "case_uni"
    res_uni = build_ganga_tier1_case(
        case_dir=case_dir_uni,
        dem_path=dem_path,
        tier0_envelope_path=tier0_env,
        worldcover_path=lc_path,
        buffer_m=300.0,
        dx=50.0,
        uniform_mannings_n=0.035,
        tstop_s=7200.0,
    )

    mesh_info = res_uni["mesh_info"]
    assert 1000 < mesh_info["n_faces"] < 100000

    assert (case_dir_uni / "grid_net.nc").exists()
    assert (case_dir_uni / "flow2d3d.mdu").exists()
    assert (case_dir_uni / "boundary_conditions.ext").exists()
    assert (case_dir_uni / "inflow.bc").exists()
    assert (case_dir_uni / "downstream.bc").exists()
    assert (case_dir_uni / "outlet_obs.pli").exists()
    # Uniform case must not have initialFields.ini
    assert not (case_dir_uni / "initialFields.ini").exists()

    mdu_uni = (case_dir_uni / "flow2d3d.mdu").read_text(encoding="utf-8")
    assert "mapFormat" in mdu_uni and "4" in mdu_uni
    assert "crsFile               = outlet_obs.pli" in mdu_uni
    assert "unifFrictCoef         = 0.0350" in mdu_uni
    assert "TransportMethod" not in mdu_uni or "# OBSOLETE" in mdu_uni

    inflow_bc_txt = (case_dir_uni / "inflow.bc").read_text(encoding="utf-8")
    assert "inflow_bnd_0001" in inflow_bc_txt
    assert "dischargebnd" in inflow_bc_txt

    down_bc_txt = (case_dir_uni / "downstream.bc").read_text(encoding="utf-8")
    assert "downstream_bnd" in down_bc_txt
    assert "qhbnd discharge" in down_bc_txt
    assert "qhbnd waterlevel" in down_bc_txt

    # 2. Distributed WorldCover roughness variant
    case_dir_wc = tmp_path / "case_wc"
    build_ganga_tier1_case(
        case_dir=case_dir_wc,
        dem_path=dem_path,
        tier0_envelope_path=tier0_env,
        worldcover_path=lc_path,
        buffer_m=300.0,
        dx=50.0,
        uniform_mannings_n=None,
        tstop_s=7200.0,
    )
    assert (case_dir_wc / "initialFields.ini").exists()
    assert (case_dir_wc / "roughness.xyz").exists()
    ini_txt = (case_dir_wc / "initialFields.ini").read_text(encoding="utf-8")
    assert "frictioncoefficient" in ini_txt
    assert "triangulation" in ini_txt
    assert "[Initial]" not in ini_txt  # No invalid [Initial] block


def test_evaluate_validity_gates(tmp_path: Path) -> None:
    """Verify validity gates evaluation logic."""
    from pravahx.engines.delft3d_fm.ganga_tier1 import evaluate_validity_gates

    case_dir = tmp_path / "mock_gate_case"
    case_dir.mkdir(parents=True)

    # Mock clean run log
    log_file = case_dir / "run.log"
    log_file.write_text(
        "Boundary 'inflow_bnd' opened 8 cells\nDownstream opened 8 cells\n",
        encoding="utf-8",
    )

    gates = evaluate_validity_gates(case_dir, spinup_s=5400.0)
    assert gates["gate_a"] is True  # No 0 cells opened
    assert gates["gate_b"] is True  # No errors
    assert "PASS" in gates["gate_a_msg"]


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
