"""Unit tests for F18 data catalogue and validated upload API (B4 Missing Features)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.conftest import get_auth_headers

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_data_catalogue_listing(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/data/catalog")
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) >= 6

    # Verify WorldPop dataset checksum and provenance
    worldpop = next((d for d in datasets if d["dataset_id"] == "worldpop-ind-100m-2020"), None)
    assert worldpop is not None
    assert worldpop["sha256"] == "645851494924c58f000da2bb100fa1b614d9b23b49c065e1823eb2e5d9575d27"
    assert "WorldPop" in worldpop["attribution"]
    assert worldpop["licence"] == "CC-BY 4.0"

    # Verify Copernicus DEM
    dem = next((d for d in datasets if d["dataset_id"] == "copernicus-dem-glo30"), None)
    assert dem is not None
    assert dem["category"] == "elevation"


@pytest.mark.asyncio
async def test_data_catalogue_single_item(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/data/catalog/copernicus-dem-glo30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dataset_id"] == "copernicus-dem-glo30"
    assert "Copernicus" in data["name"]

    # Not found case
    not_found = await client.get("/api/v1/data/catalog/non-existent-dataset")
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_data_catalogue_upload_validation(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    # Valid GeoTIFF upload
    files = {"file": ("test_extent.tif", b"\x49\x49\x2a\x00\x08\x00\x00\x00", "image/tiff")}
    resp = await client.post("/api/v1/data/catalog/validate-upload", files=files, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["format"] == "GeoTIFF"
    assert "sha256" in data

    # Unsupported format upload
    bad_files = {"file": ("invalid_data.exe", b"binarycontent", "application/octet-stream")}
    bad_resp = await client.post(
        "/api/v1/data/catalog/validate-upload", files=bad_files, headers=headers
    )
    assert bad_resp.status_code == 400
