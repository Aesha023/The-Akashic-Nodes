"""Unit tests for Phase 6 pipeline orchestrator, checkpointing, and execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pravahx.config.schema import (
    BreachConfig,
    CascadeConfig,
    CompareConfig,
    DomainConfig,
    FailureMode,
    ImpactConfig,
    InputsConfig,
    ScenarioConfig,
    ScenarioHeader,
    ScenarioType,
    SourceConfig,
    TiersConfig,
)
from pravahx.pipeline import (
    ArtifactRecord,
    CheckpointManager,
    WorkflowOrchestrator,
    compute_file_sha256,
    run_scenario_sync,
    verify_artifacts,
)

if TYPE_CHECKING:
    from pathlib import Path


def _build_test_scenario_config(scenario_id: str = "test_scen") -> ScenarioConfig:
    """Helper to build a valid ScenarioConfig for testing."""
    return ScenarioConfig(
        scenario=ScenarioHeader(
            id=scenario_id,
            name="Test Dam Break Scenario",
            type=ScenarioType.DAM_BREAK,
            failure_mode=FailureMode.OVERTOPPING,
        ),
        source=SourceConfig(
            point=(78.30, 30.15),
            dam_height_m=45.0,
            storage_m3=5_000_000.0,
        ),
        domain=DomainConfig(reach_length_km=20.0, buffer_km=2.0),
        inputs=InputsConfig(),
        breach=BreachConfig(
            width_uncertainty_factor=1.3,
            time_uncertainty_factor=1.4,
        ),
        tiers=TiersConfig(),
        compare=CompareConfig(enabled=True),
        cascade=CascadeConfig(enabled=True),
        impact=ImpactConfig(enabled=False),
    )


class TestCheckpointManager:
    def test_save_and_load_checkpoint(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(work_dir=tmp_path, run_id="run-123")
        dummy_file = tmp_path / "dummy.txt"
        dummy_file.write_text("sample artifact", encoding="utf-8")

        art = ArtifactRecord(
            path="dummy.txt",
            sha256=compute_file_sha256(dummy_file),
            size_bytes=dummy_file.stat().st_size,
            kind="txt",
        )

        cp_path = mgr.save_checkpoint(
            stage="stage_a",
            completed_stages=["stage_a"],
            artifacts=[art],
            data_payload={"key": "val"},
        )
        assert cp_path.exists()

        loaded = mgr.load_checkpoint("stage_a")
        assert loaded is not None
        assert loaded.run_id == "run-123"
        assert loaded.stage == "stage_a"
        assert loaded.completed_stages == ["stage_a"]
        assert loaded.data_payload == {"key": "val"}

    def test_latest_checkpoint(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(work_dir=tmp_path, run_id="run-123")
        mgr.save_checkpoint("stage_1", ["stage_1"], [])
        mgr.save_checkpoint("stage_2", ["stage_1", "stage_2"], [])

        latest = mgr.get_latest_checkpoint()
        assert latest is not None
        assert latest.stage == "stage_2"


class TestWorkflowOrchestrator:
    def test_execute_full_workflow(self, tmp_path: Path) -> None:
        config = _build_test_scenario_config()
        progress_log: list[tuple[str, float, str]] = []

        def track_progress(stage: str, frac: float, msg: str) -> None:
            progress_log.append((stage, frac, msg))

        orchestrator = WorkflowOrchestrator(
            work_dir=tmp_path,
            progress_callback=track_progress,
        )
        manifest = orchestrator.execute(config=config, resume=False)

        assert manifest.status == "succeeded"
        assert len(manifest.stages) >= 3
        assert len(manifest.artifacts) >= 2

        # Verify artifacts exist on disk and hashes match
        issues = verify_artifacts(manifest, tmp_path)
        assert not issues, f"Artifact verification issues: {issues}"

        # Verify progress was reported
        assert len(progress_log) >= 3
        assert progress_log[-1][1] == 1.0

    def test_resume_workflow(self, tmp_path: Path) -> None:
        config = _build_test_scenario_config()
        orchestrator = WorkflowOrchestrator(work_dir=tmp_path)

        # First run
        manifest1 = orchestrator.execute(config=config, resume=False)
        assert manifest1.status == "succeeded"

        # Second run with resume=True should skip completed stages without error
        manifest2 = orchestrator.execute(config=config, resume=True)
        assert manifest2.status == "succeeded"

    def test_run_scenario_sync(self, tmp_path: Path) -> None:
        config = _build_test_scenario_config()
        config_dict = config.model_dump()

        result = run_scenario_sync(config_data=config_dict, work_dir=str(tmp_path))
        assert result["status"] == "succeeded"
        assert result["scenario_id"] == config.scenario.id
