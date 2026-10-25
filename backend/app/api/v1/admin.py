"""Administrative user and role management endpoints (B4 Feature F22)."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.app.core.audit import log_audit_event
from backend.app.core.auth import require_admin
from backend.app.core.security import hash_password
from backend.app.db.session import get_db
from backend.app.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])


EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class AdminUserCreate(BaseModel):
    """Payload to provision a user account via admin console."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=8)
    role: str = Field("analyst", pattern="^(admin|analyst|viewer)$")
    full_name: str = ""
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    """Payload to modify user role, permissions, or activation status."""

    full_name: str | None = None
    role: str | None = Field(None, pattern="^(admin|analyst|viewer)$")
    is_active: bool | None = None


class AdminUserResponse(BaseModel):
    """User account details returned to administrators."""

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    mfa_enabled: bool
    created_at: datetime.datetime


def _user_to_admin_response(u: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        is_active=u.is_active,
        mfa_enabled=bool(u.mfa_enabled),
        created_at=u.created_at,
    )


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users_admin(
    role: str | None = Query(None, pattern="^(admin|analyst|viewer)$"),
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> list[AdminUserResponse]:
    """List registered users with optional role and status filters (admin-only)."""
    stmt = select(User).order_by(User.created_at.desc())
    if role:
        stmt = stmt.where(User.role == role)
    if active_only:
        stmt = stmt.where(User.is_active == True)  # noqa: E712

    res = await db.execute(stmt)
    users = res.scalars().all()
    return [_user_to_admin_response(u) for u in users]


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    payload: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """Create a new user with administrative assignment of role (admin-only)."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists.",
        )

    user = User(
        id=str(uuid.uuid4()),
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=payload.is_active,
        mfa_enabled=False,
    )
    db.add(user)
    await db.flush()

    await log_audit_event(
        db,
        action="user.create",
        resource_type="user",
        resource_id=user.id,
        user_id=admin_user.id,
        details={"email": user.email, "role": user.role},
    )

    return _user_to_admin_response(user)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user_admin(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """Retrieve details for a specific user (admin-only)."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )
    return _user_to_admin_response(user)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user_admin(
    user_id: str,
    payload: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """Update role, active state, or profile for a user (admin-only)."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    changes: dict[str, Any] = {}
    if payload.full_name is not None:
        user.full_name = payload.full_name
        changes["full_name"] = payload.full_name
    if payload.role is not None:
        user.role = payload.role
        changes["role"] = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
        changes["is_active"] = payload.is_active

    await db.flush()

    await log_audit_event(
        db,
        action="user.update",
        resource_type="user",
        resource_id=user.id,
        user_id=admin_user.id,
        details=changes,
    )

    return _user_to_admin_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> None:
    """Deactivate or remove a user account (admin-only)."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own active account.",
        )

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    user.is_active = False
    await db.flush()

    await log_audit_event(
        db,
        action="user.deactivate",
        resource_type="user",
        resource_id=user.id,
        user_id=admin_user.id,
    )
