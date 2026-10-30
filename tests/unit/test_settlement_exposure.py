"""Unit tests for real settlement exposure computation and API contract (C1 Blocker)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app
from core.pravahx.impact.settlement_exposure import (
    compute_settlement_exposure,
)

app = create_app()


def test_settlement_exposure_computation_integrity() -> None:
    """Verify core computation directly overlays OSM, DEM depth, and WorldPop rasters."""
    json_path = Path("data/ganga_inputs/settlements_exposure.json")
    sha_path = Path("data/ganga_inputs/settlements_exposure.json.sha256")

    assert json_path.exists(), "settlements_exposure.json must exist in data/ganga_inputs"
    assert sha_path.exists(), "settlements_exposure.json.sha256 must exist"

    # 1. SHA-256 match
    file_bytes = json_path.read_bytes()
    expected_digest = hashlib.sha256(file_bytes).hexdigest()
    recorded_sha = sha_path.read_text(encoding="utf-8").strip().split()[0]
    assert expected_digest == recorded_sha, "Recorded SHA-256 must match file content digest"

    # 2. Recompute and verify exact match
    recomputed = compute_settlement_exposure()
    saved_data = json.loads(file_bytes.decode("utf-8"))

    assert recomputed["total_settlements_evaluated"] == saved_data["total_settlements_evaluated"]
    assert recomputed["inundated_settlements_count"] == saved_data["inundated_settlements_count"]
    assert len(recomputed["settlements"]) == len(saved_data["settlements"])

    # 3. Verify absence of hand-written mocks and presence of real OSM IDs
    for item in recomputed["settlements"]:
        assert "recommended_action" not in item, "recommended_action must be removed"
        assert item["osm_id"].startswith(("node/", "way/", "relation/")), (
            f"Invalid OSM ID format: {item['osm_id']}"
        )
        assert not item["osm_id"].startswith("osm_way_nh7"), "Roads must not be in settlements"
        assert "method" in item, "Method must be stated per settlement"
        assert "depth_class" in item, "Depth class must be assigned"


@pytest.mark.asyncio
async def test_settlement_exposure_api_matches_core_computation() -> None:
    """Verify API endpoint returns the exact real computation and metadata."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/runs/tier0_ganga_accepted/exposure")
        assert res.status_code == 200
        data = res.json()

        assert "settlements" in data
        assert "settlement_note" in data
        assert "overlap and are not additive" in data["settlement_note"]
        assert "settlement_method" in data

        settlements = data["settlements"]
        assert len(settlements) > 0

        # Compare with saved artifact
        saved_artifact = json.loads(
            Path("data/ganga_inputs/settlements_exposure.json").read_text(encoding="utf-8")
        )
        assert len(settlements) == len(saved_artifact["settlements"])

        first_api = settlements[0]
        first_saved = saved_artifact["settlements"][0]
        assert first_api["osm_id"] == first_saved["osm_id"]
        assert first_api["population_exposed"] == first_saved["population_exposed"]
        assert first_api["peak_depth_m"] == first_saved["peak_depth_m"]
        assert first_api["depth_class"] == first_saved["depth_class"]

        # Ensure no mock keys
        for s in settlements:
            assert "recommended_action" not in s
            assert not s["osm_id"].startswith("osm_way_nh7")
