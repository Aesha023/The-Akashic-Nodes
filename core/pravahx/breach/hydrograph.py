"""Breach outflow hydrograph from parameters and volume."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class HydrographPoint(TypedDict):
    time_hr: float
    discharge_m3s: float
    volume_remaining_m3: float
    head_m: float


@dataclass
class BreachHydrograph:
    """Routed breach hydrograph with independent empirical validation checks."""

    points: list[HydrographPoint]
    peak_discharge_m3s: float
    time_to_peak_hr: float
    froehlich_1995_peak_m3s: float
    ratio_to_froehlich_1995: float
    warning_flag: str | None = None

    def __iter__(self) -> Iterator[HydrographPoint]:
        return iter(self.points)

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, index: int) -> HydrographPoint:
        return self.points[index]


def route_hydrograph(
    initial_volume_m3: float,
    dam_height_m: float,
    b_avg_m: float,
    t_f_hr: float,
    reservoir_exponent: float,
    side_slope_z: float = 1.0,
    progression_mode: Literal[
        "vertical_and_horizontal", "horizontal_only"
    ] = "vertical_and_horizontal",
    dt_hr: float = 0.01,
    c_v1: float = 1.70,
    c_v2: float = 1.35,
) -> BreachHydrograph:
    """Route stored volume through a growing trapezoidal breach using broad-crested weir relations.

    The breach outflow Q(t) is computed using the standard trapezoidal broad-crested weir
    equation combining rectangular bottom and triangular side-slope components:
        Q(t) = C_v1 * b(t) * h_weir(t)^1.5 + C_v2 * z(t) * h_weir(t)^2.5

    where:
        b(t)       = Instantaneous breach bottom width (m), expanding linearly to
                     b_bottom = max(0, b_avg - z * dam_height) over t_f.
        z(t)       = Instantaneous breach side slope (z:1 H:V), expanding linearly to z over t_f.
        h_weir(t)  = Instantaneous water head above current breach invert (m).
                     In 'vertical_and_horizontal' mode (HEC-RAS standard), the breach invert falls
                     linearly from crest to final bottom elevation over t_f:
                         Z_invert(t) = (1 - t/t_f) * dam_height
                         h_weir(t) = max(0, h_pool(t) - Z_invert(t))
                     In 'horizontal_only' mode, the invert is at full depth from t=0:
                         h_weir(t) = h_pool(t)
        h_pool(t)  = Instantaneous pool water surface elevation above final breach invert (m),
                     derived from remaining volume V(t) via stage-storage power law:
                         V(h) = K_v * h^m  =>  h_pool(t) = H_0 * (V(t) / V_0)^(1/m).
        m          = Reservoir hypsometric shape exponent (required input, no default):
                         m = 3.0: Pyramidal / V-shaped mountain valley (A proportional to h^2)
                         m = 2.0: Parabolic valley (A proportional to h)
                         m = 1.0: Vertical-walled prismatic tank
                     Source: Singh (1996), Dam Breach Modeling Technology.
        C_v1       = Metric broad-crested rectangular weir coefficient (~1.70 m^0.5/s).
                     Source: Fread (1988), Wahl (1998, Eq. 2), HEC-RAS Manual Ch. 14.
        C_v2       = Metric broad-crested triangular side-slope coefficient (~1.35 m^0.5/s;
                     2.45 in US Customary). Source: Fread (1988), Wahl (1998, Eq. 2).

    Args:
        initial_volume_m3: Initial reservoir storage volume (m^3).
        dam_height_m: Initial water height / breach height (m).
        b_avg_m: Final average breach width (m).
        t_f_hr: Breach formation time (hours).
        reservoir_exponent: Hypsometric shape exponent m in V = K * h^m (required).
        side_slope_z: Final breach side slope z (horizontal:vertical). Default 1.0.
        progression_mode: 'vertical_and_horizontal' (HEC-RAS) or 'horizontal_only'.
        dt_hr: Time step for routing (hours). Default 0.01 hr.
        c_v1: Rectangular weir coefficient (m^0.5/s). Default 1.70.
        c_v2: Triangular side-slope weir coefficient (m^0.5/s). Default 1.35.

    Returns:
        BreachHydrograph containing hydrograph points and empirical validation metrics.
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
    max_q = 0.0
    t_peak = 0.0

    # Continue until 99.9% of volume is released
    while vol > 0.001 * initial_volume_m3:
        # Current pool water surface elevation above final breach invert
        h_pool = (vol / k_shape) ** (1.0 / reservoir_exponent)

        # Linear breach growth over formation time t_f
        expansion_factor = min(1.0, time_hr / t_f_hr) if t_f_hr > 0 else 1.0
        b_t = b_bottom_final * expansion_factor
        z_t = side_slope_z * expansion_factor

        # Active head over instantaneous breach invert
        if progression_mode == "vertical_and_horizontal":
            # Invert falls linearly from crest (dam_height) to bottom (0) over t_f
            h_invert_above_bottom = (1.0 - expansion_factor) * dam_height_m
            h_weir = max(0.0, h_pool - h_invert_above_bottom)
        else:
            # Full depth from t=0
            h_weir = h_pool

        # Trapezoidal weir discharge: rectangular bottom + triangular side slopes
        q_m3s = c_v1 * b_t * (h_weir**1.5) + c_v2 * z_t * (h_weir**2.5)

        if q_m3s > max_q:
            max_q = q_m3s
            t_peak = time_hr

        points.append(
            HydrographPoint(
                time_hr=time_hr,
                discharge_m3s=q_m3s,
                volume_remaining_m3=vol,
                head_m=h_pool,
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

    # Independent check: Froehlich (1995) empirical peak outflow regression (SI)
    qp_froehlich_1995 = 0.607 * (initial_volume_m3**0.295) * (dam_height_m**1.24)
    ratio = max_q / qp_froehlich_1995 if qp_froehlich_1995 > 0 else 1.0

    warning_flag = None
    if ratio > 2.0 or ratio < 0.5:
        warning_flag = (
            f"Routed peak discharge ({max_q:,.1f} m3/s) deviates from Froehlich (1995) "
            f"empirical peak ({qp_froehlich_1995:,.1f} m3/s) by factor {ratio:.2f} (> 2.0x)."
        )
        logger.warning(warning_flag)

    return BreachHydrograph(
        points=points,
        peak_discharge_m3s=max_q,
        time_to_peak_hr=t_peak,
        froehlich_1995_peak_m3s=qp_froehlich_1995,
        ratio_to_froehlich_1995=ratio,
        warning_flag=warning_flag,
    )
