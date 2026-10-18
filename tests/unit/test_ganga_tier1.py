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
    assert (case_dir_uni / "cross_sections.pli").exists()
    assert (case_dir_uni / "outlet_obs.pli").exists()
    # Uniform case must not have initialFields.ini
    assert not (case_dir_uni / "initialFields.ini").exists()

    mdu_uni = (case_dir_uni / "flow2d3d.mdu").read_text(encoding="utf-8")
    assert "mapFormat" in mdu_uni and "4" in mdu_uni
    assert "crsFile               = cross_sections.pli" in mdu_uni
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


def test_stub_and_postprocess_ganga_tier1(tmp_path: Path) -> None:
    """Verify stub output generation and post-processing into GeoTIFF, SHP, and KML."""
    from pravahx.engines.delft3d_fm.ganga_tier1 import (
        evaluate_validity_gates,
        postprocess_ganga_tier1_run,
        stub_ganga_tier1_output,
    )

    data_dir = Path("data/ganga_inputs")
    dem_path = data_dir / "dem_ganga_32644.tif"
    tier0_env = data_dir / "tier0_envelope.shp"
    if not dem_path.exists() or not tier0_env.exists():
        return

    case_dir = tmp_path / "stub_case"
    build_ganga_tier1_case(
        case_dir=case_dir,
        dem_path=dem_path,
        tier0_envelope_path=tier0_env,
        buffer_m=300.0,
        dx=50.0,
        spinup_s=5400.0,
        breach_duration_s=10800.0,
    )

    stub_ganga_tier1_output(case_dir, spinup_s=5400.0, simulate_pass=True)

    gates = evaluate_validity_gates(case_dir, spinup_s=5400.0)
    assert gates["all_passed"] is True
    assert gates["gate_a"] is True
    assert gates["gate_b"] is True
    assert gates["gate_c"] is True
    assert gates["gate_d"] is True
    assert gates["gate_e"] is True
    assert gates["gate_f"] is True
    assert "dead_storage_m3" in gates
    assert (case_dir / "DFM_OUTPUT_flow2d3d" / "flow2d3d_rst.nc").exists()

    out_dir = tmp_path / "stub_outputs"
    post = postprocess_ganga_tier1_run(
        case_dir=case_dir,
        dem_path=dem_path,
        out_dir=out_dir,
        spinup_s=5400.0,
    )

    assert post["max_depth_tif"].exists()
    assert post["max_velocity_tif"].exists()
    assert post["arrival_time_0_05_tif"].exists()
    assert post["arrival_time_0_30_tif"].exists()
    assert post["extent_shp"].exists()
    assert post["extent_kml"].exists()


