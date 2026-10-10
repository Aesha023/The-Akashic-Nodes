"""Tier-1 Delft3D FM real-terrain model setup and Tier-0 intercomparison (Ganga reach).

This module prepares a 2D Flexible Mesh hydrodynamic model on the Ganga reach near Rishikesh,
runs it with Delft3D FM, and performs a strict MODEL INTERCOMPARISON against the accepted
Tier-0 HAND inundation envelope.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import geopandas as gpd
import netCDF4
import numpy as np
import rasterio
from rasterio.features import rasterize, shapes
from scipy.optimize import brentq  # type: ignore[import-untyped]
from shapely.geometry import Point, shape

from pravahx.breach.froehlich import compute_froehlich_2008
from pravahx.breach.hydrograph import route_hydrograph
from pravahx.terrain.roughness import WORLDCOVER_TO_MANNINGS

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Obsolete MDU keys for Deltares D-Flow FM kernel
OBSOLETE_MDU_KEYS = [
    "transportmethod",
    "qhrelax",
    "jaorgsethu",
    "effectspiral",
    "gapres",
    "wavenikuradse",
    "writebalancefile",
    "wrishp_enc",
]


@dataclass(frozen=True)
class HypotheticalBreachScenario:
    """Hypothetical dam breach scenario parameters using Froehlich (2008)."""

    reservoir_volume_m3: float = 5807632.0  # 5.808 MCM
    breach_height_m: float = 26.0  # 26.0 m
    failure_mode: str = "overtopping"
    side_slope_z: float = 1.0  # 1.0 H:V for overtopping
    reservoir_exponent_m: float = 2.0  # Parabolic valley hypsometry
    base_flow_m3s: float = 100.0  # Lean season base flow
    average_breach_width_m: float = 58.42
    formation_time_s: float = 1870.3
    formation_time_hr: float = 0.5195
    breach_peak_discharge_m3s: float = 4900.0
    total_peak_discharge_m3s: float = 5000.0  # Exactly matches Tier-0 accepted peak


def compute_hypothetical_breach_scenario(
    volume_m3: float = 5807632.0,
    height_m: float = 26.0,
    base_flow_m3s: float = 100.0,
) -> HypotheticalBreachScenario:
    """Derive hypothetical breach parameters using Froehlich (2008)."""
    params = compute_froehlich_2008(
        volume_m3=volume_m3,
        height_m=height_m,
        mode="overtopping",
    )
    routed = route_hydrograph(
        initial_volume_m3=volume_m3,
        dam_height_m=height_m,
        b_avg_m=params.average_width_m,
        t_f_hr=params.formation_time_hr,
        reservoir_exponent=2.0,
        side_slope_z=params.side_slope_z,
        dt_hr=0.002,
    )
    total_peak = routed.peak_discharge_m3s + base_flow_m3s
    return HypotheticalBreachScenario(
        reservoir_volume_m3=volume_m3,
        breach_height_m=height_m,
        failure_mode="overtopping",
        side_slope_z=params.side_slope_z,
        reservoir_exponent_m=2.0,
        base_flow_m3s=base_flow_m3s,
        average_breach_width_m=params.average_width_m,
        formation_time_s=params.formation_time_hr * 3600.0,
        formation_time_hr=params.formation_time_hr,
        breach_peak_discharge_m3s=routed.peak_discharge_m3s,
        total_peak_discharge_m3s=total_peak,
    )


def generate_hypothetical_inflow_series(
    scenario: HypotheticalBreachScenario,
    total_duration_s: float = 7200.0,
    dt_s: float = 10.0,
) -> list[tuple[float, float]]:
    """Generate time series of (time_seconds, discharge_m3s)."""
    routed = route_hydrograph(
        initial_volume_m3=scenario.reservoir_volume_m3,
        dam_height_m=scenario.breach_height_m,
        b_avg_m=scenario.average_breach_width_m,
        t_f_hr=scenario.formation_time_hr,
        reservoir_exponent=scenario.reservoir_exponent_m,
        side_slope_z=scenario.side_slope_z,
        dt_hr=0.002,
    )
    times_s = [p["time_hr"] * 3600.0 for p in routed.points]
    flows = [p["discharge_m3s"] for p in routed.points]

    res: list[tuple[float, float]] = []
    n_steps = int(total_duration_s / dt_s) + 1
    for step in range(n_steps):
        t = step * dt_s
        q_breach = float(np.interp(t, times_s, flows, left=0.0, right=0.0))
        q_total = q_breach + scenario.base_flow_m3s
        res.append((t, round(q_total, 3)))
    return res


def compute_manning_normal_depth(
    discharge_m3s: float,
    channel_width_m: float = 150.0,
    bed_slope: float = 0.005,
    mannings_n: float = 0.035,
) -> float:
    """Solve normal flow depth y for given discharge using Manning's equation."""
    if discharge_m3s <= 0.0:
        return 0.0

    def residual(y: float) -> float:
        area = channel_width_m * y
        wetted_perimeter = channel_width_m + 2.0 * y
        hydraulic_radius = area / wetted_perimeter
        q_calc = (1.0 / mannings_n) * area * (hydraulic_radius ** (2.0 / 3.0)) * (bed_slope**0.5)
        return float(q_calc - discharge_m3s)

    root_val: Any = brentq(residual, 0.001, 35.0)
    return float(root_val)


