"""Unit tests for F20 operational system health monitoring (B4 Missing Features)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_system_health_detailed_endpoint(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/system/health/detailed")
    assert resp.status_code == 200
    data = resp.json()

    assert "status" in data
    assert "database" in data
    assert "broker" in data
    assert "queue_depth" in data["broker"]
    assert "workers" in data
    assert "storage" in data
    assert "disk" in data
    assert "total_gb" in data["disk"]
    assert "free_gb" in data["disk"]
    assert "percent_used" in data["disk"]
    assert "checked_at" in data
    assert "version" in data
