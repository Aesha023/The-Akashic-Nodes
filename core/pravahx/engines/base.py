"""Engine adapter protocol and shared types (Section 7 of the build spec).

Every hydrodynamic engine implements the ``EngineAdapter`` protocol.
No other code may call a solver directly.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pravahx.config.schema import ScenarioConfig


# ── Shared types ─────────────────────────────────────────────────────────────


class EngineStatus(str, Enum):
    """Solver execution outcome."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class RunContext:
    """Everything an engine adapter needs to build and run a case.

    Attributes:
        config: Validated scenario configuration.
        work_dir: Working directory for this run (engine-specific sub-dir).
        terrain_dir: Directory containing prepared terrain data (DEM, roughness, HAND).
        breach_hydrograph_path: Path to the computed breach outflow hydrograph.
        run_id: Unique run identifier for provenance.
        engine_versions: Dict of engine name → version string.
        input_hashes: Dict of input file path → SHA-256 hash for provenance.
    """

    config: ScenarioConfig
    work_dir: Path
    terrain_dir: Path
    breach_hydrograph_path: Path | None
    run_id: str
    engine_versions: dict[str, str] = field(default_factory=dict)
    input_hashes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PreparedCase:
    """Output of the prepare step: all solver input files ready to execute.

    Attributes:
        engine_name: Name of the engine that prepared this case.
        case_dir: Directory containing all solver input files.
        input_file_hashes: SHA-256 of each input file for provenance.
        metadata: Engine-specific preparation metadata.
    """

    engine_name: str
    case_dir: Path
    input_file_hashes: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RawResult:
    """Output of the run step: solver completed with logs captured.

    Attributes:
        engine_name: Name of the engine that ran.
        status: Solver exit status.
        output_dir: Directory containing raw solver output.
        log_path: Path to the captured solver log.
        wall_time_s: Wall-clock time in seconds.
        exit_code: Solver process exit code.
        error_message: Error description if failed.
    """

    engine_name: str
    status: EngineStatus
    output_dir: Path
    log_path: Path
    wall_time_s: float
    exit_code: int
    error_message: str | None = None


@dataclass(frozen=True)
class NormalisedLayer:
    """A single normalised output raster (Section 8).

    Attributes:
        name: Layer name (max_depth, max_velocity, arrival_time, etc.).
        path: Path to the Cloud Optimised GeoTIFF.
        unit: Physical unit (m, m/s, minutes, 0/1).
        sha256: SHA-256 hash of the file.
        nodata: No-data value used.
    """

    name: str
    path: Path
    unit: str
    sha256: str
    nodata: float | None


@dataclass(frozen=True)
class NormalisedOutput:
    """Normalised output from any engine (Section 8).

    All engines produce the same set of rasters on the scenario grid,
    in the scenario CRS, as Cloud Optimised GeoTIFF.

    Attributes:
        engine_name: Name of the engine.
        engine_version: Version of the engine.
        layers: List of normalised raster layers.
        crs: CRS of all output rasters (EPSG code).
        grid_resolution_m: Resolution of the output grid in metres.
        depth_threshold_m: Depth threshold used for extent and arrival time.
        wall_time_s: Total wall-clock time in seconds.
        input_hashes: SHA-256 of input files used.
        timeseries_path: Optional path to NetCDF time series for the time slider.
        metadata: Additional engine-specific metadata.
        is_precomputed: Whether this output was imported (not run locally).
        precomputed_run_date: ISO date of the original run, if precomputed.
    """

    engine_name: str
    engine_version: str
    layers: list[NormalisedLayer]
    crs: str
    grid_resolution_m: float
    depth_threshold_m: float
    wall_time_s: float
    input_hashes: dict[str, str]
    timeseries_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_precomputed: bool = False
    precomputed_run_date: str | None = None

    def get_layer(self, name: str) -> NormalisedLayer:
        """Get a layer by name. Raises KeyError if not found."""
        for layer in self.layers:
            if layer.name == name:
                return layer
        msg = f"Layer '{name}' not found. Available: {[l.name for l in self.layers]}"
        raise KeyError(msg)

    @property
    def layer_names(self) -> list[str]:
        """Names of all layers in this output."""
        return [layer.name for layer in self.layers]


# ── Required layer names ─────────────────────────────────────────────────────

REQUIRED_LAYERS: frozenset[str] = frozenset(
    {
        "max_depth",
        "max_velocity",
        "arrival_time",
        "time_to_peak",
        "extent",
    }
)

LAYER_UNITS: dict[str, str] = {
    "max_depth": "m",
    "max_velocity": "m/s",
    "arrival_time": "minutes",
    "time_to_peak": "minutes",
    "extent": "0/1",
}


def validate_normalised_output(output: NormalisedOutput) -> list[str]:
    """Check that a normalised output has all required layers with correct units.

    Returns a list of issues (empty if valid).
    """
    issues: list[str] = []
    present_names = set(output.layer_names)

    for required in REQUIRED_LAYERS:
        if required not in present_names:
            issues.append(f"Missing required layer: {required}")

    for layer in output.layers:
        expected_unit = LAYER_UNITS.get(layer.name)
        if expected_unit and layer.unit != expected_unit:
            issues.append(
                f"Layer '{layer.name}' has unit '{layer.unit}', expected '{expected_unit}'."
            )

    return issues


# ── Protocol ─────────────────────────────────────────────────────────────────


@runtime_checkable
class EngineAdapter(Protocol):
    """Protocol that every hydrodynamic engine must implement (Section 7).

    No other code may call a solver directly.
    """

    @property
    def name(self) -> str:
        """Unique engine name."""
        ...

    def prepare(self, ctx: RunContext) -> PreparedCase:
        """Build all solver input files from the run context.

        No solver execution happens here.

        Raises:
            EngineError: if input preparation fails.
        """
        ...

    def run(self, case: PreparedCase) -> RawResult:
        """Execute the solver. Capture logs, exit status, wall time.

        Raises:
            EngineError: if the solver fails (with the solver log attached).
        """
        ...

    def postprocess(self, raw: RawResult, ctx: RunContext) -> NormalisedOutput:
        """Convert solver output to the normalised output format (Section 8).

        Raises:
            EngineError: if postprocessing fails.
        """
        ...


# ── Utilities ────────────────────────────────────────────────────────────────


def compute_file_hash(path: Path, algorithm: str = "sha256") -> str:
    """Compute a hex-digest hash of a file, reading in chunks."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