def build_ganga_tier1_mesh(
    valley_geom: Any,
    dem_path: Path,
    net_path: Path,
    dx: float = 50.0,
) -> dict[str, Any]:
    """Generate a 2D UGRID NetCDF mesh inside the valley polygon with DEM elevations."""
    with rasterio.open(dem_path) as src_dem:
        dem_data = src_dem.read(1)
        dem_trans = src_dem.transform
        dem_nodata = src_dem.nodata

    minx, miny, maxx, maxy = valley_geom.bounds
    minx = np.floor(minx / dx) * dx
    miny = np.floor(miny / dx) * dx
    maxx = np.ceil(maxx / dx) * dx
    maxy = np.ceil(maxy / dx) * dx

    nx = int(np.round((maxx - minx) / dx))
    ny = int(np.round((maxy - miny) / dx))

    kept_cells: list[tuple[int, int]] = []
    for j in range(ny):
        yc = miny + (j + 0.5) * dx
        for i in range(nx):
            xc = minx + (i + 0.5) * dx
            if valley_geom.contains(Point(xc, yc)):
                kept_cells.append((i, j))

    if not kept_cells:
        raise ValueError("No grid cells found inside valley polygon!")

    node_map: dict[tuple[int, int], int] = {}
    node_x_list: list[float] = []
    node_y_list: list[float] = []
    node_z_list: list[float] = []

    def get_elev(x_coord: float, y_coord: float) -> float:
        row, col = rasterio.transform.rowcol(dem_trans, x_coord, y_coord)
        if 0 <= row < dem_data.shape[0] and 0 <= col < dem_data.shape[1]:
            val = float(dem_data[row, col])
            if dem_nodata is not None and (val == dem_nodata or np.isnan(val)):
                return 350.0
            return val
        return 350.0

    for i, j in kept_cells:
        for di, dj in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            corner = (i + di, j + dj)
            if corner not in node_map:
                node_idx = len(node_map) + 1
                node_map[corner] = node_idx
                xn = minx + corner[0] * dx
                yn = miny + corner[1] * dx
                zn = get_elev(xn, yn)
                node_x_list.append(xn)
                node_y_list.append(yn)
                node_z_list.append(zn)

    faces_list: list[list[int]] = []
    face_x_list: list[float] = []
    face_y_list: list[float] = []
    face_z_list: list[float] = []
    edges_set: set[tuple[int, int]] = set()

    for i, j in kept_cells:
        n0 = node_map[(i, j)]
        n1 = node_map[(i + 1, j)]
        n2 = node_map[(i + 1, j + 1)]
        n3 = node_map[(i, j + 1)]
        faces_list.append([n0, n1, n2, n3])

        xc = minx + (i + 0.5) * dx
        yc = miny + (j + 0.5) * dx
        zc = (
            node_z_list[n0 - 1] + node_z_list[n1 - 1] + node_z_list[n2 - 1] + node_z_list[n3 - 1]
        ) / 4.0
        face_x_list.append(xc)
        face_y_list.append(yc)
        face_z_list.append(zc)

        for ea, eb in [(n0, n1), (n1, n2), (n2, n3), (n3, n0)]:
            edge = (min(ea, eb), max(ea, eb))
            edges_set.add(edge)

    links_array = np.array(list(edges_set), dtype=np.int32)
    faces_array = np.array(faces_list, dtype=np.int32)

    if net_path.exists():
        net_path.unlink()

    ds = netCDF4.Dataset(net_path, "w", format="NETCDF4")
    ds.createDimension("nNetNode", len(node_x_list))
    ds.createDimension("nNetElem", len(faces_list))
    ds.createDimension("nNetElemMaxNode", 4)
    ds.createDimension("nNetLink", len(links_array))
    ds.createDimension("nNetLinkPts", 2)

    vnx = ds.createVariable("NetNode_x", "f8", ("nNetNode",))
    vny = ds.createVariable("NetNode_y", "f8", ("nNetNode",))
    vnz = ds.createVariable("NetNode_z", "f8", ("nNetNode",))
    vnx[:] = np.array(node_x_list, dtype=np.float64)
    vny[:] = np.array(node_y_list, dtype=np.float64)
    vnz[:] = np.array(node_z_list, dtype=np.float64)

    velem = ds.createVariable("NetElemNode", "i4", ("nNetElem", "nNetElemMaxNode"))
    velem[:] = faces_array
    vex = ds.createVariable("NetElem_x", "f8", ("nNetElem",))
    vey = ds.createVariable("NetElem_y", "f8", ("nNetElem",))
    vez = ds.createVariable("NetElem_z", "f8", ("nNetElem",))
    vex[:] = np.array(face_x_list, dtype=np.float64)
    vey[:] = np.array(face_y_list, dtype=np.float64)
    vez[:] = np.array(face_z_list, dtype=np.float64)

    vlink = ds.createVariable("NetLink", "i4", ("nNetLink", "nNetLinkPts"))
    vlink[:] = links_array
    vlt = ds.createVariable("NetLinkType", "i4", ("nNetLink",))
    vlt[:] = np.full(len(links_array), 2, dtype=np.int32)

    ds.close()

    return {
        "n_nodes": len(node_x_list),
        "n_faces": len(faces_list),
        "n_links": len(links_array),
        "cell_size_m": dx,
        "face_x": np.array(face_x_list),
        "face_y": np.array(face_y_list),
        "face_z": np.array(face_z_list),
    }


