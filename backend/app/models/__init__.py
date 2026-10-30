"""Database models package."""

from __future__ import annotations

from backend.app.models.alert import Alert, AlertRule
from backend.app.models.api_key import ApiKey
from backend.app.models.asset import CriticalAsset
from backend.app.models.audit import AuditLogEntry
from backend.app.models.backup import Backup
from backend.app.models.base import Base
from backend.app.models.batch import Batch, BatchItem
from backend.app.models.dataset import Dataset
from backend.app.models.evacuation_route import EvacuationRoute
from backend.app.models.exposure_result import ExposureResult
from backend.app.models.extent_geometry import ExtentGeometry
from backend.app.models.role import Role
from backend.app.models.run import Run
from backend.app.models.run_artifact import RunArtifact
from backend.app.models.scenario import Scenario
from backend.app.models.scenario_version import ScenarioVersion
from backend.app.models.share_link import ShareLink
from backend.app.models.user import User
from backend.app.models.watched_lake import WatchedLake

__all__ = [
    "Alert",
    "AlertRule",
    "ApiKey",
    "AuditLogEntry",
    "Backup",
    "Base",
    "Batch",
    "BatchItem",
    "CriticalAsset",
    "Dataset",
    "EvacuationRoute",
    "ExposureResult",
    "ExtentGeometry",
    "Role",
    "Run",
    "RunArtifact",
    "Scenario",
    "ScenarioVersion",
    "ShareLink",
    "User",
    "WatchedLake",
]
