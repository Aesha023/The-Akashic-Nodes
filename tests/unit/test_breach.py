"""Unit tests for breach parameter calculations and hydrograph routing."""

from pravahx.breach.froehlich import compute_froehlich_2008
from pravahx.breach.hydrograph import route_hydrograph


def test_froehlich_2008() -> None:
    """Verify Froehlich 2008 produces sane values."""
    vol = 1_000_000.0  # 1 MCM
    h = 20.0
    params = compute_froehlich_2008(volume_m3=vol, height_m=h, mode="overtopping")

    assert params.average_width_m > 0
    assert params.formation_time_hr > 0
    assert params.peak_discharge_m3s > 0
    assert params.side_slope_z == 1.0

    # For these inputs:
    # b_avg = 0.27 * 1.3 * (1e6^0.32) * (20^0.04)
    # tf = 63.2 * sqrt(1e6 / (9.81 * 400)) / 3600
    expected_b = 0.27 * 1.3 * (vol**0.32) * (h**0.04)
    expected_tf = 63.2 * ((vol / (9.81 * h**2)) ** 0.5) / 3600.0
    expected_qp = 0.607 * (vol**0.295) * (h**1.24)

    assert abs(params.average_width_m - expected_b) < 1e-4
    assert abs(params.formation_time_hr - expected_tf) < 1e-4
    assert abs(params.peak_discharge_m3s - expected_qp) < 1.0


def test_froehlich_2008_hec_ras_regression() -> None:
    """HEC-RAS regression test for Froehlich 2008.

    Inputs: V_w = 357.98e6 m3, h_b = 42.9 m, overtopping
    Outputs: B_avg = 222.76 m, t_f = 2.47 h, bottom width = 179.9 m
    """
    vol = 357.98e6
    h = 42.9
    params = compute_froehlich_2008(volume_m3=vol, height_m=h, mode="overtopping")

    assert abs(params.average_width_m - 222.76) < 0.1
    assert abs(params.formation_time_hr - 2.47) < 0.1
    assert abs(params.bottom_width_m - 179.9) < 0.1
    assert params.side_slope_z == 1.0


def test_hydrograph_integration() -> None:
    """Verify the routed hydrograph integrates to the initial volume."""
    vol = 1_000_000.0
    h = 20.0
    params = compute_froehlich_2008(vol, h)

    dt = 0.01
    hydrograph = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=params.average_width_m,
        t_f_hr=params.formation_time_hr,
        reservoir_exponent=3.0,
        side_slope_z=params.side_slope_z,
        dt_hr=dt,
        c_v1=1.70,
        c_v2=1.35,
    )

    assert len(hydrograph) > 0

    # Integrate discharge over time
    total_volume_released = 0.0
    dt_s = dt * 3600.0
    for i in range(len(hydrograph) - 1):
        pt = hydrograph[i]
        next_pt = hydrograph[i + 1]

        # Trapezoidal integration for volume
        q_avg = (pt["discharge_m3s"] + next_pt["discharge_m3s"]) / 2.0
        total_volume_released += q_avg * dt_s

    # Check that released volume matches the initial volume within 1%
    error = abs(total_volume_released - vol) / vol
    assert error < 0.01, f"Hydrograph volume integration error: {error * 100:.2f}%"

    # Also verify that volume_remaining reaches approximately zero
    assert hydrograph[-1]["volume_remaining_m3"] < 0.01 * vol


def test_synthetic_hydrograph_routing_progression_modes() -> None:
    """Verify routing mechanics under both progression modes on synthetic reservoir."""
    vol = 357.98e6
    h = 42.9
    params = compute_froehlich_2008(vol, h, mode="overtopping")

    # 1. Horizontal only progression mode (instantaneous invert drop)
    hg_horiz = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=params.average_width_m,
        t_f_hr=params.formation_time_hr,
        reservoir_exponent=3.0,
        side_slope_z=params.side_slope_z,
        progression_mode="horizontal_only",
        dt_hr=0.01,
    )
    assert 45_000.0 < hg_horiz.peak_discharge_m3s < 50_000.0
    assert 1.6 < hg_horiz.time_to_peak_hr < 1.9

    # 2. Linear vertical + horizontal progression mode
    hg_vert = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=params.average_width_m,
        t_f_hr=params.formation_time_hr,
        reservoir_exponent=3.0,
        side_slope_z=params.side_slope_z,
        progression_mode="vertical_and_horizontal",
        dt_hr=0.01,
    )
    assert 60_000.0 < hg_vert.peak_discharge_m3s < 70_000.0
    assert abs(hg_vert.time_to_peak_hr - params.formation_time_hr) < 0.05

    # Froehlich 1995 empirical peak
    qp_f95 = 0.607 * (vol**0.295) * (h**1.24)
    assert abs(qp_f95 - 21_420.2) < 1.0

    # Warning flag is set because ratio > 2.0
    assert hg_vert.warning_flag is not None
    assert "deviates from Froehlich (1995)" in hg_vert.warning_flag


