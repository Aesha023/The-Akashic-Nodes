"""DualSPHysics engine adapter implementing EngineAdapter protocol (Phase 3)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from pravahx.engines.base import (
    EngineAdapter,
    EngineStatus,
    NormalisedOutput,
    PreparedCase,
    RawResult,
    RunContext,
)
from pravahx.engines.dualsphysics.builder import build_dualsphysics_case
from pravahx.engines.dualsphysics.reader import read_dualsphysics_output
from pravahx.engines.dualsphysics.runner import DualSPHysicsExecutionMode, DualSPHysicsRunner
from pravahx.errors import EngineError

logger = logging.getLogger(__name__)


class DualSPHysicsAdapter(EngineAdapter):
    """DualSPHysics 3D Smoothed Particle Hydrodynamics (SPH) solver adapter (Tier 2).

    Supports three execution modes:
    1. 'cpu': Local CPU binary execution or verified dry-run.
    2. 'remote_gpu': Standalone GPU package generation for remote/cloud execution.
    3. 'import' / 'precomputed': Ingestion of precomputed results with SHA-256 validation.
    """

    def __init__(
        self,
        bin_dir: Path | None = None,
        default_mode: DualSPHysicsExecutionMode | str = DualSPHysicsExecutionMode.CPU,
    ) -> None:
        self.runner = DualSPHysicsRunner(bin_dir=bin_dir)
        self.default_mode = DualSPHysicsExecutionMode(str(default_mode).lower())
        self.status = EngineStatus.IDLE

    @property
    def name(self) -> str:
        return "dualsphysics"

    def prepare(self, context: RunContext) -> PreparedCase:
        """Prepare DualSPHysics simulation input files and XML case definition.

        Args:
            context: Scenario run context with domain bounds, source specs, and paths.

        Returns:
            PreparedCase containing case XML and input file hashes.
        """
        logger.info("Preparing DualSPHysics SPH simulation case...")
        self.status = EngineStatus.PREPARING
        try:
            prepared = build_dualsphysics_case(context)
            self.status = EngineStatus.IDLE
            return prepared
        except Exception as e:
            self.status = EngineStatus.FAILED
            raise EngineError(
                f"Failed to prepare DualSPHysics case: {e}",
                engine="dualsphysics",
            ) from e

    def run(
        self,
        case: PreparedCase,
        mode: DualSPHysicsExecutionMode | str | None = None,
        import_source: Path | None = None,
    ) -> RawResult:
        """Execute DualSPHysics simulation according to selected execution mode.

        Args:
            case: Prepared simulation case.
            mode: 'cpu', 'remote_gpu', or 'import' (defaults to config setting).
            import_source: Path to precomputed results directory or archive.

        Returns:
            RawResult with solver execution outcome and output paths.
        """
        logger.info("Running DualSPHysics simulation...")
        self.status = EngineStatus.RUNNING

        # Determine mode from arguments or case metadata
        exec_mode = mode or case.metadata.get("mode", self.default_mode)

        try:
            raw = self.runner.run(case, mode=exec_mode, import_source=import_source)
            self.status = raw.status
            return raw
        except Exception as e:
            self.status = EngineStatus.FAILED
            if isinstance(e, EngineError):
                raise
            raise EngineError(
                f"DualSPHysics execution failed: {e}",
                engine="dualsphysics",
            ) from e

    def postprocess(self, raw_result: RawResult, context: RunContext) -> NormalisedOutput:
        """Convert DualSPHysics particle output files to 5 standard GeoTIFF rasters.

        Args:
            raw_result: RawResult from solver execution.
            context: RunContext containing CRS, grid definitions, and working paths.

        Returns:
            NormalisedOutput with GeoTIFF raster layers and downstream hydrograph.
        """
        logger.info("Post-processing DualSPHysics simulation outputs...")
        try:
            return read_dualsphysics_output(raw_result, context)
        except Exception as e:
            if isinstance(e, EngineError):
                raise
            raise EngineError(
                f"Failed to postprocess DualSPHysics outputs: {e}",
                engine="dualsphysics",
            ) from e
