"""Unit tests for Earth Engine, satellite flood mapping, and lake watch (Phase 6 / Section 6)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import numpy as np
import pytest
import rasterio
from affine import Affine

from pravahx.gee.client import GEEClient
from pravahx.gee.flood_mapping import (
    extract_optical_water_extent,
    extract_sar_flood_extent,
    process_satellite_flood_raster,
)
from pravahx.gee.lake_watch import LakeObservation, analyze_lake_time_series
from pravahx.gee.scoring import (
    calculate_flood_extent_metrics,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_gee_client_unconfigured() -> None:
    client = GEEClient(service_account=None, key_file=None)
    # Should safely return False without crashing in offline / non-auth environments
    connected = client.initialize()
    assert isinstance(connected, bool)
    assert client.is_connected == connected


def test_sar_flood_extraction() -> None:
    # Calm open water: low backscatter (< -15 dB)
    # Dry rough ground: higher backscatter (-8 to -12 dB)
    post_sar = np.array(
        [
            [-18.0, -16.0, -9.0],
            [-17.0, -10.0, -8.0],
            [-8.0, -7.0, -6.0],
        ]
    )
    pre_sar = np.array(
        [
            [-10.0, -10.0, -9.0],
            [-9.0, -9.0, -8.0],
            [-8.0, -7.0, -6.0],
        ]
    )

    mask = extract_sar_flood_extent(
        post_event_backscatter_db=post_sar,
        pre_event_backscatter_db=pre_sar,
        threshold_db=-15.0,
    )
    assert mask[0, 0] == 1  # -18 dB (drop of -8 dB) -> Flood
    assert mask[0, 1] == 1  # -16 dB (drop of -6 dB) -> Flood
    assert mask[1, 0] == 1  # -17 dB (drop of -8 dB) -> Flood
    assert mask[0, 2] == 0  # -9 dB -> Dry
    assert mask[2, 2] == 0  # -6 dB -> Dry


def test_optical_flood_extraction() -> None:
    # Water: high Green, low SWIR -> MNDWI > 0
    green = np.array([[0.25, 0.10], [0.30, 0.05]])
    swir = np.array([[0.05, 0.35], [0.02, 0.40]])

    mask = extract_optical_water_extent(green_band=green, swir_band=swir, threshold=0.0)
    assert mask[0, 0] == 1  # (0.25-0.05)/(0.25+0.05) = 0.20/0.30 = +0.67 -> Water
    assert mask[0, 1] == 0  # (0.10-0.35)/(0.10+0.35) = -0.25/0.45 = -0.55 -> Land
    assert mask[1, 0] == 1  # (0.30-0.02)/(0.30+0.02) = +0.875 -> Water
    assert mask[1, 1] == 0  # -0.35/0.45 -> Land


def test_process_satellite_flood_raster(tmp_path: Path) -> None:
    width, height = 10, 10
    transform = Affine.translation(500000.0, 3300000.0) @ Affine.scale(10.0, -10.0)
    crs = "EPSG:32644"

    sar_data = np.full((height, width), -8.0, dtype=np.float32)
    sar_data[3:7, 3:7] = -18.0  # 16 cells flooded

    perm_data = np.zeros((height, width), dtype=np.uint8)
    perm_data[3, 3] = 1  # 1 cell permanent river

    sar_path = tmp_path / "post_sar.tif"
    perm_path = tmp_path / "perm_water.tif"
    out_mask = tmp_path / "extracted_flood.tif"

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": rasterio.float32,
        "crs": crs,
        "transform": transform,
    }

    with rasterio.open(sar_path, "w", **profile) as dst:
        dst.write(sar_data, 1)

    profile["dtype"] = rasterio.uint8
    with rasterio.open(perm_path, "w", **profile) as dst:
        dst.write(perm_data, 1)

    res = process_satellite_flood_raster(
        post_event_raster_path=sar_path,
        output_mask_path=out_mask,
        sensor_type="SAR_Sentinel1",
        permanent_water_mask_path=perm_path,
    )

    assert res.total_flooded_area_km2 > 0
    assert res.total_permanent_water_km2 > 0
    with rasterio.open(out_mask) as src:
        arr = src.read(1)
        # Permanent water cell (3, 3) should be subtracted (0)
        assert arr[3, 3] == 0
        # Other flooded cells should be 1
        assert arr[4, 4] == 1


def test_lake_watch_anomaly_detection() -> None:
    base_time = datetime.datetime(2026, 6, 1, 0, 0, tzinfo=datetime.UTC)

    # 1. Stable Lake
    stable_obs = [
        LakeObservation(
            observed_at=base_time,
            water_area_m2=1_000_000.0,
            water_area_km2=1.0,
            sensor_platform="Sentinel-2",
        ),
        LakeObservation(
            observed_at=base_time + datetime.timedelta(days=30),
            water_area_m2=1_020_000.0,
            water_area_km2=1.02,
            sensor_platform="Sentinel-2",
        ),
    ]
    summary_stable = analyze_lake_time_series(
        lake_id="lake_gangotri_1",
        lake_name="Upper Gangotri Moraine Lake",
        lake_type="glacial",
        observations=stable_obs,
    )
    assert summary_stable.status == "STABLE"
    assert summary_stable.area_change_percent == 2.0

    # 2. Rapid Expansion (+25%)
    expanding_obs = [
        LakeObservation(
            observed_at=base_time,
            water_area_m2=1_000_000.0,
            water_area_km2=1.0,
            sensor_platform="Sentinel-2",
        ),
        LakeObservation(
            observed_at=base_time + datetime.timedelta(days=20),
            water_area_m2=1_250_000.0,
            water_area_km2=1.25,
            sensor_platform="Sentinel-2",
        ),
    ]
    summary_exp = analyze_lake_time_series(
        lake_id="lake_chorabari",
        lake_name="Chorabari Glacial Lake",
        lake_type="glacial",
        observations=expanding_obs,
    )
    assert summary_exp.status == "RAPID_EXPANSION_WARNING"
    assert summary_exp.area_change_percent == 25.0

    # 3. Sudden Drainage (-35% in 5 days)
    drain_obs = [
        LakeObservation(
            observed_at=base_time,
            water_area_m2=1_000_000.0,
            water_area_km2=1.0,
            sensor_platform="Sentinel-2",
        ),
        LakeObservation(
            observed_at=base_time + datetime.timedelta(days=5),
            water_area_m2=650_000.0,
            water_area_km2=0.65,
            sensor_platform="Sentinel-2",
        ),
    ]
    summary_drain = analyze_lake_time_series(
        lake_id="lake_rishiganga",
        lake_name="Rishiganga Blockage Lake",
        lake_type="landslide",
        observations=drain_obs,
    )
    assert summary_drain.status == "SUDDEN_DRAINAGE_OUTBURST"
    assert summary_drain.area_change_percent == -35.0


def test_satellite_validation_scoring(tmp_path: Path) -> None:
    # Synthetic observed vs simulated
    obs_mask = np.array(
        [
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )  # 4 wet
    sim_mask = np.array(
        [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )  # 4 wet: TP=2, FP=2, FN=2, Union=6 -> CSI = 2/6 = 0.3333

    metrics = calculate_flood_extent_metrics(observed_mask=obs_mask, simulated_mask=sim_mask)
    assert pytest.approx(metrics.critical_success_index, abs=0.001) == 0.3333
    assert pytest.approx(metrics.hit_rate, abs=0.001) == 0.5000
    assert pytest.approx(metrics.precision, abs=0.001) == 0.5000
    assert pytest.approx(metrics.dice_f1_score, abs=0.001) == 0.5000
