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

    # For these inputs:
    # b_avg = 0.27 * 1.3 * (1e6^0.32) * (20^0.04)
    # tf = 63.2 * sqrt(1e6 / (9.81 * 400)) / 3600
    expected_b = 0.27 * 1.3 * (vol**0.32) * (h**0.04)
    expected_tf = 63.2 * ((vol / (9.81 * h**2)) ** 0.5) / 3600.0
    expected_qp = 60.7 * (vol**0.295) * (h**1.24)

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
        dt_hr=dt,
        c_d=1.7,
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