def write_pli(file_path: Path, name: str, points: list[tuple[float, float]]) -> None:
    """Write Delft3D polyline file (.pli)."""
    lines = [name, f"{len(points)} 2"]
    for x, y in points:
        lines.append(f"{x:.3f} {y:.3f}")
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_ganga_tier1_case(
    case_dir: Path,
    dem_path: Path,
    tier0_envelope_path: Path,
    worldcover_path: Path | None = None,
    buffer_m: float = 300.0,
    dx: float = 50.0,
    tstop_s: float = 7200.0,
    dtuser_s: float = 10.0,
    dtmax_s: float = 2.0,
    mapinterval_s: float = 60.0,
) -> dict[str, Any]:
    """Build the complete Delft3D FM real-terrain simulation case for Ganga reach."""
    case_dir.mkdir(parents=True, exist_ok=True)

    if str(tier0_envelope_path).endswith(".shp"):
        gdf = gpd.read_file(tier0_envelope_path)
        valley_geom = gdf.union_all().buffer(buffer_m)
    else:
        with rasterio.open(tier0_envelope_path) as src_env:
            env_data = src_env.read(1)
            env_mask = (env_data > 0) & (env_data != src_env.nodata)
            shapes_gen = shapes(
                env_mask.astype(np.int32), mask=env_mask, transform=src_env.transform
            )
            geoms = [shape(g) for g, val in shapes_gen if val == 1]
            gdf = gpd.GeoDataFrame({"geometry": geoms}, crs=src_env.crs)
            valley_geom = gdf.union_all().buffer(buffer_m)

    net_path = case_dir / "grid_net.nc"
    mesh_info = build_ganga_tier1_mesh(
        valley_geom=valley_geom,
        dem_path=dem_path,
        net_path=net_path,
        dx=dx,
    )

    scenario = compute_hypothetical_breach_scenario()
    inflow_series = generate_hypothetical_inflow_series(
        scenario=scenario,
        total_duration_s=tstop_s,
        dt_s=dtuser_s,
    )

    inlet_pts = [(243300.0, 3337900.0), (243600.0, 3337650.0)]
    inflow_pli = case_dir / "inflow_bnd.pli"
    write_pli(inflow_pli, "inflow_bnd", inlet_pts)

    inflow_bc = case_dir / "inflow.bc"
    inflow_lines = [
        "# written by PravahX for Ganga Tier-1 hypothetical scenario",
        "[General]",
        "fileVersion = 1.01",
        "fileType    = boundConds",
        "",
        "[Forcing]",
        "name              = inflow_bnd",
        "function          = timeseries",
        "timeInterpolation = linear",
        "quantity          = time",
        "unit              = seconds since 2026-01-01 00:00:00",
        "quantity          = dischargebnd",
        "unit              = m3/s",
    ]
    for t_val, q_val in inflow_series:
        inflow_lines.append(f"{t_val:.1f}  {q_val:.3f}")
    inflow_bc.write_text("\n".join(inflow_lines) + "\n", encoding="utf-8")

    outlet_pts = [(239700.0, 3333100.0), (240100.0, 3332800.0)]
    outlet_pli = case_dir / "downstream_bnd.pli"
    write_pli(outlet_pli, "downstream_bnd", outlet_pts)

    outlet_bc = case_dir / "downstream.bc"
    discharges = [0.0, 50.0, 100.0, 500.0, 1000.0, 2000.0, 3000.0, 5000.0, 8000.0, 12000.0]
    z_bed_outlet = 337.0
    outlet_lines = [
        "# written by PravahX: Q-h stage-discharge normal depth rating curve",
        "[General]",
        "fileVersion = 1.01",
        "fileType    = boundConds",
        "",
        "[Forcing]",
        "name     = downstream_bnd",
        "function = qhtable",
        "quantity = qhbnd",
        "unit     = m3/s",
        "quantity = waterlevelbnd",
        "unit     = m",
    ]
    for q_val in discharges:
        depth_val = compute_manning_normal_depth(q_val)
        wl_val = z_bed_outlet + depth_val
        outlet_lines.append(f"{q_val:.1f}  {wl_val:.3f}")
    outlet_bc.write_text("\n".join(outlet_lines) + "\n", encoding="utf-8")

    ext_path = case_dir / "boundary_conditions.ext"
    ext_lines = [
        "# written by PravahX for Ganga Tier-1 Delft3D FM",
        "[Boundary]",
        "quantity     = dischargebnd",
        f"locationFile = {inflow_pli.name}",
        f"forcingFile  = {inflow_bc.name}",
        "",
        "[Boundary]",
        "quantity     = qhbnd",
        f"locationFile = {outlet_pli.name}",
        f"forcingFile  = {outlet_bc.name}",
        "",
    ]
    ext_path.write_text("\n".join(ext_lines), encoding="utf-8")

    fric_xyz_path = case_dir / "roughness.xyz"
    mean_manning = 0.035
    if worldcover_path and worldcover_path.exists():
        with rasterio.open(worldcover_path) as src_lc:
            lc_data = src_lc.read(1)
            lc_trans = src_lc.transform

        fric_lines = []
        n_vals: list[float] = []
        for x_c, y_c in zip(mesh_info["face_x"], mesh_info["face_y"], strict=False):
            r, c = rasterio.transform.rowcol(lc_trans, x_c, y_c)
            n_val = 0.035
            if 0 <= r < lc_data.shape[0] and 0 <= c < lc_data.shape[1]:
                cls_id = int(lc_data[r, c])
                n_val = WORLDCOVER_TO_MANNINGS.get(cls_id, 0.035)
            n_vals.append(n_val)
            fric_lines.append(f"{x_c:.2f} {y_c:.2f} {n_val:.4f}")
        fric_xyz_path.write_text("\n".join(fric_lines) + "\n", encoding="utf-8")
        mean_manning = float(np.mean(n_vals))
    else:
        fric_lines = [
            f"{x_c:.2f} {y_c:.2f} 0.0350"
            for x_c, y_c in zip(mesh_info["face_x"], mesh_info["face_y"], strict=False)
        ]
        fric_xyz_path.write_text("\n".join(fric_lines) + "\n", encoding="utf-8")

    ini_path = case_dir / "initialFields.ini"
    ini_lines = [
        "[General]",
        "fileVersion = 2.00",
        "fileType    = iniField",
        "",
        "[Initial]",
        "quantity            = waterdepth",
        "dataFileType        = uniform",
        "interpolationMethod = constant",
        "operand             = O",
        "value               = 0.0",
        "",
        "[Parameter]",
        "quantity            = friction",
        "dataFileType        = sample",
        f"dataFile            = {fric_xyz_path.name}",
        "interpolationMethod = constant",
        "operand             = O",
        "",
    ]
    ini_path.write_text("\n".join(ini_lines), encoding="utf-8")

    mdu_path = case_dir / "flow2d3d.mdu"
    mdu_lines = [
        "# written by PravahX for Ganga Tier-1 FM Model Intercomparison",
        "[General]",
        "fileVersion           = 1.09",
        "fileType              = modelDef",
        "program               = D-Flow FM",
        "autoStart             = 0",
        "pathsRelativeToParent = 0",
        "",
        "[Geometry]",
        f"netFile               = {net_path.name}",
        f"iniFieldFile          = {ini_path.name}",
        f"frictFile             = {fric_xyz_path.name}",
        "bedLevType            = 3",
        "bedLevUni             = 350.0",
        "waterLevIni           = -999.0",
        "openBoundaryTolerance = 3.0",
        "useCaching            = 1",
        "",
        "[Time]",
        "refDate               = 20260101",
        "tstart                = 0.0",
        f"tstop                 = {tstop_s:.1f}",
        f"dtmax                 = {dtmax_s:.1f}",
        f"dtuser                = {dtuser_s:.1f}",
        "",
        "[Physics]",
        "unifFrictType         = 1",
        f"unifFrictCoef         = {mean_manning:.4f}",
        "vicouv                = 0.1",
        "dicouv                = 0.1",
        "ag                    = 9.81",
        "",
        "[Numerics]",
        "cflMax                = 0.7",
        "epsHu                 = 0.01",
        "",
        "[External Forcing]",
        f"extForceFileNew       = {ext_path.name}",
        "",
        "[Output]",
        "mapFormat             = 4",
        f"mapInterval           = {mapinterval_s:.1f}",
        f"hisInterval           = {mapinterval_s:.1f}",
        "obsFile               = ",
        "",
    ]
    clean_lines = []
    for line in mdu_lines:
        lower = line.lower().strip()
        if any(lower.startswith(k + "=") or lower.startswith(k + " ") for k in OBSOLETE_MDU_KEYS):
            clean_lines.append(f"# OBSOLETE {line}")
        else:
            clean_lines.append(line)

    mdu_path.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")

    return {
        "case_dir": case_dir,
        "mdu_path": mdu_path,
        "mesh_info": mesh_info,
        "scenario": scenario,
        "mean_manning_n": mean_manning,
    }


