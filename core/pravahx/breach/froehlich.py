"""Froehlich (2008) embankment dam breach parameters."""

import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FroehlichParams:
    """Estimated breach parameters using Froehlich (2008)."""

    average_width_m: float
    bottom_width_m: float
    side_slope_z: float
    formation_time_hr: float
    peak_discharge_m3s: float


def compute_froehlich_2008(
    volume_m3: float, height_m: float, mode: Literal["overtopping", "piping"] = "overtopping"
) -> FroehlichParams:
    """Compute breach parameters using Froehlich (2008) equations.

    Args:
        volume_m3: Reservoir volume at time of failure (Vw in m^3)
        height_m: Height of the breach (Hb in m)
        mode: Failure mode, either 'overtopping' or 'piping'

    Returns:
        FroehlichParams with width, time, side slope, and peak discharge estimates.
    """
    if volume_m3 <= 0 or height_m <= 0:
        raise ValueError("Volume and height must be positive")

    k_o = 1.3 if mode == "overtopping" else 1.0
    g = 9.81

    # Average breach width (m) - Froehlich (2008) Eq. 1
    b_avg = 0.27 * k_o * (volume_m3**0.32) * (height_m**0.04)

    # Breach formation time (hrs) - Froehlich (2008) Eq. 2
    t_f_hr = 63.2 * math.sqrt(volume_m3 / (g * (height_m**2))) / 3600.0

    # Side slope z:1 (H:V) - Froehlich (2008)
    z = 1.0 if mode == "overtopping" else 0.7

    # Bottom breach width (m)
    b_bottom = max(0.0, b_avg - z * height_m)

    # Peak discharge (m3/s) for reference from Froehlich (1995) SI regression:
    # Qp = 0.607 * (Vw ** 0.295) * (hw ** 1.24)
    q_p = 0.607 * (volume_m3**0.295) * (height_m**1.24)

    return FroehlichParams(
        average_width_m=b_avg,
        bottom_width_m=b_bottom,
        side_slope_z=z,
        formation_time_hr=t_f_hr,
        peak_discharge_m3s=q_p,
    )
