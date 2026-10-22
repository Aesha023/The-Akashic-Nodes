"""Integration test for Run Lifecycle API and Result Protection Gate (B1. Platform Core)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.db.session import sync_session_factory
from backend.app.main import app
from backend.app.models.run import Run
from backend.app.models.scenario import Scenario
from backend.app.models.user import User


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    user_id = "user_lifecycle_analyst"
    with sync_session_factory() as session:
        user = session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                email="lifecycle_analyst@pravahx.test",
                hashed_password="mock_hashed_password",
                role="analyst",
                is_active=True,
            )
            session.add(user)
            session.commit()
    token = create_access_token(
        data={"sub": user_id, "email": "lifecycle_analyst@pravahx.test", "role": "analyst"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def setup_scenario() -> str:
    scenario_id = "scen_lifecycle_test_01"
    with sync_session_factory() as session:
        scen = session.get(Scenario, scenario_id)
        if not scen:
            scen = Scenario(
                id=scenario_id,
                name="Lifecycle Test Scenario",
                scenario_type="tier0_screening",
                config_json='{"name": "test"}',
            )
            session.add(scen)
            session.commit()
    return scenario_id


@pytest.mark.integration
def test_run_create_and_status(
    test_client: TestClient,
    auth_headers: dict[str, str],
    setup_scenario: str,
) -> None:
    """Test run dispatch and status retrieval."""
    resp = test_client.post(
        "/api/v1/runs",
        json={"scenario_id": setup_scenario, "resume": True},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "id" in data
    assert data["scenario_id"] == setup_scenario
    assert data["is_valid"] is True

    run_id = data["id"]
    status_resp = test_client.get(f"/api/v1/runs/{run_id}", headers=auth_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == run_id


@pytest.mark.integration
def test_run_cancel_and_retry(
    test_client: TestClient,
    auth_headers: dict[str, str],
    setup_scenario: str,
) -> None:
    """Test cancelling a running job and retrying it."""
    # Seed a running run directly in DB
    run_id = "run_to_cancel_01"
    with sync_session_factory() as session:
        run = Run(
            id=run_id,
            scenario_id=setup_scenario,
            status="running",
            progress_percent=25.0,
            current_stage="rating_curve",
            work_dir="./runs/cancel_test",
            is_valid=True,
        )
        session.merge(run)
        session.commit()

    # Cancel
    cancel_resp = test_client.post(f"/api/v1/runs/{run_id}/cancel", headers=auth_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Retry
    retry_resp = test_client.post(f"/api/v1/runs/{run_id}/retry", headers=auth_headers)
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] in ("running", "succeeded", "failed")


@pytest.mark.integration
def test_run_sse_and_websocket(test_client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test SSE event stream and WebSocket endpoint for simulation progress."""
    # SSE
    sse_resp = test_client.get("/api/v1/runs/tier0_ganga/events")
    assert sse_resp.status_code == 200
    assert "text/event-stream" in sse_resp.headers["content-type"]
    assert "event: progress" in sse_resp.text

    # WebSocket
    with test_client.websocket_connect("/api/v1/runs/tier0_ganga/ws") as ws:
        msg = ws.receive_json()
        assert msg["run_id"] == "tier0_ganga"
        assert msg["status"] == "succeeded"


@pytest.mark.integration
def test_result_protection_gate(
    test_client: TestClient,
    auth_headers: dict[str, str],
    setup_scenario: str,
) -> None:
    """CRITICAL TEST: Failed or INVALID runs must NEVER be served as results (B1)."""
    # 1. Seed a FAILED run
    failed_id = "run_gate_failed_01"
    with sync_session_factory() as session:
        failed_run = Run(
            id=failed_id,
            scenario_id=setup_scenario,
            status="failed",
            progress_percent=40.0,
            current_stage="diverged",
            error_message="Simulation diverged at step 104",
            work_dir="./runs/failed_run",
            is_valid=True,
        )
        session.merge(failed_run)
        session.commit()

    # Querying results on failed run must return 400 Bad Request
    extent_resp = test_client.get(f"/api/v1/runs/{failed_id}/extent")
    assert extent_resp.status_code == 400
    assert "Results unavailable" in extent_resp.json()["detail"]
    assert "failed" in extent_resp.json()["detail"]

    point_resp = test_client.get(f"/api/v1/runs/{failed_id}/point-query?lon=78.32&lat=30.12")
    assert point_resp.status_code == 400
    assert "Results unavailable" in point_resp.json()["detail"]

    manifest_resp = test_client.get(f"/api/v1/runs/{failed_id}/manifest", headers=auth_headers)
    assert manifest_resp.status_code == 400

    art_resp = test_client.get(f"/api/v1/runs/{failed_id}/artifacts/test.tif", headers=auth_headers)
    assert art_resp.status_code == 400

    # 2. Seed an INVALID run (even if status is marked succeeded)
    invalid_id = "run_gate_invalid_02"
    with sync_session_factory() as session:
        invalid_run = Run(
            id=invalid_id,
            scenario_id=setup_scenario,
            status="succeeded",
            progress_percent=100.0,
            current_stage="completed",
            work_dir="./runs/invalid_run",
            is_valid=False,  # Marked invalid by QC / validation check
        )
        session.merge(invalid_run)
        session.commit()

    invalid_extent = test_client.get(f"/api/v1/runs/{invalid_id}/extent")
    assert invalid_extent.status_code == 400
    assert "valid: False" in invalid_extent.json()["detail"]

    invalid_point = test_client.get(f"/api/v1/runs/{invalid_id}/point-query?lon=78.32&lat=30.12")
    assert invalid_point.status_code == 400
    assert "valid: False" in invalid_point.json()["detail"]
