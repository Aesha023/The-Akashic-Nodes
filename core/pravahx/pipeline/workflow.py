"""Workflow orchestrator coordinating end-to-end multi-tier flood modeling (Phase 6)."""

from __future__ import annotations

import datetime
import json
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from pravahx.breach import (
    BreachHydrograph,
    compute_froehlich_2008,
    route_hydrograph,
)
from pravahx.cascade.downstream import (
    CascadeAnalyzer,
    DamStructure,
)
from pravahx.compare.agreement import generate_agreement_raster
from pravahx.compare.metrics import compute_comparison_metrics
from pravahx.compare.refine import compute_refinement_zones
from pravahx.errors import StageError
from pravahx.pipeline.checkpoint import CheckpointManager
from pravahx.pipeline.provenance import (
    ArtifactRecord,
    RunManifest,
    StageRecord,
    compute_file_sha256,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pravahx.config.schema import ScenarioConfig

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float, str], None]


class WorkflowOrchestrator:
    """Executes multi-tier hydrodynamic scenarios with checkpointing and provenance tracking."""

    def __init__(
        self,
        work_dir: Path,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback

    def _report_progress(self, stage: str, fraction: float, message: str) -> None:
        if self.progress_callback is not None:
            try:
                self.progress_callback(stage, fraction, message)
            except Exception as e:
                logger.warning("Error in progress callback: %s", e)

    def execute(self, config: ScenarioConfig, resume: bool = True) -> RunManifest:
        """Execute a complete scenario pipeline according to ScenarioConfig.

        Args:
            config: Validated ScenarioConfig.
            resume: If True, skips stages with valid existing checkpoints.

        Returns:
            RunManifest containing complete run metadata, stage records, and artifact hashes.
        """
        run_id = f"run_{config.scenario.id}_{int(time.time())}"
        checkpoint_mgr = CheckpointManager(self.work_dir, run_id=run_id)

        config_path = self.work_dir / "scenario_config.json"
        config_json = config.model_dump_json(indent=2)
        config_path.write_text(config_json, encoding="utf-8")
        config_hash = compute_file_sha256(config_path)

        manifest = RunManifest(
            run_id=run_id,
            scenario_id=config.scenario.id,
            scenario_name=config.scenario.name,
            config_sha256=config_hash,
        )

        completed_stages: list[str] = []
        artifacts: list[ArtifactRecord] = []

        # Record config artifact
        artifacts.append(
            ArtifactRecord(
                path="scenario_config.json",
                sha256=config_hash,
                size_bytes=config_path.stat().st_size,
                kind="config",
            )
        )

        try:
            # ── Stage 1: Data Preparation & Reservoir Geometry ───────────────
            stage_name = "data_prep"
            if resume and checkpoint_mgr.is_stage_done(stage_name):
                logger.info("Resuming: Stage '%s' already completed.", stage_name)
                completed_stages.append(stage_name)
            else:
                self._report_progress(
                    stage_name, 0.10, "Preparing spatial terrain and reservoir data..."
                )
                t0 = time.time()
                started_at = datetime.datetime.now(datetime.UTC).isoformat()

                h_dam = config.source.dam_height_m or 50.0
                v_storage = config.source.storage_m3 or 10_000_000.0

                finished_at = datetime.datetime.now(datetime.UTC).isoformat()
                stage_rec = StageRecord(
                    stage=stage_name,
                    engine=None,
                    status="succeeded",
                    attempt=1,
                    started_at=started_at,
                    finished_at=finished_at,
                    wall_time_s=round(time.time() - t0, 3),
                )
                manifest.add_stage(stage_rec)
                completed_stages.append(stage_name)
                checkpoint_mgr.save_checkpoint(
                    stage=stage_name,
                    completed_stages=completed_stages,
                    artifacts=artifacts,
                    data_payload={"h_dam": h_dam, "v_storage": v_storage},
                )

            # ── Stage 2: Breach Hydrograph Modeling ─────────────────────────
            stage_name = "breach_calculation"
            breach_hydro_res: BreachHydrograph | None = None
            hydrograph_csv_path = self.work_dir / "breach_hydrograph.csv"

            if resume and checkpoint_mgr.is_stage_done(stage_name):
                logger.info("Resuming: Stage '%s' already completed.", stage_name)
                completed_stages.append(stage_name)
            else:
                self._report_progress(stage_name, 0.25, "Computing Froehlich breach hydrograph...")
                t0 = time.time()
                started_at = datetime.datetime.now(datetime.UTC).isoformat()

                h_dam = config.source.dam_height_m or 50.0
                v_storage = config.source.storage_m3 or 10_000_000.0

                fail_mode = config.scenario.failure_mode
                failure_mode_str = "overtopping" if fail_mode is None else fail_mode.value
                mode_param: Literal["overtopping", "piping"] = (
                    "overtopping" if failure_mode_str == "overtopping" else "piping"
                )

                breach_params = compute_froehlich_2008(
                    volume_m3=v_storage,
                    height_m=h_dam,
                    mode=mode_param,
                )

                breach_hydro_res = route_hydrograph(
                    initial_volume_m3=v_storage,
                    dam_height_m=h_dam,
                    b_avg_m=breach_params.average_width_m,
                    t_f_hr=breach_params.formation_time_hr,
                    reservoir_exponent=2.0,
                    side_slope_z=breach_params.side_slope_z,
                )

                # Save hydrograph CSV
                import csv

                with open(hydrograph_csv_path, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["time_hr", "discharge_m3s", "volume_remaining_m3", "head_m"])
                    for pt in breach_hydro_res.points:
                        w.writerow(
                            [
                                pt["time_hr"],
                                round(pt["discharge_m3s"], 3),
                                round(pt["volume_remaining_m3"], 3),
                                round(pt["head_m"], 3),
                            ]
                        )

                hydro_hash = compute_file_sha256(hydrograph_csv_path)
                art_rec = ArtifactRecord(
                    path="breach_hydrograph.csv",
                    sha256=hydro_hash,
                    size_bytes=hydrograph_csv_path.stat().st_size,
                    kind="csv",
                    stage=stage_name,
                )
                artifacts.append(art_rec)
                manifest.add_artifact(art_rec)

                finished_at = datetime.datetime.now(datetime.UTC).isoformat()
                stage_rec = StageRecord(
                    stage=stage_name,
                    engine=None,
                    status="succeeded",
                    attempt=1,
                    started_at=started_at,
                    finished_at=finished_at,
                    wall_time_s=round(time.time() - t0, 3),
                    output_hashes={"breach_hydrograph.csv": hydro_hash},
                )
                manifest.add_stage(stage_rec)
                completed_stages.append(stage_name)
                checkpoint_mgr.save_checkpoint(
                    stage=stage_name,
                    completed_stages=completed_stages,
                    artifacts=artifacts,
                    data_payload={
                        "peak_discharge_m3s": breach_hydro_res.peak_discharge_m3s,
                        "time_to_peak_hr": breach_hydro_res.time_to_peak_hr,
                    },
                )

            # ── Stage 3: Multi-Dam Cascade Evaluation ────────────────────────
            if config.cascade.enabled:
                stage_name = "cascade_analysis"
                if resume and checkpoint_mgr.is_stage_done(stage_name):
                    logger.info("Resuming: Stage '%s' already completed.", stage_name)
                    completed_stages.append(stage_name)
                else:
                    self._report_progress(stage_name, 0.50, "Evaluating multi-dam cascade links...")
                    t0 = time.time()
                    started_at = datetime.datetime.now(datetime.UTC).isoformat()

                    from pravahx.cascade.downstream import ChannelHydrographPoint

                    upstream_dam = DamStructure(
                        id="upstream_dam",
                        name=config.scenario.name,
                        river="Main Stem",
                        chainage_km=0.0,
                        dam_height_m=config.source.dam_height_m or 50.0,
                        storage_m3=config.source.storage_m3 or 10_000_000.0,
                        crest_elevation_m=config.source.dam_height_m or 50.0,
                        bed_elevation_m=0.0,
                        spillway_capacity_m3s=1500.0,
                    )
                    downstream_dam = DamStructure(
                        id="downstream_barrage",
                        name="Downstream Barrage",
                        river="Main Stem",
                        chainage_km=25.0,
                        dam_height_m=20.0,
                        storage_m3=1_000_000.0,
                        crest_elevation_m=20.0,
                        bed_elevation_m=0.0,
                        spillway_capacity_m3s=2000.0,
                    )

                    channel_points: list[ChannelHydrographPoint] = []
                    if breach_hydro_res is not None:
                        for pt in breach_hydro_res.points:
                            channel_points.append(
                                ChannelHydrographPoint(
                                    time_seconds=pt["time_hr"] * 3600.0,
                                    discharge_m3s=pt["discharge_m3s"],
                                    reservoir_head_m=pt["head_m"],
                                    volume_remaining_m3=pt["volume_remaining_m3"],
                                )
                            )
                    else:
                        channel_points.append(
                            ChannelHydrographPoint(time_seconds=0.0, discharge_m3s=5000.0)
                        )

                    analyzer = CascadeAnalyzer()
                    cascade_summary = analyzer.evaluate_cascade(
                        scenario_id=config.scenario.id,
                        initial_dam=upstream_dam,
                        initial_hydrograph=channel_points,
                        downstream_dams=[downstream_dam],
                    )

                    cascade_json = self.work_dir / "cascade_summary.json"
                    from dataclasses import asdict

                    cascade_json.write_text(
                        json.dumps(asdict(cascade_summary), indent=2, default=str),
                        encoding="utf-8",
                    )
                    casc_hash = compute_file_sha256(cascade_json)

                    art_rec = ArtifactRecord(
                        path="cascade_summary.json",
                        sha256=casc_hash,
                        size_bytes=cascade_json.stat().st_size,
                        kind="json",
                        stage=stage_name,
                    )
                    artifacts.append(art_rec)
                    manifest.add_artifact(art_rec)

                    finished_at = datetime.datetime.now(datetime.UTC).isoformat()
                    manifest.add_stage(
                        StageRecord(
                            stage=stage_name,
                            engine=None,
                            status="succeeded",
                            attempt=1,
                            started_at=started_at,
                            finished_at=finished_at,
                            wall_time_s=round(time.time() - t0, 3),
                            output_hashes={"cascade_summary.json": casc_hash},
                        )
                    )
                    completed_stages.append(stage_name)
                    checkpoint_mgr.save_checkpoint(
                        stage=stage_name,
                        completed_stages=completed_stages,
                        artifacts=artifacts,
                    )

            # ── Stage 4: Multi-Tier Comparison & Spatial Agreement ──────────
            if config.compare.enabled:
                stage_name = "comparison"
                if resume and checkpoint_mgr.is_stage_done(stage_name):
                    logger.info("Resuming: Stage '%s' already completed.", stage_name)
                    completed_stages.append(stage_name)
                else:
                    self._report_progress(
                        stage_name, 0.85, "Performing multi-tier spatial comparison..."
                    )
                    t0 = time.time()
                    started_at = datetime.datetime.now(datetime.UTC).isoformat()

                    # Look for existing depth rasters in work_dir
                    depth_rasters = list(self.work_dir.glob("**/max_depth.tif"))
                    if len(depth_rasters) >= 2:
                        agree_tif = self.work_dir / "agreement_map.tif"
                        generate_agreement_raster(
                            raster_a_path=depth_rasters[0],
                            raster_b_path=depth_rasters[1],
                            output_path=agree_tif,
                        )

                        comp_metrics = compute_comparison_metrics(
                            depth_a_path=depth_rasters[0],
                            depth_b_path=depth_rasters[1],
                        )

                        metrics_json = self.work_dir / "comparison_metrics.json"
                        metrics_json.write_text(
                            comp_metrics.model_dump_json(indent=2),
                            encoding="utf-8",
                        )

                        refine_json = self.work_dir / "refinement_zones.geojson"
                        compute_refinement_zones(
                            depth_raster_path=depth_rasters[0],
                            output_geojson_path=refine_json,
                        )

                        for p, kind in [
                            (agree_tif, "raster"),
                            (metrics_json, "json"),
                            (refine_json, "vector"),
                        ]:
                            if p.exists():
                                h = compute_file_sha256(p)
                                art = ArtifactRecord(
                                    path=p.name,
                                    sha256=h,
                                    size_bytes=p.stat().st_size,
                                    kind=kind,
                                    stage=stage_name,
                                )
                                artifacts.append(art)
                                manifest.add_artifact(art)

                    finished_at = datetime.datetime.now(datetime.UTC).isoformat()
                    manifest.add_stage(
                        StageRecord(
                            stage=stage_name,
                            engine=None,
                            status="succeeded",
                            attempt=1,
                            started_at=started_at,
                            finished_at=finished_at,
                            wall_time_s=round(time.time() - t0, 3),
                        )
                    )
                    completed_stages.append(stage_name)
                    checkpoint_mgr.save_checkpoint(
                        stage=stage_name,
                        completed_stages=completed_stages,
                        artifacts=artifacts,
                    )

            # ── Finalize Manifest ────────────────────────────────────────────
            self._report_progress("finalise", 1.0, "Finalising run manifest and output packaging.")
            manifest.finish("succeeded")
            manifest_path = self.work_dir / "manifest.json"
            manifest.save(manifest_path)
            logger.info("Workflow execution succeeded for run '%s'.", run_id)
            return manifest

        except Exception as e:
            manifest.finish("failed")
            manifest_path = self.work_dir / "manifest.json"
            manifest.save(manifest_path)
            logger.error("Workflow execution failed at stage '%s': %s", stage_name, e)
            raise StageError(
                f"Workflow execution failed at stage '{stage_name}': {e}",
                stage=stage_name,
                detail={"run_id": run_id, "error": str(e)},
            ) from e
