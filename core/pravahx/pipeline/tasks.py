"""Celery asynchronous task definitions for pipeline background execution (Phase 6)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pravahx.config.schema import ScenarioConfig
from pravahx.pipeline.workflow import WorkflowOrchestrator

logger = logging.getLogger(__name__)

celery_app: Any = None
try:
    from celery import Celery

    celery_app = Celery("pravahx")
    celery_app.config_from_object("pravahx.config.celery_config", silent=True)
except Exception:
    celery_app = None


def run_scenario_sync(
    config_data: dict[str, Any],
    work_dir: str,
    resume: bool = True,
) -> dict[str, Any]:
    """Execute a scenario synchronously in-process.

    Args:
        config_data: Raw or validated ScenarioConfig dictionary.
        work_dir: Path string to the execution directory.
        resume: Whether to resume from stage checkpoints.

    Returns:
        Dictionary representation of the completed RunManifest.
    """
    config = ScenarioConfig.model_validate(config_data)
    orchestrator = WorkflowOrchestrator(work_dir=Path(work_dir))
    manifest = orchestrator.execute(config=config, resume=resume)
    return manifest.to_dict()


if celery_app is not None:

    @celery_app.task(bind=True, name="pravahx.run_scenario")  # type: ignore[untyped-decorator]
    def run_scenario_task(
        self: Any,
        config_data: dict[str, Any],
        work_dir: str,
        resume: bool = True,
    ) -> dict[str, Any]:
        """Celery background task executing a hydrodynamic scenario."""

        def progress_tracker(stage: str, fraction: float, message: str) -> None:
            self.update_state(
                state="PROGRESS",
                meta={
                    "stage": stage,
                    "progress": round(fraction * 100, 1),
                    "message": message,
                },
            )

        config = ScenarioConfig.model_validate(config_data)
        orchestrator = WorkflowOrchestrator(
            work_dir=Path(work_dir),
            progress_callback=progress_tracker,
        )
        manifest = orchestrator.execute(config=config, resume=resume)
        return manifest.to_dict()
else:

    def run_scenario_task(
        config_data: dict[str, Any],
        work_dir: str,
        resume: bool = True,
    ) -> dict[str, Any]:
        """Fallback synchronous executor when Celery is not active."""
        return run_scenario_sync(config_data, work_dir, resume=resume)
