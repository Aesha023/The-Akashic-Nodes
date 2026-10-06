"""Ensemble generator for breach parameters across HEC-RAS regression equations.

Equations documented in the USACE HEC-RAS Hydraulic Reference Manual (Chapter 14):
1. Froehlich (2008) - Predicts B_avg, t_f, side slope z.
2. Froehlich (1995a) - Predicts B_avg, t_f, side slope z.
3. Von Thun and Gillette (1990) - Predicts B_avg, t_f (function of erodibility), side slope z.
4. MacDonald and Langridge-Monopolis (1984) - Predicts volume of eroded material V_eroded
   and formation time t_f. In HEC-RAS, breach width is obtained by equating V_eroded to the
   cross-sectional volume of the embankment cut, requiring the dam's cross-section geometry
   (crest width and embankment slopes). Standalone empirical width is omitted here.
5. Xu and Zhang (2009) - Predicts B_top, B_bottom, and T_f. Excluded from the automated
   4-parameter spread because it requires 5 categorical parameters (dam type, corewall type,
   foundation type, failure mode, erodibility index) not present in basic reservoir inventories,
   and its failure time definition includes pre- and post-breach erosion phases.

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
    average_width_m: float | None
    formation_time_hr: float
    side_slope_z: float


@dataclass(frozen=True)
class EnsembleParams:
    """Summary breach parameters from multi-model regression spread (min, median, max)."""

    average_width_m: float
    formation_time_hr: float
    metric: Literal["min", "median", "max"]
    models_used_width: list[str]
    models_used_time: list[str]


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
    volume_m3: float,
    height_m: float,
    mode: Literal["overtopping", "piping"] = "overtopping",
    erodibility: Literal["erosion_resistant", "easily_erodible"] = "erosion_resistant",
) -> RegressionResult:
    """Von Thun and Gillette (1990) breach regression.

    Source: HEC-RAS Hydraulic Reference Manual Chapter 14 (Von Thun and Gillette 1990).

    Args:
        volume_m3: Reservoir storage at failure (m^3).
        height_m: Water height at breach (m).
        mode: Failure mode ("overtopping" or "piping").
        erodibility: "erosion_resistant" (t_f = 0.015*h_w) or "easily_erodible" (t_f = 0.020*h_w).
    """
    # C_b depends on reservoir volume (converted from acre-ft steps: 1k, 5k, 10k acre-ft)
    if volume_m3 < 1.233e6:
        c_b = 6.1
    elif volume_m3 < 6.167e6:
        c_b = 18.3
    elif volume_m3 < 1.233e7:
        c_b = 30.5
    else:
        c_b = 45.7

    b_avg = 2.5 * height_m + c_b

    # Formation time depends on embankment erodibility
    if erodibility == "easily_erodible":
        t_f = max(0.05, 0.020 * height_m)
    else:
        t_f = max(0.05, 0.015 * height_m)

    z = 0.5 if mode == "piping" else 1.0
    return RegressionResult("Von Thun and Gillette (1990)", b_avg, t_f, z)


def calc_macdonald_langridge_monopolis_1984(
    volume_m3: float, height_m: float, mode: Literal["overtopping", "piping"] = "overtopping"
) -> RegressionResult:
    """MacDonald and Langridge-Monopolis (1984) breach regression for earthfill dams.

    Predicts volume of eroded material V_eroded and formation time t_f.
    Breach width is omitted as MLM requires dam geometry (crest width and slopes)
    to calculate trapezoidal cross-section width from V_eroded.

    Source: HEC-RAS Hydraulic Reference Manual Chapter 14 (MacDonald and Langridge-Monopolis 1984).
    """
    # Volume of eroded material (m^3)
    v_eroded = 0.0261 * ((volume_m3 * height_m) ** 0.77)
    # Formation time (hours)
    t_f = 0.0179 * (v_eroded**0.364)
    z = 0.5
    return RegressionResult("MacDonald and Langridge-Monopolis (1984)", None, t_f, z)


def compute_breach_ensemble(
    volume_m3: float,
    height_m: float,
    mode: Literal["overtopping", "piping"] = "overtopping",
    erodibility: Literal["erosion_resistant", "easily_erodible"] = "erosion_resistant",
    metrics: list[Literal["min", "median", "max"]] | None = None,
) -> dict[str, EnsembleParams]:
    """Compute breach parameter ensemble (min, median, max) across HEC-RAS regression methods.

    Evaluates the empirical regression models from the HEC-RAS manual:
    - Width spread: Froehlich (2008), Froehlich (1995), Von Thun and Gillette (1990).
      (MacDonald & Langridge-Monopolis excluded from width spread because MLM predicts
      eroded volume V_eroded rather than width directly without dam geometry).
    - Time spread: Froehlich (2008), Froehlich (1995), Von Thun and Gillette (1990),
      MacDonald and Langridge-Monopolis (1984).

    Args:
        volume_m3: Reservoir volume at failure (m^3).
        height_m: Breach height (m).
        mode: Failure mode ("overtopping" or "piping").
        erodibility: Erodibility classification ("erosion_resistant" or "easily_erodible").
        metrics: Spread metrics to return (default: ["min", "median", "max"]).

    Returns:
        Dictionary mapping metric name ("min", "median", "max") to EnsembleParams.
    """
    if volume_m3 <= 0 or height_m <= 0:
        raise ValueError("Volume and height must be positive")

    if metrics is None:
        metrics = ["min", "median", "max"]

    # 1. Run all regression models
    models = [
        calc_froehlich_2008(volume_m3, height_m, mode),
        calc_froehlich_1995(volume_m3, height_m, mode),
        calc_von_thun_gillette_1990(volume_m3, height_m, mode, erodibility=erodibility),
        calc_macdonald_langridge_monopolis_1984(volume_m3, height_m, mode),
    ]

    # Models with direct width formulas
    width_models = [m for m in models if m.average_width_m is not None]
    widths = [m.average_width_m for m in width_models if m.average_width_m is not None]
    width_model_names = [m.method_name for m in width_models]

    # All models predicting formation time
    times = [m.formation_time_hr for m in models]
    time_model_names = [m.method_name for m in models]

    # 2. Compute min, median, max across the method spread
    ensemble: dict[str, EnsembleParams] = {}

    for m_name in metrics:
        if m_name == "min":
            w_val = float(min(widths))
            t_val = float(min(times))
        elif m_name == "median":
            w_val = float(np.median(widths))
            t_val = float(np.median(times))
        elif m_name == "max":
            w_val = float(max(widths))
            t_val = float(max(times))
        else:
            raise ValueError(f"Unknown metric: {m_name}")

        ensemble[m_name] = EnsembleParams(
            average_width_m=w_val,
            formation_time_hr=t_val,
            metric=m_name,
            models_used_width=width_model_names,
            models_used_time=time_model_names,
        )

    return ensemble
