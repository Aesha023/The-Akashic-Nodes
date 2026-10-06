"""Ensemble generator for breach parameters across HEC-RAS regression equations.

Equations implemented from the USACE HEC-RAS Hydraulic Reference Manual (Chapter 14):
1. Froehlich (2008)
2. Froehlich (1995)
3. Von Thun and Gillette (1990)
4. MacDonald and Langridge-Monopolis (1984)

Source: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/performing-a-dam-break-study-with-hec-ras/
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class RegressionResult:
    """Estimated breach parameters from a single regression method."""

    method_name: str
    average_width_m: float
    formation_time_hr: float
    side_slope_z: float


@dataclass(frozen=True)
class EnsembleParams:
    """Quantile breach parameters derived from the multi-model regression spread."""

    average_width_m: float
    formation_time_hr: float
    quantile: Literal["p10", "p50", "p90"]
    models_used: list[str]


def calc_froehlich_2008(
    volume_m3: float, height_m: float, mode: Literal["overtopping", "piping"] = "overtopping"
) -> RegressionResult:
    """Froehlich (2008) breach regression.

    Source: HEC-RAS Hydraulic Reference Manual Chapter 14 (Froehlich 2008).
    """
    k_o = 1.3 if mode == "overtopping" else 1.0
    g = 9.81
    b_avg = 0.27 * k_o * (volume_m3**0.32) * (height_m**0.04)
    t_f = 63.2 * math.sqrt(volume_m3 / (g * (height_m**2))) / 3600.0
    z = 1.0 if mode == "overtopping" else 0.7
    return RegressionResult("Froehlich (2008)", b_avg, t_f, z)


def calc_froehlich_1995(
    volume_m3: float, height_m: float, mode: Literal["overtopping", "piping"] = "overtopping"
) -> RegressionResult:
    """Froehlich (1995) breach regression.

    Source: HEC-RAS Hydraulic Reference Manual Chapter 14 (Froehlich 1995).
    """
    k_o = 1.4 if mode == "overtopping" else 1.0
    b_avg = 0.1803 * k_o * (volume_m3**0.32) * (height_m**0.19)
    t_f = 0.00254 * (volume_m3**0.53) * (height_m**-0.90)
    z = 1.4 if mode == "overtopping" else 0.9
    return RegressionResult("Froehlich (1995)", b_avg, t_f, z)


def calc_von_thun_gillette_1990(
    volume_m3: float, height_m: float, mode: Literal["overtopping", "piping"] = "overtopping"
) -> RegressionResult:
    """Von Thun and Gillette (1990) breach regression.

    Source: HEC-RAS Hydraulic Reference Manual Chapter 14 (Von Thun and Gillette 1990).
    """
    # C_b depends on reservoir volume
    if volume_m3 < 1.233e6:
        c_b = 6.1
    elif volume_m3 < 6.167e6:
        c_b = 18.3
    elif volume_m3 < 1.233e7:
        c_b = 30.5
    else:
        c_b = 45.7

    b_avg = 2.5 * height_m + c_b
    # Formation time for erosion-resistant / standard embankment
    t_f = max(0.1, 0.015 * height_m)
    z = 0.5 if mode == "piping" else 1.0
    return RegressionResult("Von Thun and Gillette (1990)", b_avg, t_f, z)


def calc_macdonald_langridge_monopolis_1984(
    volume_m3: float, height_m: float, mode: Literal["overtopping", "piping"] = "overtopping"
) -> RegressionResult:
    """MacDonald and Langridge-Monopolis (1984) breach regression.

    Source: HEC-RAS Hydraulic Reference Manual Chapter 14 (MacDonald and Langridge-Monopolis 1984).
    """
    # Volume of eroded material (m^3)
    v_eroded = 0.0261 * ((volume_m3 * height_m) ** 0.77)
    # Formation time (hours)
    t_f = 0.0179 * (v_eroded**0.364)
    # Approximate breach average width from eroded volume
    b_avg = max(1.0, math.sqrt(v_eroded / max(1.0, height_m)))
    z = 0.5
    return RegressionResult("MacDonald and Langridge-Monopolis (1984)", b_avg, t_f, z)


def compute_breach_ensemble(
    volume_m3: float,
    height_m: float,
    mode: Literal["overtopping", "piping"] = "overtopping",
    quantiles: list[Literal["p10", "p50", "p90"]] | None = None,
) -> dict[str, EnsembleParams]:
    """Compute breach parameter ensemble (p10, p50, p90) from HEC-RAS regression equations.

    Evaluates the 4 empirical regression models in the HEC-RAS manual and computes percentiles
    across their predictions.

    Args:
        volume_m3: Reservoir volume at failure (m^3).
        height_m: Breach height (m).
        mode: Failure mode ("overtopping" or "piping").
        quantiles: Quantiles to evaluate (default: ["p10", "p50", "p90"]).

    Returns:
        Dictionary mapping quantile string to EnsembleParams.
    """
    if volume_m3 <= 0 or height_m <= 0:
        raise ValueError("Volume and height must be positive")

    if quantiles is None:
        quantiles = ["p10", "p50", "p90"]

    # 1. Run all 4 regression models from HEC-RAS manual
    models = [
        calc_froehlich_2008(volume_m3, height_m, mode),
        calc_froehlich_1995(volume_m3, height_m, mode),
        calc_von_thun_gillette_1990(volume_m3, height_m, mode),
        calc_macdonald_langridge_monopolis_1984(volume_m3, height_m, mode),
    ]

    widths = [m.average_width_m for m in models]
    times = [m.formation_time_hr for m in models]
    model_names = [m.method_name for m in models]

    # 2. Compute percentiles across the regression spread
    q_map = {"p10": 10.0, "p50": 50.0, "p90": 90.0}
    ensemble: dict[str, EnsembleParams] = {}

    for q in quantiles:
        q_pct = q_map[q]
        w_q = float(np.percentile(widths, q_pct))
        t_q = float(np.percentile(times, q_pct))
        ensemble[q] = EnsembleParams(
            average_width_m=w_q,
            formation_time_hr=t_q,
            quantile=q,
            models_used=model_names,
        )

    return ensemble
