"""Impact and population exposure results model (F09)."""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ExposureResult(Base):
    """Aggregated population, building, and road exposure metrics for a run."""

    __tablename__ = "exposure_results"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("runs.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    total_population: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    exposed_population: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pop_depth_0_05m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pop_depth_05_15m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pop_depth_gt15m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_buildings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flooded_buildings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_roads_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    flooded_roads_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    critical_facilities_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
