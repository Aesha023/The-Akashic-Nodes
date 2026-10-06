"""Unit tests for reservoir volume estimation methods (Phase 2a)."""

from __future__ import annotations

import numpy as np
import pytest

from pravahx.reservoir.volume_register import get_dam_volume
from pravahx.reservoir.volume_satellite import (
    compute_volume_existing_lake,
    compute_volume_new_lake,
)


def test_compute_volume_new_lake() -> None:
    """Test volume calculation for a newly formed landslide/blockage lake."""
    # Create a 10x10 synthetic bowl DEM:
    # Bed elevation = 100.0 m in a 4x4 inner area
    # Surrounding ridge/shore elevation = 120.0 m
    dem = np.full((10, 10), 120.0, dtype=np.float32)
    dem[3:7, 3:7] = 100.0  # 16 cells of bed at 100m (depth 20m)

    # Water mask covering the 4x4 bowl plus edge cells
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:8, 2:8] = True  # 6x6 water mask (outer perimeter is on the 120m shore)

    cell_area_m2 = 900.0  # 30m x 30m cells

    vol = compute_volume_new_lake(dem, mask, cell_area_m2)

    # Water surface elevation along mask perimeter (edges) is 120m.
    # Inside the 4x4 bowl (16 cells), bed is 100m -> depth = 20m.
    # Along the 1-cell border (20 cells), elevation is 120m -> depth = 0m.
    # Total volume = 16 cells * 20m * 900 m2 = 288,000 m3
    expected_vol = 16 * 20.0 * 900.0
    assert abs(vol - expected_vol) < 1.0, f"Expected {expected_vol}, got {vol}"


def test_compute_volume_new_lake_empty_mask() -> None:
    """Empty water mask returns 0.0 volume."""
    dem = np.full((5, 5), 100.0, dtype=np.float32)
    mask = np.zeros((5, 5), dtype=bool)
    assert compute_volume_new_lake(dem, mask, cell_area_m2=900.0) == 0.0


def test_compute_volume_existing_lake() -> None:
    """Test area-volume power law scaling for existing lakes."""
    # 1 km2 lake = 1,000,000 m2
    area_m2 = 1_000_000.0
    vol = compute_volume_existing_lake(area_m2, kappa=0.043, zeta=1.146)

    # V = 0.043 * (1.0)^1.146 km3 = 0.043 km3 = 43,000,000 m3
    expected_vol = 43_000_000.0
    assert abs(vol - expected_vol) < 1000.0, f"Expected {expected_vol}, got {vol}"

    # Non-positive area returns 0.0
    assert compute_volume_existing_lake(0.0, kappa=0.043, zeta=1.146) == 0.0
    assert compute_volume_existing_lake(-100.0, kappa=0.043, zeta=1.146) == 0.0

    # Missing required parameters raises TypeError
    with pytest.raises(TypeError):
        compute_volume_existing_lake(area_m2)  # type: ignore[call-arg]


def test_get_dam_volume_not_implemented() -> None:
    """Dam register lookup raises NotImplementedError until connected."""
    with pytest.raises(NotImplementedError, match="Dam register lookup not yet implemented"):
        get_dam_volume("dam_tehri_001")


def test_estimate_volume_from_terrain_extrapolation() -> None:
    """Test terrain slope extrapolation and warning flag for existing unmonitored lakes."""
    from pravahx.reservoir.volume_satellite import estimate_volume_from_terrain_extrapolation

    # Create a 20x20 DEM with a flat lake in the center (100m) and 1:1 slopes outside
    dem = np.zeros((20, 20), dtype=np.float32)
    mask = np.zeros((20, 20), dtype=bool)

    # Lake in cells [7:13, 7:13] (6x6 cells) at elevation 100.0 m
    mask[7:13, 7:13] = True
    dem[:, :] = 100.0

    # Surrounding hills climb 20 m over 5 cells
    for r in range(20):
        for c in range(20):
            if not mask[r, c]:
                dist = max(0, max(abs(r - 9.5), abs(c - 9.5)) - 2.5)
                dem[r, c] = 100.0 + dist * 4.0

    vol, m, warning = estimate_volume_from_terrain_extrapolation(
        dem=dem, mask=mask, cell_area_m2=900.0, buffer_cells=3, assumed_m=2.0
    )

    assert vol > 0.0
    assert m == 2.0
    assert "High uncertainty" in warning
