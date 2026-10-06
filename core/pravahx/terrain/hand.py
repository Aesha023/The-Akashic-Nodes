"""Terrain analysis using WhiteboxTools (Phase 1).

Provides functions to condition DEMs, extract stream networks,
isolate the main reach, and compute the Height Above Nearest Drainage (HAND) model.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import rasterio
import whitebox

from pravahx.errors import DataError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# WhiteboxTools D8 pointer bitmask directions:
# 1: (-1, 1)  [North-East]
# 2: (0, 1)   [East]
# 4: (1, 1)   [South-East]
# 8: (1, 0)   [South]
# 16: (1, -1) [South-West]
# 32: (0, -1) [West]
# 64: (-1, -1)[North-West]
# 128: (-1, 0)[North]
WBT_D8_TO_DELTA: dict[int, tuple[int, int]] = {
    1: (-1, 1),
    2: (0, 1),
    4: (1, 1),
    8: (1, 0),
    16: (1, -1),
    32: (0, -1),
    64: (-1, -1),
    128: (-1, 0),
}

DELTA_TO_WBT_D8: dict[tuple[int, int], int] = {
    (-1, 1): 1,
    (0, 1): 2,
    (1, 1): 4,
    (1, 0): 8,
    (1, -1): 16,
    (0, -1): 32,
    (-1, -1): 64,
    (-1, 0): 128,
}


def validate_channel_nodata(dem_path: Path, stream_raster_path: Path) -> None:
    """Validate that all cells along the stream channel contain valid elevation data.

    Raises:
        DataError: If any channel cell has NoData or NaN elevation.
    """
    with rasterio.open(dem_path) as src_dem:
        elev = src_dem.read(1)
        nodata = src_dem.nodata
        trans = src_dem.transform

    with rasterio.open(stream_raster_path) as src_str:
        streams = src_str.read(1)

    channel_mask = streams > 0
    if not np.any(channel_mask):
        raise DataError("Stream channel raster is empty; cannot validate channel elevations.")

    if nodata is not None:
        invalid_mask = channel_mask & ((elev == nodata) | np.isnan(elev) | (elev <= -32767.0))
    else:
        invalid_mask = channel_mask & np.isnan(elev)

    if np.any(invalid_mask):
        invalid_coords = np.argwhere(invalid_mask)
        r, c = int(invalid_coords[0][0]), int(invalid_coords[0][1])
        x, y = rasterio.transform.xy(trans, r, c)
        raise DataError(
            f"NoData cell detected on stream channel at pixel ({r}, {c}) / "
            f"coords ({x:.4f}, {y:.4f}) with elevation {elev[r, c]}. "
            "Channel DEM must be continuous and fully defined without missing data."
        )


def extract_main_reach(
    d8_pntr_path: Path,
    d8_accum_path: Path,
    out_reach_path: Path,
    threshold: int = 500,
    source_point: tuple[float, float] | None = None,
) -> Path:
    """Extract the continuous main reach channel from D8 flow direction and accumulation.

    If source_point (dam/breach location in map coordinates) is provided, traces downstream
    from the source point to the domain boundary. Otherwise, identifies the domain outlet
    (maximum accumulation cell) and traces upstream along the primary flow corridor.

    Args:
        d8_pntr_path: Path to D8 pointer GeoTIFF.
        d8_accum_path: Path to D8 accumulation GeoTIFF.
        out_reach_path: Output GeoTIFF path for the 1-bit main reach mask.
        threshold: Upstream accumulation termination threshold.
        source_point: Optional (x, y) coordinates of the breach/dam source.

    Returns:
        Path to the generated main reach raster.
    """
    with rasterio.open(d8_accum_path) as src_accum:
        accum = src_accum.read(1)
        meta = src_accum.meta.copy()
        trans = src_accum.transform

    with rasterio.open(d8_pntr_path) as src_pntr:
        pntr = src_pntr.read(1)

    height, width = accum.shape
    main_mask = np.zeros_like(accum, dtype=np.uint8)

    if source_point is not None:
        inv_trans = ~trans
        src_c, src_r = inv_trans * source_point
        start_r, start_c = round(src_r), round(src_c)
        start_r = max(0, min(height - 1, start_r))
        start_c = max(0, min(width - 1, start_c))

        curr_r, curr_c = start_r, start_c
        steps = 0
        while 0 <= curr_r < height and 0 <= curr_c < width and steps < height * width:
            main_mask[curr_r, curr_c] = 1
            steps += 1
            ptr = int(pntr[curr_r, curr_c])
            if ptr not in WBT_D8_TO_DELTA:
                break
            dr, dc = WBT_D8_TO_DELTA[ptr]
            curr_r += dr
            curr_c += dc
    else:
        # Trace upstream from outlet (maximum accumulation)
        outlet_r, outlet_c = np.unravel_index(np.argmax(accum), accum.shape)
        main_mask[outlet_r, outlet_c] = 1

        curr_r, curr_c = int(outlet_r), int(outlet_c)
        steps = 0
        while steps < height * width:
            steps += 1
            best_accum = -1.0
            best_neighbor = None
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = curr_r + dr, curr_c + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        # Neighbor must point in direction (-dr, -dc) to flow into (curr_r, curr_c)
                        req_ptr = DELTA_TO_WBT_D8[(-dr, -dc)]
                        if pntr[nr, nc] == req_ptr and accum[nr, nc] > best_accum:
                            best_accum = float(accum[nr, nc])
                            best_neighbor = (nr, nc)
            if best_neighbor is None or best_accum < threshold:
                break
            main_mask[best_neighbor] = 1
            curr_r, curr_c = best_neighbor

    meta.update(dtype="uint8", nodata=0, count=1)
    with rasterio.open(out_reach_path, "w", **meta) as dest:
        dest.write(main_mask, 1)

    logger.info(f"Main reach raster extracted with {int(np.sum(main_mask))} cells.")
    return out_reach_path


def compute_hand(
    dem_path: Path,
    out_dir: Path,
    accumulation_threshold: int = 500,
    source_point: tuple[float, float] | None = None,
) -> Path:
    """Compute the Height Above Nearest Drainage (HAND) relative to the main reach.

    Uses WhiteboxTools to fill depressions, compute flow accumulation,
    extract the main stem reach, validate channel integrity, and calculate
    relative elevation above the main drainage.

    Args:
        dem_path: Path to the input DEM GeoTIFF.
        out_dir: Directory to store intermediate and final outputs.
        accumulation_threshold: Number of upstream cells to define a stream.
        source_point: Optional (x, y) coordinates of the breach/dam source.

    Returns:
        Path to the generated HAND GeoTIFF.

    Raises:
        DataError: If WhiteboxTools execution fails or channel validation fails.
    """
    out_dir = out_dir.resolve()
    dem_path = dem_path.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Initialize WhiteboxTools
    wbt = whitebox.WhiteboxTools()
    wbt.set_working_dir(str(out_dir))
    wbt.set_verbose_mode(True)

    # Define paths
    dem = str(dem_path)
    filled_dem = "filled.tif"
    d8_pntr = "d8_pointer.tif"
    d8_accum = "d8_accum.tif"
    streams = "streams.tif"
    main_reach = "main_reach.tif"
    hand = "hand.tif"

    logger.info("Filling depressions in DEM...")
    if wbt.fill_depressions_wang_and_liu(dem, filled_dem) != 0:
        raise DataError("WhiteboxTools failed at fill_depressions_wang_and_liu.")

    logger.info("Computing flow direction (D8)...")
    if wbt.d8_pointer(filled_dem, d8_pntr) != 0:
        raise DataError("WhiteboxTools failed at d8_pointer.")

    logger.info("Computing flow accumulation...")
    if wbt.d8_flow_accumulation(d8_pntr, d8_accum, out_type="cells", pntr=True) != 0:
        raise DataError("WhiteboxTools failed at d8_flow_accumulation.")

    logger.info(f"Extracting full stream network (threshold={accumulation_threshold})...")
    if wbt.extract_streams(d8_accum, streams, threshold=accumulation_threshold) != 0:
        raise DataError("WhiteboxTools failed at extract_streams.")

    # Convert full stream network to vector lines
    streams_shp = "streams.shp"
    wbt.raster_streams_to_vector(streams, d8_pntr, streams_shp)

    # Extract main reach channel (downstream of source or primary stem)
    logger.info("Extracting main reach channel...")
    extract_main_reach(
        d8_pntr_path=out_dir / d8_pntr,
        d8_accum_path=out_dir / d8_accum,
        out_reach_path=out_dir / main_reach,
        threshold=accumulation_threshold,
        source_point=source_point,
    )

    # Validate channel cells for NoData
    validate_channel_nodata(dem_path=out_dir / filled_dem, stream_raster_path=out_dir / main_reach)

    # Convert main reach to vector lines
    main_reach_shp = "main_reach.shp"
    wbt.raster_streams_to_vector(main_reach, d8_pntr, main_reach_shp)

    # Compute HAND relative to the main reach only
    logger.info("Computing Height Above Nearest Drainage (HAND) relative to main reach...")
    if wbt.elevation_above_stream(filled_dem, main_reach, hand) != 0:
        raise DataError("WhiteboxTools failed at elevation_above_stream.")

    hand_path = out_dir / hand
    if not hand_path.exists():
        raise DataError("HAND computation finished but output file is missing.")

    logger.info(f"HAND raster generated at {hand_path}")
    return hand_path
