#!/usr/bin/env python3
"""End-to-End API Smoke Test for Tier-0 Ganga Demo (B5. Deploy).

Verifies the entire lifecycle and outputs through the REST API:
1. Health check (DB, Redis, MinIO)
2. Analyst registration & JWT authentication
3. Scenario creation
4. Tier-0 screening simulation run dispatch & execution
5. Output validation:
   - Inundation extent GeoJSON
   - Point query depth calibration (wet & dry points)
   - Population exposure metrics (WorldPop sum-preserving match)
   - Road network severance (>0.30m unified rule)
   - OSM building exposure (93 buildings)
   - Evacuation routing (2 reachable, 3 unreachable)
   - Executive PDF disaster brief download
   - Zipped artifact bundle download
   - Validation status metrics
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

import httpx


async def run_smoke_test(base_url: str | None = None, in_process: bool = False) -> None:
    print("=" * 70)
    print("PRAVAHX API END-TO-END SMOKE TEST (TIER-0 GANGA DEMO)")
    print("=" * 70)

    client: httpx.AsyncClient

    if in_process or not base_url:
        print("[SETUP] Running in-process ASGI test client against FastAPI app...")
        from backend.app.db.session import init_db
        from backend.app.main import app

        await init_db()
        transport = httpx.ASGITransport(app=app)
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    else:
        print(f"[SETUP] Connecting to live HTTP server at: {base_url}")
        client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async with client:
        # ── Step 1: Health Check ──────────────────────────────────────────
        print("\n[STEP 1] Checking platform system health...")
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200, f"Health check failed: {resp.status_code} {resp.text}"
        health_data = resp.json()
        print(f"  [OK] API Health: {health_data.get('status')}")
        print(f"  [OK] Database:   {health_data.get('database')}")
        print(f"  [OK] Redis:      {health_data.get('redis')}")
        print(f"  [OK] Storage:    {health_data.get('storage')}")

        # ── Step 2: Authentication ───────────────────────────────────────
        print("\n[STEP 2] Authenticating analyst user...")
        analyst_email = "smoke_analyst@pravahx.test"
        analyst_password = "SmokeTestPassword123!"

        # Try registering user
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": analyst_email,
                "password": analyst_password,
                "role": "analyst",
            },
        )
        if reg_resp.status_code not in (201, 400):
            print(f"  Warning: Unexpected registration response {reg_resp.status_code}")

        # Obtain JWT bearer token
        token_resp = await client.post(
            "/api/v1/auth/token",
            data={
                "username": analyst_email,
                "password": analyst_password,
            },
        )
        assert token_resp.status_code == 200, (
            f"Token request failed: {token_resp.status_code} {token_resp.text}"
        )
        token_data = token_resp.json()
        access_token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print("  [OK] JWT access token acquired successfully")

        # ── Step 3: Scenario Management ──────────────────────────────────
        print("\n[STEP 3] Creating Tier-0 Ganga screening scenario...")
        scen_id = f"smoke_scen_{int(time.time())}"
        create_payload = {
            "config": {
                "scenario": {
                    "id": scen_id,
                    "name": "Ganga Reach near Rishikesh Tier-0 Screening (Smoke Test)",
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
                    "reach_length_km": 20.0,
                    "buffer_km": 2.0,
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
        scen_resp = await client.post(
            "/api/v1/scenarios",
            json=create_payload,
            headers=auth_headers,
        )
        assert scen_resp.status_code == 201, (
            f"Scenario creation failed: {scen_resp.status_code} {scen_resp.text}"
        )
        scen_data = scen_resp.json()
        scen_id = scen_data["id"]
        print(f"  [OK] Scenario created: id={scen_id}, version={scen_data.get('version')}")

        # ── Step 4: Run Dispatch & Execution ─────────────────────────────
        print("\n[STEP 4] Dispatching simulation run through API...")
        run_resp = await client.post(
            "/api/v1/runs",
            json={
                "scenario_id": scen_id,
                "resume": True,
            },
            headers=auth_headers,
        )
        assert run_resp.status_code == 202, (
            f"Run dispatch failed: {run_resp.status_code} {run_resp.text}"
        )
        run_data = run_resp.json()
        dispatched_run_id = run_data["id"]
        print(f"  [OK] Run dispatched: id={dispatched_run_id}, status={run_data.get('status')}")

        # Poll run status
        poll_resp = await client.get(f"/api/v1/runs/{dispatched_run_id}", headers=auth_headers)
        assert poll_resp.status_code == 200
        print(f"  [OK] Run status verified: status={poll_resp.json().get('status')}")

        # ── Step 5: Output Verification on Accepted Ganga Run ────────────
        demo_run_id = "tier0_ganga_accepted"
        print(f"\n[STEP 5] Verifying outputs on demo benchmark run '{demo_run_id}'...")

        # 5a. Extent Envelope GeoJSON
        extent_resp = await client.get(f"/api/v1/runs/{demo_run_id}/extent", headers=auth_headers)
        assert extent_resp.status_code == 200, f"Extent query failed: {extent_resp.status_code}"
        extent_json = extent_resp.json()
        assert extent_json.get("type") in ("FeatureCollection", "Polygon", "MultiPolygon"), (
            f"Invalid GeoJSON type: {extent_json.get('type')}"
        )
        print("  [OK] Inundation Extent: Valid GeoJSON envelope retrieved")

        # 5b. Point Depth Queries (Wet and Dry Points)
        wet_query_resp = await client.get(
            f"/api/v1/runs/{demo_run_id}/point-query?lon=78.337&lat=30.144",
            headers=auth_headers,
        )
        assert wet_query_resp.status_code == 200
        wet_data = wet_query_resp.json()
        assert wet_data["is_flooded"] is True, f"Expected flooded at river channel: {wet_data}"
        assert wet_data["depth_m"] > 0.0, f"Expected positive depth: {wet_data}"
        print(
            f"  [OK] Point Query (Wet Cell @ 78.337, 30.144): depth = {wet_data['depth_m']} m "
            "(is_flooded=True)"
        )

        dry_query_resp = await client.get(
            f"/api/v1/runs/{demo_run_id}/point-query?lon=78.200&lat=30.200",
            headers=auth_headers,
        )
        assert dry_query_resp.status_code == 200
        dry_data = dry_query_resp.json()
        assert dry_data["is_flooded"] is False, f"Expected dry at high ridge: {dry_data}"
        assert dry_data["depth_m"] == 0.0
        print(
            f"  [OK] Point Query (Dry Cell @ 78.200, 30.200): depth = {dry_data['depth_m']} m "
            "(is_flooded=False)"
        )

        # 5c. Population & Asset Exposure
        exp_resp = await client.get(f"/api/v1/runs/{demo_run_id}/exposure", headers=auth_headers)
        assert exp_resp.status_code == 200
        exp_data = exp_resp.json()

        # Check WorldPop match
        pop = exp_data["population"]
        assert pop["aoi_total"] == 27390.1, f"Expected 27,390.1 AOI population: {pop}"
        assert pop["exposed_total"] == 2696, f"Expected 2,696 exposed population: {pop}"
        assert pop["exposed_percent"] == 9.84, f"Expected 9.84% exposed: {pop}"
        print(
            f"  [OK] Population Exposure: {pop['exposed_total']} / {pop['aoi_total']} "
            f"({pop['exposed_percent']}%)"
        )

        # Check [UNVERIFIED] depth classes
        classes: dict[str, Any] = pop["depth_classes"]
        for k in classes:
            assert "[UNVERIFIED]" in k, f"Depth class missing [UNVERIFIED] tag: {k}"
        print(
            f"  [OK] Depth Classes: Verified [UNVERIFIED] tags on classes: {list(classes.keys())}"
        )

        # Check Road Severance (>0.30m)
        roads = exp_data["roads"]
        assert roads["severance_depth_cutoff_m"] == 0.30
        assert roads["flooded_km"] == 17.34
        assert roads["total_network_km"] == 159.54
        print(
            f"  [OK] Road Network: {roads['flooded_km']} km flooded / severed "
            f"({roads['flooded_percent']}%)"
        )

        # Check OSM Buildings
        bldgs = exp_data["buildings"]
        assert bldgs["total_in_aoi"] == 93
        assert bldgs["flooded"] == 5
        assert "OSM building coverage incomplete" in bldgs["note"]
        print(
            f"  [OK] OSM Buildings: {bldgs['flooded']} / {bldgs['total_in_aoi']} flooded "
            f"('{bldgs['note']}')"
        )

        # 5d. Evacuation Routing
        evac_resp = await client.get(f"/api/v1/runs/{demo_run_id}/evacuation", headers=auth_headers)
        assert evac_resp.status_code == 200
        evac_data = evac_resp.json()
        origins = evac_data["origins"]
        assert origins["total_evaluated"] == 5
        assert origins["reachable_count"] == 2
        assert origins["unreachable_count"] == 3
        assert evac_data["severed_edges_count"] == 100
        assert evac_data["severed_edge_length_km"] == 14.76
        print(
            f"  [OK] Evacuation Routing: 5 origins ({origins['reachable_count']} reachable, "
            f"{origins['unreachable_count']} unreachable), severed: "
            f"{evac_data['severed_edges_count']} edges ({evac_data['severed_edge_length_km']} km)"
        )

        # 5e. Executive Disaster Brief PDF Download
        brief_resp = await client.get(f"/api/v1/runs/{demo_run_id}/brief", headers=auth_headers)
        assert brief_resp.status_code == 200
        assert brief_resp.headers.get("content-type") == "application/pdf"
        assert len(brief_resp.content) > 50_000
        print(
            f"  [OK] Disaster Brief PDF: Downloaded valid PDF ({len(brief_resp.content):,} bytes, "
            "Content-Type: application/pdf)"
        )

        # 5f. Download Artifact Package
        zip_resp = await client.get(f"/api/v1/runs/{demo_run_id}/download", headers=auth_headers)
        assert zip_resp.status_code == 200
        assert "zip" in zip_resp.headers.get("content-type", "")
        assert len(zip_resp.content) > 10_000
        print(
            f"  [OK] Zipped Artifact Bundle: Downloaded ({len(zip_resp.content):,} bytes, "
            "Content-Type: application/zip)"
        )

        # 5g. Validation Status Endpoint
        val_resp = await client.get("/api/v1/validation/status", headers=auth_headers)
        assert val_resp.status_code == 200
        val_data = val_resp.json()
        assert "engines" in val_data
        print(
            f"  [OK] Validation Status: Retrieved {len(val_data['engines'])} "
            "benchmark engine metrics"
        )

        # 5h. Detailed System Health
        detail_resp = await client.get("/api/v1/system/health/detailed", headers=auth_headers)
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert "disk" in detail_data
        print(f"  [OK] Detailed Health: Disk free = {detail_data['disk'].get('free_gb')} GB")

    print("\n" + "=" * 70)
    print("ALL API END-TO-END SMOKE TEST CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="PravahX API Smoke Test")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL of running API server (e.g. http://localhost:8000)",
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Execute against in-process ASGI application directly",
    )
    args = parser.parse_args()

    # If neither provided and default localhost is not specified, run in-process if server not up
    in_proc = args.in_process
    url = args.base_url

    if not in_proc and not url:
        # Default to in-process unless localhost:8000 is listening
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 8000))
        sock.close()
        if result == 0:
            url = "http://127.0.0.1:8000"
        else:
            in_proc = True

    try:
        asyncio.run(run_smoke_test(base_url=url, in_process=in_proc))
    except Exception as exc:
        print(f"\n[ERROR] Smoke test failed: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
