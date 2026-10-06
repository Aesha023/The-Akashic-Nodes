"""Unit tests for DualSPHysics engine adapter, runner, reader, and benchmark (Phase 3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pravahx.config.schema import (
    BreachConfig,
    BreachMethod,
    DEMSource,
    DualSPHysicsConfig,
    DualSPHysicsMode,
    EnsembleQuantile,
    InputsConfig,
    ScenarioConfig,
    ScenarioHeader,
    ScenarioType,
    SourceConfig,
    TiersConfig,
)
from pravahx.engines.base import (
    EngineStatus,
    RunContext,
    validate_normalised_output,
)
from pravahx.engines.dualsphysics.adapter import DualSPHysicsAdapter
from pravahx.engines.dualsphysics.benchmark import (
    run_idealized_dam_break_benchmark,
)
from pravahx.engines.dualsphysics.builder import (
    DualSPHysicsBuilder,
    SPHDomainBounds,
    SPHFluidBlock,
    SPHSimulationParams,
    build_dualsphysics_case,
)
from pravahx.engines.dualsphysics.colab import export_colab_case_package
from pravahx.engines.dualsphysics.runner import (
    DualSPHysicsExecutionMode,
    DualSPHysicsRunner,
)
from pravahx.errors import EngineError


@pytest.fixture
def sample_scenario_config(tmp_path: Path) -> ScenarioConfig:
    """Create a minimal valid ScenarioConfig for testing."""
    return ScenarioConfig(
        scenario=ScenarioHeader(
            id="test-sph-01",
            name="Test DualSPHysics Scenario",
            type=ScenarioType.DAM_BREAK,
            failure_mode="overtopping",  # type: ignore[arg-type]
        ),
        source=SourceConfig(
            point=(78.30, 30.15),
            dam_height_m=25.0,
            storage_m3=200_000.0,
        ),
        inputs=InputsConfig(
            dem=DEMSource.COPERNICUS_GLO30,
        ),
        breach=BreachConfig(
            method=BreachMethod.FROEHLICH_2008,
            ensemble=[EnsembleQuantile.P10, EnsembleQuantile.P50, EnsembleQuantile.P90],
            width_uncertainty_factor=1.2,
            time_uncertainty_factor=1.3,
        ),
        tiers=TiersConfig(
            dualsphysics=DualSPHysicsConfig(
                enabled=True,
                particle_spacing_m=1.0,
                near_field_km=0.5,
                mode=DualSPHysicsMode.CPU,
            )
        ),
    )


@pytest.fixture
def sample_run_context(tmp_path: Path, sample_scenario_config: ScenarioConfig) -> RunContext:
    """Create a RunContext for DualSPHysics execution."""
    work_dir = tmp_path / "work"
    terrain_dir = tmp_path / "terrain"
    work_dir.mkdir(parents=True, exist_ok=True)
    terrain_dir.mkdir(parents=True, exist_ok=True)

    return RunContext(
        config=sample_scenario_config,
        work_dir=work_dir,
        terrain_dir=terrain_dir,
        breach_hydrograph_path=None,
        run_id="run-sph-test-01",
    )


def test_builder_dam_break_case(tmp_path: Path) -> None:
    """Verify builder produces a valid GenCase XML definition."""
    domain = SPHDomainBounds(x_min=0.0, x_max=10.0, y_min=0.0, y_max=2.0, z_min=0.0, z_max=4.0)
    fluid = SPHFluidBlock(x_min=0.0, x_max=3.0, y_min=0.0, y_max=2.0, z_min=0.0, z_max=2.0)
    params = SPHSimulationParams(dp_m=0.05, time_max_s=1.0)

    builder = DualSPHysicsBuilder(params)
    xml_path = builder.build_dam_break_case(
        domain=domain,
        fluid=fluid,
        output_dir=tmp_path,
        case_name="CaseTest",
        gauges=[(5.0, 1.0, 0.0)],
        downstream_flux_x=9.5,
    )

    assert xml_path.exists()
    content = xml_path.read_text(encoding="utf-8")
    assert "<case>" in content
    assert 'dp="0.0500"' in content
    assert 'key="Kernel" value="2"' in content
    assert "<flux_plane" in content
    assert '<gauge id="G1"' in content


def test_runner_cpu_mode(sample_run_context: RunContext) -> None:
    """Verify runner CPU mode generates outputs and valid manifest."""
    case = build_dualsphysics_case(sample_run_context)
    runner = DualSPHysicsRunner()

    raw = runner.run(case, mode=DualSPHysicsExecutionMode.CPU)

    assert raw.status in (EngineStatus.FINISHED, EngineStatus.SUCCESS)
    assert raw.output_dir.exists()
    assert raw.log_path.exists()

    manifest_path = raw.output_dir / "manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "files" in manifest
    assert len(manifest["files"]) > 0


def test_runner_remote_gpu_package(sample_run_context: RunContext) -> None:
    """Verify runner remote GPU mode creates standalone archive package."""
    case = build_dualsphysics_case(sample_run_context)
    runner = DualSPHysicsRunner()

    raw = runner.run(case, mode=DualSPHysicsExecutionMode.REMOTE_GPU)

    assert raw.status == EngineStatus.FINISHED
    pkg_files = list(raw.output_dir.glob("*.tar.gz"))
    assert len(pkg_files) == 1
    assert "gpu_package.tar.gz" in pkg_files[0].name


def test_runner_import_mode_valid_and_tamper_detection(sample_run_context: RunContext) -> None:
    """Verify runner import mode validates cryptographic hashes and detects tampering."""
    case = build_dualsphysics_case(sample_run_context)
    runner = DualSPHysicsRunner()

    # 1. First generate clean results in CPU mode
    raw_cpu = runner.run(case, mode=DualSPHysicsExecutionMode.CPU)
    clean_output = raw_cpu.output_dir

    # 2. Import clean output
    raw_imported = runner.run(
        case, mode=DualSPHysicsExecutionMode.IMPORT, import_source=clean_output
    )
    assert raw_imported.status == EngineStatus.SUCCESS

    # 3. Tamper with one output file
    csv_file = next(clean_output.glob("PartFluid_*.csv"))
    original_text = csv_file.read_text(encoding="utf-8")
    csv_file.write_text(original_text + "\n# TAMPERED LINE\n", encoding="utf-8")

    # 4. Import tampered output -> must raise EngineError
    with pytest.raises(EngineError, match=r"hash mismatch|validation failed"):
        runner.run(case, mode=DualSPHysicsExecutionMode.IMPORT, import_source=clean_output)


def test_idealized_dam_break_benchmark_against_reference() -> None:
    """Verify idealized dam break benchmark matches Martin & Moyce (1952) reference."""
    result = run_idealized_dam_break_benchmark()

    assert result.passes_tolerance is True
    assert result.relative_l2_error < 0.05  # Within 5% error
    assert result.rmse_m < 0.25  # RMSE under 25 cm on 14m surge front
    assert len(result.time_steps_s) > 5


def test_adapter_full_lifecycle(sample_run_context: RunContext) -> None:
    """Verify DualSPHysicsAdapter lifecycle: prepare -> run -> postprocess -> 5 GeoTIFFs."""
    adapter = DualSPHysicsAdapter()

    # 1. Prepare
    prepared = adapter.prepare(sample_run_context)
    assert prepared.engine_name == "dualsphysics"
    assert len(prepared.input_file_hashes) > 0

    # 2. Run
    raw = adapter.run(prepared, mode="cpu")
    assert raw.status in (EngineStatus.FINISHED, EngineStatus.SUCCESS)

    # 3. Postprocess
    output = adapter.postprocess(raw, sample_run_context)
    assert output.engine_name == "dualsphysics"
    assert len(output.layers) == 5

    # Check required layers
    layer_names = set(output.layer_names)
    for req in ["max_depth", "max_velocity", "arrival_time", "time_to_peak", "extent"]:
        assert req in layer_names
        layer = output.get_layer(req)
        assert layer.path.exists()
        assert len(layer.sha256) == 64

    # Check validation
    issues = validate_normalised_output(output)
    assert issues == []

    # Check hydrograph metadata
    assert "hydrograph_path" in output.metadata
    hg_file = Path(output.metadata["hydrograph_path"])
    assert hg_file.exists()


def test_colab_case_package_export(sample_run_context: RunContext, tmp_path: Path) -> None:
    """Verify Google Colab package export utility."""
    prepared = build_dualsphysics_case(sample_run_context)
    tar_path = tmp_path / "dualsphysics_colab_case.tar.gz"

    exported = export_colab_case_package(prepared, tar_path)
    assert exported.exists()
    assert exported.stat().st_size > 0
