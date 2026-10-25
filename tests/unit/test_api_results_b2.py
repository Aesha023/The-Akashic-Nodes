"""Unit tests for simulation results, brief, exposure, evacuation, and downloads.

Part B2 API Completion tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db.session import get_db
from backend.app.main import create_app
from backend.app.models.run import Run

app = create_app()


@pytest.mark.asyncio
async def test_demo_results_endpoints() -> None:
    """Test brief, exposure, evacuation, download, and artifact endpoints for demo run."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Brief PDF endpoint
        res_brief = await client.get("/api/v1/runs/tier0_ganga/brief")
        assert res_brief.status_code == 200
        assert res_brief.headers["content-type"] == "application/pdf"
        assert len(res_brief.content) > 50_000

        # 2. Exposure endpoint
        res_exp = await client.get("/api/v1/runs/tier0_ganga/exposure")
        assert res_exp.status_code == 200
        data_exp = res_exp.json()
        assert data_exp["run_id"] == "tier0_ganga"
        assert data_exp["population"]["aoi_total"] == 27390.1
        assert data_exp["population"]["exposed_total"] == 2696
        assert data_exp["population"]["depth_classes"]["0.0-0.5m [UNVERIFIED]"] == 230.3
        assert data_exp["population"]["depth_classes"]["0.5-1.5m [UNVERIFIED]"] == 253.3
        assert data_exp["population"]["depth_classes"][">1.5m [UNVERIFIED]"] == 2212.9
        assert data_exp["roads"]["flooded_km"] == 17.34
        assert data_exp["buildings"]["flooded"] == 5
        assert data_exp["buildings"]["note"] == "OSM building coverage incomplete"
        assert data_exp["critical_facilities"]["flooded"] == 0

        # 3. Evacuation endpoint
        res_evac = await client.get("/api/v1/runs/tier0_ganga/evacuation")
        assert res_evac.status_code == 200
        data_evac = res_evac.json()
        assert data_evac["severed_edges_count"] == 930
        assert data_evac["severed_edge_length_km"] == 311.84
        assert data_evac["origins"]["reachable_count"] == 2
        assert data_evac["origins"]["unreachable_count"] == 3

        # 4. Artifact download
        res_art = await client.get("/api/v1/runs/tier0_ganga/artifacts/tier0_envelope.geojson")
        assert res_art.status_code == 200
        assert len(res_art.content) > 100

        # 5. Zip bundle download
        res_dl = await client.get("/api/v1/runs/tier0_ganga/download")
        assert res_dl.status_code == 200
        assert res_dl.headers["content-type"] == "application/zip"
        assert len(res_dl.content) > 1000


@pytest.mark.asyncio
async def test_result_protection_gate() -> None:
    """Verify that failed or invalid runs never serve results (400 Bad Request)."""
    import uuid

    failed_id = f"run_b2_failed_{uuid.uuid4().hex[:8]}"
    invalid_id = f"run_b2_invalid_{uuid.uuid4().hex[:8]}"

    async for db in get_db():
        failed_run = Run(
            id=failed_id,
            scenario_id="scen_b2_test",
            status="failed",
            is_valid=False,
            work_dir=f"tmp/{failed_id}",
            error_message="Simulation diverged",
        )
        invalid_run = Run(
            id=invalid_id,
            scenario_id="scen_b2_test",
            status="succeeded",
            is_valid=False,
            work_dir=f"tmp/{invalid_id}",
            error_message="Numerical conservation failed",
        )
        db.add(failed_run)
        db.add(invalid_run)
        await db.commit()
        break

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for bad_id in (failed_id, invalid_id):
            res_brief = await client.get(f"/api/v1/runs/{bad_id}/brief")
            assert res_brief.status_code == 400
            assert "Only valid succeeded runs can serve results" in res_brief.json()["detail"]

            res_exp = await client.get(f"/api/v1/runs/{bad_id}/exposure")
            assert res_exp.status_code == 400

            res_evac = await client.get(f"/api/v1/runs/{bad_id}/evacuation")
            assert res_evac.status_code == 400

            res_dl = await client.get(f"/api/v1/runs/{bad_id}/download")
            assert res_dl.status_code == 400

            res_art = await client.get(f"/api/v1/runs/{bad_id}/artifacts/envelope.geojson")
            assert res_art.status_code == 400
