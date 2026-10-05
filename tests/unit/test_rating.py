"""Unit tests for the HAND rating curve and stage solver (Phase 1)."""

from __future__ import annotations

import numpy as np

from pravahx.engines.tier0_hand.rating import (
    compute_hydraulic_geometry,
    mannings_discharge,
)


class TestRating:
    def test_compute_hydraulic_geometry_flat_channel(self) -> None:
        """Test a flat rectangular channel."""
        # 10x10 grid, cell size 2m.
        # Stream bed (HAND=0) is 3 cells wide.
        hand = np.full((10, 10), 10.0)
        hand[:, 4:7] = 0.0

        # Stage = 2.0m.
        # Inundated cells per row = 3. Total inundated cells = 30.
        # Wetted width = 30 * 2 = 60m.
        # Area = 30 cells * (2.0 - 0.0) depth * 2m cell size = 120 m^2
        # Wait, the compute_hydraulic_geometry formula:
        # A = sum(depth) * cell_size = 30 * 2.0 * 2.0 = 120.0
        # P = 30 * 2.0 = 60.0

        area, perim = compute_hydraulic_geometry(hand, cell_size_m=2.0, stage=2.0)

        assert np.isclose(area, 120.0)
        assert np.isclose(perim, 60.0)

    def test_mannings_discharge(self) -> None:
        """Test Manning's equation calculation."""
        # A = 120, P = 60 => R = 2
        # S = 0.001, n = 0.035
        # Q = (1/0.035) * 120 * (2^(2/3)) * sqrt(0.001)
        # 2^(2/3) = 1.5874
        # sqrt(0.001) = 0.03162
        # Q = 28.57 * 120 * 1.5874 * 0.03162 = 172.1 m^3/s

        q = mannings_discharge(area=120.0, perimeter=60.0, slope=0.001, mannings_n=0.035)

        expected_q = (1.0 / 0.035) * 120.0 * (2.0 ** (2.0 / 3.0)) * (0.001**0.5)
        assert np.isclose(q, expected_q)

    def test_zero_stage_zero_discharge(self) -> None:
        hand = np.zeros((5, 5))
        area, perim = compute_hydraulic_geometry(hand, 1.0, 0.0)
        assert area == 0.0
        assert perim == 0.0

        q = mannings_discharge(area, perim, 0.001, 0.035)
        assert q == 0.0