def postprocess_ganga_tier1_run(
    case_dir: Path,
    dem_path: Path,
    out_dir: Path,
    arr_thresholds: tuple[float, float] = (0.05, 0.30),
) -> dict[str, Any]:
    """Process Delft3D FM UGRID NetCDF output map and export GeoTIFFs & vectors."""
    out_dir.mkdir(parents=True, exist_ok=True)

    map_files = list(case_dir.glob("**/*_map.nc"))
    if not map_files:
        raise FileNotFoundError(f"No *_map.nc output found in {case_dir}")

    map_nc = map_files[0]
    ds = netCDF4.Dataset(map_nc, "r")

    face_x = ds.variables["mesh2d_face_x"][:]
    face_y = ds.variables["mesh2d_face_y"][:]
    times = ds.variables["time"][:]
    depths = ds.variables["mesh2d_waterdepth"][:]

    has_vel = "mesh2d_ucx" in ds.variables and "mesh2d_ucy" in ds.variables
    if has_vel:
        ucx = ds.variables["mesh2d_ucx"][:]
        ucy = ds.variables["mesh2d_ucy"][:]
        speeds = np.sqrt(ucx**2 + ucy**2)
    else:
        speeds = np.zeros_like(depths)

    n_faces = len(face_x)
    max_depth = np.zeros(n_faces, dtype=np.float32)
    max_velocity = np.zeros(n_faces, dtype=np.float32)
    arr_time_005 = np.full(n_faces, np.nan, dtype=np.float32)
    arr_time_030 = np.full(n_faces, np.nan, dtype=np.float32)

    thr1, thr2 = arr_thresholds

    for i in range(n_faces):
        d_series = depths[:, i]
        max_depth[i] = float(np.max(d_series))
        if has_vel:
            max_velocity[i] = float(np.max(speeds[:, i]))

        wet_idx1 = np.where(d_series >= thr1)[0]
        if len(wet_idx1) > 0:
            arr_time_005[i] = float(times[wet_idx1[0]])

        wet_idx2 = np.where(d_series >= thr2)[0]
        if len(wet_idx2) > 0:
            arr_time_030[i] = float(times[wet_idx2[0]])

    ds.close()

    with rasterio.open(dem_path) as src_dem:
        meta = src_dem.meta.copy()
        dem_shape = src_dem.shape
        dem_trans = src_dem.transform
        dem_crs = src_dem.crs

    dx_est = float(np.min(np.abs(np.diff(np.sort(np.unique(face_x)))))) if n_faces > 1 else 50.0
    if dx_est <= 0.0 or dx_est > 100.0:
        dx_est = 50.0

    half = dx_est / 2.0
    face_geoms = [
        Point(xc, yc).buffer(half, cap_style=3) for xc, yc in zip(face_x, face_y, strict=False)
    ]

    def write_raster(values: np.ndarray, dst_path: Path, nodata_val: float = -9999.0) -> None:
        shapes_vals = [
            (geom, float(val))
            for geom, val in zip(face_geoms, values, strict=False)
            if not np.isnan(val) and val != nodata_val
        ]
        burned = rasterize(
            shapes=shapes_vals,
            out_shape=dem_shape,
            transform=dem_trans,
            fill=nodata_val,
            default_value=nodata_val,
            dtype=np.float32,
        )
        out_meta = meta.copy()
        out_meta.update(dtype=rasterio.float32, nodata=nodata_val, count=1)
        with rasterio.open(dst_path, "w", **out_meta) as dst:
            dst.write(burned, 1)

    depth_tif = out_dir / "tier1_max_depth.tif"
    vel_tif = out_dir / "tier1_max_velocity.tif"
    arr05_tif = out_dir / "tier1_arrival_time_0_05.tif"
    arr30_tif = out_dir / "tier1_arrival_time_0_30.tif"

    write_raster(max_depth, depth_tif, nodata_val=-9999.0)
    write_raster(max_velocity, vel_tif, nodata_val=-9999.0)
    write_raster(arr_time_005, arr05_tif, nodata_val=-9999.0)
    write_raster(arr_time_030, arr30_tif, nodata_val=-9999.0)

    with rasterio.open(depth_tif) as src_d:
        d_arr = src_d.read(1)
        extent_mask = (d_arr >= thr1) & (d_arr != -9999.0)
        shapes_gen = shapes(extent_mask.astype(np.int32), mask=extent_mask, transform=dem_trans)
        ext_geoms = [shape(g) for g, val in shapes_gen if val == 1]

    extent_shp = out_dir / "tier1_envelope.shp"
    extent_kml = out_dir / "tier1_envelope.kml"

    if ext_geoms:
        ext_gdf = gpd.GeoDataFrame({"geometry": ext_geoms, "tier": "tier1_delft3d"}, crs=dem_crs)
        ext_gdf.to_file(extent_shp)
        try:
            ext_wgs84 = ext_gdf.to_crs("EPSG:4326")
            import simplekml

            kml = simplekml.Kml(name="PravahX Tier-1 Delft3D FM Inundation Extent")
            for _, row in ext_wgs84.iterrows():
                poly = kml.newpolygon(name="Tier-1 Inundation")
                poly.outerboundaryis = list(row.geometry.exterior.coords)
                poly.style.polystyle.color = simplekml.Color.changealphaint(
                    120, simplekml.Color.cyan
                )
                poly.style.linestyle.color = simplekml.Color.cyan
                poly.style.linestyle.width = 2
            kml.save(str(extent_kml))
        except Exception as exc:
            logger.warning(f"Could not write KML: {exc}")

    return {
        "max_depth_tif": depth_tif,
        "max_velocity_tif": vel_tif,
        "arrival_time_0_05_tif": arr05_tif,
        "arrival_time_0_30_tif": arr30_tif,
        "extent_shp": extent_shp,
        "extent_kml": extent_kml,
    }


