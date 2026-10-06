"""FastAPI authentication dependencies and RBAC permission guards (Phase 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from backend.app.core.security import decode_token
from backend.app.db.session import get_db
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
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate current authenticated user from JWT token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Bearer token required.",
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
