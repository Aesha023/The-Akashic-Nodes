"""Satellite hindcast validation and extent comparison scoring (Phase 6 / Section 6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pydantic import BaseModel

from pravahx.compare.regrid import regrid_raster_to_target


class SatelliteValidationMetrics(BaseModel):
    """Statistical verification metrics comparing simulated against satellite-observed flood."""

    critical_success_index: float  # IoU / CSI: TP / (TP + FP + FN)
    dice_f1_score: float  # 2*TP / (2*TP + FP + FN)
    hit_rate: float  # Recall: TP / (TP + FN)
    precision: float  # TP / (TP + FP)
    false_alarm_ratio: float  # FP / (TP + FP)
    missing_ratio: float  # FN / (TP + FN)
    true_positive_km2: float
    false_positive_km2: float
    false_negative_km2: float
    observed_flood_km2: float
    simulated_flood_km2: float


def calculate_flood_extent_metrics(
    observed_mask: np.ndarray[Any, Any],
    simulated_mask: np.ndarray[Any, Any],
    cell_area_km2: float = 0.0001,
) -> SatelliteValidationMetrics:
    """Calculate contingency table flood metrics from boolean/uint8 masks."""
    obs = np.asarray(observed_mask > 0, dtype=bool)
    sim = np.asarray(simulated_mask > 0, dtype=bool)

    tp = int(np.sum(obs & sim))
    fp = int(np.sum(~obs & sim))
    fn = int(np.sum(obs & ~sim))

    union = tp + fp + fn
    csi = tp / union if union > 0 else 1.0
    f1 = (2.0 * tp) / (2.0 * tp + fp + fn) if (2.0 * tp + fp + fn) > 0 else 1.0
    hit_rate = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    missing = fn / (tp + fn) if (tp + fn) > 0 else 0.0

    return SatelliteValidationMetrics(
        critical_success_index=round(csi, 4),
        dice_f1_score=round(f1, 4),
        hit_rate=round(hit_rate, 4),
        precision=round(precision, 4),
        false_alarm_ratio=round(far, 4),
        missing_ratio=round(missing, 4),
        true_positive_km2=round(tp * cell_area_km2, 4),
        false_positive_km2=round(fp * cell_area_km2, 4),
        false_negative_km2=round(fn * cell_area_km2, 4),
        observed_flood_km2=round((tp + fn) * cell_area_km2, 4),
        simulated_flood_km2=round((tp + fp) * cell_area_km2, 4),
    )


def score_simulation_against_satellite(
    simulated_depth_path: str | Path,
    observed_mask_path: str | Path,
    depth_threshold_m: float = 0.15,
    temp_dir: str | Path | None = None,
) -> SatelliteValidationMetrics:
    """Align and score a simulated depth raster against a satellite observation mask."""
    obs_p = Path(observed_mask_path)
    sim_p = Path(simulated_depth_path)

    work_dir = Path(temp_dir) if temp_dir else sim_p.parent
    work_dir.mkdir(parents=True, exist_ok=True)
    regridded_sim = work_dir / f"regridded_{sim_p.name}"

    regrid_raster_to_target(
        source_path=sim_p,
        target_path=obs_p,
        output_path=regridded_sim,
    )

    with rasterio.open(obs_p) as obs_src, rasterio.open(regridded_sim) as sim_src:
        obs_data = obs_src.read(1)
        sim_data = sim_src.read(1)

        cell_area_km2 = (abs(obs_src.res[0]) * abs(obs_src.res[1])) / 1e6

        sim_mask = sim_data >= depth_threshold_m
        obs_mask = obs_data > 0

        return calculate_flood_extent_metrics(
            observed_mask=obs_mask,
            simulated_mask=sim_mask,
            cell_area_km2=cell_area_km2,
        )
