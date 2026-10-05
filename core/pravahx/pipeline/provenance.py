"""Run provenance — hashes, versions, run manifest (Section 1.3, 8, 14.2).

Every run stores its config, input hashes, software versions and output hashes
so that results are reproducible and verifiable.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

import pravahx

if TYPE_CHECKING:
    from pathlib import Path


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file, reading in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_string_sha256(text: str) -> str:
    """Compute SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class ArtifactRecord:
    """Record of a single output artefact."""

    path: str
    sha256: str
    size_bytes: int
    kind: str  # e.g. "raster", "vector", "log", "config", "netcdf", "pdf"
    engine: str | None = None
    stage: str | None = None


@dataclass
class StageRecord:
    """Record of a completed pipeline stage."""

    stage: str
    engine: str | None
    status: str  # "succeeded", "failed", "skipped"
    attempt: int
    started_at: str  # ISO 8601
    finished_at: str  # ISO 8601
    wall_time_s: float
    input_hashes: dict[str, str] = field(default_factory=dict)
    output_hashes: dict[str, str] = field(default_factory=dict)
    error: str | None = None


@dataclass
class RunManifest:
    """Complete provenance manifest for a run.

    Written to ``manifest.json`` alongside the run outputs.
    Stores everything needed to verify and reproduce the run.
    """

    run_id: str
    scenario_id: str
    scenario_name: str
    config_sha256: str
    pravahx_version: str = field(default_factory=lambda: pravahx.__version__)
    python_version: str = field(default_factory=lambda: sys.version)
    platform: str = field(default_factory=lambda: platform.platform())
    secure_mode: bool = False
    deployment_mode: str = "full"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    finished_at: str | None = None

    # Versions of external engines used
    engine_versions: dict[str, str] = field(default_factory=dict)

    # Pinned dependency versions
    dependency_versions: dict[str, str] = field(default_factory=dict)

    # Input data provenance
    input_hashes: dict[str, str] = field(default_factory=dict)

    # Stage-by-stage record
    stages: list[StageRecord] = field(default_factory=list)

    # Output artefacts
    artifacts: list[ArtifactRecord] = field(default_factory=list)

    # Overall status
    status: str = "created"  # created, running, succeeded, partially_succeeded, failed

    # Precomputed import metadata (constraint A)
    precomputed_imports: list[dict[str, Any]] = field(default_factory=list)

    def add_stage(self, stage: StageRecord) -> None:
        """Record a completed stage."""
        self.stages.append(stage)

    def add_artifact(self, artifact: ArtifactRecord) -> None:
        """Record an output artefact."""
        self.artifacts.append(artifact)

    def record_precomputed_import(
        self,
        engine: str,
        source_dir: str,
        run_date: str,
        file_hashes: dict[str, str],
    ) -> None:
        """Record that precomputed results were imported (constraint A)."""
        self.precomputed_imports.append(
            {
                "engine": engine,
                "source_dir": source_dir,
                "run_date": run_date,
                "import_time": datetime.datetime.now(datetime.UTC).isoformat(),
                "file_hashes": file_hashes,
                "verified": True,
            }
        )

    def finish(self, status: str) -> None:
        """Mark the run as finished."""
        self.status = status
        self.finished_at = datetime.datetime.now(datetime.UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a dict suitable for JSON."""
        return asdict(self)

    def save(self, path: Path) -> str:
        """Write the manifest to a JSON file and return its SHA-256."""
        text = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        path.write_text(text, encoding="utf-8")
        return compute_string_sha256(text)

    @classmethod
    def load(cls, path: Path) -> RunManifest:
        """Load a manifest from a JSON file."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        stages = [StageRecord(**s) for s in raw.pop("stages", [])]
        artifacts = [ArtifactRecord(**a) for a in raw.pop("artifacts", [])]
        manifest = cls(**raw)
        manifest.stages = stages
        manifest.artifacts = artifacts
        return manifest


def verify_artifacts(manifest: RunManifest, base_dir: Path) -> list[str]:
    """Verify SHA-256 hashes of all artefacts in a manifest.

    Returns a list of issues (empty if all hashes match).
    """
    issues: list[str] = []
    for artifact in manifest.artifacts:
        artifact_path = base_dir / artifact.path
        if not artifact_path.exists():
            issues.append(f"Missing artefact: {artifact.path}")
            continue
        actual = compute_file_sha256(artifact_path)
        if actual != artifact.sha256:
            issues.append(
                f"Hash mismatch for {artifact.path}: "
                f"expected {artifact.sha256[:16]}…, got {actual[:16]}…"
            )
    return issues
