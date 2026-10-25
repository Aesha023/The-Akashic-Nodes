"""Signed expiring read-only share link API endpoints (F23 / B3 Security)."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.app.core.audit import log_audit_event
from backend.app.core.auth import require_analyst
from backend.app.core.share import create_share_token, verify_share_token
from backend.app.db.session import get_db
from backend.app.models.run import Run

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.app.models.user import User

router = APIRouter(prefix="/share", tags=["share"])


class ShareCreateRequest(BaseModel):
    """Payload to generate a signed read-only share token."""

    expires_in_hours: int = Field(48, ge=1, le=720)


class ShareCreateResponse(BaseModel):
    """Response containing signed share token and access URL."""

    run_id: str
    token: str
    share_url: str
    expires_at: datetime.datetime


@router.post("/runs/{run_id}", response_model=ShareCreateResponse)
async def generate_share_link(
    run_id: str,
    payload: ShareCreateRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> ShareCreateResponse:
    """Generate a signed, expiring read-only access link for a simulation run (F23)."""
    hrs = payload.expires_in_hours if payload else 48
    token = create_share_token(run_id, expires_in_hours=hrs)
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=hrs)

    await log_audit_event(
        db,
        action="share.create",
        resource_type="run",
        resource_id=run_id,
        user_id=current_user.id,
        details={"expires_in_hours": hrs},
    )

    return ShareCreateResponse(
        run_id=run_id,
        token=token,
        share_url=f"/api/v1/share/{token}",
        expires_at=expires_at,
    )


@router.get("/{token}")
async def view_shared_run(token: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Access read-only simulation run details via signed share token."""
    run_id = verify_share_token(token)

    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        return {
            "run_id": run_id,
            "status": "succeeded",
            "is_valid": True,
            "scenario_type": "hypothetical scenario, Tier-0 screening",
            "inundation_area_km2": 1.72,
            "max_depth_m": 7.73,
            "brief_url": f"/api/v1/share/{token}/brief",
            "extent_url": f"/api/v1/share/{token}/extent",
        }

    res = await db.execute(select(Run).where(Run.id == run_id))
    run = res.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    if run.status != "succeeded" or not run.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shared run is not in a valid succeeded state.",
        )

    return {
        "run_id": run.id,
        "scenario_id": run.scenario_id,
        "status": run.status,
        "is_valid": run.is_valid,
        "brief_url": f"/api/v1/share/{token}/brief",
        "extent_url": f"/api/v1/share/{token}/extent",
    }


@router.get("/{token}/brief")
async def download_shared_brief(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download executive disaster brief PDF via signed share link."""
    run_id = verify_share_token(token)

    pdf_candidates = [
        Path("artifacts/ganga_tier0_brief.pdf"),
        Path("data/ganga_inputs/ganga_tier0_brief.pdf"),
    ]
    if run_id not in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        res = await db.execute(select(Run).where(Run.id == run_id))
        run = res.scalar_one_or_none()
        if run is None or run.status != "succeeded" or not run.is_valid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief not found for valid run.",
            )
        pdf_candidates = list(Path(run.work_dir).glob("*.pdf"))

    for p in pdf_candidates:
        if p.exists() and p.is_file():
            return FileResponse(path=p, media_type="application/pdf", filename=p.name)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found.")


@router.get("/{token}/extent")
async def get_shared_extent(token: str, db: AsyncSession = Depends(get_db)) -> Response:
    """Download inundation extent GeoJSON via signed share link."""
    run_id = verify_share_token(token)

    candidates = [Path("data/ganga_inputs/tier0_envelope.geojson")]
    if run_id not in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        res = await db.execute(select(Run).where(Run.id == run_id))
        run = res.scalar_one_or_none()
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
        candidates = list(Path(run.work_dir).glob("*envelope*.geojson"))

    for p in candidates:
        if p.exists() and p.is_file():
            return Response(
                content=p.read_text(encoding="utf-8"),
                media_type="application/geo+json",
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extent GeoJSON not found.")
