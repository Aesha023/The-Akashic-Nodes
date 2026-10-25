"""Validation status and engine benchmark verification endpoints (B2 API Completion)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/status")
async def get_validation_status() -> dict[str, Any]:
    """Retrieve structured validation evidence, benchmark engine metrics, and feature statuses."""
    return {
        "title": "PravahX Validation & Benchmark Audit Status",
        "provenance_standard": (
            "All numbers traceable verbatim to VALIDATION.md or reproducible run logs"
        ),
        "engines": [
            {
                "engine": "Tier-0 HAND Ganga",
                "label": "RUN AND PASSED",
                "evidence": "VALIDATION.md §9.1, §11",
                "metrics": {
                    "inundation_area_km2": 1.72,
                    "max_depth_m": 7.73,
                    "mean_depth_m": 6.31,
                    "median_depth_m": 7.23,
                    "p10_depth_m": 3.12,
                    "peak_discharge_m3s": 5000.0,
                    "manning_n": 0.035,
                    "grid_res_m": 30,
                    "crs": "EPSG:32644",
                },
                "scenario_type": "hypothetical scenario, Tier-0 screening",
            },
            {
                "engine": "Delft3D FM Build / Portability + Ritter",
                "label": "RUN AND PASSED",
                "evidence": "VALIDATION.md §8.1, §8.2",
                "metrics": {
                    "depth_rmse_dx5m_t10_20_30_s": [0.055, 0.055, 0.059],
                    "depth_rmse_dx2_5m_t10_20_30_s": [0.031, 0.034, 0.042],
                    "initial_mass_m3": 500000.0,
                    "final_mass_m3": 500000.0,
                    "mass_error_m3": 0.0,
                    "front_location_gate": "FAIL vs 5% (thin-film artefact)",
                },
            },
            {
                "engine": "Delft3D FM Ganga Real Terrain",
                "label": "RUN AND FAILED",
                "evidence": "VALIDATION.md §9",
                "notes": (
                    "Failed numerical stability gates d/e on steep Himalayan bathymetry; "
                    "engine mass balance exact (5,801,809 m3)."
                ),
            },
            {
                "engine": "DualSPHysics 3D SPH Solver",
                "label": "RUN AND PASSED",
                "evidence": (
                    "Colab T4 run (314,801 particles, 2.0 s sim, 389 s wall, 41 PARTs, "
                    "results sha256 461646b67d4954f52dcfca0000a36f41a0)"
                ),
                "notes": "Martin & Moyce comparison NOT VERIFIED (paywalled)",
            },
            {
                "engine": "GEE Flood Mapping (Kuttanad 2018)",
                "label": "RUN AND PASSED",
                "evidence": "VALIDATION.md §10",
                "metrics": {"mapped_extent_km2": 40.52},
                "notes": "qualitatively consistent with Tiwari et al. 2020",
            },
        ],
        "demo_pipeline": {
            "scenario": "hypothetical scenario, Tier-0 screening",
            "aoi_population_sum": 27390.1,
            "exposed_population": 2696,
            "depth_classes": {
                "0.0-0.5m [UNVERIFIED]": 230.3,
                "0.5-1.5m [UNVERIFIED]": 253.3,
                ">1.5m [UNVERIFIED]": 2212.9,
            },
            "flooded_roads_km": 17.34,
            "total_road_network_km": 159.54,
            "severed_edges_count": 930,
            "severed_edge_length_km": 311.84,
            "flooded_buildings": 5,
            "total_buildings_in_aoi": 93,
            "building_coverage_note": "OSM building coverage incomplete",
            "critical_facilities_flooded": 0,
            "total_critical_facilities": 28,
            "evacuation_reachable_origins": 2,
            "evacuation_unreachable_origins": 3,
        },
        "artifact_hashes": {
            "tier0_max_depth_cog.tif": (
                "d3168ae8ae7483660a922312b9dff21df9012a6cb8ca350849c7198bbda33ea3"
            ),
            "tier0_envelope.geojson": (
                "2cca3b08f643f8e562725fa84bc6f284e3650226c6d17978cece42c67cf7f3e8"
            ),
            "evacuation_routes.geojson": (
                "38eaddceaac7564acd483a80b1c2640d3604ab00c1c8a2801a8dfef43c244a7f"
            ),
            "ganga_tier0_brief.pdf": (
                "a1580e27e1bf5e1b413f50afd505add77ff0d0ec11f59ac1d86ef753d5adfaf7"
            ),
        },
    }
