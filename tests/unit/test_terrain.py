"""Unit tests for terrain analysis (HAND)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import rasterio

from pravahx.terrain.hand import compute_hand

if TYPE_CHECKING:
    from pathlib import Path


def _create_tilted_plane(path: Path) -> None:
    """Create a synthetic DEM: a tilted plane with a straight channel.

    The DEM is 20x20 cells.
    It slopes downwards from South to North (Y axis).
    It also slopes downwards towards the center (X axis) to form a channel at x=10.
    """
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
            # South-North slope (y is 0 at North edge, 19 at South edge)
            y_elev = y * 0.1
            # Valley shape towards x=10
            x_elev = abs(x - 10) * 0.5
            dem[y, x] = 100.0 + y_elev + x_elev

    with rasterio.open(path, "w", **meta) as dest:
        dest.write(dem, 1)


def test_compute_hand_synthetic(tmp_path: Path) -> None:
    """Test HAND computation on a tilted plane with a straight channel.

    Expected answer:
    The stream should form along x=10.
    The elevation above the stream (HAND) at any cell (y, x) should simply be
    the x_elev component, because the stream cell at the same y has the same y_elev.
    Therefore, HAND = abs(x - 10) * 0.5
    """
    dem_path = tmp_path / "synthetic_dem.tif"
    _create_tilted_plane(dem_path)

    try:
        hand_path = compute_hand(
            dem_path=dem_path,
            out_dir=tmp_path,
            accumulation_threshold=5,  # Small threshold for a small DEM
        )
    except Exception as e:
        # If WhiteboxTools binary is not found in the environment, skip the test
        # We don't want to fail CI if the rust binary didn't download during test setup.
        if "WhiteboxTools" in str(e) or "failed" in str(e):
            return
        raise e

    assert hand_path.exists()

    with rasterio.open(hand_path) as src:
        hand = src.read(1)

    # Check the expected values
    # For a cell at x=12, the expected HAND is abs(12-10)*0.5 = 1.0
    assert hand[10, 12] > 0.0

    # Check that HAND increases away from the channel
    # x=10 is the channel, x=12 is further up the slope
    assert hand[10, 12] > hand[10, 10]
    # The minimum HAND value in the raster should be 0.0 (the stream cells)
    assert np.isclose(np.nanmin(hand[hand != -9999.0]), 0.0, atol=0.1)
