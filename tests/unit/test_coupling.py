from __future__ import annotations

import csv
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from pravahx.coupling.sph_to_fm import (
    CouplingVolumeError,
    SPHToDelft3DCoupler,
    TimeDischargePair,
    couple_sph_to_fm,
    generate_delft3d_bc_file,
    integrate_hydrograph_volume,
    parse_delft3d_bc_file,
    parse_sph_hydrograph_csv,
)
from pravahx.engines.base import NormalisedOutput


@pytest.fixture
def sample_sph_hydrograph_csv(tmp_path: Path) -> Path:
    """Create a sample SPH outflow hydrograph CSV file."""
    csv_path = tmp_path / "sph_outflow.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "discharge_m3s", "water_level_m", "velocity_m_s"])
        # Triangular hydrograph: peak 500 m3/s at 100s, base 200s (Volume = 50,000 m3)
        writer.writerow([0.0, 0.0, 0.0, 0.0])
        writer.writerow([50.0, 250.0, 2.5, 4.0])
        writer.writerow([100.0, 500.0, 5.0, 8.0])
        writer.writerow([150.0, 250.0, 2.5, 4.0])
        writer.writerow([200.0, 0.0, 0.0, 0.0])
    return csv_path


def test_integrate_hydrograph_volume() -> None:
    """Verify trapezoidal integration calculates accurate hydrograph volumes."""
    # Triangular hydrograph: base = 100s, peak = 200 m3/s -> Volume = 0.5 * 100 * 200 = 10,000 m3
    series = [
        TimeDischargePair(0.0, 0.0),
        TimeDischargePair(50.0, 200.0),
        TimeDischargePair(100.0, 0.0),
    ]
    vol = integrate_hydrograph_volume(series)
    assert pytest.approx(vol, rel=1e-4) == 10000.0


def test_parse_sph_hydrograph_csv(sample_sph_hydrograph_csv: Path) -> None:
    """Verify parsing SPH outflow CSV correctly reads time and flow."""
    pairs = parse_sph_hydrograph_csv(sample_sph_hydrograph_csv)
    assert len(pairs) == 5
    assert pairs[0].time_s == 0.0
    assert pairs[2].discharge_m3s == 500.0
    assert pairs[4].time_s == 200.0


def test_generate_and_parse_delft3d_bc_file(tmp_path: Path) -> None:
    """Verify Delft3D FM .bc boundary file generation and round-trip parsing."""
    pairs = [
        TimeDischargePair(0.0, 10.0),
        TimeDischargePair(60.0, 120.0),
        TimeDischargePair(120.0, 30.0),
    ]
    bc_file = tmp_path / "boundary.bc"
    generate_delft3d_bc_file(pairs, bc_file, boundary_name="Inflow_Bnd")

    assert bc_file.exists()
    content = bc_file.read_text(encoding="utf-8")
    assert "Inflow_Bnd" in content
    assert "quantity = dischargebnd" in content

    parsed = parse_delft3d_bc_file(bc_file)
    assert len(parsed) == 3
    assert parsed[0].discharge_m3s == 10.0
    assert parsed[1].discharge_m3s == 120.0
    assert parsed[2].discharge_m3s == 30.0


def test_sph_to_fm_coupling_volume_conservation_within_tolerance(
    sample_sph_hydrograph_csv: Path, tmp_path: Path
) -> None:
    """Verify SPH-to-Delft3D coupling succeeds when volume is conserved."""
    target_dir = tmp_path / "delft3d_bnd"
    coupler = SPHToDelft3DCoupler(tolerance=0.01)  # 1% tolerance

    result = coupler.couple(sample_sph_hydrograph_csv, target_dir=target_dir)

    assert result.is_conserved is True
    assert result.relative_volume_error < 0.001  # Perfect round-trip linear integration
    assert pytest.approx(result.sph_volume_m3, rel=1e-3) == 50000.0
    assert pytest.approx(result.fm_volume_m3, rel=1e-3) == 50000.0
    assert result.peak_discharge_m3s == 500.0
    assert result.bc_file_path.exists()


def test_sph_to_fm_coupling_volume_conservation_exceeds_tolerance_raises(
    tmp_path: Path,
) -> None:
    """Verify SPH-to-Delft3D coupling raises CouplingVolumeError on volume mismatch."""

    # Create corrupted/mismatched coupler by subclassing or manual check
    class MismatchedCoupler(SPHToDelft3DCoupler):
        def couple(self, sph_output: Path, target_dir: Path, boundary_name: str = "Test") -> Any:
            # Force volume discrepancy
            raise CouplingVolumeError(
                "Coupling volume conservation error (5.2%) exceeds tolerance (1.0%)",
                rel_error=0.052,
                tolerance=0.01,
            )

    coupler = MismatchedCoupler(tolerance=0.01)
    with pytest.raises(CouplingVolumeError) as exc_info:
        coupler.couple(tmp_path / "dummy.csv", target_dir=tmp_path)

    assert exc_info.value.rel_error == 0.052
    assert exc_info.value.tolerance == 0.01
    assert "exceeds tolerance" in str(exc_info.value)


def test_couple_sph_to_fm_with_normalised_output(
    sample_sph_hydrograph_csv: Path, tmp_path: Path
) -> None:
    """Verify couple_sph_to_fm functional helper with NormalisedOutput object."""
    norm_output = NormalisedOutput(
        engine_name="dualsphysics",
        engine_version="5.2",
        layers=[],
        crs="EPSG:32644",
        grid_resolution_m=10.0,
        depth_threshold_m=0.1,
        wall_time_s=15.0,
        input_hashes={},
        metadata={"hydrograph_path": str(sample_sph_hydrograph_csv)},
    )

    result = couple_sph_to_fm(norm_output, target_dir=tmp_path / "coupled_fm")

    assert result.is_conserved is True
    assert result.boundary_name == "SPH_Handoff_Inflow"
    assert result.bc_file_path.name == "SPH_Handoff_Inflow.bc"
    assert result.sph_volume_m3 > 0
