"""Unit tests for Phase 5 comparison, spatial metrics, agreement mapping, and ensemble."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from pravahx.compare import (
    aggregate_ensemble_rasters,
    align_rasters_to_common_grid,
    compute_comparison_metrics,
    compute_refinement_zones,
    generate_agreement_raster,
    regrid_raster_to_target,
)
from pravahx.errors import RasterAlignmentError

if TYPE_CHECKING:
    from pathlib import Path


def _create_synthetic_raster(
    path: Path,
    data: np.ndarray,
    bounds: tuple[float, float, float, float] = (0.0, 0.0, 100.0, 100.0),
    crs: str = "EPSG:32644",
    nodata: float = -9999.0,
) -> Path:
    """Helper to generate a synthetic GeoTIFF raster for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = data.shape
    transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=rasterio.float32,
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data.astype(np.float32), 1)
    return path


def test_regrid_raster_to_target(tmp_path: Path) -> None:
    """Test reprojecting and resampling a coarse raster to match a finer target raster."""
    # Source: 5x5 grid over (0, 0, 100, 100)
    src_data = np.ones((5, 5), dtype=np.float32) * 5.0
    src_path = _create_synthetic_raster(tmp_path / "src.tif", src_data, bounds=(0, 0, 100, 100))

    # Target: 10x10 grid over (0, 0, 100, 100)
    tgt_data = np.zeros((10, 10), dtype=np.float32)
    tgt_path = _create_synthetic_raster(tmp_path / "tgt.tif", tgt_data, bounds=(0, 0, 100, 100))

    out_path = tmp_path / "regridded.tif"
    result = regrid_raster_to_target(src_path, tgt_path, out_path)

    assert result.exists()
    with rasterio.open(result) as dst:
        assert dst.shape == (10, 10)
        arr = dst.read(1)
        assert np.allclose(arr, 5.0, atol=1e-3)


def test_regrid_non_overlapping_error(tmp_path: Path) -> None:
    """Test that RasterAlignmentError is raised when rasters do not overlap."""
    r1 = _create_synthetic_raster(tmp_path / "r1.tif", np.ones((5, 5)), bounds=(0, 0, 50, 50))
    r2 = _create_synthetic_raster(tmp_path / "r2.tif", np.ones((5, 5)), bounds=(100, 100, 150, 150))

    with pytest.raises(RasterAlignmentError, match="do not spatially overlap"):
        regrid_raster_to_target(r1, r2, tmp_path / "out.tif")


def test_align_rasters_to_common_grid(tmp_path: Path) -> None:
    """Test aligning multiple rasters to an intersecting common grid."""
    r1 = _create_synthetic_raster(
        tmp_path / "r1.tif", np.ones((10, 10)) * 2.0, bounds=(0, 0, 100, 100)
    )
    r2 = _create_synthetic_raster(
        tmp_path / "r2.tif", np.ones((10, 10)) * 4.0, bounds=(50, 50, 150, 150)
    )

    out_dir = tmp_path / "aligned"
    aligned = align_rasters_to_common_grid(
        [r1, r2], out_dir, target_resolution_m=10.0, extent_mode="intersection"
    )

    assert len(aligned) == 2
    for p in aligned:
        assert p.exists()
        with rasterio.open(p) as src:
            # Overlap is x in [50, 100], y in [50, 100] -> 50m x 50m / 10m = 5x5
            assert src.shape == (5, 5)


def test_compute_comparison_metrics(tmp_path: Path) -> None:
    """Test spatial extent and depth comparison metrics between Model A and Model B."""
    grid_a = np.zeros((4, 4), dtype=np.float32)
    grid_a[0:3, 0:3] = 2.0  # 9 cells wet

    grid_b = np.zeros((4, 4), dtype=np.float32)
    grid_b[0:2, 0:2] = 1.5  # 4 cells wet (all 4 overlap with A)

    time_a = np.zeros((4, 4), dtype=np.float32)
    time_a[0:3, 0:3] = 10.0
    time_b = np.zeros((4, 4), dtype=np.float32)
    time_b[0:2, 0:2] = 8.0

    p_a = _create_synthetic_raster(tmp_path / "depth_a.tif", grid_a, bounds=(0, 0, 40, 40))
    p_b = _create_synthetic_raster(tmp_path / "depth_b.tif", grid_b, bounds=(0, 0, 40, 40))
    t_a = _create_synthetic_raster(tmp_path / "time_a.tif", time_a, bounds=(0, 0, 40, 40))
    t_b = _create_synthetic_raster(tmp_path / "time_b.tif", time_b, bounds=(0, 0, 40, 40))

    metrics = compute_comparison_metrics(
        p_a, p_b, arrival_a_path=t_a, arrival_b_path=t_b, wet_threshold_m=0.1
    )

    assert metrics.tp_cells == 4
    assert metrics.fp_cells == 5
    assert metrics.fn_cells == 0
    assert metrics.tn_cells == 7

    assert metrics.iou == round(4 / 9, 4)
    assert metrics.f1_score == round(8 / 13, 4)
    assert metrics.precision == round(4 / 9, 4)
    assert metrics.recall == 1.0

    assert metrics.depth_rmse_m == 0.5
    assert metrics.depth_mae_m == 0.5
    assert metrics.depth_bias_m == 0.5
    assert metrics.depth_max_a_m == 2.0
    assert metrics.depth_max_b_m == 1.5

    assert metrics.arrival_mae_min == 2.0
    assert metrics.arrival_rmse_min == 2.0
    assert metrics.arrival_bias_min == 2.0


