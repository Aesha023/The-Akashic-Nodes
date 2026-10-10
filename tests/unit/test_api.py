"""Unit tests for Phase 7 FastAPI REST endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_health_and_system_endpoints() -> None:
    """Test public health and system information endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/health/live")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

        res = await client.get("/api/v1/health/ready")
        assert res.status_code == 200
        assert res.json()["status"] == "ready"

        res = await client.get("/api/v1/system/info")
        assert res.status_code == 200
        assert "version" in res.json()


@pytest.mark.asyncio
async def test_auth_and_user_flow() -> None:
    """Test user registration, login, and authenticated profile access."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        reg_payload = {
            "email": "analyst@pravahx.in",
            "password": "ValidPassword123!",
            "full_name": "Senior Hydro Analyst",
            "role": "analyst",
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code in (201, 409)

        # Login
        login_res = await client.post(
            "/api/v1/auth/token",
            data={"username": "analyst@pravahx.in", "password": "ValidPassword123!"},
        )
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        access_tok = tokens["access_token"]

        # Get profile
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_tok}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "analyst@pravahx.in"
        assert me_res.json()["role"] == "analyst"


@pytest.mark.asyncio
async def test_scenario_crud_and_run_dispatch() -> None:
    """Test scenario creation, listing, run dispatch, and manifest retrieval."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login admin
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@pravahx.in",
                "password": "AdminPassword123!",
                "full_name": "System Admin",
                "role": "admin",
            },
        )
        tok_res = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin@pravahx.in", "password": "AdminPassword123!"},
        )
        token = tok_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Create scenario
        scen_payload = {
            "config": {
                "scenario": {
                    "id": "api_test_scenario_01",
                    "name": "API Test Scenario",
                    "type": "dam_break",
                    "failure_mode": "overtopping",
                },
                "source": {
                    "point": [78.30, 30.15],
                    "dam_height_m": 45.0,
                    "storage_m3": 5000000.0,
                },
                "domain": {"reach_length_km": 20.0, "buffer_km": 2.0},
                "inputs": {},
                "breach": {
                    "width_uncertainty_factor": 1.3,
                    "time_uncertainty_factor": 1.4,
                },
                "tiers": {},
                "compare": {"enabled": True},
                "cascade": {"enabled": True},
                "impact": {"enabled": False},
            }
        }
        create_res = await client.post(
            "/api/v1/scenarios",
            json=scen_payload,
            headers=auth_headers,
        )
        assert create_res.status_code in (201, 409)

        # List scenarios
        list_res = await client.get("/api/v1/scenarios", headers=auth_headers)
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # Dispatch run
        run_res = await client.post(
            "/api/v1/scenarios/api_test_scenario_01/runs",
            json={"resume": True},
            headers=auth_headers,
        )
        assert run_res.status_code == 202
        run_data = run_res.json()
        assert run_data["scenario_id"] == "api_test_scenario_01"
        assert run_data["status"] in ("succeeded", "running")
        run_id = run_data["id"]

        # Get run manifest
        manifest_res = await client.get(
            f"/api/v1/runs/{run_id}/manifest",
            headers=auth_headers,
        )
        assert manifest_res.status_code == 200
        assert manifest_res.json()["scenario_id"] == "api_test_scenario_01"


@pytest.mark.asyncio
async def test_impact_and_gee_endpoints() -> None:
    """Test Flood Hazard Rating, Damage Valuation, Evacuation, Brief, and GEE endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login analyst
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "analyst2@pravahx.in",
                "password": "Password123!",
                "full_name": "Analyst Two",
                "role": "analyst",
            },
        )
        tok_res = await client.post(
            "/api/v1/auth/token",
            data={"username": "analyst2@pravahx.in", "password": "Password123!"},
        )
        token = tok_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Defra Hazard Rating
        h_res = await client.post(
            "/api/v1/impact/hazard",
            json={"depth_m": 1.2, "velocity_m_s": 2.0},
            headers=headers,
        )
        assert h_res.status_code == 200
        h_data = h_res.json()
        assert h_data["hazard_rating"] > 0
        assert h_data["hazard_class"] in ("low", "moderate", "high", "extreme")

        # 2. Exposure & Damage
        v_payload = [
            {
                "village_id": "V01",
                "name": "Aluva East",
                "population": 5000,
                "buildings": 1200,
                "max_depth_m": 1.5,
                "arrival_time_hr": 2.5,
            }
        ]
        exp_res = await client.post(
            "/api/v1/impact/exposure",
            json={"villages": v_payload},
            headers=headers,
        )
        assert exp_res.status_code == 200
        assert exp_res.json()["total_population_exposed"] > 0

        dmg_res = await client.post(
            "/api/v1/impact/damage",
            json={"villages": v_payload},
            headers=headers,
        )
        assert dmg_res.status_code == 200
        assert dmg_res.json()["total_loss_inr"] > 0

        # 3. GEE Status
        gee_status_res = await client.get("/api/v1/gee/status", headers=headers)
        assert gee_status_res.status_code == 200
        assert "authenticated" in gee_status_res.json()
