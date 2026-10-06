"""Delft3D Flexible Mesh engine adapter (Phase 2b)."""

from __future__ import annotations

import logging

from pravahx.engines.base import (
    EngineAdapter,
    EngineStatus,
    NormalisedOutput,
    PreparedCase,
    RawResult,
    RunContext,
)
from pravahx.engines.delft3d_fm.builder import build_delft3d_case
from pravahx.engines.delft3d_fm.reader import read_delft3d_output
from pravahx.errors import EngineError

logger = logging.getLogger(__name__)


class Delft3DFMAdapter(EngineAdapter):
    """Delft3D Flexible Mesh hydrodynamic solver adapter (Tier 1)."""

    def __init__(self) -> None:
        self.status = EngineStatus.IDLE

    @property
    def name(self) -> str:
        return "delft3d_fm"

    def prepare(self, context: RunContext) -> PreparedCase:
        """Prepare Delft3D FM simulation input files using HYDROLIB-core.

        Generates .mdu, .ext, .bc, and .pli files for the scenario.
        """
        logger.info("Preparing Delft3D FM simulation case...")
        self.status = EngineStatus.PREPARING
        try:
            prepared = build_delft3d_case(context)
            self.status = EngineStatus.IDLE
            return prepared
        except Exception as e:
            self.status = EngineStatus.FAILED
            raise EngineError(
                f"Failed to prepare Delft3D FM case: {e}",
                engine="delft3d_fm",
            ) from e

    def run(self, prepared: PreparedCase) -> RawResult:
        """Execute Delft3D FM solver in its container.

        Currently blocked pending access to Deltares Harbor container registry.
        """
        self.status = EngineStatus.FAILED
        raise EngineError(
            "Delft3D FM solver execution is blocked pending Deltares container registry access "
            "and container runner deployment (Phase 2b).",
            engine="delft3d_fm",
        )

    def postprocess(self, raw_result: RawResult, context: RunContext) -> NormalisedOutput:
        """Read Delft3D FM NetCDF map output (*_map.nc) and export normalised layers."""
        logger.info("Post-processing Delft3D FM NetCDF simulation outputs...")
        try:
            return read_delft3d_output(raw_result, context)
        except Exception as e:
            raise EngineError(
                f"Failed to postprocess Delft3D FM outputs: {e}",
                engine="delft3d_fm",
            ) from e