def test_teton_dam_historical_benchmark() -> None:
    """Benchmark routing against Teton Dam (1976) published historical failure.

    Verified Sources:
    - USBR / RCEM / ASDSO Case Study: V_w = 251,700 acre-ft (310.47 MCM),
      h_w = 270 ft (82.3 m), mode = piping.
    - USGS OFR 77-765 (Ray et al., 1978): Slope-area post-failure peak
      estimate 65,129 m3/s (2.3M cfs).
    - Literature observed geometry [UNVERIFIED]: B_avg = 151 m, t_f = 1.25 hr, z = 0.5.
    """
    vol = 310_467_378.0  # 251,700 acre-feet in m^3
    h = 82.296  # 270 ft in m
    q_obs_post_failure = 65_129.0

    # 1. Froehlich 2008 predicted parameters
    params_pred = compute_froehlich_2008(volume_m3=vol, height_m=h, mode="piping")
    assert 150.0 < params_pred.average_width_m < 180.0
    assert 1.0 < params_pred.formation_time_hr < 1.4

    # 2. Routing with Observed Parameters (B_avg=151m, tf=1.25h, z=0.5, m=2.0)
    hg_obs_horiz = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=151.0,
        t_f_hr=1.25,
        reservoir_exponent=2.0,
        side_slope_z=0.5,
        progression_mode="horizontal_only",
        dt_hr=0.005,
    )
    hg_obs_vert = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=151.0,
        t_f_hr=1.25,
        reservoir_exponent=2.0,
        side_slope_z=0.5,
        progression_mode="vertical_and_horizontal",
        dt_hr=0.005,
    )

    # 3. Routing with Predicted Parameters (Froehlich 2008)
    hg_pred_horiz = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=params_pred.average_width_m,
        t_f_hr=params_pred.formation_time_hr,
        reservoir_exponent=2.0,
        side_slope_z=params_pred.side_slope_z,
        progression_mode="horizontal_only",
        dt_hr=0.005,
    )
    hg_pred_vert = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=params_pred.average_width_m,
        t_f_hr=params_pred.formation_time_hr,
        reservoir_exponent=2.0,
        side_slope_z=params_pred.side_slope_z,
        progression_mode="vertical_and_horizontal",
        dt_hr=0.005,
    )

    # Verify all 4 hydrographs execute and report sane peak discharges
    assert 65_000.0 < hg_obs_horiz.peak_discharge_m3s < 80_000.0
    assert 90_000.0 < hg_obs_vert.peak_discharge_m3s < 110_000.0
    assert 65_000.0 < hg_pred_horiz.peak_discharge_m3s < 85_000.0
    assert 95_000.0 < hg_pred_vert.peak_discharge_m3s < 115_000.0

    # Under horizontal_only mode with observed geometry, routed peak is ~72,040 m3/s (2.54M cfs),
    # within 11% of the post-failure slope-area survey estimate (65,129 m3/s)
    err_horiz = abs(hg_obs_horiz.peak_discharge_m3s - q_obs_post_failure) / q_obs_post_failure
    assert err_horiz < 0.12, f"Horizontal mode error: {err_horiz * 100:.2f}%"


def test_hydrograph_requires_reservoir_exponent() -> None:
    """Verify that reservoir_exponent is a required parameter with no default."""
    import pytest

    with pytest.raises(TypeError):
        route_hydrograph(  # type: ignore[call-arg]
            initial_volume_m3=1e6,
            dam_height_m=20.0,
            b_avg_m=50.0,
            t_f_hr=1.0,
        )


def test_hydrograph_piping_orifice_to_weir_progression() -> None:
    """Verify piping breach orifice flow and transition to open-channel weir flow."""
    vol = 1_000_000.0  # 1 MCM
    h = 25.0
    b_avg = 40.0
    t_f = 1.5

    hg_piping = route_hydrograph(
        initial_volume_m3=vol,
        dam_height_m=h,
        b_avg_m=b_avg,
        t_f_hr=t_f,
        reservoir_exponent=2.0,
        side_slope_z=1.0,
        progression_mode="piping_orifice_to_weir",
        piping_collapse_fraction=0.4,
    )

    assert len(hg_piping) > 0
    assert hg_piping.peak_discharge_m3s > 0

    # Volume integration check
    dt_s = 0.01 * 3600.0
    total_vol = sum(
        (hg_piping[i]["discharge_m3s"] + hg_piping[i + 1]["discharge_m3s"]) / 2.0 * dt_s
        for i in range(len(hg_piping) - 1)
    )
    rel_vol_err = abs(total_vol - vol) / vol
    assert rel_vol_err < 0.015, f"Piping volume integration error: {rel_vol_err * 100:.2f}%"


def test_hydrograph_piping_requires_collapse_fraction() -> None:
    """Verify that piping_collapse_fraction is required with no default in piping mode."""
    import pytest

    with pytest.raises(ValueError, match="piping_collapse_fraction is a required parameter"):
        route_hydrograph(
            initial_volume_m3=1e6,
            dam_height_m=20.0,
            b_avg_m=40.0,
            t_f_hr=1.5,
            reservoir_exponent=2.0,
            progression_mode="piping_orifice_to_weir",
        )


