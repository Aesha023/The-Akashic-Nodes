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
    vtg = calc_von_thun_gillette_1990(vol, h, mode="overtopping")
    mlm = calc_macdonald_langridge_monopolis_1984(vol, h, mode="overtopping")

    for model in [f08, f95, vtg, mlm]:
        assert model.average_width_m > 0.0
        assert model.formation_time_hr > 0.0
        assert model.side_slope_z > 0.0


def test_compute_breach_ensemble() -> None:
    """Verify multi-model ensemble derives p10, p50, p90 quantiles from regression spread."""
    vol = 10.0e6
    h = 30.0

    ensemble = compute_breach_ensemble(vol, h, mode="overtopping")

    assert "p10" in ensemble
    assert "p50" in ensemble
    assert "p90" in ensemble

    p10 = ensemble["p10"]
    p50 = ensemble["p50"]
    p90 = ensemble["p90"]

    # Width quantile order: p10 <= p50 <= p90
    assert p10.average_width_m <= p50.average_width_m <= p90.average_width_m

    # Formation time quantile order: p10 <= p50 <= p90
    assert p10.formation_time_hr <= p50.formation_time_hr <= p90.formation_time_hr

    # Check models list
    assert len(p50.models_used) == 4
    assert "Froehlich (2008)" in p50.models_used
    assert "Froehlich (1995)" in p50.models_used
    assert "Von Thun and Gillette (1990)" in p50.models_used
    assert "MacDonald and Langridge-Monopolis (1984)" in p50.models_used


def test_compute_breach_ensemble_invalid_inputs() -> None:
    """Non-positive volume or height raises ValueError."""
    with pytest.raises(ValueError):
        compute_breach_ensemble(-1e6, 20.0)
    with pytest.raises(ValueError):
        compute_breach_ensemble(1e6, -20.0)
