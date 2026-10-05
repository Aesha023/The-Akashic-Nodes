"""Tests for provenance — run manifest, hashing, verification."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pravahx.pipeline.provenance import (
    ArtifactRecord,
    RunManifest,
    StageRecord,
    compute_file_sha256,
    compute_string_sha256,
    verify_artifacts,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestHashing:
    def test_file_sha256_deterministic(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("reproducible", encoding="utf-8")
        h1 = compute_file_sha256(f)
        h2 = compute_file_sha256(f)
        assert h1 == h2
        assert len(h1) == 64

    def test_string_sha256(self) -> None:
        h = compute_string_sha256("hello")
        assert len(h) == 64
        assert h == compute_string_sha256("hello")
        assert h != compute_string_sha256("world")


class TestRunManifest:
    def test_create_and_serialize(self) -> None:
        manifest = RunManifest(
            run_id="run-001",
            scenario_id="scen-001",
            scenario_name="Test",
            config_sha256="abc123",
        )
        d = manifest.to_dict()
        assert d["run_id"] == "run-001"
        assert d["status"] == "created"
        assert isinstance(d["stages"], list)
        assert isinstance(d["artifacts"], list)

    def test_add_stage(self) -> None:
        manifest = RunManifest(
            run_id="r1", scenario_id="s1", scenario_name="Test", config_sha256="x"
        )
        stage = StageRecord(
            stage="terrain",
            engine=None,
            status="succeeded",
            attempt=1,
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:05:00Z",
            wall_time_s=300.0,
        )
        manifest.add_stage(stage)
        assert len(manifest.stages) == 1
        assert manifest.stages[0].stage == "terrain"

    def test_finish(self) -> None:
        manifest = RunManifest(
            run_id="r1", scenario_id="s1", scenario_name="Test", config_sha256="x"
        )
        manifest.finish("succeeded")
        assert manifest.status == "succeeded"
        assert manifest.finished_at is not None

    def test_save_and_load(self, tmp_path: Path) -> None:
        manifest = RunManifest(
            run_id="r1",
            scenario_id="s1",
            scenario_name="Test Save",
            config_sha256="abc",
        )
        manifest.add_artifact(
            ArtifactRecord(
                path="output/max_depth.tif",
                sha256="fake_hash",
                size_bytes=1024,
                kind="raster",
                engine="delft3d_fm",
                stage="postprocess",
            )
        )
        manifest.finish("succeeded")

        path = tmp_path / "manifest.json"
        sha = manifest.save(path)
        assert len(sha) == 64
        assert path.exists()

        loaded = RunManifest.load(path)
        assert loaded.run_id == "r1"
        assert loaded.scenario_name == "Test Save"
        assert loaded.status == "succeeded"
        assert len(loaded.artifacts) == 1
        assert loaded.artifacts[0].engine == "delft3d_fm"

    def test_precomputed_import_recorded(self) -> None:
        manifest = RunManifest(run_id="r1", scenario_id="s1", scenario_name="T", config_sha256="x")
        manifest.record_precomputed_import(
            engine="dualsphysics",
            source_dir="/data/sph",
            run_date="2026-09-15",
            file_hashes={"out.tif": "abc123"},
        )
        assert len(manifest.precomputed_imports) == 1
        assert manifest.precomputed_imports[0]["engine"] == "dualsphysics"
        assert manifest.precomputed_imports[0]["verified"] is True


class TestVerifyArtifacts:
    def test_all_valid(self, tmp_path: Path) -> None:
        f = tmp_path / "out.tif"
        f.write_bytes(b"raster data")
        sha = compute_file_sha256(f)

        manifest = RunManifest(run_id="r1", scenario_id="s1", scenario_name="T", config_sha256="x")
        manifest.add_artifact(
            ArtifactRecord(path="out.tif", sha256=sha, size_bytes=11, kind="raster")
        )

        issues = verify_artifacts(manifest, tmp_path)
        assert issues == []

    def test_missing_file(self, tmp_path: Path) -> None:
        manifest = RunManifest(run_id="r1", scenario_id="s1", scenario_name="T", config_sha256="x")
        manifest.add_artifact(
            ArtifactRecord(path="missing.tif", sha256="x", size_bytes=0, kind="raster")
        )
        issues = verify_artifacts(manifest, tmp_path)
        assert any("Missing" in i for i in issues)

    def test_hash_mismatch(self, tmp_path: Path) -> None:
        f = tmp_path / "corrupted.tif"
        f.write_bytes(b"original")

        manifest = RunManifest(run_id="r1", scenario_id="s1", scenario_name="T", config_sha256="x")
        manifest.add_artifact(
            ArtifactRecord(path="corrupted.tif", sha256="wrong_hash", size_bytes=8, kind="raster")
        )
        issues = verify_artifacts(manifest, tmp_path)
        assert any("mismatch" in i for i in issues)
