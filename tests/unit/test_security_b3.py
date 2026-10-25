"""Unit tests for Security, RBAC, API Keys, Audit Hash Chain, and Share Links (B3)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.core.audit import verify_audit_chain
from backend.app.core.rate_limit import SlidingWindowRateLimiter
from backend.app.db.session import get_db
from backend.app.main import create_app
from backend.app.models.audit import AuditLogEntry

app = create_app()


@pytest.mark.asyncio
async def test_role_based_access_control() -> None:
    """Verify role-based access control (admin / analyst / viewer) across endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create viewer user
        v_email = f"viewer_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": v_email, "password": "Password123!", "role": "viewer"},
        )
        v_tok = (
            await client.post(
                "/api/v1/auth/token",
                data={"username": v_email, "password": "Password123!"},
            )
        ).json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {v_tok}"}

        # Create analyst user
        a_email = f"analyst_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": a_email, "password": "Password123!", "role": "analyst"},
        )
        a_tok = (
            await client.post(
                "/api/v1/auth/token",
                data={"username": a_email, "password": "Password123!"},
            )
        ).json()["access_token"]
        analyst_headers = {"Authorization": f"Bearer {a_tok}"}

        # Create admin user
        adm_email = f"admin_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": adm_email, "password": "Password123!", "role": "admin"},
        )
        adm_tok = (
            await client.post(
                "/api/v1/auth/token",
                data={"username": adm_email, "password": "Password123!"},
            )
        ).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {adm_tok}"}

        # 1. Viewer trying to create scenario -> 403 Forbidden
        scen_id = f"scen_rbac_{uuid.uuid4().hex[:8]}"
        payload = {
            "config": {
                "scenario": {
                    "id": scen_id,
                    "name": "RBAC Test",
                    "type": "dam_break",
                    "failure_mode": "overtopping",
                },
                "source": {
                    "point": [78.0, 25.0],
                    "dam_height_m": 30.0,
                    "storage_m3": 50000000.0,
                    "volume_method": "user",
                },
                "domain": {"reach_length_km": 40.0, "buffer_km": 3.0},
                "inputs": {"dem": "copernicus_glo30", "landcover": "worldcover"},
                "breach": {
                    "method": "froehlich_2008",
                    "ensemble": ["p50"],
                    "width_uncertainty_factor": 0.3,
                    "time_uncertainty_factor": 0.3,
                },
                "tiers": {"tier0": {"enabled": True}},
            }
        }
        res_v_create = await client.post("/api/v1/scenarios", json=payload, headers=viewer_headers)
        assert res_v_create.status_code == 403
        assert "Minimum role required: 'analyst'" in res_v_create.json()["detail"]

        # 2. Analyst creating scenario -> 201 Created
        res_a_create = await client.post("/api/v1/scenarios", json=payload, headers=analyst_headers)
        assert res_a_create.status_code == 201

        # 3. Viewer and Analyst trying to access audit log -> 403 Forbidden
        res_v_audit = await client.get("/api/v1/audit/logs", headers=viewer_headers)
        assert res_v_audit.status_code == 403

        res_a_audit = await client.get("/api/v1/audit/logs", headers=analyst_headers)
        assert res_a_audit.status_code == 403

        # 4. Admin accessing audit log -> 200 OK
        res_adm_audit = await client.get("/api/v1/audit/logs", headers=admin_headers)
        assert res_adm_audit.status_code == 200
        assert res_adm_audit.json()["total"] >= 1


@pytest.mark.asyncio
async def test_api_key_lifecycle_and_authentication() -> None:
    """Test API key creation, authentication, listing, and revocation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login an analyst
        email = f"apikey_user_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!", "role": "analyst"},
        )
        login_res = await client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": "Password123!"},
        )
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Create API key
        key_create_payload = {"name": "CI Service Key", "role": "analyst"}
        create_res = await client.post(
            "/api/v1/auth/api-keys", json=key_create_payload, headers=auth_headers
        )
        assert create_res.status_code == 201
        data = create_res.json()
        assert "raw_key" in data
        raw_key = data["raw_key"]
        key_id = data["id"]
        assert raw_key.startswith("pvx_")

        # 2. Use API key via X-API-Key header to authenticate
        api_headers = {"X-API-Key": raw_key}
        me_res = await client.get("/api/v1/auth/me", headers=api_headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == email

        # 3. Use API key via Authorization: Bearer pvx_... header
        bearer_api_headers = {"Authorization": f"Bearer {raw_key}"}
        me_res2 = await client.get("/api/v1/auth/me", headers=bearer_api_headers)
        assert me_res2.status_code == 200
        assert me_res2.json()["email"] == email

        # 4. List API keys
        list_res = await client.get("/api/v1/auth/api-keys", headers=auth_headers)
        assert list_res.status_code == 200
        keys = list_res.json()
        assert any(k["id"] == key_id for k in keys)

        # 5. Revoke API key
        del_res = await client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=auth_headers)
        assert del_res.status_code == 204

        # 6. Authenticating with revoked key must fail with 401
        revoked_res = await client.get("/api/v1/auth/me", headers=api_headers)
        assert revoked_res.status_code == 401
        assert "Invalid or expired API key" in revoked_res.json()["detail"]


@pytest.mark.asyncio
async def test_token_refresh_rotation() -> None:
    """Test JWT token refresh rotation returning a new access token and new refresh token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        email = f"rot_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!", "role": "analyst"},
        )
        tok_res = await client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": "Password123!"},
        )
        tokens1 = tok_res.json()
        refresh_1 = tokens1["refresh_token"]

        # Refresh tokens
        ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
        assert ref_res.status_code == 200
        tokens2 = ref_res.json()
        assert "access_token" in tokens2
        assert "refresh_token" in tokens2
        assert tokens2["access_token"] != tokens1["access_token"]
        assert tokens2["refresh_token"] != refresh_1


