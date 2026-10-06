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
    created_at: datetime.datetime


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
