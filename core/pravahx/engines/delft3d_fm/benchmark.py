"""Idealized dam break benchmark against Ritter (1892) analytical solution."""

from __future__ import annotations

import math
import tarfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

import netCDF4
import numpy as np
from hydrolib.core.dflowfm.mdu.models import FMModel

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class BenchmarkResult:
    """Quantitative comparison between Delft3D FM simulation and reference solution."""

    case_name: str
    rmse_m: float
    front_error_m: float
    front_error_rel: float
    passes_tolerance: bool
    notes: str


class Delft3DBenchmark:
    """Executes and verifies idealized dam break against Ritter (1892)."""

    def __init__(
        self,
        length: float = 2000.0,
        width: float = 50.0,
        dx: float = 5.0,
        dam_x: float = 1000.0,
        h0: float = 10.0,
        g: float = 9.81,
        uniffrictcoef: float = 0.0,
        epshu: float | None = None,
    ):
        self.length = length
        self.width = width
        self.dx = dx
        self.dam_x = dam_x
        self.h0 = h0
        self.g = g
        self.uniffrictcoef = uniffrictcoef
        self.epshu = epshu

    def generate_mesh(self, net_path: Path) -> None:
        """Generate a 2D UGRID NetCDF mesh."""
        nx = int(self.length / self.dx)
        ny = int(self.width / self.dx)

        # Nodes
        x_nodes = np.linspace(0, self.length, nx + 1)
        y_nodes = np.linspace(0, self.width, ny + 1)
        x_grid, y_grid = np.meshgrid(x_nodes, y_nodes)
        node_x = x_grid.flatten()
        node_y = y_grid.flatten()

        # Faces
        faces_list = []
        for j in range(ny):
            for i in range(nx):
                n0 = j * (nx + 1) + i
                n1 = n0 + 1
                n2 = (j + 1) * (nx + 1) + (i + 1)
                n3 = (j + 1) * (nx + 1) + i
                # 1-based indexing for d-flowfm net.nc
                faces_list.append([n0 + 1, n1 + 1, n2 + 1, n3 + 1])
        faces = np.array(faces_list, dtype=np.int32)

        # Face coordinates (centers)
        face_x = np.zeros(len(faces))
        face_y = np.zeros(len(faces))
        face_z = np.zeros(len(faces))  # Flat bed at z=0
        for i, face in enumerate(faces):
            idxs = face - 1
            face_x[i] = np.mean(node_x[idxs])
            face_y[i] = np.mean(node_y[idxs])

        # Edges (Links)
        # Delft3D requires NetLink: [node1, node2] (1-based)
        links_list = []
        # Horizontal edges
        for j in range(ny + 1):
            for i in range(nx):
                links_list.append([j * (nx + 1) + i + 1, j * (nx + 1) + i + 2])
        # Vertical edges
        for j in range(ny):
            for i in range(nx + 1):
                links_list.append([j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1])
        links = np.array(links_list, dtype=np.int32)

        ds = netCDF4.Dataset(net_path, "w", format="NETCDF4")

        ds.createDimension("nNetNode", len(node_x))
        ds.createDimension("nNetElem", len(faces))
        ds.createDimension("nNetElemMaxNode", 4)
        ds.createDimension("nNetLink", len(links))
        ds.createDimension("nNetLinkPts", 2)

        # Nodes
        var_nx = ds.createVariable("NetNode_x", "f8", ("nNetNode",))
        var_ny = ds.createVariable("NetNode_y", "f8", ("nNetNode",))
        var_nz = ds.createVariable("NetNode_z", "f8", ("nNetNode",))
        var_nx[:] = node_x
        var_ny[:] = node_y
        var_nz[:] = np.zeros(len(node_x))

        # Faces
        var_elem = ds.createVariable("NetElemNode", "i4", ("nNetElem", "nNetElemMaxNode"))
        var_elem[:] = faces
        var_ex = ds.createVariable("NetElem_x", "f8", ("nNetElem",))
        var_ey = ds.createVariable("NetElem_y", "f8", ("nNetElem",))
        var_ez = ds.createVariable("NetElem_z", "f8", ("nNetElem",))
        var_ex[:] = face_x
        var_ey[:] = face_y
        var_ez[:] = face_z

        # Links
        var_link = ds.createVariable("NetLink", "i4", ("nNetLink", "nNetLinkPts"))
        var_link[:] = links
        var_lt = ds.createVariable("NetLinkType", "i4", ("nNetLink",))
        var_lt[:] = np.full(len(links), 2)  # 2 = internal/computational link

        ds.close()

    def generate_case(self, work_dir: Path) -> Path:
        """Generate the complete Delft3D FM case directory."""
        case_dir = work_dir / "delft3d_benchmark"
        case_dir.mkdir(parents=True, exist_ok=True)

        net_path = case_dir / "grid_net.nc"
        self.generate_mesh(net_path)

        # Initial condition (water depth h0 upstream)
        pol_path = case_dir / "upstream.pol"
        with open(pol_path, "w") as f:
            f.write("upstream\n5 2\n")
            f.write(f"{-10.0} {-10.0}\n")
            f.write(f"{self.dam_x} {-10.0}\n")
            f.write(f"{self.dam_x} {self.width + 10.0}\n")
            f.write(f"{-10.0} {self.width + 10.0}\n")
            f.write(f"{-10.0} {-10.0}\n")

        # Custom INI file for initial fields
        ini_path = case_dir / "initialFields.ini"
        with open(ini_path, "w") as f:
            f.write("[General]\n")
            f.write("fileVersion = 2.00\n")
            f.write("fileType = iniField\n")
            f.write("[Initial]\n")
            f.write("quantity = waterlevel\n")
            f.write("dataFileType = polygon\n")
            f.write("interpolationMethod = constant\n")
            f.write("operand = O\n")
            f.write(f"value = {self.h0}\n")
            f.write("locationFile = upstream.pol\n")

        mdu_path = case_dir / "ritter.mdu"
        fm = FMModel()
        fm.geometry.netfile = "grid_net.nc"
        fm.time.refdate = 20260101
        fm.time.tstart = 0.0
        fm.time.tstop = 40.0
        fm.time.dtmax = 0.5
        fm.time.dtuser = 5.0
        fm.output.mapinterval = [5.0]
        fm.output.hisinterval = [5.0]
        fm.physics.uniffrictcoef = self.uniffrictcoef
        if self.epshu is not None:
            fm.numerics.epshu = self.epshu
        fm.save(filepath=mdu_path)

        # Fix obsolete keys and set MapFormat
        mdu_text = mdu_path.read_text(encoding="utf-8")
        lines = mdu_text.splitlines()
        obsolete_keys = [
            "TransportMethod",
            "Qhrelax",
            "Jaorgsethu",
            "EffectSpiral",
            "Gapres",
            "WaveNikuradse",
            "Writebalancefile",
            "wrishp_enc",
        ]
        new_lines = []
        for line in lines:
            lower_line = line.lower().strip()
            if any(
                lower_line.startswith(k.lower() + "=") or lower_line.startswith(k.lower() + " ")
                for k in obsolete_keys
            ):
                new_lines.append(f"# {line}")
                continue
            if lower_line.startswith("mapformat"):
                new_lines.append("MapFormat = 4")
                continue
            new_lines.append(line)

        # Inject IniFieldFile if it's not present
        if not any(entry.lower().startswith("inifieldfile") for entry in new_lines):
            for idx, line in enumerate(new_lines):
                if line.lower().startswith("[geometry]"):
                    new_lines.insert(idx + 1, "IniFieldFile = initialFields.ini")
                    break

        mdu_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        # Run script
        sh_path = case_dir / "run_linux.sh"
        sh_content = (
            "#!/bin/bash\nset -e\n"
            "export LD_LIBRARY_PATH=/content/delft3d_bin/lib:$LD_LIBRARY_PATH\n"
            "/content/delft3d_bin/bin/dflowfm --nodisplay --autostart ritter.mdu\n"
            "if grep -E 'keyword.*is obsolete' *_*.dia; then\n"
            "  echo 'ERROR: Engine found obsolete keys in MDU! See above.'\n"
            "  exit 1\n"
            "fi\n"
        )
        sh_path.write_text(sh_content, encoding="utf-8")
        sh_path.chmod(0o755)

        return case_dir

    def package_for_remote(self, case_dir: Path, output_tar: Path) -> None:
        with tarfile.open(output_tar, "w:gz") as tar:
            for item in case_dir.iterdir():
                tar.add(item, arcname=item.name)

    def evaluate_results(self, map_nc_path: Path) -> BenchmarkResult:
        """Compare output against Ritter (1892)."""
        ds = netCDF4.Dataset(map_nc_path, "r")

        # Face coordinates
        face_x = ds.variables["mesh2d_face_x"][:]
        face_y = ds.variables["mesh2d_face_y"][:]

        # We look at the centerline (y ≈ width/2)
        center_mask = np.abs(face_y - self.width / 2.0) < self.dx
        cx = face_x[center_mask]

        # Sort by x
        sort_idx = np.argsort(cx)
        cx = cx[sort_idx]

        times = ds.variables["time"][:]
        depths = ds.variables["mesh2d_waterdepth"][:]

        c = math.sqrt(self.g * self.h0)

        max_rmse = 0.0
        max_front_err = 0.0
        max_front_rel = 0.0

        notes = []

        # Compare at t=10, 20, 30
        for target_t in [10.0, 20.0, 30.0]:
            # Find closest time index
            t_idx = np.argmin(np.abs(times - target_t))
            actual_t = times[t_idx]

            d_t = depths[t_idx, :]
            cd = d_t[center_mask][sort_idx]

            # Theoretical front
            x_front_theory = self.dam_x + 2 * actual_t * c

            # Continuous front (first x after dam where depth < threshold)
            front_sims = {}
            for thresh in [0.01, 0.05, 0.1]:
                # find indices after dam
                post_dam = np.where(cx >= self.dam_x)[0]
                if len(post_dam) > 0:
                    dry = np.where(cd[post_dam] < thresh)[0]
                    if len(dry) > 0:
                        # front is the last wet cell before the dry one
                        idx = post_dam[dry[0]] - 1
                        idx = max(idx, 0)
                        front_sims[thresh] = cx[idx]
                    else:
                        front_sims[thresh] = cx[-1]
                else:
                    front_sims[thresh] = cx[-1]

            x_front_sim_05 = front_sims[0.05]
            front_err = abs(x_front_sim_05 - x_front_theory)
            front_rel = front_err / x_front_theory if x_front_theory > 0 else 0.0

            # Theoretical depth profile
            h_theory = np.zeros_like(cx)
            for i, x in enumerate(cx):
                if x <= self.dam_x - actual_t * c:
                    h_theory[i] = self.h0
                elif x >= self.dam_x + 2 * actual_t * c:
                    h_theory[i] = 0.0
                else:
                    h_theory[i] = (1.0 / (9.0 * self.g)) * (
                        2 * c - (x - self.dam_x) / actual_t
                    ) ** 2

            rmse = float(np.sqrt(np.mean((cd - h_theory) ** 2)))

            max_rmse = max(max_rmse, rmse)
            max_front_err = max(max_front_err, front_err)
            max_front_rel = max(max_front_rel, front_rel)

            rel_pct = front_rel * 100
            f_01 = front_sims[0.01]
            f_05 = front_sims[0.05]
            f_10 = front_sims[0.1]
            fronts_str = f"fronts(0.01/0.05/0.1m)={f_01:.1f}/{f_05:.1f}/{f_10:.1f}"
            notes.append(
                f"t={actual_t}s: RMSE={rmse:.3f}m, "
                f"FrontErr={front_err:.1f}m ({rel_pct:.1f}%), {fronts_str}"
            )

        ds.close()

        # Pass tolerances from VALIDATION.md
        passes = (max_front_rel <= 0.05) and (max_rmse <= 0.5)

        status_note = "RUN AND PASSED" if passes else "FAILED"
        notes_str = " | ".join(notes)
        full_note = (
            f"Evaluated against Delestre et al. (2013) SWASHES. {notes_str}. Status: {status_note}."
        )

        return BenchmarkResult(
            case_name="Ritter (1892) Idealized Dam Break",
            rmse_m=max_rmse,
            front_error_m=max_front_err,
            front_error_rel=max_front_rel,
            passes_tolerance=passes,
            notes=full_note,
        )
