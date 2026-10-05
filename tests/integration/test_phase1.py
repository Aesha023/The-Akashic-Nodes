"""Integration tests for Phase 1 (Tier 0 HAND pipeline)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import pytest
import rasterio

from pravahx.engines.base import RunContext
from pravahx.engines.tier0_hand.adapter import Tier0HandAdapter
from pravahx.export.vector import generate_exports
from pravahx.terrain.hand import compute_hand

if TYPE_CHECKING:
    from pathlib import Path


def _create_tilted_plane(path: Path) -> None:
    """Create a synthetic DEM: a tilted plane with a straight channel."""
    meta = {
        "driver": "GTiff",
        "height": 20,
        "width": 20,
        "count": 1,
        "dtype": rasterio.float32,
        "nodata": -9999.0,
        "transform": rasterio.transform.from_origin(0, 20, 1, 1),
        "crs": "EPSG:32644",
    }
    dem = np.zeros((20, 20), dtype=np.float32)
    for y in range(20):
        for x in range(20):
            # South-North slope
            y_elev = y * 0.1
            # Valley shape towards x=10
            x_elev = abs(x - 10) * 0.5
            dem[y, x] = 100.0 + y_elev + x_elev

    with rasterio.open(path, "w", **meta) as dest:
        dest.write(dem, 1)


@pytest.mark.integration
def test_phase1_pipeline(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Run the complete Phase 1 pipeline on a synthetic DEM."""
    caplog.set_level(logging.INFO)

    # 1. Create dummy terrain (simulate DEM fetching)
    dem_path = tmp_path / "dem.tif"
    _create_tilted_plane(dem_path)

    # 2. Compute HAND (WhiteboxTools)
    try:
        hand_path = compute_hand(
            dem_path=dem_path,
            out_dir=tmp_path,
            accumulation_threshold=5,
        )
    except Exception as e:
        if "WhiteboxTools" in str(e) or "failed" in str(e):
            pytest.skip(f"WhiteboxTools binary not available: {e}")
        raise e

    assert hand_path.exists()

    # Rename to hand.tif since adapter expects it
    expected_hand_path = tmp_path / "hand.tif"
    if hand_path.name != "hand.tif":
        hand_path.rename(expected_hand_path)

    # 3. Setup RunContext
    ctx = RunContext(
        run_id="test-run-1",
        config=None,  # type: ignore
        work_dir=tmp_path,
        terrain_dir=tmp_path,
        breach_hydrograph_path=tmp_path / "breach.csv",
    )

    engine = Tier0HandAdapter()

    # 4. Prepare
    prepared = engine.prepare(ctx)
    assert "hand.tif" in prepared.input_file_hashes

    # 5. Run (Rating curve + map)
    result = engine.run(prepared)
    assert result.status == "success"
    assert result.exit_code == 0
    assert (result.output_dir / "tier0_max_depth.tif").exists()

    # 6. Postprocess
    norm = engine.postprocess(result, ctx)
    assert len(norm.layers) == 1
    assert norm.layers[0].name == "max_depth"

    # 7. Exports
    exports_dir = tmp_path / "exports"
    exported = generate_exports(norm, exports_dir)
    names = [p.name for p in exported]
    assert "tier0_envelope.tif" in names
    assert "tier0_envelope.shp" in names
    assert "tier0_envelope.kml" in names
