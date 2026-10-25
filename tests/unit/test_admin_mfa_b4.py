"""Unit tests for F22 admin console and MFA TOTP setup/verify (B4 Missing Features)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyotp
import pytest

from tests.conftest import get_auth_headers

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_user_crud(client: AsyncClient) -> None:
    admin_headers = await get_auth_headers(client, "admin")
    analyst_headers = await get_auth_headers(client, "analyst")

    # 1. Analyst cannot access admin endpoints (RBAC 403)
    forbidden_resp = await client.get("/api/v1/admin/users", headers=analyst_headers)
    assert forbidden_resp.status_code == 403

    # 2. Admin can list users
    list_resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)

    # 3. Admin can create new user
    import uuid

    new_email = f"dr_sharma_{uuid.uuid4().hex[:8]}@cwc.gov.in"
    create_payload = {
        "email": new_email,
        "password": "SecurePassword123!",
        "full_name": "Dr. Sharma",
        "role": "analyst",
    }
    create_resp = await client.post(
        "/api/v1/admin/users", json=create_payload, headers=admin_headers
    )
    assert create_resp.status_code == 201
    user_data = create_resp.json()
    new_user_id = user_data["id"]
    assert user_data["email"] == new_email
    assert user_data["role"] == "analyst"

    # 4. Admin can get specific user
    get_resp = await client.get(f"/api/v1/admin/users/{new_user_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == new_user_id

    # 5. Admin can update user role and profile
    patch_payload = {"role": "viewer", "full_name": "Dr. R. K. Sharma"}
    patch_resp = await client.patch(
        f"/api/v1/admin/users/{new_user_id}", json=patch_payload, headers=admin_headers
    )
    assert patch_resp.status_code == 200
    updated_data = patch_resp.json()
    assert updated_data["role"] == "viewer"
    assert updated_data["full_name"] == "Dr. R. K. Sharma"

    # 6. Admin can deactivate user
    del_resp = await client.delete(f"/api/v1/admin/users/{new_user_id}", headers=admin_headers)
    assert del_resp.status_code == 204

    # Verify deactivated
    verify_resp = await client.get(f"/api/v1/admin/users/{new_user_id}", headers=admin_headers)
    assert verify_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_mfa_setup_and_verify(client: AsyncClient) -> None:
    headers = await get_auth_headers(client, "analyst")

    # 1. Setup MFA
    setup_resp = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup_resp.status_code == 200
    setup_data = setup_resp.json()
    secret = setup_data["secret"]
    assert len(secret) >= 16
    assert "otpauth://" in setup_data["provisioning_uri"]

    # 2. Verify with wrong code -> 400
    bad_resp = await client.post(
        "/api/v1/auth/mfa/verify", json={"code": "000000"}, headers=headers
    )
    assert bad_resp.status_code == 400

    # 3. Generate correct TOTP code using pyotp
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    good_resp = await client.post(
        "/api/v1/auth/mfa/verify", json={"code": valid_code}, headers=headers
    )
    assert good_resp.status_code == 200
    assert good_resp.json()["status"] == "mfa_enabled"
    assert good_resp.json()["mfa_enabled"] is True
