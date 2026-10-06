"""PravahX dam breach modeling package."""

from __future__ import annotations

from pravahx.breach.ensemble import (
    EnsembleParams,
    RegressionResult,
    compute_breach_ensemble,
)
from pravahx.breach.froehlich import (
    FroehlichParams,
    compute_froehlich_2008,
)
from pravahx.breach.hydrograph import (
    BreachHydrograph,
    HydrographPoint,
    route_hydrograph,
)

__all__ = [
    "BreachHydrograph",
    "EnsembleParams",
    "FroehlichParams",
    "HydrographPoint",
    "RegressionResult",
    "compute_breach_ensemble",
    "compute_froehlich_2008",
    "route_hydrograph",
]
