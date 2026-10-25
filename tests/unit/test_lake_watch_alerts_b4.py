"""Unit tests for F16 lake watch and F17 alert dispatch (B4 Missing Features)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from backend.app.core.alerts import AlertDispatcher
from tests.conftest import get_auth_headers

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_alert_dispatcher_webhook_mock() -> None:
    dispatcher = AlertDispatcher(webhook_url="http://mock-alert-server.local/webhook")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        success, code, err = await dispatcher.send_webhook({"alert": "test", "val": 42})
        assert success is True
        assert code == 200
        assert err is None


def test_alert_dispatcher_email_mock() -> None:
    dispatcher = AlertDispatcher(
        email_to="emergency@gov.in",
        email_from="pravahx@internal.local",
        smtp_host="localhost",
        smtp_port=1025,
    )

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        success, err = dispatcher.send_email(
            subject="Flash Flood Risk", body_text="Warning message"
        )
        assert success is True
        assert err is None
        assert mock_server.send_message.called


@pytest.mark.asyncio
async def test_lake_watch_evaluate_and_trigger_alert(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    base_time = datetime.datetime(2026, 6, 1, 0, 0, tzinfo=datetime.UTC)
    t1 = base_time.isoformat()
    t2 = (base_time + datetime.timedelta(days=15)).isoformat()

    # Rapid expansion from 1.0 km2 to 1.30 km2 (+30%)
    payload = {
        "lake_id": "lake_chorabari_test",
        "lake_name": "Chorabari Glacial Lake",
        "lake_type": "glacial",
        "observations": [
            {
                "observed_at": t1,
                "water_area_m2": 1000000.0,
                "water_area_km2": 1.0,
                "sensor_platform": "Sentinel-2",
            },
            {
                "observed_at": t2,
                "water_area_m2": 1300000.0,
                "water_area_km2": 1.30,
                "sensor_platform": "Sentinel-2",
            },
        ],
        "dispatch_alerts": True,
        "webhook_url": "http://mock-alerts.local/webhook",
    }

    with patch.object(
        AlertDispatcher,
        "send_webhook",
        return_value=(True, 200, None),
    ):
        resp = await client.post("/api/v1/lake-watch/evaluate", json=payload, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["status"] == "RAPID_EXPANSION_WARNING"
        assert data["summary"]["area_change_percent"] == 30.0
        assert data["alert_dispatched"] is True
        assert data["alert_details"]["webhook"]["success"] is True


@pytest.mark.asyncio
async def test_alert_test_endpoint(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    resp = await client.post(
        "/api/v1/alerts/test",
        json={"title": "Verification Alert", "details": {"probe": "health"}},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Verification Alert"
    assert data["event_type"] == "SYSTEM_TEST_ALERT"
