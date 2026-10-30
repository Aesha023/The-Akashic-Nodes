"""Role model for RBAC authorization."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Role(Base):
    """User role definition with permissions."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    permissions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
