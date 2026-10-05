"""Tier 0 engine adapter (Phase 1).

Produces a rapid inundation envelope using the Height Above Nearest
Drainage (HAND) model and a synthetic rating curve.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np
import rasterio

from pravahx.engines.base import (
    EngineAdapter,
    EngineStatus,
    NormalisedLayer,
    NormalisedOutput,
    PreparedCase,
    RawResult,
    RunContext,
    compute_file_hash,
)
from pravahx.errors import EngineError
from pravahx.pipeline.rating import find_stage_for_discharge

logger = logging.getLogger(__name__)


class Tier0Engine(EngineAdapter):
    """Tier 0 (HAND) rapid inundation engine."""

    def __init__(self) -> None:
        self.status = EngineStatus.IDLE

    def prepare(self, context: RunContext) -> PreparedCase:
        """Prepare the Tier 0 run (verify HAND and inputs)."""
        logger.info("Preparing Tier 0 HAND envelope...")
        self.status = EngineStatus.PREPARING
        
        # Verify required inputs are available
        # We need a HAND raster and a peak discharge.
        # In Phase 1, the full breach hydrograph isn't built yet, so we assume
        # it is provided in context or we use a placeholder.
        hand_path = context.work_dir / "hand.tif"
        if not hand_path.exists():
            raise EngineError("HAND raster not found in working directory.", engine="tier0")
            
        return PreparedCase(
            engine_name="tier0",
            case_dir=context.work_dir,
            entrypoint_command="",
            input_hashes={"hand.tif": compute_file_hash(hand_path)},
        )

    def run(self, prepared: PreparedCase) -> RawResult:
        """Run the Tier 0 stage-discharge solver."""
        logger.info("Running Tier 0 envelope solver...")
        self.status = EngineStatus.RUNNING
        
        start_time = time.time()
        hand_path = prepared.case_dir / "hand.tif"
        
        # In later phases, this comes from the breach hydrograph.
        # For Phase 1 testing, we assume a peak discharge from config or a default.
        peak_discharge = 5000.0  # Placeholder, should come from context/config
        reach_slope = 0.001      # Placeholder
        mannings_n = 0.035       # Placeholder
        
        try:
            stage = find_stage_for_discharge(
                hand_path=hand_path,
                target_discharge=peak_discharge,
                slope=reach_slope,
                mannings_n=mannings_n,
            )
            logger.info(f"Tier 0 computed max stage: {stage:.2f} m")
            
            # Generate the inundation map (max_depth)
            out_path = prepared.case_dir / "tier0_max_depth.tif"
            with rasterio.open(hand_path) as src:
                hand = src.read(1)
                meta = src.meta.copy()
                nodata = src.nodata
                
            if nodata is not None:
                mask = (hand != nodata)
            else:
                mask = np.ones_like(hand, dtype=bool)
                
            # Depth = max(0, stage - hand)
            depth = np.zeros_like(hand, dtype=np.float32)
            valid = mask & (hand < stage)
            depth[valid] = stage - hand[valid]
            
            # Mask out non-inundated and nodata areas completely with nodata
            out_nodata = -9999.0
            depth[~valid] = out_nodata
            
            meta.update(dtype=rasterio.float32, nodata=out_nodata)
            
            with rasterio.open(out_path, "w", **meta) as dest:
                dest.write(depth, 1)
                
        except Exception as exc:
            self.status = EngineStatus.FAILED
            raise EngineError(f"Tier 0 run failed: {exc}", engine="tier0") from exc
            
        wall_time = time.time() - start_time
        self.status = EngineStatus.FINISHED
        
        return RawResult(
            engine_name="tier0",
            output_dir=prepared.case_dir,
            success=True,
            wall_time_s=wall_time,
            output_files=[out_path],
        )

    def postprocess(self, result: RawResult) -> NormalisedOutput:
        """Convert Tier 0 output to NormalisedOutput."""
        logger.info("Post-processing Tier 0 outputs...")
        
        depth_file = result.output_dir / "tier0_max_depth.tif"
        if not depth_file.exists():
            raise EngineError("Expected output tier0_max_depth.tif not found.", engine="tier0")
            
        layer = NormalisedLayer(
            name="max_depth",
            path=depth_file,
            unit="m",
            sha256=compute_file_hash(depth_file),
            nodata=-9999.0,
        )
        
        with rasterio.open(depth_file) as src:
            crs = src.crs.to_string() if src.crs else "unknown"
            res = src.res[0]
            
        return NormalisedOutput(
            engine_name="tier0",
            engine_version="0.1.0",
            layers=[layer],
            crs=crs,
            grid_resolution_m=res,
            depth_threshold_m=0.1,
            wall_time_s=result.wall_time_s,
            input_hashes={},  # In a full flow, map from run context
        )
