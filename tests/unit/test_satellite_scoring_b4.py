"""Unit tests for F07 satellite scoring and validation endpoints (B4 Missing Features)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
import rasterio
from affine import Affine

from pravahx.gee.scoring import (
    calculate_flood_extent_metrics,
    score_simulation_against_satellite,
)

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import AsyncClient


def test_calculate_flood_extent_metrics_exact() -> None:
    # 4x4 binary masks
    obs = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )  # 4 wet
    sim = np.array(
        [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )  # 4 wet
    # TP = 2 (col 1, row 0 and row 1)
    # FP = 2 (col 2, row 0 and row 1)
    # FN = 2 (col 0, row 0 and row 1)
    # Union = 6 -> CSI / IoU = 2/6 = 0.3333
    # F1 = 2*2 / (2*2 + 2 + 2) = 4/8 = 0.5000
    # Hit Rate / Recall = 2 / (2 + 2) = 0.5000
    # Precision = 2 / (2 + 2) = 0.5000
    # False Alarm Ratio = 2 / (2 + 2) = 0.5000
    # Missing Ratio = 2 / (2 + 2) = 0.5000

    metrics = calculate_flood_extent_metrics(
        observed_mask=obs, simulated_mask=sim, cell_area_km2=0.01
    )
    assert pytest.approx(metrics.critical_success_index, abs=0.001) == 0.3333
    assert pytest.approx(metrics.dice_f1_score, abs=0.001) == 0.5000
    assert pytest.approx(metrics.hit_rate, abs=0.001) == 0.5000
    assert pytest.approx(metrics.precision, abs=0.001) == 0.5000
    assert pytest.approx(metrics.false_alarm_ratio, abs=0.001) == 0.5000
    assert pytest.approx(metrics.missing_ratio, abs=0.001) == 0.5000
    assert pytest.approx(metrics.true_positive_km2, abs=0.001) == 0.02
    assert pytest.approx(metrics.false_positive_km2, abs=0.001) == 0.02
    assert pytest.approx(metrics.false_negative_km2, abs=0.001) == 0.02


def test_score_simulation_against_satellite_rasters(tmp_path: Path) -> None:
    width, height = 10, 10
    transform = Affine.translation(500000.0, 3300000.0) @ Affine.scale(10.0, -10.0)
    crs = "EPSG:32644"

    sim_depth = np.zeros((height, width), dtype=np.float32)
    sim_depth[2:6, 2:6] = 1.5  # 16 cells wet (depth > 0.15m)

    obs_mask = np.zeros((height, width), dtype=np.uint8)
    obs_mask[3:7, 3:7] = 1  # 16 cells wet

    sim_path = tmp_path / "sim_depth.tif"
    obs_path = tmp_path / "obs_mask.tif"

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "crs": crs,
        "transform": transform,
    }

    profile["dtype"] = rasterio.float32
    with rasterio.open(sim_path, "w", **profile) as dst:
        dst.write(sim_depth, 1)

    profile["dtype"] = rasterio.uint8
    with rasterio.open(obs_path, "w", **profile) as dst:
        dst.write(obs_mask, 1)

    res = score_simulation_against_satellite(
        simulated_depth_path=sim_path,
        observed_mask_path=obs_path,
        depth_threshold_m=0.15,
        temp_dir=tmp_path / "work",
    )

    # Overlap between (2:6, 2:6) and (3:7, 3:7) is 3x3 = 9 cells
    # sim = 16, obs = 16, TP = 9, FP = 7, FN = 7 -> Union = 23 -> CSI = 9/23 = 0.3913
    assert pytest.approx(res.critical_success_index, abs=0.01) == 0.3913
    assert res.true_positive_km2 > 0


@pytest.mark.asyncio
async def test_satellite_scoring_api_endpoint(client: AsyncClient, tmp_path: Path) -> None:
    # Create test rasters
    width, height = 5, 5
    transform = Affine.translation(100.0, 200.0) @ Affine.scale(10.0, -10.0)
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "crs": "EPSG:32644",
        "transform": transform,
    }

    sim_p = tmp_path / "api_sim.tif"
    obs_p = tmp_path / "api_obs.tif"

    profile["dtype"] = rasterio.float32
    with rasterio.open(sim_p, "w", **profile) as dst:
        dst.write(np.ones((height, width), dtype=np.float32), 1)

    profile["dtype"] = rasterio.uint8
    with rasterio.open(obs_p, "w", **profile) as dst:
        dst.write(np.ones((height, width), dtype=np.uint8), 1)

    resp = await client.post(
        "/api/v1/validation/satellite-scoring",
        json={
            "simulated_depth_path": str(sim_p),
            "observed_mask_path": str(obs_p),
            "depth_threshold_m": 0.10,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "evaluated"
    assert data["metrics"]["critical_success_index"] == 1.0
    assert "NOT RUN on Ganga" in data["status_label"]