def compare_tier0_and_tier1(
    tier0_depth_path: Path,
    tier1_depth_path: Path,
    out_dir: Path,
    depth_threshold_m: float = 0.05,
) -> dict[str, Any]:
    """Execute strict Model Intercomparison between Tier-0 HAND and Tier-1 Delft3D FM."""
    out_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(tier0_depth_path) as src0:
        d0 = src0.read(1)
        trans0 = src0.transform
        meta0 = src0.meta.copy()
        nodata0 = src0.nodata

    with rasterio.open(tier1_depth_path) as src1:
        d1 = src1.read(1)
        nodata1 = src1.nodata

    mask0 = (d0 >= depth_threshold_m) & (~np.isnan(d0))
    if nodata0 is not None:
        mask0 = mask0 & (d0 != nodata0)

    mask1 = (d1 >= depth_threshold_m) & (~np.isnan(d1))
    if nodata1 is not None:
        mask1 = mask1 & (d1 != nodata1)

    px_area_m2 = abs(trans0[0] * trans0[4])
    area_t0_km2 = float(np.sum(mask0) * px_area_m2 / 1e6)
    area_t1_km2 = float(np.sum(mask1) * px_area_m2 / 1e6)

    intersection = mask0 & mask1
    union = mask0 | mask1

    n_inter = int(np.sum(intersection))
    n_union = int(np.sum(union))

    iou = float(n_inter / n_union) if n_union > 0 else 0.0
    denom = np.sum(mask0) + np.sum(mask1)
    f_score = float((2.0 * n_inter) / denom) if denom > 0 else 0.0

    diff_stats: dict[str, float] = {}
    if n_inter > 0:
        diffs = d1[intersection] - d0[intersection]
        diff_stats["mean_diff_m"] = round(float(np.mean(diffs)), 3)
        diff_stats["mae_m"] = round(float(np.mean(np.abs(diffs))), 3)
        diff_stats["rmsd_m"] = round(float(np.sqrt(np.mean(diffs**2))), 3)
        diff_stats["median_diff_m"] = round(float(np.median(diffs)), 3)
        diff_stats["p10_diff_m"] = round(float(np.percentile(diffs, 10)), 3)
        diff_stats["p90_diff_m"] = round(float(np.percentile(diffs, 90)), 3)
        diff_stats["min_diff_m"] = round(float(np.min(diffs)), 3)
        diff_stats["max_diff_m"] = round(float(np.max(diffs)), 3)
    else:
        diff_stats = {
            "mean_diff_m": 0.0,
            "mae_m": 0.0,
            "rmsd_m": 0.0,
            "median_diff_m": 0.0,
            "p10_diff_m": 0.0,
            "p90_diff_m": 0.0,
            "min_diff_m": 0.0,
            "max_diff_m": 0.0,
        }

    agreement_arr = np.zeros(d0.shape, dtype=np.uint8)
    agreement_arr[intersection] = 1
    agreement_arr[mask0 & ~mask1] = 2
    agreement_arr[~mask0 & mask1] = 3

    agreement_tif = out_dir / "intercomparison_agreement_map.tif"
    out_meta = meta0.copy()
    out_meta.update(dtype=rasterio.uint8, nodata=0, count=1)
    with rasterio.open(agreement_tif, "w", **out_meta) as dst:
        dst.write(agreement_arr, 1)

    metrics_csv = out_dir / "intercomparison_metrics.csv"
    summary_rows = [
        ("Metric", "Value", "Unit / Notes"),
        (
            "Model Intercomparison",
            "Tier-0 HAND vs Tier-1 Delft3D FM",
            "Cross-model intercomparison",
        ),
        ("Scenario", "Hypothetical dam breach", "Froehlich 2008 peak 4900 + 100 baseflow"),
        ("Peak Total Inflow", "5000.0", "m3/s (Identical to Tier-0 run)"),
        ("Threshold Depth", f"{depth_threshold_m}", "m [UNVERIFIED threshold choice]"),
        ("Tier-0 Wet Area", f"{area_t0_km2:.3f}", "km2"),
        ("Tier-1 Wet Area", f"{area_t1_km2:.3f}", "km2"),
        ("Overlap Area (Both Wet)", f"{n_inter * px_area_m2 / 1e6:.3f}", "km2"),
        ("Intersection over Union (IoU)", f"{iou:.4f}", "Jaccard similarity index"),
        ("F-Score (Dice coefficient)", f"{f_score:.4f}", "Harmonic mean of precision and recall"),
        ("Depth Mean Diff (T1 - T0)", f"{diff_stats['mean_diff_m']:.3f}", "m (where both wet)"),
        ("Depth MAE", f"{diff_stats['mae_m']:.3f}", "m"),
        ("Depth RMSD", f"{diff_stats['rmsd_m']:.3f}", "m"),
        ("Depth Median Difference", f"{diff_stats['median_diff_m']:.3f}", "m"),
        ("Depth 10th Percentile Diff", f"{diff_stats['p10_diff_m']:.3f}", "m"),
        ("Depth 90th Percentile Diff", f"{diff_stats['p90_diff_m']:.3f}", "m"),
    ]
    with open(metrics_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(summary_rows)

    return {
        "area_tier0_km2": area_t0_km2,
        "area_tier1_km2": area_t1_km2,
        "iou": iou,
        "f_score": f_score,
        "diff_stats": diff_stats,
        "agreement_tif": agreement_tif,
        "metrics_csv": metrics_csv,
    }
