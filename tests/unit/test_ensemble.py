"""Unit tests for ensemble generator."""

import math

from pravahx.breach.ensemble import generate_ensemble


def test_generate_ensemble() -> None:
    """Verify log-normal ensemble generation."""
    b_base = 100.0
    t_base = 2.0
    se_b = 0.3  # Standard error of ln(B)
    se_t = 0.5  # Standard error of ln(t)

    ensemble = generate_ensemble(b_base, t_base, se_b, se_t)

    assert "p10" in ensemble
    assert "p50" in ensemble
    assert "p90" in ensemble

    # p50 should be the base values
    assert abs(ensemble["p50"].average_width_m - b_base) < 1e-5
    assert abs(ensemble["p50"].formation_time_hr - t_base) < 1e-5

    # p10 should be smaller
    assert ensemble["p10"].average_width_m < b_base
    assert ensemble["p10"].formation_time_hr < t_base

    # p90 should be larger
    assert ensemble["p90"].average_width_m > b_base
    assert ensemble["p90"].formation_time_hr > t_base

    # Verify exact math for p90
    expected_b_90 = b_base * math.exp(1.28155 * se_b)
    expected_t_90 = t_base * math.exp(1.28155 * se_t)

    assert abs(ensemble["p90"].average_width_m - expected_b_90) < 1e-5
    assert abs(ensemble["p90"].formation_time_hr - expected_t_90) < 1e-5


def test_unsupported_quantile() -> None:
    import pytest

    with pytest.raises(ValueError, match="Unsupported quantile"):
        generate_ensemble(100, 2, 0.1, 0.1, quantiles=["p99"])
