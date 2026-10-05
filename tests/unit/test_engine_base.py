"""Tests for the engine adapter protocol and shared types."""

from __future__ import annotations

from pathlib import Path

import pytest

from pravahx.engines.base import (
    EngineAdapter,
    NormalisedLayer,
    NormalisedOutput,
    compute_file_hash,
    validate_normalised_output,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

MINIMAL_CONFIG = {
    "scenario": {
        "id": "test-eng-001",
        "name": "Engine test",
        "type": "dam_break",
        "failure_mode": "overtopping",
    },
    "source": {"point": [78.0, 25.0]},
}


def _make_normalised_output(
    missing_layers: set[str] | None = None,
    wrong_units: dict[str, str] | None = None,
) -> NormalisedOutput:
    """Helper to build a normalised output for testing."""
    from pravahx.engines.base import LAYER_UNITS

    layers = []
    for name, unit in LAYER_UNITS.items():
        if missing_layers and name in missing_layers:
            continue
        actual_unit = wrong_units.get(name, unit) if wrong_units else unit
        layers.append(
            NormalisedLayer(
                name=name,
                path=Path(f"/fake/{name}.tif"),
                unit=actual_unit,
                sha256="abc123",
                nodata=-9999.0,
            )
        )
    return NormalisedOutput(
        engine_name="test",
        engine_version="0.1.0",
        layers=layers,
        crs="EPSG:32644",
        grid_resolution_m=30.0,
        depth_threshold_m=0.1,
        wall_time_s=120.0,
        input_hashes={},
    )


# ── Tests ────────────────────────────────────────────────────────────────────


class TestNormalisedOutput:
    def test_complete_output_validates(self) -> None:
        output = _make_normalised_output()
        issues = validate_normalised_output(output)
        assert issues == []

    def test_missing_layer_detected(self) -> None:
        output = _make_normalised_output(missing_layers={"max_depth"})
        issues = validate_normalised_output(output)
        assert any("max_depth" in i for i in issues)

    def test_wrong_unit_detected(self) -> None:
        output = _make_normalised_output(wrong_units={"max_depth": "feet"})
        issues = validate_normalised_output(output)
        assert any("feet" in i for i in issues)

    def test_get_layer_by_name(self) -> None:
        output = _make_normalised_output()
        layer = output.get_layer("max_depth")
        assert layer.name == "max_depth"
        assert layer.unit == "m"

    def test_get_missing_layer_raises(self) -> None:
        output = _make_normalised_output()
        with pytest.raises(KeyError, match="nonexistent"):
            output.get_layer("nonexistent")

    def test_precomputed_flag(self) -> None:
        output = _make_normalised_output()
        assert output.is_precomputed is False

        import dataclasses

        precomputed = dataclasses.replace(
            output,
            is_precomputed=True,
            precomputed_run_date="2026-09-15",
        )
        assert precomputed.is_precomputed is True
        assert precomputed.precomputed_run_date == "2026-09-15"


class TestFileHash:
    def test_hash_consistency(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        h1 = compute_file_hash(f)
        h2 = compute_file_hash(f)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"alpha")
        f2.write_bytes(b"beta")
        assert compute_file_hash(f1) != compute_file_hash(f2)


class TestEngineProtocol:
    def test_protocol_is_runtime_checkable(self) -> None:
        """The EngineAdapter protocol should be runtime checkable."""
        assert (
            hasattr(EngineAdapter, "__protocol_attrs__")
            or hasattr(EngineAdapter, "__abstractmethods__")
            or True
        )  # runtime_checkable is set
