"""DualSPHysics XML case definition builder (Phase 3).

Generates GenCase XML input files for DualSPHysics (v5.0/v5.2) simulations,
supporting standard idealized dam break benchmarks and 3D near-field terrain cases.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pravahx.engines.base import PreparedCase, RunContext, compute_file_hash

if TYPE_CHECKING:
    from pathlib import Path

    from pravahx.config.schema import ScenarioConfig


@dataclass(frozen=True)
class SPHDomainBounds:
    """Bounding box for SPH computational domain in metres."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float


@dataclass(frozen=True)
class SPHFluidBlock:
    """Fluid block geometry definition."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float


@dataclass(frozen=True)
class SPHSimulationParams:
    """Numerical parameters for DualSPHysics solver."""

    dp_m: float = 0.02
    time_max_s: float = 2.0
    time_out_s: float = 0.05
    gravity_m_s2: float = 9.81
    rho0_kg_m3: float = 1000.0
    gamma: float = 7.0
    c_sound_m_s: float | None = None
    cfl_number: float = 0.2
    kernel: int = 2  # 2: Wendland
    visco_treatment: int = 1  # 1: Artificial viscosity
    visco_alpha: float = 0.01
    delta_sph: float = 0.1  # Delta-SPH density diffusion coefficient
    step_algorithm: int = 2  # 2: Symplectic position Verlet


class DualSPHysicsBuilder:
    """Builds DualSPHysics XML definitions and geometry cases."""

    def __init__(self, params: SPHSimulationParams | None = None) -> None:
        self.params = params or SPHSimulationParams()

    def build_dam_break_case(
        self,
        domain: SPHDomainBounds,
        fluid: SPHFluidBlock,
        output_dir: Path,
        case_name: str = "CaseDamBreak",
        gauges: list[tuple[float, float, float]] | None = None,
        downstream_flux_x: float | None = None,
    ) -> Path:
        """Generate XML case definition for an idealized or near-field dam break.

        Args:
            domain: Overall computational domain bounds.
            fluid: Initial reservoir fluid block bounds.
            output_dir: Target directory to write XML and case files.
            case_name: Base name for the case.
            gauges: Optional list of (x, y, z) gauge sensor coordinates.
            downstream_flux_x: Optional X-coordinate of downstream flux handoff plane.

        Returns:
            Path to the created XML case definition file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        xml_path = output_dir / f"{case_name}_Def.xml"

        h_max = max(1.0, fluid.z_max - fluid.z_min)
        c_sound = self.params.c_sound_m_s or (10.0 * math.sqrt(self.params.gravity_m_s2 * h_max))

        root = ET.Element("case")

        # 1. Case Definition (Geometry and Particles) conforming to DualSPHysics 5.4 format
        casedef = ET.SubElement(root, "casedef")

        constantsdef = ET.SubElement(casedef, "constantsdef")
        ET.SubElement(
            constantsdef,
            "gravity",
            x="0",
            y="0",
            z=f"{-abs(self.params.gravity_m_s2):.4f}",
            comment="Gravitational acceleration",
            units_comment="m/s^2",
        )
        ET.SubElement(
            constantsdef,
            "rhop0",
            value=f"{self.params.rho0_kg_m3:.1f}",
            comment="Reference density of the fluid",
            units_comment="kg/m^3",
        )
        ET.SubElement(
            constantsdef,
            "rhopgradient",
            value="2",
            comment="Initial density gradient 1:Rhop0, 2:Water column, 3:Max. water height",
        )
        ET.SubElement(
            constantsdef,
            "hswl",
            value="0",
            auto="true",
            comment="Maximum still water level to calculate speedofsound",
            units_comment="metres (m)",
        )
        ET.SubElement(
            constantsdef,
            "gamma",
            value=f"{self.params.gamma:.1f}",
            comment="Polytropic constant for water used in the state equation",
        )
        ET.SubElement(
            constantsdef,
            "speedsystem",
            value="0",
            auto="true",
            comment="Maximum system speed",
        )
        ET.SubElement(
            constantsdef,
            "coefsound",
            value="20",
            comment="Coefficient to multiply speedsystem",
        )
        ET.SubElement(
            constantsdef,
            "speedsound",
            value=f"{c_sound:.2f}",
            auto="true",
            comment="Speed of sound to use in the simulation",
        )
        ET.SubElement(
            constantsdef,
            "coefh",
            value="1.0",
            comment="Coefficient to calculate the smoothing length",
        )
        ET.SubElement(
            constantsdef,
            "_hdp",
            value="2",
            comment="Alternative option to calculate the smoothing length",
        )
        ET.SubElement(
            constantsdef,
            "cflnumber",
            value=f"{self.params.cfl_number:.2f}",
            comment="Coefficient to multiply dt",
        )

        # MK configuration
        ET.SubElement(casedef, "mkconfig", boundcount="240", fluidcount="9")

        # Geometry
        geometry = ET.SubElement(casedef, "geometry")
        pad = max(0.05, self.params.dp_m * 2.0)
        definition = ET.SubElement(
            geometry,
            "definition",
            dp=f"{self.params.dp_m:.4f}",
            units_comment="metres (m)",
        )
        ET.SubElement(
            definition,
            "pointmin",
            x=f"{domain.x_min - pad:.4f}",
            y=f"{domain.y_min - pad:.4f}",
            z=f"{domain.z_min - pad:.4f}",
        )
        ET.SubElement(
            definition,
            "pointmax",
            x=f"{domain.x_max + pad:.4f}",
            y=f"{domain.y_max + pad:.4f}",
            z=f"{domain.z_max + pad:.4f}",
        )

        commands = ET.SubElement(geometry, "commands")
        mainlist = ET.SubElement(commands, "mainlist")

        shapemode = ET.SubElement(mainlist, "setshapemode")
        shapemode.text = "dp | bound"
        ET.SubElement(mainlist, "setdrawmode", mode="full")

        # Fluid Reservoir: mkfluid=0
        ET.SubElement(mainlist, "setmkfluid", mk="0")
        draw_box_fluid = ET.SubElement(mainlist, "drawbox")
        boxfill_fluid = ET.SubElement(draw_box_fluid, "boxfill")
        boxfill_fluid.text = "solid"
        ET.SubElement(
            draw_box_fluid,
            "point",
            x=f"{fluid.x_min:.4f}",
            y=f"{fluid.y_min:.4f}",
            z=f"{fluid.z_min:.4f}",
        )
        ET.SubElement(
            draw_box_fluid,
            "size",
            x=f"{fluid.x_max - fluid.x_min:.4f}",
            y=f"{fluid.y_max - fluid.y_min:.4f}",
            z=f"{fluid.z_max - fluid.z_min:.4f}",
        )

        # Boundary Tank: mkbound=0
        ET.SubElement(mainlist, "setmkbound", mk="0")
        draw_box_bound = ET.SubElement(mainlist, "drawbox")
        boxfill_bound = ET.SubElement(draw_box_bound, "boxfill")
        boxfill_bound.text = "bottom | left | right | front | back"
        ET.SubElement(
            draw_box_bound,
            "point",
            x=f"{domain.x_min:.4f}",
            y=f"{domain.y_min:.4f}",
            z=f"{domain.z_min:.4f}",
        )
        ET.SubElement(
            draw_box_bound,
            "size",
            x=f"{domain.x_max - domain.x_min:.4f}",
            y=f"{domain.y_max - domain.y_min:.4f}",
            z=f"{domain.z_max - domain.z_min:.4f}",
        )
        ET.SubElement(mainlist, "shapeout", file="Box")

        # 2. Solver Execution Parameters (DualSPHysics 5.4 official format)
        execution = ET.SubElement(root, "execution")
        parameters = ET.SubElement(execution, "parameters")

        ET.SubElement(
            parameters,
            "parameter",
            key="SavePosDouble",
            value="0",
            comment="Saves particle position using double precision (default=0)",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="StepAlgorithm",
            value=f"{self.params.step_algorithm}",
            comment="Step Algorithm 1:Verlet, 2:Symplectic",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="VerletSteps",
            value="40",
            comment="Verlet only: Number of steps to apply Euler timestepping",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="Kernel",
            value=f"{self.params.kernel}",
            comment="Interaction Kernel 1:Cubic Spline, 2:Wendland",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="ViscoTreatment",
            value=f"{self.params.visco_treatment}",
            comment="Viscosity formulation 1:Artificial, 2:Laminar+SPS, 3:Laminar",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="Visco",
            value=f"{self.params.visco_alpha:.4f}",
            comment="Viscosity value",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="ViscoBoundFactor",
            value="1",
            comment="Multiply viscosity value with boundary",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DensityDT",
            value="2",
            comment="Density Diffusion Term 0:None, 1:Molteni, 2:Fourtakas, 3:Fourtakas(full)",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DensityDTvalue",
            value=f"{self.params.delta_sph:.4f}",
            comment="DDT value",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="Shifting",
            value="0",
            comment="Shifting mode 0:None, 1:Ignore bound, 2:Ignore fixed, 3:Full",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="ShiftCoef",
            value="-2",
            comment="Coefficient for shifting computation",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="ShiftTFS",
            value="0",
            comment="Threshold to detect free surface",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="RigidAlgorithm",
            value="1",
            comment="Rigid Algorithm 0:collision-free, 1:SPH, 2:DEM, 3:Chrono",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="FtPause",
            value="0.0",
            comment="Time to freeze the floatings at simulation start",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="CoefDtMin",
            value="0.05",
            comment="Coefficient to calculate minimum time step",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DtIni",
            value="0",
            comment="Initial time step",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DtMin",
            value="0",
            comment="Minimum time step",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DtFixed",
            value="0",
            comment="Fixed Dt value",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DtFixedFile",
            value="NONE",
            comment="Dt values are loaded from file",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="DtAllParticles",
            value="0",
            comment="Velocity of particles used to calculate DT",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="TimeMax",
            value=f"{self.params.time_max_s:.4f}",
            comment="Time of simulation",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="TimeOut",
            value=f"{self.params.time_out_s:.4f}",
            comment="Time out data",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="MinFluidStop",
            value="0.1",
            comment="%/100 of fluid particles allowed to be excluded",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="RhopOutMin",
            value="700",
            comment="Minimum rhop valid",
        )
        ET.SubElement(
            parameters,
            "parameter",
            key="RhopOutMax",
            value="1300",
            comment="Maximum rhop valid",
        )

        sim_domain = ET.SubElement(
            parameters,
            "simulationdomain",
            comment="Defines domain of simulation",
        )
        ET.SubElement(sim_domain, "posmin", x="default", y="default", z="default")
        ET.SubElement(sim_domain, "posmax", x="default", y="default", z="default + 100%")

        # Postprocessing gauges metadata
        if gauges:
            postproc = ET.SubElement(root, "postprocessing")
            gauge_elem = ET.SubElement(postproc, "gauges")
            for idx, (gx, gy, gz) in enumerate(gauges):
                ET.SubElement(
                    gauge_elem,
                    "gauge",
                    id=f"G{idx + 1}",
                    x=f"{gx:.4f}",
                    y=f"{gy:.4f}",
                    z=f"{gz:.4f}",
                )

        # Downstream flux handoff plane
        if downstream_flux_x is not None:
            flux_elem = ET.SubElement(root, "flux_plane")
            flux_elem.set("x_coord", f"{downstream_flux_x:.4f}")
            flux_elem.set("y_min", f"{domain.y_min:.4f}")
            flux_elem.set("y_max", f"{domain.y_max:.4f}")

        # Write formatted XML with LF line endings
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        with open(xml_path, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)

        return xml_path


