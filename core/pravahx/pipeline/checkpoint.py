"""Pipeline stage checkpointing and failure recovery (Phase 6)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from pravahx.errors import CheckpointError
from pravahx.pipeline.provenance import ArtifactRecord, compute_file_sha256

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class CheckpointData(BaseModel):
    """Serialized state of a single pipeline checkpoint."""

    run_id: str
    stage: str
    completed_stages: list[str]
    artifacts: list[dict[str, Any]]
    data_payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class CheckpointManager:
    """Manages disk-based stage checkpoints for resumption and error recovery."""

    def __init__(self, work_dir: Path, run_id: str) -> None:
        self.work_dir = work_dir
        self.run_id = run_id
        self.checkpoint_dir = work_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(self, stage: str) -> Path:
        return self.checkpoint_dir / f"checkpoint_{stage}.json"

    def save_checkpoint(
        self,
        stage: str,
        completed_stages: list[str],
        artifacts: list[ArtifactRecord],
        data_payload: dict[str, Any] | None = None,
    ) -> Path:
        """Save a checkpoint after successfully finishing a stage.

        Args:
            stage: Name of the completed stage.
            completed_stages: List of all stages completed up to this point.
            artifacts: List of output artifacts created by this stage.
            data_payload: Optional intermediate data / metadata.

        Returns:
            Path to the saved checkpoint JSON file.
        """
        import datetime

        path = self._get_checkpoint_path(stage)
        payload = CheckpointData(
            run_id=self.run_id,
            stage=stage,
            completed_stages=completed_stages,
            artifacts=[a.__dict__ for a in artifacts],
            data_payload=data_payload or {},
            timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        )

        try:
            path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
            logger.info("Saved checkpoint for stage '%s' -> %s", stage, path.name)
            return path
        except Exception as e:
            raise CheckpointError(
                f"Failed to save checkpoint for stage '{stage}': {e}",
                detail={"stage": stage, "path": str(path)},
            ) from e

    def load_checkpoint(self, stage: str) -> CheckpointData | None:
        """Load checkpoint data for a specific stage if present and valid."""
        path = self._get_checkpoint_path(stage)
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            data = CheckpointData.model_validate_json(content)
            # Verify artifact integrity if files exist
            for a_dict in data.artifacts:
                a_path = self.work_dir / a_dict["path"]
                if a_path.exists():
                    actual_hash = compute_file_sha256(a_path)
                    if actual_hash != a_dict["sha256"]:
                        logger.warning(
                            "Checkpoint artifact hash mismatch for %s. Invalidation required.",
                            a_dict["path"],
                        )
                        return None
            return data
        except Exception as e:
            logger.warning("Corrupt checkpoint for stage '%s': %e", stage, e)
            return None

    def get_latest_checkpoint(self) -> CheckpointData | None:
        """Find the latest valid checkpoint in chronological order."""
        checkpoints = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
        )
        if not checkpoints:
            return None

        for cp_path in reversed(checkpoints):
            stage_name = cp_path.stem.replace("checkpoint_", "")
            cp = self.load_checkpoint(stage_name)
            if cp is not None:
                return cp
        return None

    def is_stage_done(self, stage: str) -> bool:
        """Check if a stage has a valid saved checkpoint."""
        return self.load_checkpoint(stage) is not None
