"""Terrain analysis using WhiteboxTools (Phase 1).

Provides functions to condition DEMs, extract stream networks,
and compute the Height Above Nearest Drainage (HAND) model.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import whitebox

from pravahx.errors import DataError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def compute_hand(
    dem_path: Path,
    out_dir: Path,
    accumulation_threshold: int = 1000,
) -> Path:
    """Compute the Height Above Nearest Drainage (HAND) from a DEM.

    Uses WhiteboxTools to fill depressions, compute flow accumulation,
    extract a synthetic stream network, and calculate the relative
    elevation of each cell above its nearest drainage cell.

    Args:
        dem_path: Path to the input DEM GeoTIFF.
        out_dir: Directory to store intermediate and final outputs.
        accumulation_threshold: Number of upstream cells to define a stream.

    Returns:
        Path to the generated HAND GeoTIFF.

    Raises:
        DataError: If WhiteboxTools execution fails.
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

    logger.info(f"Extracting streams (threshold={accumulation_threshold})...")
    if wbt.extract_streams(d8_accum, streams, threshold=accumulation_threshold) != 0:
        raise DataError("WhiteboxTools failed at extract_streams.")

    # Convert extracted stream raster to vector lines for downstream export and verification
    streams_shp = "streams.shp"
    wbt.raster_streams_to_vector(streams, d8_pntr, streams_shp)

    logger.info("Computing Height Above Nearest Drainage (HAND)...")
    if wbt.elevation_above_stream(filled_dem, streams, hand) != 0:
        raise DataError("WhiteboxTools failed at elevation_above_stream.")

    hand_path = out_dir / hand
    if not hand_path.exists():
        raise DataError("HAND computation finished but output file is missing.")

    logger.info(f"HAND raster generated at {hand_path}")
    return hand_path
