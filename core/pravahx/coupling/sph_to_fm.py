"""SPH to Delft3D Flexible Mesh coupling and volume conservation validation (Phase 4).

Translates DualSPHysics near-field SPH outflow hydrograph into Delft3D FM
upstream boundary conditions (.bc / .pli) with strict volume conservation checks.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from pravahx.errors import EngineError

if TYPE_CHECKING:
    from pravahx.engines.base import NormalisedOutput

logger = logging.getLogger(__name__)

DEFAULT_COUPLING_VOLUME_TOLERANCE = 0.01  # 1.0% volume conservation tolerance


class CouplingVolumeError(EngineError):
    """Raised when volume conservation across SPH-to-Delft3D handoff exceeds tolerance."""

    def __init__(self, message: str, rel_error: float, tolerance: float) -> None:
        super().__init__(message, engine="coupling")
        self.rel_error = rel_error
        self.tolerance = tolerance


@dataclass(frozen=True)
class TimeDischargePair:
    """Time and discharge pair."""

    time_s: float
    discharge_m3s: float


@dataclass(frozen=True)
class CouplingResult:
    """Result of SPH-to-Delft3D coupling handoff."""

    bc_file_path: Path
    boundary_name: str
    sph_volume_m3: float
    fm_volume_m3: float
    relative_volume_error: float
    peak_discharge_m3s: float
    duration_s: float
    time_series_points: int
    is_conserved: bool
    metadata: dict[str, Any]


def integrate_hydrograph_volume(time_series: list[TimeDischargePair]) -> float:
    """Integrate hydrograph discharge time series using the trapezoidal rule.

    Args:
        time_series: List of (time_s, discharge_m3s) points.

    Returns:
        Total volume in cubic metres (m³).
    """
    if len(time_series) < 2:
        return 0.0

    times = np.array([pt.time_s for pt in time_series], dtype=np.float64)
    flows = np.array([pt.discharge_m3s for pt in time_series], dtype=np.float64)

    # Sort by time to ensure monotonic integration
    sort_idx = np.argsort(times)
    times = times[sort_idx]
    flows = flows[sort_idx]

    volume_m3 = float(np.trapezoid(flows, times))
    return max(0.0, volume_m3)


def parse_sph_hydrograph_csv(hydrograph_path: Path) -> list[TimeDischargePair]:
    """Parse SPH outflow hydrograph from CSV file.

    Args:
        hydrograph_path: Path to CSV with columns time_s, discharge_m3s (or similar).

    Returns:
        List of TimeDischargePair data.
    """
    if not hydrograph_path.exists():
        raise EngineError(
            f"SPH outflow hydrograph CSV not found: {hydrograph_path}",
            engine="coupling",
        )

    pairs: list[TimeDischargePair] = []
    with open(hydrograph_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle variations in column names
            t_val = float(row.get("time_s") or row.get("time") or row.get("t", 0.0))
            q_val = float(
                row.get("discharge_m3s")
                or row.get("discharge")
                or row.get("q_m3s")
                or row.get("q", 0.0)
            )
            pairs.append(TimeDischargePair(time_s=t_val, discharge_m3s=q_val))

    if not pairs:
        raise EngineError(
            f"SPH outflow hydrograph CSV at {hydrograph_path} is empty",
            engine="coupling",
        )

    return pairs


def generate_delft3d_bc_file(
    time_series: list[TimeDischargePair],
    output_bc_path: Path,
    boundary_name: str = "SPH_Handoff_Inflow",
    time_unit: str = "seconds",
) -> Path:
    """Generate HYDROLIB-compatible Delft3D FM boundary condition (.bc) file.

    Args:
        time_series: List of (time_s, discharge_m3s) points.
        output_bc_path: Target .bc file path.
        boundary_name: Boundary identifier name.
        time_unit: Time unit string (default: 'seconds').

    Returns:
        Path to written .bc file.
    """
    output_bc_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "[General]",
        "fileVersion = 1.01",
        "fileType = boundConds",
        "",
        "[Boundary]",
        f"name = {boundary_name}",
        "quantity = dischargebnd",
        "function = timeseries",
        "timeInterpolation = linear",
        "",
    ]

    for pt in time_series:
        lines.append(f"{pt.time_s:.2f} {pt.discharge_m3s:.4f}")

    output_bc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_bc_path


def parse_delft3d_bc_file(bc_path: Path) -> list[TimeDischargePair]:
    """Parse Delft3D FM .bc file back into TimeDischargePair list for verification.

    Args:
        bc_path: Path to .bc file.

    Returns:
        List of TimeDischargePair points.
    """
    if not bc_path.exists():
        raise EngineError(f"Delft3D .bc file not found: {bc_path}", engine="coupling")

    pairs: list[TimeDischargePair] = []
    lines = bc_path.read_text(encoding="utf-8").splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("[") or line_clean.startswith("#"):
            continue
        if "=" in line_clean:
            continue

        parts = line_clean.split()
        if len(parts) >= 2:
            try:
                t = float(parts[0])
                q = float(parts[1])
                pairs.append(TimeDischargePair(time_s=t, discharge_m3s=q))
            except ValueError:
                continue

    return pairs


class SPHToDelft3DCoupler:
    """Couples near-field 3D SPH outflow to downstream 2D Delft3D Flexible Mesh."""

    def __init__(self, tolerance: float = DEFAULT_COUPLING_VOLUME_TOLERANCE) -> None:
        self.tolerance = tolerance

    def couple(
        self,
        sph_output: NormalisedOutput | Path,
        target_dir: Path,
        boundary_name: str = "SPH_Handoff_Inflow",
    ) -> CouplingResult:
        """Execute SPH-to-Delft3D coupling workflow with volume conservation verification.

        Args:
            sph_output: NormalisedOutput from DualSPHysics or Path to hydrograph CSV.
            target_dir: Directory to store generated Delft3D boundary condition files.
            boundary_name: Unique identifier for the boundary condition.

        Returns:
            CouplingResult containing generated paths, volume metrics, and validation status.

        Raises:
            CouplingVolumeError: If handoff volume conservation error exceeds tolerance.
        """
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Extract hydrograph CSV path
        if isinstance(sph_output, Path):
            hydrograph_path = sph_output
        else:
            hg_meta = sph_output.metadata.get("hydrograph_path")
            if not hg_meta:
                raise EngineError(
                    "DualSPHysics NormalisedOutput contains no hydrograph_path in metadata",
                    engine="coupling",
                )
            hydrograph_path = Path(hg_meta)

        # 2. Parse SPH hydrograph
        sph_time_series = parse_sph_hydrograph_csv(hydrograph_path)
        sph_vol = integrate_hydrograph_volume(sph_time_series)

        # 3. Generate Delft3D FM .bc file
        bc_path = target_dir / f"{boundary_name}.bc"
        generate_delft3d_bc_file(
            time_series=sph_time_series,
            output_bc_path=bc_path,
            boundary_name=boundary_name,
        )

        # 4. Verify boundary file and compute FM integrated volume
        fm_time_series = parse_delft3d_bc_file(bc_path)
        fm_vol = integrate_hydrograph_volume(fm_time_series)

        # 5. Volume conservation check
        if sph_vol > 0:
            rel_error = abs(sph_vol - fm_vol) / sph_vol
        else:
            rel_error = 0.0 if fm_vol == 0.0 else 1.0

        is_conserved = rel_error <= self.tolerance

        logger.info(
            "SPH-to-Delft3D Coupling: SPH Volume=%.2f m³, FM Volume=%.2f m³, "
            "Error=%.4f%% (Tolerance=%.2f%%)",
            sph_vol,
            fm_vol,
            rel_error * 100.0,
            self.tolerance * 100.0,
        )

        if not is_conserved:
            msg = (
                f"Coupling volume conservation error ({rel_error * 100.0:.3f}%) exceeds "
                f"tolerance ({self.tolerance * 100.0:.1f}%).\n"
                f"  SPH Outflow Volume:  {sph_vol:.2f} m³\n"
                f"  Delft3D Handoff Vol: {fm_vol:.2f} m³"
            )
            logger.error(msg)
            raise CouplingVolumeError(msg, rel_error=rel_error, tolerance=self.tolerance)

        peak_q = max((pt.discharge_m3s for pt in sph_time_series), default=0.0)
        dur_s = max((pt.time_s for pt in sph_time_series), default=0.0) - min(
            (pt.time_s for pt in sph_time_series), default=0.0
        )

        metadata: dict[str, Any] = {
            "source_hydrograph": str(hydrograph_path),
            "generated_bc_file": str(bc_path),
            "boundary_name": boundary_name,
            "sph_volume_m3": sph_vol,
            "fm_volume_m3": fm_vol,
            "relative_volume_error": rel_error,
            "tolerance": self.tolerance,
            "peak_discharge_m3s": peak_q,
            "duration_s": dur_s,
        }

        return CouplingResult(
            bc_file_path=bc_path,
            boundary_name=boundary_name,
            sph_volume_m3=sph_vol,
            fm_volume_m3=fm_vol,
            relative_volume_error=rel_error,
            peak_discharge_m3s=peak_q,
            duration_s=dur_s,
            time_series_points=len(sph_time_series),
            is_conserved=is_conserved,
            metadata=metadata,
        )


def couple_sph_to_fm(
    sph_output: NormalisedOutput | Path,
    target_dir: Path,
    boundary_name: str = "SPH_Handoff_Inflow",
    tolerance: float = DEFAULT_COUPLING_VOLUME_TOLERANCE,
) -> CouplingResult:
    """Convenience functional interface for SPH-to-Delft3D coupling.

    Args:
        sph_output: NormalisedOutput or Path to SPH outflow CSV.
        target_dir: Working directory to write Delft3D .bc boundary file.
        boundary_name: Boundary name identifier.
        tolerance: Maximum relative volume error allowed (default 0.01 = 1%).

    Returns:
        CouplingResult with path and conservation metrics.
    """
    coupler = SPHToDelft3DCoupler(tolerance=tolerance)
    return coupler.couple(sph_output, target_dir=target_dir, boundary_name=boundary_name)
