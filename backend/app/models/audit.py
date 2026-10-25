"""Append-only tamper-evident audit log model with SHA-256 hash chain (B3 Security)."""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class AuditLogEntry(Base):
    """Tamper-evident audit log entry secured by cryptographic hash chaining."""

    __tablename__ = "audit_log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(128), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    __table_args__ = (Index("idx_audit_resource", "resource_type", "resource_id"),)
