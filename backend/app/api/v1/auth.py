"""Authentication API endpoints (Phase 7)."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from backend.app.core.audit import log_audit_event
from backend.app.core.auth import get_current_user, require_analyst
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.models.api_key import ApiKey
from backend.app.models.user import User
from backend.app.schemas.auth import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
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
        is_active=True,
    )
    db.add(user)
    await db.flush()

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/token", response_model=TokenResponse)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with username/password and receive JWT tokens."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
        )

    access_tok = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    refresh_tok = create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_tok,
        refresh_token=refresh_tok,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token pair."""
    try:
        data = decode_token(payload.refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    if data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: refresh token required.",
        )

    user_id = data.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    access_tok = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    refresh_tok = create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_tok,
        refresh_token=refresh_tok,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return profile information for the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post(
    "/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key_endpoint(
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> ApiKeyCreatedResponse:
    """Create a new programmatic API key."""
    raw_key, prefix, key_hash = generate_api_key()
    key_id = str(uuid.uuid4())
    assigned_role = payload.role or current_user.role

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=payload.expires_in_days
        )

    api_key_obj = ApiKey(
        id=key_id,
        prefix=prefix,
        key_hash=key_hash,
        name=payload.name,
        user_id=current_user.id,
        role=assigned_role,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(api_key_obj)
    await db.flush()

    await log_audit_event(
        db,
        action="apikey.create",
        resource_type="api_key",
        resource_id=key_id,
        user_id=current_user.id,
        details={"name": payload.name, "prefix": prefix, "role": assigned_role},
    )

    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        prefix=api_key_obj.prefix,
        name=api_key_obj.name,
        role=api_key_obj.role,
        is_active=api_key_obj.is_active,
        created_at=api_key_obj.created_at,
        expires_at=api_key_obj.expires_at,
        raw_key=raw_key,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApiKeyResponse]:
    """List active API keys for the current user."""
    query = (
        select(ApiKey)
        .where(
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True,  # noqa: E712
        )
        .order_by(ApiKey.created_at.desc())
    )
    res = await db.execute(query)
    keys = res.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            prefix=k.prefix,
            name=k.name,
            role=k.role,
            is_active=k.is_active,
            created_at=k.created_at,
            expires_at=k.expires_at,
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key_endpoint(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Revoke an API key."""
    query = select(ApiKey).where(ApiKey.id == key_id)
    if current_user.role != "admin":
        query = query.where(ApiKey.user_id == current_user.id)

    res = await db.execute(query)
    key_obj = res.scalar_one_or_none()
    if key_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_id}' not found.",
        )

    key_obj.is_active = False
    await db.flush()

    await log_audit_event(
        db,
        action="apikey.revoke",
        resource_type="api_key",
        resource_id=key_id,
        user_id=current_user.id,
    )
