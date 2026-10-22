"""Initial PostGIS schema migration for PravahX.

Revision ID: 001_initial_postgis
Revises: None
Create Date: 2026-10-22
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import geoalchemy2
import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "001_initial_postgis"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable PostGIS extension if running on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # 2. scenarios
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("scenario_type", sa.String(64), nullable=False),
        sa.Column("failure_mode", sa.String(64), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_scenario_id", sa.String(128), nullable=True),
        sa.Column(
            "aoi_geom",
            geoalchemy2.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. runs
    op.create_table(
        "runs",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("scenario_id", sa.String(128), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("current_stage", sa.String(64), nullable=False, server_default="created"),
        sa.Column("manifest_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("work_dir", sa.String(512), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "envelope_geom",
            geoalchemy2.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_runs_scenario_id", "runs", ["scenario_id"])
    op.create_index("ix_runs_status", "runs", ["status"])

    # 4. critical_assets
    op.create_table(
        "critical_assets",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("depth_threshold_m", sa.Float(), nullable=False, server_default="0.30"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_critical_assets_asset_type", "critical_assets", ["asset_type"])


def downgrade() -> None:
    op.drop_table("critical_assets")
    op.drop_table("runs")
    op.drop_table("scenarios")
    op.drop_table("users")