def test_two_runs_warmup_and_restart_breach(tmp_path: Path) -> None:
    """Verify that two-run sequence evaluates gates d/e/f from isolated time windows."""
    from pravahx.engines.delft3d_fm.ganga_tier1 import (
        build_ganga_tier1_case,
        evaluate_validity_gates,
        postprocess_ganga_tier1_run,
        stub_ganga_tier1_output,
    )

    data_dir = Path("data/ganga_inputs")
    dem_path = data_dir / "dem_ganga_32644.tif"
    tier0_env = data_dir / "tier0_envelope.shp"
    if not dem_path.exists() or not tier0_env.exists():
        return

    case_base = tmp_path / "two_runs_case"
    wu_dir = case_base / "01_warmup"
    br_dir = case_base / "02_breach"

    # 1. Build Warm-up Pre-run (Run 1): 10,800 s base-flow spin-up, writes restart
    build_ganga_tier1_case(
        case_dir=wu_dir,
        dem_path=dem_path,
        tier0_envelope_path=tier0_env,
        buffer_m=300.0,
        dx=50.0,
        spinup_s=10800.0,
        breach_duration_s=0.0,
        tstop_s=10800.0,
        dtuser_s=10.0,
        rst_interval_s=600.0,
        is_warmup_only=True,
    )

    # 2. Stub Warm-up Pre-run: base flow 100 m3/s reaches 95 m3/s at outlet at t=9600s
    stub_ganga_tier1_output(wu_dir, is_warmup_only=True, spinup_s=10800.0, simulate_pass=True)
    rst_file = wu_dir / "flow2d3d_rst.nc"
    assert rst_file.exists(), "Warm-up must generate flow2d3d_rst.nc restart file"

    # 3. Build Breach Run from Restart (Run 2): 14,400 s breach run, starts from restart
    build_ganga_tier1_case(
        case_dir=br_dir,
        dem_path=dem_path,
        tier0_envelope_path=tier0_env,
        buffer_m=300.0,
        dx=50.0,
        spinup_s=0.0,
        breach_duration_s=14400.0,
        tstop_s=14400.0,
        dtuser_s=10.0,
        is_warmup_only=False,
        restart_file=rst_file,
    )
    assert (br_dir / "flow2d3d_rst.nc").exists(), "Restart file must be copied to breach directory"

    # 4. Stub Breach Run from Restart: starts from wet restart state, flood peaks, drains 75%
    stub_ganga_tier1_output(br_dir, restart_file=rst_file, spinup_s=0.0, simulate_pass=True)

    # 5. Evaluate validity gates across both runs
    gates = evaluate_validity_gates(br_dir, warmup_case_dir=wu_dir)
    assert gates["all_passed"] is True, f"Gates failed: {gates}"

    # Confirm Gate d is evaluated strictly from warm-up time window (0 <= t <= 10800 s)
    assert gates["gate_d"] is True
    assert gates["warmup_time_s"] == 9420.0, f"Expected T_eq = 9420 s, got {gates['warmup_time_s']}"
    assert "9420 s" in gates["gate_d_msg"]

    # Confirm Gate e is evaluated strictly over the breach time window (0 <= t <= 14400 s)
    assert gates["gate_e"] is True
    assert gates["breach_drainage_pct"] >= 70.0, (
        f"Breach drainage {gates['breach_drainage_pct']}% < 70%"
    )
    assert gates["drainage_time_s"] > 0.0

    # Confirm Gate f evaluates mass balance on breach run accounting for restart storage at t=0
    assert gates["gate_f"] is True
    assert gates["balance_error_pct"] < 1.0, (
        f"Mass balance error {gates['balance_error_pct']}% >= 1.0%"
    )
    assert gates["dead_storage_m3"] >= 0.0

    # Confirm Gate c evaluates inflow on the breach run
    assert gates["gate_c"] is True
    assert gates["inflow_diff_pct"] <= 2.0

    # Confirm parent directory auto-detection finds 01_warmup and 02_breach
    gates_auto = evaluate_validity_gates(case_base)
    assert gates_auto["all_passed"] is True
    assert gates_auto["warmup_time_s"] == 9420.0

    # --- NEGATIVE TEST 1: Window Contamination Isolation for Gate d ---
    # If warm-up outlet flow never reached 90 m3/s, Gate d MUST FAIL even though
    # the breach run in 02_breach has Q_peak > 1000 m3/s!
    fake_wu = tmp_path / "fake_wu_failed"
    fake_wu.mkdir(parents=True)
    fake_wu_out = fake_wu / "DFM_OUTPUT_flow2d3d"
    fake_wu_out.mkdir()
    # Write a his.nc where outlet flow stays at 30 m3/s forever (failed warm-up)
    import netCDF4

    hds = netCDF4.Dataset(fake_wu_out / "flow2d3d_his.nc", "w")
    hds.createDimension("time", None)
    hds.createDimension("cross_section", 2)
    hds.createDimension("cross_section_name_len", 16)
    t_v = hds.createVariable("time", "f8", ("time",))
    q_v = hds.createVariable("cross_section_discharge", "f8", ("time", "cross_section"))
    n_v = hds.createVariable(
        "cross_section_name", "S1", ("cross_section", "cross_section_name_len")
    )
    n_v[:] = np.array(
        [[c.encode("ascii") for c in nm.ljust(16)[:16]] for nm in ["inflow_obs", "outlet_obs"]],
        dtype="S1",
    )
    t_v[:] = [0.0, 3600.0, 7200.0, 10800.0]
    q_v[:] = np.column_stack([[100.0, 100.0, 100.0, 100.0], [0.0, 10.0, 25.0, 30.0]])
    hds.close()

    gates_failed_wu = evaluate_validity_gates(br_dir, warmup_case_dir=fake_wu)
    assert gates_failed_wu["gate_d"] is False, "Gate d must FAIL if warm-up did not reach steady!"
    assert gates_failed_wu["all_passed"] is False
    assert "FAIL" in gates_failed_wu["gate_d_msg"]

    # --- NEGATIVE TEST 2: Gate e Failure when Breach Wave Does Not Drain ---
    fake_br = tmp_path / "fake_br_undrained"
    fake_br.mkdir(parents=True)
    fake_br_out = fake_br / "DFM_OUTPUT_flow2d3d"
    fake_br_out.mkdir()
    (fake_br / "inflow.bc").write_text("0.0 5000.0\n14400.0 100.0\n", encoding="utf-8")
    (fake_br / "run.log").write_text("Boundary inflow_bnd opened 8 cells\n", encoding="utf-8")
    hds2 = netCDF4.Dataset(fake_br_out / "flow2d3d_his.nc", "w")
    hds2.createDimension("time", None)
    hds2.createDimension("cross_section", 2)
    hds2.createDimension("cross_section_name_len", 16)
    t_v2 = hds2.createVariable("time", "f8", ("time",))
    q_v2 = hds2.createVariable("cross_section_discharge", "f8", ("time", "cross_section"))
    n_v2 = hds2.createVariable(
        "cross_section_name", "S1", ("cross_section", "cross_section_name_len")
    )
    n_v2[:] = np.array(
        [[c.encode("ascii") for c in nm.ljust(16)[:16]] for nm in ["inflow_obs", "outlet_obs"]],
        dtype="S1",
    )
    t_v2[:] = [0.0, 7200.0, 14400.0]
    # Outlet flow stayed at base flow 100 m3/s, 0% breach volume exited
    q_v2[:] = np.column_stack([[5000.0, 2000.0, 100.0], [100.0, 100.0, 100.0]])
    hds2.close()

    gates_failed_drain = evaluate_validity_gates(fake_br, warmup_case_dir=wu_dir)
    assert gates_failed_drain["gate_e"] is False, "Gate e must FAIL if breach volume did not drain!"
    assert "FAIL" in gates_failed_drain["gate_e_msg"]

    # Verify postprocessing on two-run case_base
    out_dir = tmp_path / "two_runs_post_out"
    post = postprocess_ganga_tier1_run(
        case_dir=case_base,
        dem_path=dem_path,
        out_dir=out_dir,
        spinup_s=0.0,
    )
    assert post["max_depth_tif"].exists()
    assert post["arrival_time_0_05_tif"].exists()
    assert post["gates"]["all_passed"] is True


