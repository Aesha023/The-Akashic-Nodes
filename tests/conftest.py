from __future__ import annotations

from typing import TYPE_CHECKING

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

app = create_app()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous HTTP test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


async def get_auth_headers(client: AsyncClient, role: str = "analyst") -> dict[str, str]:
    """Register and login a real user in the database to generate authenticated headers."""
    import uuid

    email = f"user_{role}_{uuid.uuid4().hex[:8]}@pravahx.in"
    password = "ValidPassword123!"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
