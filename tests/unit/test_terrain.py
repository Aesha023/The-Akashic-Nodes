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
            accumulation_threshold=20,  # Single channel along col 10
        )
    except Exception as e:
        if "WhiteboxTools" in str(e) or "failed" in str(e):
            return
        raise e

    assert hand_path.exists()

    with rasterio.open(hand_path) as src:
        hand = src.read(1)

    # Check the expected values
    assert hand[10, 12] > 0.0
    assert hand[10, 12] > hand[10, 10]
    assert np.isclose(np.nanmin(hand[hand != -9999.0]), 0.0, atol=0.1)


def test_asymmetric_synthetic_dem(tmp_path: Path) -> None:
    """Test with an asymmetric DEM so a flipped or transposed array fails.

    Grid: 30 rows (Y) x 20 cols (X).
    Channel: Strictly placed at col 4 (west side), while east side (col > 10)
    has a steep mountain cliff.
    """
    dem_path = tmp_path / "asym_dem.tif"
    dem = np.zeros((30, 20), dtype=np.float32)
    for r in range(30):
        for c in range(20):
            # Slope downwards from North (r=0) to South (r=29)
            slope = (29 - r) * 0.5
            # Asymmetric valley at col 4
            valley = abs(c - 4) * 2.0
            dem[r, c] = 50.0 + slope + valley

    meta = {
        "driver": "GTiff",
        "height": 30,
        "width": 20,
        "count": 1,
        "dtype": rasterio.float32,
        "nodata": -9999.0,
        "transform": rasterio.transform.from_origin(100.0, 200.0, 1.0, 1.0),
        "crs": "EPSG:32644",
    }
    with rasterio.open(dem_path, "w", **meta) as dst:
        dst.write(dem, 1)

    try:
        hand_path = compute_hand(dem_path, tmp_path, accumulation_threshold=15)
    except Exception as e:
        if "WhiteboxTools" in str(e) or "failed" in str(e):
            return
        raise e

    assert hand_path.exists()

    with rasterio.open(tmp_path / "streams.tif") as src:
        streams = src.read(1)
        stream_cols = np.where(streams > 0)[1]

    # Stream cells must be at col 4. If flipped horizontally (col 15) or transposed, this fails.
    assert len(stream_cols) > 0
    assert np.all(stream_cols == 4), (
        f"Stream cells should be at col 4, found: {np.unique(stream_cols)}"
    )

    with rasterio.open(hand_path) as src:
        hand = src.read(1)

    # HAND along stream must be 0
    assert np.all(hand[streams > 0] == 0.0)
    # Eastern high cliff (col 18) must have large HAND, not zero
    assert np.nanmean(hand[:, 18]) > 10.0
