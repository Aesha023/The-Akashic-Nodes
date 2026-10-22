"""Tier 0 engine adapter (Phase 1).

Produces a rapid inundation envelope using the Height Above Nearest
Drainage (HAND) model and a synthetic rating curve.
"""

from __future__ import annotations

import logging
import time
from typing import Any

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
from pravahx.engines.tier0_hand.rating import find_stage_for_discharge
from pravahx.errors import EngineError

logger = logging.getLogger(__name__)


class Tier0HandAdapter(EngineAdapter):
    """Tier 0 (HAND) rapid inundation engine."""

    def __init__(self, strict: bool = True) -> None:
        self.status = EngineStatus.IDLE
        self.strict = strict

    @property
    def name(self) -> str:
        return "tier0"

    def prepare(self, context: RunContext) -> PreparedCase:
        """Prepare the Tier 0 run (verify HAND and inputs)."""
        logger.info("Preparing Tier 0 HAND envelope...")
        self.status = EngineStatus.PREPARING

        # Verify required inputs are available
        hand_path = context.work_dir / "hand.tif"
        if not hand_path.exists():
            raise EngineError("HAND raster not found in working directory.", engine="tier0")

        metadata: dict[str, Any] = {"strict": self.strict}

        # Attempt to read peak discharge from breach hydrograph if provided
        if context.breach_hydrograph_path and context.breach_hydrograph_path.exists():
            try:
                import pandas as pd

                df = pd.read_csv(context.breach_hydrograph_path)
                q_cols = [c for c in df.columns if "discharge" in c.lower() or c.lower() == "q"]
                if q_cols:
                    metadata["peak_discharge"] = float(df[q_cols[0]].max())
            except Exception as exc:
                logger.debug(f"Could not read peak discharge from hydrograph: {exc}")

        return PreparedCase(
            engine_name="tier0",
            case_dir=context.work_dir,
            input_file_hashes={"hand.tif": compute_file_hash(hand_path)},
            metadata=metadata,
        )

    def run(self, prepared: PreparedCase) -> RawResult:
        """Run the Tier 0 stage-discharge solver."""
        logger.info("Running Tier 0 envelope solver...")
        self.status = EngineStatus.RUNNING

        start_time = time.time()
        hand_path = prepared.case_dir / "hand.tif"

        raw_peak = prepared.metadata.get("peak_discharge")
        peak_discharge: float | None = float(raw_peak) if raw_peak is not None else None
        raw_slope = prepared.metadata.get("reach_slope")
        reach_slope: float | None = float(raw_slope) if raw_slope is not None else None
        raw_n = prepared.metadata.get("mannings_n")
        mannings_n: float | None = float(raw_n) if raw_n is not None else None
        strict: bool = bool(prepared.metadata.get("strict", self.strict))

        missing = []
        if peak_discharge is None:
            missing.append("peak_discharge")
        if reach_slope is None:
            missing.append("reach_slope")
        if mannings_n is None:
            missing.append("mannings_n")

        defaults_used: list[str] = []
        if missing:
            if strict:
                self.status = EngineStatus.FAILED
                raise EngineError(
                    f"Missing required Tier-0 input(s): {', '.join(missing)}. "
                    "Silent fallbacks are disabled in strict mode; provide explicit inputs.",
                    engine="tier0",
                )
            if peak_discharge is None:
                peak_discharge = 5000.0
                defaults_used.append("DEFAULT USED: peak_discharge=5000.0 m3/s")
            if reach_slope is None:
                reach_slope = 0.001
                defaults_used.append("DEFAULT USED: reach_slope=0.001")
            if mannings_n is None:
                mannings_n = 0.035
                defaults_used.append("DEFAULT USED: mannings_n=0.035")

            for warning_msg in defaults_used:
                logger.warning(f"[Tier0HandAdapter] {warning_msg}")

        assert peak_discharge is not None
        assert reach_slope is not None
        assert mannings_n is not None

        log_path = prepared.case_dir / "tier0.log"
        with open(log_path, "a", encoding="utf-8") as log_f:
            if defaults_used:
                for warning_msg in defaults_used:
                    log_f.write(f"{warning_msg}\n")
            log_f.write(
                f"Tier-0 solver configuration: peak_discharge={peak_discharge:.1f} m3/s, "
                f"reach_slope={reach_slope}, mannings_n={mannings_n}\n"
            )

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
            mask = (hand != nodata) & (~np.isnan(hand)) if nodata is not None else ~np.isnan(hand)

            # Depth = max(0, stage - hand)
            depth = np.zeros_like(hand, dtype=np.float32)
            valid = mask & (hand >= 0) & (hand < stage)

            # Spatial connectivity filtering: keep only cells connected to channel
            main_reach_path = prepared.case_dir / "main_reach.tif"
            if np.any(valid):
                from collections import deque

                main_reach = None
                if main_reach_path.exists():
                    with rasterio.open(main_reach_path) as src_reach:
                        main_reach = src_reach.read(1)

                seed_mask = (main_reach > 0) if main_reach is not None else (hand == 0)
                seed_coords = np.argwhere(seed_mask & valid)
                if len(seed_coords) == 0 and np.any(valid):
                    # If channel didn't overlap valid, seed from minimum HAND cell
                    min_h = np.min(hand[valid])
                    seed_coords = np.argwhere((hand == min_h) & valid)

                visited = np.zeros_like(valid, dtype=bool)
                queue: deque[tuple[int, int]] = deque()
                for sc in seed_coords:
                    r_s, c_s = int(sc[0]), int(sc[1])
                    visited[r_s, c_s] = True
                    queue.append((r_s, c_s))

                h_dim, w_dim = valid.shape
                while queue:
                    curr_r, curr_c = queue.popleft()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = curr_r + dr, curr_c + dc
                            if (
                                0 <= nr < h_dim
                                and 0 <= nc < w_dim
                                and valid[nr, nc]
                                and not visited[nr, nc]
                            ):
                                visited[nr, nc] = True
                                queue.append((nr, nc))

                valid = visited

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
            status=EngineStatus.SUCCESS,
            output_dir=prepared.case_dir,
            log_path=prepared.case_dir / "tier0.log",
            wall_time_s=wall_time,
            exit_code=0,
        )

    def postprocess(self, raw: RawResult, ctx: RunContext) -> NormalisedOutput:
        """Convert Tier 0 output to NormalisedOutput."""
        logger.info("Post-processing Tier 0 outputs...")

        depth_file = raw.output_dir / "tier0_max_depth.tif"
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
            wall_time_s=raw.wall_time_s,
            input_hashes={},  # In a full flow, map from run context
        )
