"""FastAPI authentication dependencies and RBAC permission guards (Phase 7)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Literal

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from backend.app.core.security import decode_token, hash_api_key
from backend.app.db.session import get_db
from backend.app.models.api_key import ApiKey
from backend.app.models.user import User
from pravahx.errors import CredentialsError, TokenExpiredError

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

ROLE_LEVELS: dict[str, int] = {
    "viewer": 1,
    "analyst": 2,
    "admin": 3,
}


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate current authenticated user from JWT token or API key."""
    # 1. API key authentication via X-API-Key or Bearer pvx_
    api_key_str = x_api_key or (token if (token and token.startswith("pvx_")) else None)
    if api_key_str:
        h = hash_api_key(api_key_str)
        now = datetime.datetime.now(datetime.UTC)
        res = await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == h,
                ApiKey.is_active == True,  # noqa: E712
            )
        )
        key_obj = res.scalar_one_or_none()
        if key_obj is None or (key_obj.expires_at and key_obj.expires_at < now):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        u_res = await db.execute(select(User).where(User.id == key_obj.user_id))
        user = u_res.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account inactive or not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if key_obj.role:
            user.role = key_obj.role
        return user

    # 2. JWT Bearer token authentication
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Bearer token or X-API-Key required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except CredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Extract authenticated user if token or API key provided, else return None without 401."""
    api_key_str = x_api_key or (token if (token and token.startswith("pvx_")) else None)
    if api_key_str:
        try:
            h = hash_api_key(api_key_str)
            now = datetime.datetime.now(datetime.UTC)
            res = await db.execute(
                select(ApiKey).where(
                    ApiKey.key_hash == h,
                    ApiKey.is_active == True,  # noqa: E712
                )
            )
            key_obj = res.scalar_one_or_none()
            if key_obj and (not key_obj.expires_at or key_obj.expires_at >= now):
                u_res = await db.execute(select(User).where(User.id == key_obj.user_id))
                user = u_res.scalar_one_or_none()
                if user and user.is_active:
                    if key_obj.role:
                        user.role = key_obj.role
                    return user
        except Exception:
            return None

    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user if user and user.is_active else None
    except Exception:
        return None


def require_role(min_role: Literal["viewer", "analyst", "admin"]) -> Callable[..., Any]:
    """Dependency factory checking minimum RBAC role level."""

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_LEVELS.get(user.role, 0)
        required_level = ROLE_LEVELS.get(min_role, 99)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Minimum role required: '{min_role}'.",
            )
        return user

    return role_checker


require_viewer = require_role("viewer")
require_analyst = require_role("analyst")
require_admin = require_role("admin")
