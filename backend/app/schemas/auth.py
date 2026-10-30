"""Authentication and user schemas (Phase 7)."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, Field

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=8)
    full_name: str = ""
    role: Literal["admin", "analyst", "viewer"] = "analyst"


class UserResponse(BaseModel):
    """User account response without sensitive fields."""

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    presentation_mode: bool = True
    created_at: datetime.datetime


class UserPreferencesUpdate(BaseModel):
    """User preferences update payload."""

    presentation_mode: bool


class LoginRequest(BaseModel):
    """Login credentials payload."""

    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Payload to refresh an expired access token."""

    refresh_token: str


class ApiKeyCreate(BaseModel):
    """Payload to generate a new API key."""

    name: str = Field(..., min_length=1, max_length=128)
    role: Literal["admin", "analyst", "viewer"] | None = None
    expires_in_days: int | None = None


class ApiKeyResponse(BaseModel):
    """API key metadata without raw key."""

    id: str
    prefix: str
    name: str
    role: str
    is_active: bool
    created_at: datetime.datetime
    expires_at: datetime.datetime | None


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Response returned upon key creation, containing the raw plaintext key once."""

    raw_key: str
