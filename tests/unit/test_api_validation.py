"""Unit tests for Validation and Benchmark Status endpoint (B2 API Completion)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_validation_status_endpoint() -> None:
    """Test validation status endpoint returning structured benchmark metrics and labels."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/validation/status")
        assert res.status_code == 200
        data = res.json()

        assert "title" in data
        assert "provenance_standard" in data

        # Check engines
        engines = {e["engine"]: e for e in data["engines"]}
        assert "Tier-0 HAND Ganga" in engines
        assert engines["Tier-0 HAND Ganga"]["label"] == "RUN AND PASSED"
        assert engines["Tier-0 HAND Ganga"]["metrics"]["inundation_area_km2"] == 1.72
        assert engines["Tier-0 HAND Ganga"]["metrics"]["max_depth_m"] == 7.73

        assert "Delft3D FM Build / Portability + Ritter" in engines
        assert engines["Delft3D FM Build / Portability + Ritter"]["label"] == "RUN AND PASSED"
        assert (
            engines["Delft3D FM Build / Portability + Ritter"]["metrics"]["initial_mass_m3"]
            == 500000.0
        )
        assert (
            engines["Delft3D FM Build / Portability + Ritter"]["metrics"]["final_mass_m3"]
            == 500000.0
        )

        assert "Delft3D FM Ganga Real Terrain" in engines
        assert engines["Delft3D FM Ganga Real Terrain"]["label"] == "RUN AND FAILED"

        assert "DualSPHysics 3D SPH Solver" in engines
        assert engines["DualSPHysics 3D SPH Solver"]["label"] == "RUN AND PASSED"

        assert "GEE Flood Mapping (Kuttanad 2018)" in engines
        assert engines["GEE Flood Mapping (Kuttanad 2018)"]["label"] == "RUN AND PASSED"

        # Check demo pipeline metrics
        demo = data["demo_pipeline"]
        assert demo["aoi_population_sum"] == 27390.1
        assert demo["exposed_population"] == 2696
        assert demo["depth_classes"]["0.0-0.5m [UNVERIFIED]"] == 230.3
        assert demo["depth_classes"]["0.5-1.5m [UNVERIFIED]"] == 253.3
        assert demo["depth_classes"][">1.5m [UNVERIFIED]"] == 2212.9
        assert demo["flooded_roads_km"] == 17.34
        assert demo["severed_edges_count"] == 930
        assert demo["severed_edge_length_km"] == 311.84
        assert demo["flooded_buildings"] == 5
        assert demo["building_coverage_note"] == "OSM building coverage incomplete"
        assert demo["critical_facilities_flooded"] == 0
        assert demo["evacuation_reachable_origins"] == 2
        assert demo["evacuation_unreachable_origins"] == 3

        # Check artifact hashes
        hashes = data["artifact_hashes"]
        assert (
            hashes["tier0_max_depth_cog.tif"]
            == "d3168ae8ae7483660a922312b9dff21df9012a6cb8ca350849c7198bbda33ea3"
        )
        assert (
            hashes["ganga_tier0_brief.pdf"]
            == "a1580e27e1bf5e1b413f50afd505add77ff0d0ec11f59ac1d86ef753d5adfaf7"
        )
