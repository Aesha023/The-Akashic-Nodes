"""Scenario database model storing scenario configuration JSON."""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Scenario(Base):
    """Scenario record storing schema validation and JSON definitions."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )
