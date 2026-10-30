"""Alert and alert rules models (F16 Lake Watch & F17 Alerts Drawer)."""

from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class AlertRule(Base):
    """Configured trigger rule for monitoring lakes and reservoir levels."""

    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    lake_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str] = mapped_column(String(32), default=">=", nullable=False)
    channels_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )


class Alert(Base):
    """Dispatched emergency notification or hydraulic advisory."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rule_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("alert_rules.id", ondelete="SET NULL"), index=True, nullable=True
    )
    severity: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
