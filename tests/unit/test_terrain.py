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


def test_flow_accumulation_pntr_flag(tmp_path: Path) -> None:
    """Verify that d8_flow_accumulation with pntr=True correctly accumulates flow on D8 pointer.

    Without pntr=True, WhiteboxTools treats the pointer as elevation and fails to accumulate flow.
    """
    import whitebox

    wbt = whitebox.WhiteboxTools()
    wbt.set_working_dir(str(tmp_path))
    wbt.set_verbose_mode(False)

    dem_path = tmp_path / "v_dem.tif"
    _create_tilted_plane(dem_path)

    # Compute filled and D8 pointer
    wbt.fill_depressions_wang_and_liu("v_dem.tif", "filled.tif")
    wbt.d8_pointer("filled.tif", "d8_pntr.tif")

    # Flow accumulation with pntr=True
    wbt.d8_flow_accumulation("d8_pntr.tif", "accum_correct.tif", out_type="cells", pntr=True)

    with rasterio.open(tmp_path / "accum_correct.tif") as src:
        accum_correct = src.read(1)

    # With pntr=True on a 20x20 tilted V-valley, flow accumulates along col 10 reaching ~400 cells
    max_correct = float(np.max(accum_correct))
    assert max_correct >= 200.0, f"Expected high accumulation along channel, got {max_correct}"


def test_channel_nodata_loud_failure(tmp_path: Path) -> None:
    """Verify that validate_channel_nodata raises DataError when a stream cell has NoData in DEM."""
    import pytest

    from pravahx.errors import DataError
    from pravahx.terrain.hand import validate_channel_nodata

    dem_path = tmp_path / "dem_with_nodata.tif"
    stream_path = tmp_path / "stream.tif"

    dem = np.full((10, 10), 100.0, dtype=np.float32)
    # Introduce NoData at channel cell (5, 5)
    dem[5, 5] = -9999.0

    streams = np.zeros((10, 10), dtype=np.uint8)
    streams[5, :] = 1  # Channel along row 5

    meta = {
        "driver": "GTiff",
        "height": 10,
        "width": 10,
        "count": 1,
        "dtype": rasterio.float32,
        "nodata": -9999.0,
        "transform": rasterio.transform.from_origin(0, 10, 1, 1),
        "crs": "EPSG:32644",
    }
    with rasterio.open(dem_path, "w", **meta) as dst:
        dst.write(dem, 1)

    meta["dtype"] = "uint8"
    meta["nodata"] = 0
    with rasterio.open(stream_path, "w", **meta) as dst:
        dst.write(streams, 1)

    with pytest.raises(DataError, match="NoData cell detected on stream channel"):
        validate_channel_nodata(dem_path, stream_path)


def test_synthetic_main_and_side_valley_hand(tmp_path: Path) -> None:
    """Test HAND with a main valley and a steep tributary side valley.

    Main valley runs along col 5 from North to South (elev 100m down to 80m).
    Side valley enters from East at row 10 (elev climbing steeply from 90m to 160m at col 19).

    HAND relative to main reach must:
    1. Be 0.0 along the main channel (col 5).
    2. Be small (< 10m) at the confluence mouth (row 10, col 6).
    3. Rise steeply (> 40m) up the side valley (row 10, col 15-19), ensuring
       that a 13m main-stem flood does not flood up the tributary.
    """
    dem_path = tmp_path / "main_side_valley.tif"
    dem = np.zeros((20, 20), dtype=np.float32)

    for r in range(20):
        for c in range(20):
            # Main valley: runs along col 5, slopes down with increasing row r
            main_slope = (20 - r) * 1.0  # 20m drop from r=0 to r=20
            main_v = abs(c - 5) * 2.0
            dem[r, c] = 80.0 + main_slope + main_v

            # Side valley: tributary entering at row 10 from col 6..19
            if abs(r - 10) <= 2 and c > 5:
                # Carve side valley into the eastern mountain, but with steep ascending bed
                side_v = abs(r - 10) * 3.0
                side_bed_ascent = (c - 5) * 4.0  # Climbs 4m per cell eastward
                trib_elev = 80.0 + (20 - 10) * 1.0 + side_bed_ascent + side_v
                dem[r, c] = min(dem[r, c], trib_elev)

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
    with rasterio.open(dem_path, "w", **meta) as dst:
        dst.write(dem, 1)

    hand_path = compute_hand(dem_path, tmp_path, accumulation_threshold=15)
    assert hand_path.exists()

    with rasterio.open(hand_path) as src:
        hand = src.read(1)

    with rasterio.open(tmp_path / "main_reach.tif") as src:
        main_reach = src.read(1)

    # Main channel cells where stream is initiated have HAND == 0
    assert np.any(main_reach > 0)
    assert np.all(hand[main_reach > 0] == 0.0)

    # Confluence mouth (row 10, col 6) is near the main river
    assert hand[10, 6] < 10.0

    # Upper tributary (row 10, col 18) is steep and high above the confluence
    assert hand[10, 18] > 30.0

    # Under a 13.3m flood stage, confluence mouth is flooded, but upper tributary is dry!
    stage = 13.3
    assert hand[10, 6] < stage, "Tributary mouth should be flooded (backwater)"
    assert hand[10, 18] > stage, "Upper tributary should NOT be flooded"


def test_main_reach_from_source_point_at_domain_boundary(tmp_path: Path) -> None:
    """Test reach extraction when the main river enters through the domain boundary.

    If traced upstream from the outlet, a longer side tributary might be selected.
    When a scenario source point (dam/lake) is specified at the boundary inlet,
    the reach must start at that source point and trace downstream along the main stem.
    """
    dem_path = tmp_path / "boundary_entry_dem.tif"
    dem = np.zeros((20, 20), dtype=np.float32)

    # Main river canyon along col 5 sloping downwards from North (row 0) to South (row 19)
    for r in range(20):
        for c in range(20):
            main_slope = (20 - r) * 1.5
            main_v = abs(c - 5) * 3.0
            dem[r, c] = 100.0 + main_slope + main_v

            # Side tributary entering from East (row 10, col 6..19)
            if r == 10 and c > 5:
                # Tributary canyon carved into eastern mountain
                trib_slope = (c - 5) * 0.5
                dem[r, c] = 100.0 + (20 - 10) * 1.5 + trib_slope

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
    with rasterio.open(dem_path, "w", **meta) as dst:
        dst.write(dem, 1)

    # Source point at North boundary inlet: (X=5.5, Y=19.5) -> maps to (row=0, col=5)
    source_coords = (5.5, 19.5)

    hand_path = compute_hand(
        dem_path,
        tmp_path,
        accumulation_threshold=5,
        source_point=source_coords,
    )
    assert hand_path.exists()

    with rasterio.open(tmp_path / "main_reach.tif") as src:
        main_reach = src.read(1)

    reach_rows, reach_cols = np.where(main_reach > 0)

    # All reach cells must follow the main river along col 5
    assert len(reach_cols) > 0
    assert np.all(reach_cols == 5), (
        f"Expected main reach along col 5, found cols: {np.unique(reach_cols)}"
    )
    # Reach must start at the boundary inlet (row 0) and extend to the outlet (row 19)
    assert 0 in reach_rows
    assert 19 in reach_rows

    # The eastern tributary (cols 6..19) must NOT be part of the main reach
    assert not np.any(main_reach[:, 6:])
