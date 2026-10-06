"""Volume from water mask and DEM, or area-volume scaling."""

from typing import Any

import numpy as np


def compute_volume_new_lake(
    dem: np.ndarray[Any, Any],
    mask: np.ndarray[Any, Any],
    cell_area_m2: float,
    nodata: float = -9999.0,
) -> float:
    """Compute volume for a new lake (formed after the DEM was acquired).

    The volume is the sum over the water mask of (water surface elevation minus DEM)
    times cell area. Water surface elevation is taken from the DEM along the mask edge.

    Args:
        dem: 2D array of elevation values.
        mask: 2D boolean array where True is water.
        cell_area_m2: Area of a single raster cell in square meters.
        nodata: No-data value in the DEM.

    Returns:
        Lake volume in cubic meters.
    """
    if not np.any(mask):
        return 0.0

    # 1. Find edge cells of the mask
    # A simple way is to dilate the mask and subtract, or just use
    # morphological gradients. We'll use a simple roll-based edge detection.
    mask_int = mask.astype(int)
    edges = np.zeros_like(mask, dtype=bool)

    # Check 4-connected neighbors
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(mask_int, shift=(dy, dx), axis=(0, 1))
        # Where the shifted mask is 0 but original is 1, it's an edge
        edges |= (mask_int == 1) & (shifted == 0)

    # In case the lake hits the very boundary of the array
    edges[0, :] = edges[-1, :] = edges[:, 0] = edges[:, -1] = False

    # Extract DEM values at the edges
    edge_elevations = dem[edges & (dem != nodata)]

    if len(edge_elevations) == 0:
        # Fallback to the maximum elevation inside the mask
        valid_dem = dem[mask & (dem != nodata)]
        if len(valid_dem) == 0:
            return 0.0
        water_surface_elev = np.max(valid_dem)
    else:
        # We can take the median or minimum of the edge elevations.
        # A stable choice is the median edge elevation.
        water_surface_elev = np.median(edge_elevations)

    # 2. Compute volume: sum of (water_surface - bed_elevation) * area
    valid_mask = mask & (dem != nodata)
    depths = water_surface_elev - dem[valid_mask]

    # Only consider positive depths (in case of noisy DEM or tilted surface)
    positive_depths = depths[depths > 0]

    volume_m3 = np.sum(positive_depths) * cell_area_m2
    return float(volume_m3)


def compute_volume_existing_lake(
    area_m2: float,
    kappa: float,
    zeta: float,
) -> float:
    """Compute volume for an existing lake using an area-volume scaling relation.

    Note: The DEM records the water surface, so subtracting DEM from the surface yields zero.
    This method uses a power-law relation V = kappa * A^zeta (with A in km^2, V in km^3).
    Because scaling parameters depend strongly on lake type (e.g., glacial moraine-dammed vs
    tectonic vs thermokarst) and geographic region, kappa and zeta are required parameters
    with no defaults.

    Args:
        area_m2: Lake surface area in square meters.
        kappa: Proportionality coefficient (for A in km^2, V in km^3).
        zeta: Scaling exponent.

    Returns:
        Estimated lake volume in cubic meters.
    """
    if area_m2 <= 0:
        return 0.0

    # The standard relation V = kappa * A^zeta is for V in km3 and A in km2
    area_km2 = area_m2 / 1_000_000.0
    volume_km3 = kappa * (area_km2**zeta)
    volume_m3 = volume_km3 * 1_000_000_000.0

    return float(volume_m3)
