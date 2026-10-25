"""Unit tests for Scenario versioning and cloning endpoints (B2 API Completion)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_scenario_create_clone_and_versioning() -> None:
    """Test scenario creation, version increment on update, and lineage in cloning."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        import uuid

        scen_id = f"scen_b2_{uuid.uuid4().hex[:8]}"
        clone_id = f"clone_{uuid.uuid4().hex[:8]}"

        # Register and login an analyst
        reg_payload = {
            "email": f"analyst_{uuid.uuid4().hex[:8]}@pravahx.in",
            "password": "ValidPassword123!",
            "full_name": "Scenario Analyst",
            "role": "analyst",
        }
        await client.post("/api/v1/auth/register", json=reg_payload)
        login_res = await client.post(
            "/api/v1/auth/token",
            data={"username": reg_payload["email"], "password": "ValidPassword123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create a scenario
        create_payload = {
            "config": {
                "scenario": {
                    "id": scen_id,
                    "name": "B2 Test Dam Breach Scenario",
                    "type": "dam_break",
                    "failure_mode": "overtopping",
                },
                "source": {
                    "point": [78.0, 25.0],
                    "dam_height_m": 30.0,
                    "storage_m3": 50000000.0,
                    "volume_method": "user",
                },
                "domain": {
                    "reach_length_km": 40.0,
                    "buffer_km": 3.0,
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
        res_create = await client.post("/api/v1/scenarios", json=create_payload, headers=headers)
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["id"] == scen_id
        assert data_create["version"] == 1
        assert data_create["parent_scenario_id"] is None

        # 2. Get scenario
        res_get = await client.get(f"/api/v1/scenarios/{scen_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["id"] == scen_id

        # 3. Update scenario -> version should increment to 2
        update_payload = {
            "config": {
                "scenario": {
                    "id": scen_id,
                    "name": "B2 Test Dam Breach Scenario Updated",
                    "type": "dam_break",
                    "failure_mode": "piping",
                },
                "source": {
                    "point": [78.0, 25.0],
                    "dam_height_m": 30.0,
                    "storage_m3": 50000000.0,
                    "volume_method": "user",
                },
                "domain": {
                    "reach_length_km": 40.0,
                    "buffer_km": 3.0,
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
        res_update = await client.put(
            f"/api/v1/scenarios/{scen_id}", json=update_payload, headers=headers
        )
        assert res_update.status_code == 200
        data_update = res_update.json()
        assert data_update["version"] == 2
        assert data_update["failure_mode"] == "piping"
        assert data_update["name"] == "B2 Test Dam Breach Scenario Updated"

        # 4. Clone scenario
        clone_payload = {
            "new_id": clone_id,
            "new_name": "B2 Test Cloned Child",
        }
        res_clone = await client.post(
            f"/api/v1/scenarios/{scen_id}/clone", json=clone_payload, headers=headers
        )
        assert res_clone.status_code == 201
        data_clone = res_clone.json()
        assert data_clone["id"] == clone_id
        assert data_clone["name"] == "B2 Test Cloned Child"
        assert data_clone["parent_scenario_id"] == scen_id
        assert data_clone["version"] == 1

        # 5. List scenarios
        res_list = await client.get("/api/v1/scenarios?skip=0&limit=10", headers=headers)
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert data_list["total"] >= 2
        ids = [item["id"] for item in data_list["items"]]
        assert scen_id in ids
        assert clone_id in ids
