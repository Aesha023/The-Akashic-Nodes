"""Security migration: api_keys and audit_log_entries tables (B3 Security).

Revision ID: 002_security_audit_apikeys
Revises: 001_initial_postgis
Create Date: 2026-10-23
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "002_security_audit_apikeys"
down_revision: str | None = "001_initial_postgis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_prefix", "api_keys", ["prefix"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("idx_api_keys_hash_active", "api_keys", ["key_hash", "is_active"])

    # 2. audit_log_entries
    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(128), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("entry_hash", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log_entries", ["timestamp"])
    op.create_index("ix_audit_log_user_id", "audit_log_entries", ["user_id"])
    op.create_index("ix_audit_log_action", "audit_log_entries", ["action"])
    op.create_index("ix_audit_log_entry_hash", "audit_log_entries", ["entry_hash"])
    op.create_index("idx_audit_resource", "audit_log_entries", ["resource_type", "resource_id"])


def downgrade() -> None:
    op.drop_table("audit_log_entries")
    op.drop_table("api_keys")
