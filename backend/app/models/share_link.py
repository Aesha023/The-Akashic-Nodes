"""Cryptographically signed share link model (F23 Share Links)."""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ShareLink(Base):
    """HMAC-signed or token-indexed read-only share link."""

    __tablename__ = "share_links"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    permission: Mapped[str] = mapped_column(String(32), default="view", nullable=False)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
