"""HAND-based hydraulic geometry and rating curve (Phase 1).

Solves Manning's equation on a HAND raster cross-section to find
the stage (water level) that carries a given discharge.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import numpy as np
import numpy.typing as npt
import rasterio

logger = logging.getLogger(__name__)


def compute_hydraulic_geometry(
    hand_array: npt.NDArray[np.float32],
    cell_size_m: float,
    stage: float,
) -> tuple[float, float]:
    """Compute cross-sectional area and wetted perimeter for a given stage.

    Assumes a reach-averaged approach where the HAND raster represents
    the geometry of the reach.

    Args:
        hand_array: 2D array of HAND values (meters).
        cell_size_m: Resolution of the grid (meters).
        stage: Water surface elevation above the stream bed (meters).

    Returns:
        (area_m2, wetted_perimeter_m)
    """
    # Cells that are inundated
    inundated = hand_array < stage

    # Area = sum of (stage - HAND) * cell_width
    # In a 1D cross-section sense across the whole reach, we sum the widths of inundated cells
    # Wait: The HAND approach for a reach integrates the volume. To treat the reach as a
    # single synthetic cross section, area is the integral of (stage - h) * W,
    # where W is the channel width (approximated here by the number of inundated cells * cell_size).
    # Since this is a synthetic reach-averaged cross-section, we divide by the reach length
    # to get the average cross-sectional area. Or, more simply, we use the 1D synthetic section
    # method from Zheng et al. (2018).

    # For a simple synthetic rating curve:
    # A_reach = sum(stage - hand) * cell_size^2 for hand < stage
    # L_reach = reach length.
    # A_avg = A_reach / L_reach
    # P_reach = sum of bed area of inundated cells.
    # P_avg = P_reach / L_reach

    # To avoid needing reach length explicitly here, we calculate A and P
    # on a per-unit-reach-length basis directly from the hypsometric curve.

    valid_hand = hand_array[inundated]

    if len(valid_hand) == 0:
        return 0.0, 0.0

    # Number of inundated cells represents the wetted width
    wetted_width = len(valid_hand) * cell_size_m

    # Area is the integral of depth over the width
    depths = stage - valid_hand
    area = float(np.sum(depths, dtype=np.float64)) * cell_size_m

    # Wetted perimeter approximation: assuming relatively flat terrain, P ~ W.
    # We could add the vertical walls (stage - hand) at the edges, but W is dominant.
    perimeter = wetted_width

    return area, perimeter


def mannings_discharge(
    area: float,
    perimeter: float,
    slope: float,
    mannings_n: float,
) -> float:
    """Compute discharge using Manning's equation.

    Args:
        area: Cross-sectional area (m^2).
        perimeter: Wetted perimeter (m).
        slope: Energy grade line slope (m/m).
        mannings_n: Roughness coefficient.

    Returns:
        Discharge (m^3/s).
    """
    if area <= 0 or perimeter <= 0 or mannings_n <= 0 or slope <= 0:
        return 0.0

    hydraulic_radius = area / perimeter
    return float((1.0 / mannings_n) * area * (hydraulic_radius ** (2.0 / 3.0)) * (slope**0.5))


def find_stage_for_discharge(
    hand_path: str | Path,
    target_discharge: float,
    slope: float,
    mannings_n: float,
    max_stage: float = 100.0,
    tolerance: float = 0.01,
) -> float:
    """Find the stage that produces the target discharge using a bisection search.

    Args:
        hand_path: Path to the HAND raster.
        target_discharge: Peak discharge (m^3/s).
        slope: Reach slope (m/m).
        mannings_n: Average Manning's n for the reach.
        max_stage: Maximum stage to search up to (meters).
        tolerance: Convergence tolerance in meters.

    Returns:
        The stage (meters) that conveys the target discharge.
    """
    with rasterio.open(hand_path) as src:
        hand = src.read(1)
        nodata = src.nodata
        cell_size = src.res[0]

    # Mask out nodata
    if nodata is not None:
        hand = np.where(hand == nodata, np.nan, hand)

    # Extract only the valid (non-NaN, non-negative) HAND values for speed
    valid_mask = ~np.isnan(hand) & (hand >= 0)
    hand_valid = hand[valid_mask]

    # Normalise to a 1D synthetic cross-section representing the average
    # We divide by the number of stream cells to get average area per length.
    # Wait, the number of stream cells (HAND=0) represents the reach length in cell units.
    num_stream_cells = np.sum(hand_valid == 0)
    if num_stream_cells == 0:
        num_stream_cells = 1  # Fallback

    reach_length_m = num_stream_cells * cell_size

    def q_for_stage(s: float) -> float:
        # Sum of depths * cell_size^2 gives total volume in reach
        # Divide by reach length to get average cross-sectional area
        inundated = hand_valid < s
        depths = s - hand_valid[inundated]

        area = float(np.sum(depths, dtype=np.float64) * (cell_size**2)) / reach_length_m
        perimeter = float(np.sum(inundated, dtype=np.float64) * (cell_size**2)) / reach_length_m

        return mannings_discharge(area, perimeter, slope, mannings_n)

    # Bisection search
    low = 0.0
    high = max_stage

    # Check if max_stage is enough
    if q_for_stage(high) < target_discharge:
        logger.warning(
            f"Target discharge {target_discharge} exceeds capacity at max stage {max_stage}"
        )
        return max_stage

    while (high - low) > tolerance:
        mid = (low + high) / 2.0
        q = q_for_stage(mid)
        if q < target_discharge:
            low = mid
        else:
            high = mid

    return (low + high) / 2.0
