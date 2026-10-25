"""Security utilities: password hashing and JWT token operations (Phase 7)."""

from __future__ import annotations

import datetime
import uuid
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
    to_encode.update({"exp": expire, "type": "access", "jti": uuid.uuid4().hex})
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
    to_encode.update({"exp": expire, "type": "refresh", "jti": uuid.uuid4().hex})
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


def hash_api_key(raw_key: str) -> str:
    """Compute SHA-256 digest of an API key."""
    import hashlib

    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key(prefix: str = "pvx_") -> tuple[str, str, str]:
    """Generate a high-entropy API key.

    Returns:
        tuple[raw_key, prefix, key_hash]
    """
    import secrets

    random_part = secrets.token_hex(24)
    raw_key = f"{prefix}{random_part}"
    key_prefix = raw_key[:10]
    key_hash = hash_api_key(raw_key)
    return raw_key, key_prefix, key_hash
