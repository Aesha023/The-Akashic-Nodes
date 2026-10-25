"""Cryptographic append-only tamper-evident audit logger (B3 Security)."""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from backend.app.models.audit import AuditLogEntry

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

GENESIS_HASH = "0" * 64


def compute_entry_hash(
    entry_id: int,
    timestamp: datetime.datetime,
    user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    details_json: str,
    previous_hash: str,
) -> str:
    """Compute SHA-256 digest binding all entry fields to the preceding block hash."""
    if isinstance(timestamp, datetime.datetime):
        if timestamp.tzinfo is None:
            ts_str = timestamp.replace(tzinfo=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            ts_str = timestamp.astimezone(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        ts_str = str(timestamp)

    uid_str = user_id or "system"
    raw_payload = (
        f"{entry_id}|{ts_str}|{uid_str}|{action}|"
        f"{resource_type}|{resource_id}|{details_json}|{previous_hash}"
    )
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLogEntry:
    """Append a new tamper-evident audit log entry chained cryptographically to previous entry."""
    details_str = json.dumps(details or {}, sort_keys=True)
    now = datetime.datetime.now(datetime.UTC).replace(microsecond=0)

    # Get the latest entry to retrieve its hash
    last_res = await db.execute(select(AuditLogEntry).order_by(AuditLogEntry.id.desc()).limit(1))
    last_entry = last_res.scalar_one_or_none()

    previous_hash = last_entry.entry_hash if last_entry is not None else GENESIS_HASH
    next_id = (last_entry.id + 1) if last_entry is not None else 1

    entry_hash = compute_entry_hash(
        entry_id=next_id,
        timestamp=now,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=details_str,
        previous_hash=previous_hash,
    )

    entry = AuditLogEntry(
        id=next_id,
        timestamp=now,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=details_str,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    await db.flush()
    return entry


async def verify_audit_chain(db: AsyncSession) -> tuple[bool, int, str | None]:
    """Verify entire audit log cryptographic chain integrity.

    Returns:
        (is_valid, count_verified, failure_reason)
    """
    res = await db.execute(select(AuditLogEntry).order_by(AuditLogEntry.id.asc()))
    entries = res.scalars().all()

    if not entries:
        return True, 0, None

    expected_prev = GENESIS_HASH
    for entry in entries:
        if entry.previous_hash != expected_prev:
            return (
                False,
                entry.id,
                f"Broken chain at entry {entry.id}: previous_hash '{entry.previous_hash}' "
                f"does not match expected '{expected_prev}'.",
            )

        recomputed = compute_entry_hash(
            entry_id=entry.id,
            timestamp=entry.timestamp,
            user_id=entry.user_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            details_json=entry.details_json,
            previous_hash=entry.previous_hash,
        )
        if recomputed != entry.entry_hash:
            return (
                False,
                entry.id,
                f"Tampered content at entry {entry.id}: entry_hash '{entry.entry_hash}' "
                f"does not match recomputed '{recomputed}'.",
            )

        expected_prev = entry.entry_hash

    return True, len(entries), None
