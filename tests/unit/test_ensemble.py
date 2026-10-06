"""Unit tests for multi-model breach regression ensemble."""

from __future__ import annotations

import pytest

from pravahx.breach.ensemble import (
    calc_froehlich_1995,
    calc_froehlich_2008,
    calc_macdonald_langridge_monopolis_1984,
    calc_von_thun_gillette_1990,
    compute_breach_ensemble,
)


def test_individual_regressions() -> None:
    """Verify individual regression equations compute positive physical values."""
    vol = 10.0e6  # 10 MCM
    h = 30.0  # 30 m

    f08 = calc_froehlich_2008(vol, h, mode="overtopping")
    f95 = calc_froehlich_1995(vol, h, mode="overtopping")
    vtg = calc_von_thun_gillette_1990(vol, h, mode="overtopping", erodibility="erosion_resistant")
    vtg_erodible = calc_von_thun_gillette_1990(
        vol, h, mode="overtopping", erodibility="easily_erodible"
    )
    mlm = calc_macdonald_langridge_monopolis_1984(vol, h, mode="overtopping")

    for model in [f08, f95, vtg, vtg_erodible]:
        assert model.average_width_m is not None
        assert model.average_width_m > 0.0
        assert model.formation_time_hr > 0.0
        assert model.side_slope_z > 0.0

    # Von Thun & Gillette erodibility comparison
    assert vtg.formation_time_hr == 0.015 * h
    assert vtg_erodible.formation_time_hr == 0.020 * h

    # MacDonald & Langridge-Monopolis: width is None (excluded from direct width spread)
    assert mlm.average_width_m is None
    assert mlm.formation_time_hr > 0.0
    assert mlm.side_slope_z == 0.5


def test_compute_breach_ensemble() -> None:
    """Verify multi-model ensemble derives min, median, max from regression spread."""
    vol = 10.0e6
    h = 30.0

    ensemble = compute_breach_ensemble(vol, h, mode="overtopping")

    assert "min" in ensemble
    assert "median" in ensemble
    assert "max" in ensemble

    e_min = ensemble["min"]
    e_med = ensemble["median"]
    e_max = ensemble["max"]

    # Width spread order: min <= median <= max
    assert e_min.average_width_m <= e_med.average_width_m <= e_max.average_width_m

    # Formation time spread order: min <= median <= max
    assert e_min.formation_time_hr <= e_med.formation_time_hr <= e_max.formation_time_hr

    # Check models list
    assert len(e_med.models_used_width) == 3
    assert "Froehlich (2008)" in e_med.models_used_width
    assert "Froehlich (1995)" in e_med.models_used_width
    assert "Von Thun and Gillette (1990)" in e_med.models_used_width

    assert len(e_med.models_used_time) == 4
    assert "Froehlich (2008)" in e_med.models_used_time
    assert "Froehlich (1995)" in e_med.models_used_time
    assert "Von Thun and Gillette (1990)" in e_med.models_used_time
    assert "MacDonald and Langridge-Monopolis (1984)" in e_med.models_used_time


def test_compute_breach_ensemble_invalid_inputs() -> None:
    """Non-positive volume or height raises ValueError."""
    with pytest.raises(ValueError):
        compute_breach_ensemble(-1e6, 20.0)
    with pytest.raises(ValueError):
        compute_breach_ensemble(1e6, -20.0)
