"""Audit logging and tamper-evident chain verification endpoints (B3 Security)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from backend.app.core.audit import verify_audit_chain
from backend.app.core.auth import require_admin
from backend.app.db.session import get_db
from backend.app.models.audit import AuditLogEntry

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: int
    timestamp: datetime.datetime
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    details_json: str
    previous_hash: str
    entry_hash: str


class AuditListResponse(BaseModel):
    """Paginated audit log entries."""

    total: int
    items: list[AuditLogResponse]


class AuditVerifyResponse(BaseModel):
    """Result of cryptographic chain verification."""

    is_valid: bool
    entries_verified: int
    failure_reason: str | None
    verified_at: datetime.datetime


@router.get("/logs", response_model=AuditListResponse)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AuditListResponse:
    """Retrieve audit logs (admin only)."""
    total_q = await db.execute(select(func.count(AuditLogEntry.id)))
    total = total_q.scalar_one() or 0

    q = select(AuditLogEntry).order_by(AuditLogEntry.id.desc()).offset(skip).limit(limit)
    res = await db.execute(q)
    entries = res.scalars().all()

    return AuditListResponse(
        total=total,
        items=[
            AuditLogResponse(
                id=e.id,
                timestamp=e.timestamp,
                user_id=e.user_id,
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                details_json=e.details_json,
                previous_hash=e.previous_hash,
                entry_hash=e.entry_hash,
            )
            for e in entries
        ],
    )


@router.get("/verify", response_model=AuditVerifyResponse)
async def verify_audit_logs_chain(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AuditVerifyResponse:
    """Cryptographically verify the tamper-evident hash chain integrity (admin only)."""
    is_valid, count, reason = await verify_audit_chain(db)
    return AuditVerifyResponse(
        is_valid=is_valid,
        entries_verified=count,
        failure_reason=reason,
        verified_at=datetime.datetime.now(datetime.UTC),
    )