@pytest.mark.asyncio
async def test_audit_log_tamper_evident_hash_chain() -> None:
    """Verify cryptographic hash chaining and tamper detection in audit logs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create admin
        adm_email = f"adm_audit_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": adm_email, "password": "Password123!", "role": "admin"},
        )
        adm_tok = (
            await client.post(
                "/api/v1/auth/token",
                data={"username": adm_email, "password": "Password123!"},
            )
        ).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {adm_tok}"}

        # Verify initial valid chain
        verify_res = await client.get("/api/v1/audit/verify", headers=admin_headers)
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["is_valid"] is True
        assert data["failure_reason"] is None

        # Verify tamper detection by tampering an entry in DB
        async for db in get_db():
            # Tamper the latest entry's action
            last_entry = (
                await db.execute(select(AuditLogEntry).order_by(AuditLogEntry.id.desc()).limit(1))
            ).scalar_one_or_none()
            if last_entry is not None:
                original_action = last_entry.action
                last_entry.action = "tampered_action"
                await db.commit()

                # Verify chain fails
                is_valid, _count, reason = await verify_audit_chain(db)
                assert is_valid is False
                assert reason is not None
                assert "Tampered content" in reason

                # Restore original action
                last_entry.action = original_action
                await db.commit()
            break


@pytest.mark.asyncio
async def test_share_links_f23() -> None:
    """Test signed, expiring, read-only share links (F23)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login analyst
        email = f"share_analyst_{uuid.uuid4().hex[:8]}@pravahx.in"
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!", "role": "analyst"},
        )
        tok = (
            await client.post(
                "/api/v1/auth/token",
                data={"username": email, "password": "Password123!"},
            )
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {tok}"}

        # 1. Generate share link for tier0 demo run
        share_res = await client.post(
            "/api/v1/share/runs/tier0_ganga",
            json={"expires_in_hours": 24},
            headers=headers,
        )
        assert share_res.status_code == 200
        share_data = share_res.json()
        assert share_data["run_id"] == "tier0_ganga"
        token = share_data["token"]

        # 2. Access shared run anonymously (no Authorization header)
        view_res = await client.get(f"/api/v1/share/{token}")
        assert view_res.status_code == 200
        view_data = view_res.json()
        assert view_data["run_id"] == "tier0_ganga"
        assert view_data["status"] == "succeeded"
        assert view_data["is_valid"] is True
        assert view_data["max_depth_m"] == 7.73

        # 3. Download shared brief anonymously
        brief_res = await client.get(f"/api/v1/share/{token}/brief")
        assert brief_res.status_code == 200
        assert brief_res.headers["content-type"] == "application/pdf"
        assert len(brief_res.content) > 50000

        # 4. Invalid share token fails with 401
        invalid_res = await client.get("/api/v1/share/invalid_bogus_token")
        assert invalid_res.status_code == 401


@pytest.mark.asyncio
async def test_rate_limiting() -> None:
    """Test sliding window rate limiting returning HTTP 429 when threshold exceeded."""
    SlidingWindowRateLimiter.reset()
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)

    from fastapi import Request

    class DummyClient:
        host = "198.51.100.1"

    scope = {"type": "http", "client": ("198.51.100.1", 12345), "headers": []}
    req = Request(scope)
    req._client = DummyClient()  # type: ignore[attr-defined]

    # First 3 requests succeed
    await limiter(req)
    await limiter(req)
    await limiter(req)

    # 4th request must raise 429
    with pytest.raises(Exception) as exc_info:
        await limiter(req)
    assert exc_info.value.status_code == 429  # type: ignore[attr-defined]
    assert "Rate limit exceeded" in str(exc_info.value.detail)  # type: ignore[attr-defined]
