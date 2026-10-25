"""Unit tests for F15 batch mode simulation queue (B4 Missing Features)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.conftest import get_auth_headers

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_batch_create_and_status_json(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    payload = {
        "name": "Himalayan Cascade Study",
        "template_tier": "tier0",
        "breach_equation": "froehlich_2008",
        "manning_n": 0.035,
        "dams": [
            {
                "name": "Dam Alpha",
                "height_m": 45.0,
                "volume_m3": 12000000.0,
                "lat": 30.12,
                "lon": 78.35,
                "river": "Bhagirathi",
            },
            {
                "name": "Dam Beta",
                "height_m": 30.0,
                "volume_m3": 4500000.0,
                "lat": 30.08,
                "lon": 78.28,
                "river": "Alaknanda",
            },
        ],
    }

    create_resp = await client.post("/api/v1/batches", json=payload, headers=headers)
    assert create_resp.status_code == 202
    data = create_resp.json()
    assert data["total_dams"] == 2
    assert len(data["queued_runs"]) == 2
    batch_id = data["batch_id"]

    # Check status
    status_resp = await client.get(f"/api/v1/batches/{batch_id}", headers=headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["batch_id"] == batch_id
    assert status_data["total_dams"] == 2
    assert status_data["status"] == "queued"
    assert len(status_data["runs"]) == 2


@pytest.mark.asyncio
async def test_batch_create_csv(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    csv_data = """dam_name,height_m,volume_m3,latitude,longitude,river
Dam Gamma,50.0,8000000.0,30.20,78.40,Ganga
Dam Delta,25.0,3000000.0,30.15,78.30,Ganga
"""

    payload = {
        "name": "CSV Batch Ingestion",
        "csv_data": csv_data,
    }

    resp = await client.post("/api/v1/batches", json=payload, headers=headers)
    assert resp.status_code == 202
    data = resp.json()
    assert data["total_dams"] == 2
    assert len(data["queued_runs"]) == 2
    assert data["queued_runs"][0]["dam_name"] == "Dam Gamma"
    assert data["queued_runs"][1]["dam_name"] == "Dam Delta"
