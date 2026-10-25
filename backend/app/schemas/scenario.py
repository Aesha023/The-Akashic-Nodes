"""Scenario CRUD schemas (Phase 7 & B2 API Completion)."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel

from pravahx.config.schema import ScenarioConfig


class ScenarioCreate(BaseModel):
    """Payload to create or import a scenario."""

    config: ScenarioConfig


class ScenarioUpdate(BaseModel):
    """Payload to update an existing scenario."""

    config: ScenarioConfig


class ScenarioCloneRequest(BaseModel):
    """Payload to clone an existing scenario."""

    new_id: str | None = None
    new_name: str | None = None


class ScenarioResponse(BaseModel):
    """Scenario response including metadata, versioning, and configuration."""

    id: str
    name: str
    scenario_type: str
    failure_mode: str | None
    version: int = 1
    parent_scenario_id: str | None = None
    config: dict[str, Any]
    created_by: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ScenarioListResponse(BaseModel):
    """Paginated list of scenarios."""

    total: int
    items: list[ScenarioResponse]
