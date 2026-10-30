"""Full-stack alignment migration: add all required platform entities and spatial tables.

Revision ID: 004_fullstack_entities
Revises: 003_mfa_support
Create Date: 2026-10-29
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import geoalchemy2
import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "004_fullstack_entities"
down_revision: str | None = "003_mfa_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def get_columns(table_name: str) -> set[str]:
        if table_name in existing_tables:
            return {c["name"] for c in inspector.get_columns(table_name)}
        return set()

    # 1. roles
    if "roles" not in existing_tables:
        op.create_table(
            "roles",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(64), nullable=False, unique=True),
            sa.Column("description", sa.String(256), nullable=False),
            sa.Column("permissions_json", sa.Text(), nullable=False, server_default="[]"),
        )

    # 2. Add demo column to scenarios
    scenario_cols = get_columns("scenarios")
    if "demo" not in scenario_cols:
        op.add_column(
            "scenarios",
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    # 3. scenario_versions
    if "scenario_versions" not in existing_tables:
        op.create_table(
            "scenario_versions",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "scenario_id",
                sa.String(128),
                sa.ForeignKey("scenarios.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("config_json", sa.Text(), nullable=False),
            sa.Column("change_summary", sa.String(512), nullable=True),
            sa.Column("created_by", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_scenario_versions_scenario_id", "scenario_versions", ["scenario_id"])

    # 4. Add precomputed, computed_at, demo columns to runs
    run_cols = get_columns("runs")
    if "precomputed" not in run_cols:
        op.add_column(
            "runs",
            sa.Column("precomputed", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "computed_at" not in run_cols:
        op.add_column(
            "runs",
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "demo" not in run_cols:
        op.add_column(
            "runs",
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    # 5. run_artifacts
    if "run_artifacts" not in existing_tables:
        op.create_table(
            "run_artifacts",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "run_id",
                sa.String(128),
                sa.ForeignKey("runs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("artifact_type", sa.String(64), nullable=False),
            sa.Column("path", sa.String(512), nullable=False),
            sa.Column("sha256", sa.String(64), nullable=False),
            sa.Column("size_bytes", sa.BigInteger(), nullable=False),
            sa.Column(
                "mime_type",
                sa.String(128),
                nullable=False,
                server_default="application/octet-stream",
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_run_artifacts_run_id", "run_artifacts", ["run_id"])
        op.create_index("ix_run_artifacts_type", "run_artifacts", ["artifact_type"])

    # 6. extent_geometries
    if "extent_geometries" not in existing_tables:
        op.create_table(
            "extent_geometries",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "run_id",
                sa.String(128),
                sa.ForeignKey("runs.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column(
                "scenario_id",
                sa.String(128),
                sa.ForeignKey("scenarios.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("layer_name", sa.String(64), nullable=False),
            sa.Column(
                "geom",
                geoalchemy2.Geometry(
                    geometry_type="GEOMETRY", srid=4326, spatial_index=is_postgres
                ),
                nullable=False,
            ),
            sa.Column("properties_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_extent_geom_run_id", "extent_geometries", ["run_id"])
        op.create_index("ix_extent_geom_scenario_id", "extent_geometries", ["scenario_id"])
        op.create_index("ix_extent_geom_layer", "extent_geometries", ["layer_name"])

    # 7. exposure_results
    if "exposure_results" not in existing_tables:
        op.create_table(
            "exposure_results",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "run_id",
                sa.String(128),
                sa.ForeignKey("runs.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("total_population", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("exposed_population", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("pop_depth_0_05m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("pop_depth_05_15m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("pop_depth_gt15m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("total_buildings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("flooded_buildings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_roads_km", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("flooded_roads_km", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column(
                "critical_facilities_count", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("summary_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_exposure_results_run_id", "exposure_results", ["run_id"])

    # 8. evacuation_routes
    if "evacuation_routes" not in existing_tables:
        op.create_table(
            "evacuation_routes",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "run_id",
                sa.String(128),
                sa.ForeignKey("runs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("origin_id", sa.String(128), nullable=False),
            sa.Column("origin_type", sa.String(64), nullable=False, server_default="building"),
            sa.Column("destination_id", sa.String(128), nullable=False),
            sa.Column(
                "destination_type", sa.String(64), nullable=False, server_default="safe_node"
            ),
            sa.Column("length_m", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("duration_s", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("status", sa.String(32), nullable=False, server_default="reachable"),
            sa.Column("is_safe", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "route_geom",
                geoalchemy2.Geometry(
                    geometry_type="LINESTRING", srid=4326, spatial_index=is_postgres
                ),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_evacuation_routes_run_id", "evacuation_routes", ["run_id"])
        op.create_index("ix_evacuation_routes_origin", "evacuation_routes", ["origin_id"])

    # 9. alert_rules
    if "alert_rules" not in existing_tables:
        op.create_table(
            "alert_rules",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("rule_type", sa.String(64), nullable=False),
            sa.Column("lake_id", sa.String(128), nullable=True),
            sa.Column("threshold_value", sa.Float(), nullable=False),
            sa.Column("condition", sa.String(32), nullable=False, server_default=">="),
            sa.Column("channels_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_alert_rules_type", "alert_rules", ["rule_type"])
        op.create_index("ix_alert_rules_lake", "alert_rules", ["lake_id"])

    # 10. alerts
    if "alerts" not in existing_tables:
        op.create_table(
            "alerts",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "rule_id",
                sa.String(128),
                sa.ForeignKey("alert_rules.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_alerts_severity", "alerts", ["severity"])
        op.create_index("ix_alerts_status", "alerts", ["status"])

    # 11. watched_lakes
    if "watched_lakes" not in existing_tables:
        op.create_table(
            "watched_lakes",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("lake_type", sa.String(64), nullable=False, server_default="glacial"),
            sa.Column("region", sa.String(128), nullable=False),
            sa.Column("latitude", sa.Float(), nullable=False),
            sa.Column("longitude", sa.Float(), nullable=False),
            sa.Column("elevation_m", sa.Float(), nullable=False),
            sa.Column("area_m2", sa.Float(), nullable=False),
            sa.Column("volume_m3", sa.Float(), nullable=False),
            sa.Column("risk_level", sa.String(32), nullable=False, server_default="low"),
            sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "geom",
                geoalchemy2.Geometry(geometry_type="POINT", srid=4326, spatial_index=is_postgres),
                nullable=True,
            ),
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_watched_lakes_name", "watched_lakes", ["name"])
        op.create_index("ix_watched_lakes_risk", "watched_lakes", ["risk_level"])

    # 12. batches
    if "batches" not in existing_tables:
        op.create_table(
            "batches",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.String(64), nullable=True),
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_batches_status", "batches", ["status"])

    # 13. batch_items
    if "batch_items" not in existing_tables:
        op.create_table(
            "batch_items",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column(
                "batch_id",
                sa.String(128),
                sa.ForeignKey("batches.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("dam_name", sa.String(256), nullable=False),
            sa.Column("scenario_id", sa.String(128), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("run_id", sa.String(128), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_batch_items_batch_id", "batch_items", ["batch_id"])

    # 14. datasets
    if "datasets" not in existing_tables:
        op.create_table(
            "datasets",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("dataset_type", sa.String(64), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("source_url", sa.String(512), nullable=True),
            sa.Column("license", sa.String(128), nullable=False),
            sa.Column("file_format", sa.String(64), nullable=False),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("sha256", sa.String(64), nullable=False),
            sa.Column(
                "coverage_geom",
                geoalchemy2.Geometry(
                    geometry_type="GEOMETRY", srid=4326, spatial_index=is_postgres
                ),
                nullable=True,
            ),
            sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_datasets_name", "datasets", ["name"])
        op.create_index("ix_datasets_type", "datasets", ["dataset_type"])

    # 15. share_links
    if "share_links" not in existing_tables:
        op.create_table(
            "share_links",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
            sa.Column("resource_type", sa.String(64), nullable=False),
            sa.Column("resource_id", sa.String(128), nullable=False),
            sa.Column("created_by", sa.String(64), nullable=True),
            sa.Column("permission", sa.String(32), nullable=False, server_default="view"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_share_links_token", "share_links", ["token_hash"])
        op.create_index("ix_share_links_resource", "share_links", ["resource_type", "resource_id"])

    # 16. backups
    if "backups" not in existing_tables:
        op.create_table(
            "backups",
            sa.Column("id", sa.String(128), primary_key=True),
            sa.Column("backup_type", sa.String(64), nullable=False),
            sa.Column("filename", sa.String(256), nullable=False),
            sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("sha256", sa.String(64), nullable=False),
            sa.Column("storage_path", sa.String(512), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="completed"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_backups_type", "backups", ["backup_type"])


def downgrade() -> None:
    op.drop_table("backups")
    op.drop_table("share_links")
    op.drop_table("datasets")
    op.drop_table("batch_items")
    op.drop_table("batches")
    op.drop_table("watched_lakes")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
    op.drop_table("evacuation_routes")
    op.drop_table("exposure_results")
    op.drop_table("extent_geometries")
    op.drop_table("run_artifacts")
    op.drop_column("runs", "demo")
    op.drop_column("runs", "computed_at")
    op.drop_column("runs", "precomputed")
    op.drop_table("scenario_versions")
    op.drop_column("scenarios", "demo")
    op.drop_table("roles")
