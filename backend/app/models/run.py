"""Simulation Run database model storing execution status and manifest."""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Run(Base):
    """Simulation run record tracking job status and output provenance."""

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("scenarios.id"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="created", index=True, nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    current_stage: Mapped[str] = mapped_column(String(64), default="created")
    manifest_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_dir: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
