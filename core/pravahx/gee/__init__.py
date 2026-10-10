"""PravahX Earth Engine and satellite remote sensing module."""

from pravahx.gee.client import GEEClient
from pravahx.gee.flood_mapping import (
    FloodExtractionResult,
    execute_unspider_sar_gee,
    export_binary_mask_to_kml,
    extract_optical_water_extent,
    extract_sar_flood_extent,
    extract_unspider_sar_flood,
    process_satellite_flood_raster,
    smooth_sar_speckle,
)
from pravahx.gee.lake_watch import (
    LakeObservation,
    LakeWatchSummary,
    analyze_lake_time_series,
)
from pravahx.gee.scoring import (
    SatelliteValidationMetrics,
    calculate_flood_extent_metrics,
    score_simulation_against_satellite,
)

__all__ = [
    "FloodExtractionResult",
    "GEEClient",
    "LakeObservation",
    "LakeWatchSummary",
    "SatelliteValidationMetrics",
    "analyze_lake_time_series",
    "calculate_flood_extent_metrics",
    "execute_unspider_sar_gee",
    "export_binary_mask_to_kml",
    "extract_optical_water_extent",
    "extract_sar_flood_extent",
    "extract_unspider_sar_flood",
    "process_satellite_flood_raster",
    "score_simulation_against_satellite",
    "smooth_sar_speckle",
]