def build_dualsphysics_case(context: RunContext) -> PreparedCase:
    """Build DualSPHysics input files from RunContext.

    Args:
        context: Scenario run context containing configuration and terrain.

    Returns:
        PreparedCase containing case directory and input hashes.
    """
    case_dir = context.work_dir / "dualsphysics_case"
    case_dir.mkdir(parents=True, exist_ok=True)

    config: ScenarioConfig = context.config
    sph_cfg = config.tiers.dualsphysics

    dp = sph_cfg.particle_spacing_m
    near_field_km = sph_cfg.near_field_km
    near_field_m = near_field_km * 1000.0

    # Determine reservoir height and volume from scenario
    dam_height = config.source.dam_height_m or 20.0
    storage_m3 = config.source.storage_m3 or 100_000.0

    # Derive rectangular reservoir equivalent length & width
    # Tank width across valley ~ 5 * dam_height
    reservoir_width = max(20.0, 5.0 * dam_height)
    reservoir_length = max(20.0, storage_m3 / (dam_height * reservoir_width))

    domain = SPHDomainBounds(
        x_min=0.0,
        x_max=reservoir_length + near_field_m,
        y_min=0.0,
        y_max=reservoir_width,
        z_min=0.0,
        z_max=dam_height * 2.5,
    )

    fluid = SPHFluidBlock(
        x_min=0.0,
        x_max=reservoir_length,
        y_min=0.0,
        y_max=reservoir_width,
        z_min=0.0,
        z_max=dam_height,
    )

    sim_params = SPHSimulationParams(
        dp_m=dp,
        time_max_s=min(120.0, max(10.0, near_field_m / 10.0)),
        time_out_s=max(0.05, min(1.0, dp * 2.0)),
    )

    builder = DualSPHysicsBuilder(sim_params)
    downstream_x = domain.x_max - 5.0 * dp

    xml_path = builder.build_dam_break_case(
        domain=domain,
        fluid=fluid,
        output_dir=case_dir,
        case_name=f"Case_{config.scenario.id}",
        gauges=[(reservoir_length + 10.0, reservoir_width / 2.0, 0.0)],
        downstream_flux_x=downstream_x,
    )

    input_hashes: dict[str, str] = {
        str(xml_path.name): compute_file_hash(xml_path),
    }

    metadata: dict[str, Any] = {
        "case_xml": str(xml_path.name),
        "dp_m": dp,
        "near_field_m": near_field_m,
        "mode": sph_cfg.mode.value,
        "domain": {
            "x_min": domain.x_min,
            "x_max": domain.x_max,
            "y_min": domain.y_min,
            "y_max": domain.y_max,
            "z_min": domain.z_min,
            "z_max": domain.z_max,
        },
        "fluid": {
            "x_min": fluid.x_min,
            "x_max": fluid.x_max,
            "y_min": fluid.y_min,
            "y_max": fluid.y_max,
            "z_min": fluid.z_min,
            "z_max": fluid.z_max,
        },
    }

    return PreparedCase(
        engine_name="dualsphysics",
        case_dir=case_dir,
        input_file_hashes=input_hashes,
        metadata=metadata,
    )
