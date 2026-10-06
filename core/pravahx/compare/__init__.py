"""PravahX comparison, spatial metrics, agreement mapping, and ensemble uncertainty (Phase 5)."""

from __future__ import annotations

from pravahx.compare.agreement import (
    AgreementCategoryStats,
    AgreementSummary,
    generate_agreement_raster,
)
from pravahx.compare.ensemble import (
    EnsembleRasterResults,
    aggregate_ensemble_rasters,
)
from pravahx.compare.metrics import (
    ComparisonMetrics,
    compute_comparison_metrics,
)
from pravahx.compare.refine import (
    RefinementPlan,
    RefinementZone,
    compute_refinement_zones,
)
from pravahx.compare.regrid import (
    align_rasters_to_common_grid,
    regrid_raster_to_target,
)

__all__ = [
    "AgreementCategoryStats",
    "AgreementSummary",
    "ComparisonMetrics",
    "EnsembleRasterResults",
    "RefinementPlan",
    "RefinementZone",
    "aggregate_ensemble_rasters",
    "align_rasters_to_common_grid",
    "compute_comparison_metrics",
    "compute_refinement_zones",
    "generate_agreement_raster",
    "regrid_raster_to_target",
]
