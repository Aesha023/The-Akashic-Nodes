"""Unit tests for F11 cascade analysis and API endpoints (B4 Missing Features)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.conftest import get_auth_headers

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cascade_evaluate_safe_and_overtopped(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    payload = {
        "scenario_id": "test_cascade_reach",
        "initial_dam": {
            "id": "dam_upstream",
            "name": "Upstream Hydro Dam",
            "river": "Bhagirathi",
            "chainage_km": 0.0,
            "dam_height_m": 60.0,
            "storage_m3": 10000000.0,
            "crest_elevation_m": 800.0,
            "bed_elevation_m": 740.0,
            "spillway_capacity_m3s": 2000.0,
        },
        "initial_hydrograph": [
            {"time_seconds": 0.0, "discharge_m3s": 100.0},
            {"time_seconds": 3600.0, "discharge_m3s": 5000.0},
            {"time_seconds": 7200.0, "discharge_m3s": 1000.0},
            {"time_seconds": 10800.0, "discharge_m3s": 200.0},
        ],
        "downstream_dams": [
            {
                "id": "dam_downstream_small",
                "name": "Downstream Low Barrage",
                "river": "Bhagirathi",
                "chainage_km": 15.0,
                "dam_height_m": 10.0,
                "storage_m3": 500000.0,
                "crest_elevation_m": 650.0,
                "bed_elevation_m": 640.0,
                "spillway_capacity_m3s": 1200.0,
                "initial_storage_fraction": 0.90,
            }
        ],
        "celerity_m_s": 5.0,
        "attenuation_rate_per_km": 0.005,
    }

    resp = await client.post("/api/v1/cascade/evaluate", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["scenario_id"] == "test_cascade_reach"
    assert data["total_dams_evaluated"] == 1
    assert "status_label" in data
    assert "NOT RUN on Ganga" in data["status_label"]
    assert len(data["links"]) == 1

    link = data["links"][0]
    assert link["dam_id"] == "dam_downstream_small"
    # Flood volume arriving from 5000 m3/s over 3 hours into a 500,000 m3 pool triggers overtopping!
    assert link["overtopped"] is True
    assert link["verdict"] == "overtopped"
