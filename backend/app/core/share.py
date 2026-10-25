"""Signed expiring read-only share token generator and validator (F23 / B3 Security)."""

from __future__ import annotations

import datetime
from typing import Any

import jwt
from fastapi import HTTPException, status

from backend.app.core.config import Settings

_settings = Settings()
SECRET_KEY = _settings.secret_key.get_secret_value() or "pravahx-dev-secret-key-change-in-prod"
ALGORITHM = "HS256"
SHARE_SCOPE = "read_only_share"


def create_share_token(run_id: str, expires_in_hours: int = 48) -> str:
    """Generate a signed, time-limited token granting read-only access to a specific run."""
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expires_in_hours)
    payload: dict[str, Any] = {
        "sub": run_id,
        "scope": SHARE_SCOPE,
        "exp": expire,
        "iat": datetime.datetime.now(datetime.UTC),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_share_token(token: str) -> str:
    """Validate a signed share token and return the associated run_id.

    Raises:
        HTTPException: 401 if expired, invalid signature, or wrong scope.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != SHARE_SCOPE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid share token: incorrect scope.",
            )
        run_id = payload.get("sub")
        if not run_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid share token: missing run identifier.",
            )
        return str(run_id)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Share link has expired.",
        ) from e
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid share token.",
        ) from e
