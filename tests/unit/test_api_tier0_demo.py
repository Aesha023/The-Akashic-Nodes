"""API integration tests for Tier-0 Demo results service endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_tile_endpoint_tier0() -> None:
    """Test rio-tiler tile rendering endpoint for Tier-0 Ganga COG."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Valid tile over Rishikesh Ganga reach at z=14
        res = await client.get("/api/v1/tiles/tier0_ganga/max_depth/14/11756/6753.png")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        assert len(res.content) > 100

        # Out-of-bounds tile returns 200 with empty 256x256 PNG
        res_oob = await client.get("/api/v1/tiles/tier0_ganga/max_depth/14/0/0.png")
        assert res_oob.status_code == 200
        assert res_oob.headers["content-type"] == "image/png"

        # Non-existent layer returns 404
        res_404 = await client.get("/api/v1/tiles/tier0_ganga/nonexistent_layer/14/0/0.png")
        assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_extent_geojson_endpoint() -> None:
    """Test GeoJSON extent endpoint for Tier-0 Ganga inundation envelope."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/runs/tier0_ganga/extent.geojson")
        assert res.status_code == 200
        assert "application/geo+json" in res.headers["content-type"]

        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1
        geom = data["features"][0]["geometry"]
        assert geom["type"] in ("Polygon", "MultiPolygon")


@pytest.mark.asyncio
async def test_point_query_endpoint() -> None:
    """Test point query endpoint at flooded and dry locations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Flooded point in the gorge
        url_flood = "/api/v1/runs/tier0_ganga/point-query?lon=78.33662&lat=30.14439"
        res_flood = await client.get(url_flood)
        assert res_flood.status_code == 200
        data_flood = res_flood.json()
        assert data_flood["run_id"] == "tier0_ganga"
        assert data_flood["scenario_type"] == "hypothetical scenario, Tier-0 screening"
        assert data_flood["is_flooded"] is True
        assert data_flood["depth_m"] > 5.0
        assert data_flood["arrival_time_s"] is None
        assert "arrival time is not simulated" in data_flood["notice"]

        # Dry point on the surrounding mountain ridge
        res_dry = await client.get("/api/v1/runs/tier0_ganga/point-query?lon=78.305&lat=30.145")
        assert res_dry.status_code == 200
        data_dry = res_dry.json()
        assert data_dry["is_flooded"] is False
        assert data_dry["depth_m"] == 0.0
        assert data_dry["arrival_time_s"] is None
        assert "arrival time is not simulated" in data_dry["notice"]


@pytest.mark.asyncio
async def test_run_manifest_and_artifact_downloads() -> None:
    """Test manifest retrieval and file download endpoints for Tier-0 demo."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login analyst for authenticated download
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "demo_analyst@pravahx.in",
                "password": "ValidPassword123!",
                "full_name": "Demo Analyst",
                "role": "analyst",
            },
        )
        tok_res = await client.post(
            "/api/v1/auth/token",
            data={"username": "demo_analyst@pravahx.in", "password": "ValidPassword123!"},
        )
        token = tok_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Manifest
        res_m = await client.get("/api/v1/runs/tier0_ganga/manifest", headers=auth_headers)
        assert res_m.status_code == 200
        m = res_m.json()
        assert m["run_id"] == "tier0_ganga_accepted"
        assert len(m["artifacts"]) >= 6

        # 2. PDF Brief Download
        res_pdf = await client.get(
            "/api/v1/runs/tier0_ganga/artifacts/ganga_tier0_brief.pdf", headers=auth_headers
        )
        assert res_pdf.status_code == 200
        assert "application/pdf" in res_pdf.headers["content-type"]
        assert len(res_pdf.content) > 50_000

        # 3. COG GeoTIFF Download
        res_cog = await client.get(
            "/api/v1/runs/tier0_ganga/artifacts/tier0_max_depth_cog.tif", headers=auth_headers
        )
        assert res_cog.status_code == 200
        assert len(res_cog.content) > 1000
