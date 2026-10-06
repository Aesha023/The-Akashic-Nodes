"""Simulation run schemas (Phase 7)."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel


class RunCreate(BaseModel):
    """Payload to dispatch a new simulation run."""

    resume: bool = True


class RunResponse(BaseModel):
    """Simulation run details and status."""

    id: str
    scenario_id: str
    status: str
    progress_percent: float
    current_stage: str
    error_message: str | None = None
    created_at: datetime.datetime
    finished_at: datetime.datetime | None = None
    manifest: dict[str, Any] | None = None


class RunListResponse(BaseModel):
    """List of simulation runs."""

    total: int
    items: list[RunResponse]
