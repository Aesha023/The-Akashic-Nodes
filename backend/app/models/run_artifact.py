"""Run artifact model tracking outputs and cryptographic checksums."""

from __future__ import annotations

import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class RunArtifact(Base):
    """File output produced by a simulation run (COG, GeoJSON, PDF, zip, etc.)."""

    __tablename__ = "run_artifacts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(
        String(128), default="application/octet-stream", nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