def test_engine_water_balance_gates_real_colab_record(tmp_path: Path) -> None:
    """Verify evaluate_validity_gates reproduces real Colab Delft3D FM water balance verbatim.

    Warm-up run:
      in 1,080,000 | out 0 | storage +1,080,000 | residual 0 m3 | engine volume_error 0.0
      -> gate d FAIL (outflow 0% of 100 m3/s after 3 h).
    Breach run:
      in 7,241,809 | out 4,166,187 | storage +3,075,622 | residual 0 m3 | engine volume_error 0.0
      -> gate f PASS. Breach excess out 2,726,187 of 5,801,809 m3 = 47.0%, outflow at end 211.5 m3/s
      -> gate e FAIL.
    """
    from pravahx.engines.delft3d_fm.ganga_tier1 import (
        evaluate_validity_gates,
        stub_ganga_tier1_output,
    )

    case_base = tmp_path / "real_colab_record"
    wu_dir = case_base / "01_warmup"
    br_dir = case_base / "02_breach"
    wu_dir.mkdir(parents=True)
    br_dir.mkdir(parents=True)

    # Stub with default simulate_pass=False generates verbatim real Colab water balance
    stub_ganga_tier1_output(wu_dir, is_warmup_only=True, spinup_s=10800.0, simulate_pass=False)
    rst_file = wu_dir / "flow2d3d_rst.nc"
    stub_ganga_tier1_output(br_dir, restart_file=rst_file, spinup_s=0.0, simulate_pass=False)

    gates = evaluate_validity_gates(br_dir, warmup_case_dir=wu_dir)

    # Gate f: Mass balance PASS (exact to 0 m3)
    assert gates["gate_f"] is True
    assert gates["engine_volume_error"] == 0.0
    assert gates["balance_error_m3"] == 0.0
    assert gates["balance_error_pct"] == 0.0
    assert "Delft3D engine water balance exact" in gates["gate_f_msg"]

    # Gate d: Warm-up FAIL (0% outflow after 3 h)
    assert gates["gate_d"] is False
    assert "outflow 0% of 100 m3/s after 3 h" in gates["gate_d_msg"]

    # Gate e: Drainage FAIL (47.0% < 70%, end Q 211.5 >= 200 m3/s)
    assert gates["gate_e"] is False
    assert gates["breach_drainage_pct"] == 47.0
    assert "47.0%" in gates["gate_e_msg"]
    assert "211.5 m3/s" in gates["gate_e_msg"]

    # Gate c: Inflow PASS
    assert gates["gate_c"] is True

    # Gate a and b: PASS
    assert gates["gate_a"] is True
    assert gates["gate_b"] is True

    # Overall: halted
    assert gates["all_passed"] is False

    # Stored depression / dead volume
    assert gates["storage_change_m3"] == 3075622.0
    assert gates["dead_storage_m3"] == 3075622.0
    assert abs(gates["dead_storage_mcm"] - 3.075622) < 1e-5
