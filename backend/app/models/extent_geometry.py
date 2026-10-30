"""Spatial extent and geometry model for vector layers."""

from __future__ import annotations

import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ExtentGeometry(Base):
    """Vector polygon / linestring extent associated with a run or scenario."""

    __tablename__ = "extent_geometries"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=True
    )
    scenario_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("scenarios.id", ondelete="CASCADE"), index=True, nullable=True
    )
    layer_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )
    properties_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
