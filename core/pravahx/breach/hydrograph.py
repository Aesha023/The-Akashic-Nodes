"""Breach outflow hydrograph from parameters and volume."""

from typing import TypedDict


class HydrographPoint(TypedDict):
    time_hr: float
    discharge_m3s: float
    volume_remaining_m3: float
    head_m: float


def route_hydrograph(
    initial_volume_m3: float,
    dam_height_m: float,
    b_avg_m: float,
    t_f_hr: float,
    side_slope_z: float = 1.0,
    dt_hr: float = 0.01,
    c_v1: float = 1.70,
    c_v2: float = 1.35,
    reservoir_exponent: float = 3.0,
) -> list[HydrographPoint]:
    """Route stored volume through a growing trapezoidal breach using broad-crested weir relations.

    The breach outflow Q(t) is computed using the standard trapezoidal broad-crested weir
    equation combining rectangular bottom and triangular side-slope components:
        Q(t) = C_v1 * b(t) * h(t)^1.5 + C_v2 * z(t) * h(t)^2.5

    where:
        b(t) = Instantaneous breach bottom width (m), expanding linearly to
               b_bottom = max(0, b_avg - z * dam_height) over t_f.
        z(t) = Instantaneous breach side slope (z:1 H:V), expanding linearly to z over t_f.
        h(t) = Instantaneous water head above breach invert (m), derived from remaining
               volume V(t) via stage-storage power law:
               V(h) = K_v * h^m  =>  h(t) = H_0 * (V(t) / V_0)^(1/m).
        C_v1 = Metric broad-crested rectangular weir coefficient (~1.70 m^0.5/s).
               Source: Fread (1988), Wahl (1998, Eq. 2), HEC-RAS Manual Ch. 14.
        C_v2 = Metric broad-crested triangular side-slope coefficient (~1.35 m^0.5/s;
               2.45 in US Customary). Source: Fread (1988), Wahl (1998, Eq. 2).
        m    = Reservoir hypsometric shape exponent (default m = 3.0 for V-shaped mountain
               valley; m = 2.0 for parabolic valley; m = 1.0 for rectangular tank).
               Source: Singh (1996).

    Args:
        initial_volume_m3: Initial reservoir storage volume (m^3).
        dam_height_m: Initial water height / breach height (m).
        b_avg_m: Final average breach width (m).
        t_f_hr: Breach formation time (hours).
        side_slope_z: Final breach side slope z (horizontal:vertical). Default 1.0.
        dt_hr: Time step for routing (hours). Default 0.01 hr.
        c_v1: Rectangular weir coefficient (m^0.5/s). Default 1.70.
        c_v2: Triangular side-slope weir coefficient (m^0.5/s). Default 1.35.
        reservoir_exponent: Hypsometric shape exponent m in V = K * h^m. Default 3.0.

    Returns:
        List of HydrographPoint entries over time.
    """
    if dam_height_m <= 0:
        raise ValueError("Dam height must be positive")
    if initial_volume_m3 <= 0:
        raise ValueError("Initial volume must be positive")
    if reservoir_exponent <= 0:
        raise ValueError("Reservoir exponent must be positive")

    # Final bottom width from average width and side slope
    b_bottom_final = max(0.0, b_avg_m - side_slope_z * dam_height_m)

    vol = initial_volume_m3
    time_hr = 0.0

    # Precompute reservoir shape coefficient K where V = K * h^m
    # Therefore h = (V / K)^(1/m)
    k_shape = initial_volume_m3 / (dam_height_m**reservoir_exponent)

    points: list[HydrographPoint] = []
    # Continue until 99.9% of volume is released
    while vol > 0.001 * initial_volume_m3:
        # Current head from remaining volume
        h = (vol / k_shape) ** (1.0 / reservoir_exponent)

        # Linear breach growth over formation time t_f
        expansion_factor = min(1.0, time_hr / t_f_hr) if t_f_hr > 0 else 1.0
        b_t = b_bottom_final * expansion_factor
        z_t = side_slope_z * expansion_factor

        # Trapezoidal weir discharge: rectangular bottom + triangular side slopes
        q_m3s = c_v1 * b_t * (h**1.5) + c_v2 * z_t * (h**2.5)

        points.append(
            HydrographPoint(
                time_hr=time_hr,
                discharge_m3s=q_m3s,
                volume_remaining_m3=vol,
                head_m=h,
            )
        )

        # Update volume (Forward Euler)
        # dV = -Q * dt
        dt_s = dt_hr * 3600.0

        # Don't overshoot 0
        released = min(vol, q_m3s * dt_s)
        vol -= released

        time_hr += dt_hr

        # Safety break if draining takes excessively long
        if time_hr > max(100.0, 20 * t_f_hr):
            break

    # Add final point at zero
    points.append(
        HydrographPoint(
            time_hr=time_hr,
            discharge_m3s=0.0,
            volume_remaining_m3=max(0.0, vol),
            head_m=0.0,
        )
    )

    return points
