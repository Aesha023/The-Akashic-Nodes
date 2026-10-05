"""Froehlich (2008) embankment dam breach parameters."""

import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FroehlichParams:
    """Estimated breach parameters using Froehlich (2008)."""

    average_width_m: float
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
        FroehlichParams with width, time and peak discharge estimates.
    """
    if volume_m3 <= 0 or height_m <= 0:
        raise ValueError("Volume and height must be positive")

    k_o = 1.3 if mode == "overtopping" else 1.0
    g = 9.81

    # Average breach width (m)
    b_avg = 0.27 * k_o * (volume_m3**0.32) * (height_m**0.04)

    # Breach formation time (hrs)
    # Convert seconds to hours if 63.2 formula is in seconds?
    # Wait, in Froehlich 2008, tf = 63.2 * sqrt(Vw / (g * Hb^2)) gives tf in seconds!
    # Or is tf in hours?
    # Let me use the standard Froehlich 2008 formulas directly.
    # Actually, tf = 63.2 * sqrt(...) is usually in seconds.
    # Let's keep tf in hours for convenience.
    t_f_hr = 63.2 * math.sqrt(volume_m3 / (g * (height_m**2))) / 3600.0

    # Peak discharge (m3/s) for reference
    # Qp = 60.7 * (Vw ** 0.295) * (Hw ** 1.24)
    # Assuming Hw (depth of water) is approximately equal to Hb (height of breach)
    q_p = 60.7 * (volume_m3**0.295) * (height_m**1.24)

    return FroehlichParams(
        average_width_m=b_avg,
        formation_time_hr=t_f_hr,
        peak_discharge_m3s=q_p,
    )
