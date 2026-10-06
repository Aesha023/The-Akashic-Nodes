"""Delft3D Flexible Mesh model case builder (HYDROLIB-core)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from hydrolib.core.dflowfm.bc.models import (
    ForcingModel,
    QuantityUnitPair,
    TimeInterpolation,
    TimeSeries,
)
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel
from hydrolib.core.dflowfm.mdu.models import FMModel
from hydrolib.core.dflowfm.polyfile.models import Metadata, Point, PolyFile, PolyObject

from pravahx.engines.base import PreparedCase, compute_file_hash

if TYPE_CHECKING:
    from pravahx.engines.base import RunContext

logger = logging.getLogger(__name__)


def build_delft3d_case(context: RunContext) -> PreparedCase:
    """Prepare a Delft3D FM simulation case using HYDROLIB-core.

    Generates the master definition file (.mdu), external forcings (.ext),
    inflow boundary time series (.bc / .tim), and polyline boundaries (.pli).

    Args:
        context: RunContext containing scenario config, work dir, terrain dir, and hydrograph.

    Returns:
        PreparedCase with all input files generated and hashed.
    """
    case_dir = context.work_dir / "delft3d_fm"
    case_dir.mkdir(parents=True, exist_ok=True)

    mdu_path = case_dir / "flow2d3d.mdu"
    ext_path = case_dir / "boundary_conditions.ext"
    bc_path = case_dir / "hydrograph.bc"
    pli_path = case_dir / "inflow_boundary.pli"

    # 1. Build Inflow Polyline Boundary (.pli)
    # Upstream boundary coordinates from scenario source location or fallback default
    if (
        context.config
        and hasattr(context.config, "source")
        and context.config.source
        and context.config.source.point
    ):
        lon, lat = context.config.source.point
        pt1 = Point(x=float(lon), y=float(lat), data=[])
        pt2 = Point(x=float(lon + 0.001), y=float(lat), data=[])
    else:
        pt1 = Point(x=78.3, y=30.1, data=[])
        pt2 = Point(x=78.301, y=30.1, data=[])
    meta = Metadata(name="inflow_bnd", n_rows=2, n_columns=2)
    poly_obj = PolyObject(metadata=meta, points=[pt1, pt2])
    poly_file = PolyFile(objects=[poly_obj])
    poly_file.save(filepath=pli_path)

    # 2. Build Inflow Boundary Hydrograph Time Series (.bc)
    # Read points from breach hydrograph if present
    time_series_data: list[list[float]] = []
    if context.breach_hydrograph_path and context.breach_hydrograph_path.exists():
        import csv

        with open(context.breach_hydrograph_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Time in minutes/seconds for Delft3D FM
                t_sec = float(row.get("time_hr", 0.0)) * 3600.0
                q_val = float(row.get("discharge_m3s", 0.0))
                time_series_data.append([t_sec, q_val])
    else:
        # Fallback default hydrograph
        time_series_data = [
            [0.0, 0.0],
            [3600.0, 5000.0],
            [7200.0, 2000.0],
            [14400.0, 0.0],
        ]

    ts_quantity = [
        QuantityUnitPair(quantity="time", unit="seconds since 2026-01-01 00:00:00"),
        QuantityUnitPair(quantity="dischargebnd", unit="m3/s"),
    ]
    ts_forcing = TimeSeries(
        name="inflow_bnd",
        timeinterpolation=TimeInterpolation.linear,
        quantityunitpair=ts_quantity,
        datablock=time_series_data,
    )
    forcing_model = ForcingModel(forcing=[ts_forcing])
    forcing_model.save(filepath=bc_path)

    # 3. Build External Forcing (.ext)
    bnd = Boundary(
        quantity="dischargebnd",
        locationfile=pli_path,
        forcingfile=bc_path,
    )
    ext_model = ExtModel(boundary=[bnd])
    ext_model.save(filepath=ext_path)

    # 4. Master Definition File (.mdu)
    fm_model = FMModel()
    fm_model.time.refdate = 20260101
    fm_model.time.tstart = 0.0
    fm_model.time.tstop = 14400.0  # 4 hours
    fm_model.time.dtmax = 30.0
    fm_model.time.dtuser = 10.0

    fm_model.external_forcing.extforcefilenew = ext_path
    fm_model.output.mapinterval = [600.0]  # 10 minute map output
    fm_model.output.hisinterval = [60.0]

    has_domain = context.config and hasattr(context.config, "domain") and context.config.domain
    crs_str = (
        context.config.domain.crs
        if has_domain and context.config.domain.crs != "auto"
        else "EPSG:32644"
    )

    fm_model.save(filepath=mdu_path)

    # 5. Compute File Hashes for Provenance
    input_hashes = {
        mdu_path.name: compute_file_hash(mdu_path),
        ext_path.name: compute_file_hash(ext_path),
        bc_path.name: compute_file_hash(bc_path),
        pli_path.name: compute_file_hash(pli_path),
    }

    logger.info(f"Delft3D FM case prepared successfully in: {case_dir}")
    return PreparedCase(
        engine_name="delft3d_fm",
        case_dir=case_dir,
        input_file_hashes=input_hashes,
        metadata={"mdu_file": mdu_path.name, "crs": crs_str},
    )
