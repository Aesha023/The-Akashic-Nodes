"""Ensemble generator for breach parameters (p10, p50, p90)."""

import math
from dataclasses import dataclass
from typing import Literal


@dataclass
class EnsembleParams:
    """A set of breach parameters for a specific quantile scenario."""

    average_width_m: float
    formation_time_hr: float
    quantile: Literal["p10", "p50", "p90"]


def generate_ensemble(
    base_width_m: float,
    base_time_hr: float,
    width_uncertainty_factor: float,
    time_uncertainty_factor: float,
    quantiles: list[str] | None = None,
) -> dict[str, EnsembleParams]:
    """Generate an ensemble of breach parameters assuming log-normal error.

    The uncertainty factors are treated as the standard error (standard deviation)
    of the natural logarithm of the parameter.

    Args:
        base_width_m: Median estimate for breach width.
        base_time_hr: Median estimate for breach formation time.
        width_uncertainty_factor: Standard deviation of ln(width).
        time_uncertainty_factor: Standard deviation of ln(time).
        quantiles: List of quantiles to generate (e.g., ["p10", "p50", "p90"]).

    Returns:
        Dictionary mapping quantile string to EnsembleParams.
    """
    if quantiles is None:
        quantiles = ["p10", "p50", "p90"]

    # Z-scores for standard normal distribution
    z_scores = {
        "p10": -1.28155,  # 10th percentile
        "p50": 0.0,  # 50th percentile (median)
        "p90": 1.28155,  # 90th percentile
    }

    ensemble = {}
    for q in quantiles:
        q_lower = q.lower()
        if q_lower not in z_scores:
            raise ValueError(f"Unsupported quantile: {q}")

        z = z_scores[q_lower]

        # Log-normal distribution assumption
        # Note: A "p10" breach width is typically narrow (smaller B), but a "p10" formation time
        # might be longer (slower breach, lower peak discharge).
        # However, for a generic 'p10' scenario of the PARAMETER, we just scale it.
        # It's up to the caller to decide if a "worst case" scenario means p90 width and p10 time.
        # Here we just provide the statistical quantiles of each parameter.
        width_q = base_width_m * math.exp(z * width_uncertainty_factor)
        time_q = base_time_hr * math.exp(z * time_uncertainty_factor)

        ensemble[q_lower] = EnsembleParams(
            average_width_m=width_q,
            formation_time_hr=time_q,
            quantile=q_lower,  # type: ignore
        )

    return ensemble
