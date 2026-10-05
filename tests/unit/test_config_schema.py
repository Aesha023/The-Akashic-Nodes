"""Tests for the scenario configuration schema.

Phase 0 acceptance: an invalid config produces a clear error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml
from pydantic import ValidationError

from pravahx.config.schema import (
    DualSPHysicsMode,
    ExportFormat,
    FailureMode,
    ScenarioConfig,
    ScenarioType,
    VolumeMethod,
    load_scenario_config,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── Valid config ─────────────────────────────────────────────────────────────


VALID_DAM_BREAK = {
    "scenario": {
        "id": "test-001",
        "name": "Test dam break",
        "type": "dam_break",
        "failure_mode": "overtopping",
    },
    "source": {
        "point": [78.0, 25.0],
        "dam_height_m": 30,
        "storage_m3": 50_000_000,
        "volume_method": "user",
    },
    "domain": {
        "reach_length_km": 40,
        "buffer_km": 3,
        "crs": "auto",
    },
    "inputs": {
        "dem": "copernicus_glo30",
        "landcover": "worldcover",
    },
    "breach": {
        "method": "froehlich_2008",
        "ensemble": ["p10", "p50", "p90"],
    },
    "tiers": {
        "tier0": {"enabled": True},
        "delft3d_fm": {
            "enabled": True,
            "cell_size_m": {"coarse": 100, "fine": 30},
            "horizon_h": 12,
        },
        "dualsphysics": {
            "enabled": True,
            "particle_spacing_m": 2,
            "near_field_km": 2,
            "mode": "cpu",
        },
    },
    "compare": {"enabled": True, "max_refinements": 2},
    "cascade": {"enabled": True},
    "gee": {"enabled": False},
    "impact": {"enabled": True},
    "exports": ["shp", "kml", "cog", "pdf"],
}


class TestValidConfig:
    """Tests for valid scenario configs."""

    def test_full_dam_break_config(self) -> None:
        config = ScenarioConfig.model_validate(VALID_DAM_BREAK)
        assert config.scenario.id == "test-001"
        assert config.scenario.type == ScenarioType.DAM_BREAK
        assert config.scenario.failure_mode == FailureMode.OVERTOPPING
        assert config.source.point == (78.0, 25.0)
        assert config.source.dam_height_m == 30
        assert config.source.volume_method == VolumeMethod.USER
        assert config.tiers.delft3d_fm.enabled is True
        assert config.tiers.dualsphysics.mode == DualSPHysicsMode.CPU
        assert ExportFormat.SHP in config.exports

    def test_minimal_dam_break(self) -> None:
        """Minimal valid config: only required fields."""
        config = ScenarioConfig.model_validate(
            {
                "scenario": {
                    "id": "min-001",
                    "name": "Minimal",
                    "type": "dam_break",
                    "failure_mode": "piping",
                },
                "source": {"dam_id": "IND-DAM-123"},
            }
        )
        assert config.scenario.type == ScenarioType.DAM_BREAK
        assert config.scenario.failure_mode == FailureMode.PIPING
        assert config.source.dam_id == "IND-DAM-123"
        # Defaults applied
        assert config.domain.reach_length_km == 60
        assert config.tiers.tier0.enabled is True

    def test_blockage_type(self) -> None:
        config = ScenarioConfig.model_validate(
            {
                "scenario": {
                    "id": "block-001",
                    "name": "Landslide blockage",
                    "type": "blockage",
                },
                "source": {"polygon": "tests/fixtures/lake.geojson"},
            }
        )
        assert config.scenario.type == ScenarioType.BLOCKAGE
        assert config.scenario.failure_mode is None

    def test_precomputed_sph_mode(self) -> None:
        """Constraint A: precomputed mode requires dir and date."""
        config = ScenarioConfig.model_validate(
            {
                "scenario": {
                    "id": "pre-001",
                    "name": "Precomputed SPH",
                    "type": "dam_break",
                    "failure_mode": "overtopping",
                },
                "source": {"point": [78.0, 25.0]},
                "tiers": {
                    "dualsphysics": {
                        "mode": "precomputed",
                        "precomputed_dir": "/data/sph_results",
                        "precomputed_run_date": "2026-09-15",
                    },
                },
            }
        )
        assert config.tiers.dualsphysics.mode == DualSPHysicsMode.PRECOMPUTED
        assert config.tiers.dualsphysics.precomputed_run_date == "2026-09-15"


# ── Invalid configs ──────────────────────────────────────────────────────────


class TestInvalidConfig:
    """Tests that invalid configs produce clear, actionable errors."""

    def test_missing_scenario_id(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig.model_validate(
                {
                    "scenario": {"name": "No ID", "type": "dam_break", "failure_mode": "piping"},
                    "source": {"point": [78.0, 25.0]},
                }
            )
        errors = exc_info.value.errors()
        assert any("id" in str(e["loc"]) for e in errors)

    def test_dam_break_without_failure_mode(self) -> None:
        with pytest.raises(ValidationError, match="failure_mode is required"):
            ScenarioConfig.model_validate(
                {
                    "scenario": {"id": "x", "name": "X", "type": "dam_break"},
                    "source": {"point": [78.0, 25.0]},
                }
            )

    def test_non_dam_break_with_failure_mode(self) -> None:
        with pytest.raises(ValidationError, match="failure_mode is only valid"):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "blockage",
                        "failure_mode": "piping",
                    },
                    "source": {"point": [78.0, 25.0]},
                }
            )

    def test_no_source_location(self) -> None:
        with pytest.raises(ValidationError, match="At least one of"):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {},
                }
            )

    def test_negative_dam_height(self) -> None:
        with pytest.raises(ValidationError):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0], "dam_height_m": -10},
                }
            )

    def test_fine_larger_than_coarse(self) -> None:
        with pytest.raises(ValidationError, match=r"fine.*smaller"):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                    "tiers": {
                        "delft3d_fm": {
                            "cell_size_m": {"coarse": 30, "fine": 100},
                        },
                    },
                }
            )

    def test_precomputed_without_dir(self) -> None:
        with pytest.raises(ValidationError, match="precomputed_dir is required"):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                    "tiers": {
                        "dualsphysics": {"mode": "precomputed"},
                    },
                }
            )

    def test_unknown_field_rejected(self) -> None:
        """extra='forbid' means unknown fields produce an error."""
        with pytest.raises(ValidationError):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                    "unknown_field": True,
                }
            )

    def test_secure_mode_not_in_config(self) -> None:
        """Decision D001: secure_mode is system-level, not in scenario config."""
        with pytest.raises(ValidationError):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                    "secure_mode": True,
                }
            )

    def test_scenario_id_invalid_chars(self) -> None:
        with pytest.raises(ValidationError):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "has spaces!",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                }
            )

    def test_reach_length_too_large(self) -> None:
        with pytest.raises(ValidationError):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                    "domain": {"reach_length_km": 999},
                }
            )

    def test_max_refinements_exceeds_limit(self) -> None:
        with pytest.raises(ValidationError):
            ScenarioConfig.model_validate(
                {
                    "scenario": {
                        "id": "x",
                        "name": "X",
                        "type": "dam_break",
                        "failure_mode": "overtopping",
                    },
                    "source": {"point": [78.0, 25.0]},
                    "compare": {"max_refinements": 5},
                }
            )


# ── YAML loading ─────────────────────────────────────────────────────────────


class TestYamlLoading:
    """Tests for loading config from YAML files."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "scenario.yaml"
        yaml_path.write_text(yaml.dump(VALID_DAM_BREAK), encoding="utf-8")
        config = load_scenario_config(yaml_path)
        assert config.scenario.id == "test-001"

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "bad.yaml"
        yaml_path.write_text("not: a: valid: scenario", encoding="utf-8")
        with pytest.raises((ValidationError, ValueError)):
            load_scenario_config(yaml_path)

    def test_load_non_dict_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "list.yaml"
        yaml_path.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(ValueError, match="YAML mapping"):
            load_scenario_config(yaml_path)
