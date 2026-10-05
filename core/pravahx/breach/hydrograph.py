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
    dt_hr: float = 0.01,
    c_d: float = 1.7,
) -> list[HydrographPoint]:
    """Route stored volume through a growing breach using a weir relation.

    Assumes a simplified V-shaped reservoir where V(h) = V_initial * (h / H_dam)^3.

    Args:
        initial_volume_m3: Initial reservoir volume (m3).
        dam_height_m: Initial head/dam height (m).
        b_avg_m: Final average breach width (m).
        t_f_hr: Breach formation time (hours).
        dt_hr: Time step for routing (hours).
        c_d: Weir coefficient. Standard metric broad-crested weir is ~1.7.

    Returns:
        List of hydrograph points over time.
    """
    if dam_height_m <= 0:
        raise ValueError("Dam height must be positive")
    if initial_volume_m3 <= 0:
        raise ValueError("Initial volume must be positive")

    vol = initial_volume_m3
    time_hr = 0.0

    # Precompute reservoir shape coefficient K where V = K * h^3
    # Therefore h = (V / K)^(1/3)
    k_shape = initial_volume_m3 / (dam_height_m**3)

    points = []
    # Continue until 99.9% of volume is released
    while vol > 0.001 * initial_volume_m3:
        # Current head from volume
        h = (vol / k_shape) ** (1.0 / 3.0)

        # Current breach width (grows linearly to b_avg over t_f)
        b_t = b_avg_m * (time_hr / t_f_hr) if time_hr < t_f_hr and t_f_hr > 0 else b_avg_m

        # Weir discharge Q = C_d * b * h^(1.5)
        q_m3s = c_d * b_t * (h**1.5)

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

        # Safety break if draining takes too long
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