def test_generate_agreement_raster(tmp_path: Path) -> None:
    """Test 5-class spatial agreement map classification."""
    grid_a = np.array(
        [
            [0.0, 1.0],  # (0,0): dry; (0,1): A=1.0, B=0.0 -> Class 1 (A only)
            [2.0, 3.0],  # (1,0): A=2.0, B=2.2 -> diff 0.2 <= 0.5 -> Class 3 (Agreed)
            # (1,1): A=3.0, B=1.0 -> diff 2.0 > 0.5 -> Class 4 (Disagreed)
        ],
        dtype=np.float32,
    )

    grid_b = np.array(
        [
            [0.0, 0.0],
            [2.2, 1.0],
        ],
        dtype=np.float32,
    )

    p_a = _create_synthetic_raster(tmp_path / "a.tif", grid_a, bounds=(0, 0, 20, 20))
    p_b = _create_synthetic_raster(tmp_path / "b.tif", grid_b, bounds=(0, 0, 20, 20))

    out_map = tmp_path / "agreement.tif"
    result_path, summary = generate_agreement_raster(
        p_a, p_b, out_map, depth_diff_threshold_m=0.5, wet_threshold_m=0.1
    )

    assert result_path.exists()
    with rasterio.open(result_path) as dst:
        arr = dst.read(1)
        assert arr[0, 0] == 0  # Both Dry
        assert arr[0, 1] == 1  # Model A only
        assert arr[1, 0] == 3  # Agreed wet
        assert arr[1, 1] == 4  # Disagreed wet

    assert summary.total_cells == 4
    assert summary.wet_agreement_ratio == 0.5


def test_aggregate_ensemble_rasters(tmp_path: Path) -> None:
    """Test ensemble raster aggregation into probability, percentiles and std rasters."""
    r1 = np.full((3, 3), 1.0, dtype=np.float32)
    r2 = np.full((3, 3), 2.0, dtype=np.float32)
    r3 = np.full((3, 3), 3.0, dtype=np.float32)

    r1[0, 0] = 0.0

    p1 = _create_synthetic_raster(tmp_path / "s1.tif", r1)
    p2 = _create_synthetic_raster(tmp_path / "s2.tif", r2)
    p3 = _create_synthetic_raster(tmp_path / "s3.tif", r3)

    out_dir = tmp_path / "ensemble_out"
    results = aggregate_ensemble_rasters(
        [p1, p2, p3],
        output_dir=out_dir,
        depth_threshold_m=0.1,
        percentiles=(10.0, 50.0, 90.0),
    )

    assert results.scenario_count == 3
    assert results.probability_raster.exists()
    assert results.depth_median_raster.exists()
    assert results.depth_std_raster.exists()

    with rasterio.open(results.probability_raster) as dst:
        prob = dst.read(1)
        assert np.isclose(prob[0, 0], 2.0 / 3.0, atol=1e-2)
        assert np.isclose(prob[1, 1], 1.0)

    with rasterio.open(results.depth_median_raster) as dst:
        med = dst.read(1)
        assert np.isclose(med[1, 1], 2.0)


def test_compute_refinement_zones(tmp_path: Path) -> None:
    """Test 2-pass mesh refinement zone detection from depth gradients and supercritical Froude."""
    depth = np.ones((10, 10), dtype=np.float32) * 1.0
    depth[4:7, 4:7] = 8.0  # High gradient box

    velocity = np.zeros((10, 10), dtype=np.float32)
    velocity[4:7, 4:7] = 12.0  # Fr = 12 / sqrt(9.81*8) ~ 1.35 > 0.9 (supercritical)

    d_path = _create_synthetic_raster(tmp_path / "depth.tif", depth, bounds=(0, 0, 100, 100))
    v_path = _create_synthetic_raster(tmp_path / "vel.tif", velocity, bounds=(0, 0, 100, 100))
    geojson_out = tmp_path / "refine_zones.geojson"

    plan = compute_refinement_zones(
        depth_raster_path=d_path,
        velocity_raster_path=v_path,
        output_geojson_path=geojson_out,
        gradient_threshold=0.2,
        froude_threshold=0.9,
        base_resolution_m=50.0,
        refinement_factor=4,
    )

    assert plan.total_refinement_zones >= 1
    assert plan.target_resolution_m == 12.5
    assert geojson_out.exists()

    with open(geojson_out, encoding="utf-8") as f:
        geo_data = json.load(f)
        assert geo_data["type"] == "FeatureCollection"
        assert len(geo_data["features"]) >= 1
