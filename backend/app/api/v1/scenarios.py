"""Scenario CRUD API endpoints (Phase 7)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from backend.app.core.auth import get_current_user, require_admin, require_analyst
from backend.app.db.session import get_db
from backend.app.models.scenario import Scenario
from backend.app.schemas.scenario import (
    ScenarioCreate,
    ScenarioListResponse,
    ScenarioResponse,
    ScenarioUpdate,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.app.models.user import User

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _scenario_to_response(s: Scenario) -> ScenarioResponse:
    config_dict = json.loads(s.config_json)
    return ScenarioResponse(
        id=s.id,
        name=s.name,
        scenario_type=s.scenario_type,
        failure_mode=s.failure_mode,
        config=config_dict,
        created_by=s.created_by,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    payload: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> ScenarioResponse:
    """Create and validate a new scenario configuration."""
    cfg = payload.config
    scen_id = cfg.scenario.id

    existing = await db.execute(select(Scenario).where(Scenario.id == scen_id))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scenario with id '{scen_id}' already exists.",
        )

    scenario = Scenario(
        id=scen_id,
        name=cfg.scenario.name,
        scenario_type=cfg.scenario.type.value,
        failure_mode=cfg.scenario.failure_mode.value if cfg.scenario.failure_mode else None,
        config_json=cfg.model_dump_json(),
        created_by=current_user.id,
    )
    db.add(scenario)
    await db.flush()

    return _scenario_to_response(scenario)


@router.get("", response_model=ScenarioListResponse)
async def list_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScenarioListResponse:
    """List all saved scenarios with pagination."""
    total_q = await db.execute(select(func.count(Scenario.id)))
    total = total_q.scalar_one() or 0

    q = select(Scenario).order_by(Scenario.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    scenarios = result.scalars().all()

    return ScenarioListResponse(
        total=total,
        items=[_scenario_to_response(s) for s in scenarios],
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScenarioResponse:
    """Retrieve details and configuration for a specific scenario."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found.",
        )

    return _scenario_to_response(scenario)


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    payload: ScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
) -> ScenarioResponse:
    """Update configuration for an existing scenario."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found.",
        )

    cfg = payload.config
    scenario.name = cfg.scenario.name
    scenario.scenario_type = cfg.scenario.type.value
    scenario.failure_mode = cfg.scenario.failure_mode.value if cfg.scenario.failure_mode else None
    scenario.config_json = cfg.model_dump_json()

    await db.flush()
    return _scenario_to_response(scenario)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete a scenario (admin only)."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found.",
        )

    await db.delete(scenario)
    await db.flush()
