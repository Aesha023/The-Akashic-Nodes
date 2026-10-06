"""Security utilities: password hashing and JWT token operations (Phase 7)."""

from __future__ import annotations

import datetime
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from backend.app.core.config import Settings
from pravahx.errors import CredentialsError, TokenExpiredError

_hasher = PasswordHasher()
_settings = Settings()

SECRET_KEY = _settings.secret_key.get_secret_value() or "pravahx-dev-secret-key-change-in-prod"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=_settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=_settings.refresh_token_expire_days
        )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Raises:
        TokenExpiredError: If the token has expired.
        CredentialsError: If the signature is invalid or payload is corrupt.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError("Token has expired.") from e
    except jwt.PyJWTError as e:
        raise CredentialsError(f"Invalid token: {e}") from e
