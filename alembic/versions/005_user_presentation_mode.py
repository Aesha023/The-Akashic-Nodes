"""Add presentation_mode column to users table for per-user mode persistence.

Revision ID: 005_user_presentation_mode
Revises: 004_fullstack_entities
Create Date: 2026-10-30
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "005_user_presentation_mode"
down_revision: str | None = "004_fullstack_entities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" in existing_tables:
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "presentation_mode" not in cols:
            op.add_column(
                "users",
                sa.Column("presentation_mode", sa.Boolean(), server_default=sa.text("1"), nullable=False),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" in existing_tables:
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "presentation_mode" in cols:
            op.drop_column("users", "presentation_mode")
