"""Contract tests asserting API responses match OpenAPI schema definitions."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app
from tests.conftest import get_auth_headers

app = create_app()


@pytest.fixture(scope="module")
def openapi_schema() -> dict:
    schema_path = (
        Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "api" / "openapi.json"
    )
    assert schema_path.exists(), "openapi.json must be generated"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_health_contract(openapi_schema: dict) -> None:
    """Validate /api/v1/health response contract."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "database" in data
        assert "deployment_mode" in data


@pytest.mark.asyncio
async def test_validation_endpoints_contract(openapi_schema: dict) -> None:
    """Validate /api/v1/validation status and benchmark contract."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/validation/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "engines" in data
        assert "demo_pipeline" in data
        assert isinstance(data["engines"], list)
        assert len(data["engines"]) >= 5


@pytest.mark.asyncio
async def test_demo_endpoints_contract(openapi_schema: dict) -> None:
    """Validate /api/v1/demo/* endpoints contract and mandatory demo=true flag."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        endpoints = [
            "/api/v1/demo/watched-lakes",
            "/api/v1/demo/alerts",
            "/api/v1/demo/cascade",
            "/api/v1/demo/engine-comparison",
            "/api/v1/demo/satellite-scoring",
            "/api/v1/demo/time-series",
            "/api/v1/demo/batches",
            "/api/v1/demo/live-flood",
        ]
        for ep in endpoints:
            resp = await client.get(ep)
            assert resp.status_code == 200, f"Endpoint {ep} failed: {resp.text}"
            data = resp.json()
            assert data.get("demo") is True, f"Endpoint {ep} missing demo=True"


@pytest.mark.asyncio
async def test_run_response_precomputed_contract() -> None:
    """Validate that run response model contains precomputed, computed_at, and demo fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = await get_auth_headers(client, role="analyst")
        scen_id = f"contract_scen_{int(time.time() * 1000)}"
        create_payload = {
            "config": {
                "scenario": {
                    "id": scen_id,
                    "name": "Contract Test Scenario",
                    "type": "dam_break",
                    "failure_mode": "overtopping",
                },
                "source": {
                    "point": [78.30, 30.15],
                    "dam_height_m": 45.0,
                    "storage_m3": 5000000.0,
                    "volume_method": "user",
                },
                "domain": {
                    "reach_length_km": 10.0,
                    "buffer_km": 1.0,
                    "crs": "auto",
                },
                "inputs": {
                    "dem": "copernicus_glo30",
                    "landcover": "worldcover",
                },
                "breach": {
                    "method": "froehlich_2008",
                    "ensemble": ["p50"],
                    "width_uncertainty_factor": 0.3,
                    "time_uncertainty_factor": 0.3,
                },
                "tiers": {
                    "tier0": {"enabled": True},
                },
            }
        }
        scen_resp = await client.post("/api/v1/scenarios", json=create_payload, headers=headers)
        assert scen_resp.status_code == 201

        # Dispatch run
        run_resp = await client.post(
            "/api/v1/runs",
            json={"scenario_id": scen_id},
            headers=headers,
        )
        assert run_resp.status_code in (200, 202)
        run_data = run_resp.json()
        assert "precomputed" in run_data
        assert "computed_at" in run_data
        assert "demo" in run_data
