"""Unit tests for System and Health check endpoints (B2 API Completion)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_system_health_endpoints() -> None:
    """Test /health, /health/live, /health/ready, and /system/info endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Liveness
        res_live = await client.get("/api/v1/health/live")
        assert res_live.status_code == 200
        assert res_live.json() == {"status": "ok"}

        # Readiness
        res_ready = await client.get("/api/v1/health/ready")
        assert res_ready.status_code == 200
        data_ready = res_ready.json()
        assert data_ready["status"] in ("ready", "unhealthy")
        assert "database" in data_ready

        # Comprehensive Health
        res_health = await client.get("/api/v1/health")
        assert res_health.status_code == 200
        data_health = res_health.json()
        assert "status" in data_health
        assert "database" in data_health
        assert "broker" in data_health
        assert "storage" in data_health
        assert "version" in data_health

        # System info
        res_info = await client.get("/api/v1/system/info")
        assert res_info.status_code == 200
        data_info = res_info.json()
        assert "version" in data_info
        assert "python_version" in data_info
