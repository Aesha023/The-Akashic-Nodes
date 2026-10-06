"""Unit tests for Phase 7 security, JWT tokens, and RBAC authentication."""

from __future__ import annotations

import datetime

import pytest

from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from pravahx.errors import CredentialsError, TokenExpiredError


def test_password_hashing() -> None:
    """Test Argon2id password hashing and verification."""
    pwd = "SuperSecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_jwt_token_flow() -> None:
    """Test JWT access token creation and decoding."""
    payload = {"sub": "user_123", "email": "test@pravahx.in", "role": "analyst"}
    token = create_access_token(payload, expires_delta=datetime.timedelta(minutes=5))
    decoded = decode_token(token)

    assert decoded["sub"] == "user_123"
    assert decoded["email"] == "test@pravahx.in"
    assert decoded["role"] == "analyst"
    assert decoded["type"] == "access"


def test_jwt_refresh_token() -> None:
    """Test JWT refresh token creation and decoding."""
    token = create_refresh_token({"sub": "user_123"}, expires_delta=datetime.timedelta(days=1))
    decoded = decode_token(token)

    assert decoded["sub"] == "user_123"
    assert decoded["type"] == "refresh"


def test_expired_token() -> None:
    """Test that expired token raises TokenExpiredError."""
    token = create_access_token({"sub": "user_123"}, expires_delta=datetime.timedelta(seconds=-10))
    with pytest.raises(TokenExpiredError):
        decode_token(token)


def test_invalid_token() -> None:
    """Test that invalid signature raises CredentialsError."""
    with pytest.raises(CredentialsError):
        decode_token("invalid.jwt.token")
