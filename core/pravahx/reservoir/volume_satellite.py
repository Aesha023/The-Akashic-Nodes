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


def estimate_volume_from_terrain_extrapolation(
    dem: np.ndarray[Any, Any],
    mask: np.ndarray[Any, Any],
    cell_area_m2: float,
    buffer_cells: int = 5,
    nodata: float = -9999.0,
    assumed_m: float = 2.0,
) -> tuple[float, float, str]:
    """Estimate lake volume and hypsometric curve from subaerial terrain slopes.

    CRITICAL NOTE: For lakes present when the DEM was acquired, the DEM records the flat water
    surface, not the submerged bed topography. The true hypsometric exponent m cannot be fitted
    directly from DEM elevations inside the water body.

    When official dam register area-capacity tables are unavailable, this method approximates
    submerged bathymetry by calculating average terrain slopes around the subaerial perimeter
    and projecting inward under an idealized valley hypsometry.

    Args:
        dem: 2D array of elevation values.
        mask: 2D boolean array where True is water.
        cell_area_m2: Cell area in m^2.
        buffer_cells: Number of cells outside the mask to evaluate terrain slope.
        nodata: No-data value in the DEM.
        assumed_m: Assumed hypsometric stage-storage exponent (default 2.0 for parabolic valley).

    Returns:
        tuple of (estimated_volume_m3, hypsometric_exponent_m, uncertainty_warning).
    """
    warning = (
        "ESTIMATE: Bathymetry extrapolated from subaerial terrain slopes above waterline. "
        "High uncertainty (typically ±50% to ±100%). Use official dam register "
        "area-capacity tables where available."
    )

    if not np.any(mask):
        return 0.0, assumed_m, warning

    # 1. Identify waterline edge cells
    mask_int = mask.astype(int)
    edges = np.zeros_like(mask, dtype=bool)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(mask_int, shift=(dy, dx), axis=(0, 1))
        edges |= (mask_int == 1) & (shifted == 0)
    edges[0, :] = edges[-1, :] = edges[:, 0] = edges[:, -1] = False

    edge_elevations = dem[edges & (dem != nodata)]
    if len(edge_elevations) == 0:
        return 0.0, assumed_m, warning
    water_surface_elev = float(np.median(edge_elevations))

    # 2. Identify terrain buffer immediately outside the lake perimeter
    dilated = mask_int.copy()
    for _ in range(buffer_cells):
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            shifted = np.roll(dilated, shift=(dy, dx), axis=(0, 1))
            dilated |= shifted
    dilated[0, :] = dilated[-1, :] = dilated[:, 0] = dilated[:, -1] = False
    buffer_mask = (dilated == 1) & (~mask) & (dem != nodata)

    buffer_elevations = dem[buffer_mask]
    if len(buffer_elevations) == 0:
        return 0.0, assumed_m, warning

    # Mean elevation rise above water surface across buffer
    delta_z = float(np.mean(np.maximum(0.0, buffer_elevations - water_surface_elev)))
    cell_size_m = float(np.sqrt(cell_area_m2))
    buffer_distance_m = float(buffer_cells) * cell_size_m
    slope = delta_z / max(1.0, buffer_distance_m)
    slope = max(0.05, min(1.5, slope))  # Bound slope to physical range

    # 3. Lake surface area & equivalent radius
    n_water_cells = float(np.sum(mask))
    area_m2 = n_water_cells * cell_area_m2
    r_eq = float(np.sqrt(area_m2 / np.pi))

    # 4. Extrapolated maximum depth and volume
    h_max_est = r_eq * slope
    # For hypsometric power-law V(h) = K * h^m, total volume V = (1/m) * Area * H_max
    volume_est_m3 = (1.0 / assumed_m) * area_m2 * h_max_est

    return float(volume_est_m3), assumed_m, warning
