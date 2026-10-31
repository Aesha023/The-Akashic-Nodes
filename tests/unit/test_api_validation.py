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
        assert demo["severed_edges_count"] == 100
        assert demo["severed_edge_length_km"] == 14.76
        assert demo["flooded_buildings"] == 5
        assert demo["building_coverage_note"] == "OSM building coverage incomplete"
        assert demo["critical_facilities_flooded"] == 0
        assert demo["evacuation_reachable_origins"] == 2
        assert demo["evacuation_unreachable_origins"] == 3

        # Check artifact hashes
        hashes = data["artifact_hashes"]
        assert (
            hashes["tier0_max_depth_cog.tif"]
            == "d3168ae8ae742171cecd2abac607fd80d36e882e0ffb32e414f721202c900194"
        )
        assert (
            hashes["ganga_tier0_brief.pdf"]
            == "acdaad391f768c5c41dbb9b2b6569e13a20fcbbdfc3c623bf715eac02b0f8866"
        )


@pytest.mark.asyncio
async def test_validation_benchmarks_endpoint() -> None:
    """Test validation benchmarks endpoint returning 5 empirical benchmarks with Ritter chart points."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/validation/benchmarks")
        assert res.status_code == 200
        data = res.json()

        assert "title" in data
        assert "benchmarks" in data
        benchmarks = {b["id"]: b for b in data["benchmarks"]}
        assert len(benchmarks) == 5

        # Ritter 1892
        assert "ritter_1892" in benchmarks
        ritter = benchmarks["ritter_1892"]
        assert ritter["status"] == "RUN AND PASSED"
        assert "chart" in ritter
        assert len(ritter["chart"]["points"]) > 20

        # Kuttanad
        assert "kuttanad_sentinel1" in benchmarks
        assert benchmarks["kuttanad_sentinel1"]["status"] == "RUN AND PASSED"

        # Delft3D Ganga
        assert "delft3d_ganga" in benchmarks
        assert benchmarks["delft3d_ganga"]["status"] == "PENDING / RUN AND FAILED"

        # DualSPHysics
        assert "dualsphysics_3d" in benchmarks
        assert benchmarks["dualsphysics_3d"]["status"] == "RUN · NOT YET VALIDATED"

        # Martin & Moyce
        assert "martin_moyce" in benchmarks
        assert benchmarks["martin_moyce"]["status"] == "NOT RUN"

