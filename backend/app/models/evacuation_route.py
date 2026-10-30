"""Evacuation route model with spatial geometry (F10)."""

from __future__ import annotations

import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class EvacuationRoute(Base):
    """Evacuation path from flooded building origin to unsevered road destination."""

    __tablename__ = "evacuation_routes"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    origin_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    origin_type: Mapped[str] = mapped_column(String(64), default="building", nullable=False)
    destination_id: Mapped[str] = mapped_column(String(128), nullable=False)
    destination_type: Mapped[str] = mapped_column(String(64), default="safe_node", nullable=False)
    length_m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_s: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="reachable", nullable=False)
    is_safe: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    route_geom: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
