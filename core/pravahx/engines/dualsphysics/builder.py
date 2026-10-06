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

        # 1. Case Definition (Geometry and Particles)
        casedef = ET.SubElement(root, "casedef")

        constantsdef = ET.SubElement(casedef, "constantsdef")
        ET.SubElement(
            constantsdef,
            "gravity",
            x="0",
            y="0",
            z=f"{-abs(self.params.gravity_m_s2):.4f}",
        )
        ET.SubElement(constantsdef, "rhop0", value=f"{self.params.rho0_kg_m3:.1f}")
        ET.SubElement(constantsdef, "gamma", value=f"{self.params.gamma:.1f}")
        ET.SubElement(constantsdef, "speedsound", value=f"{c_sound:.2f}")

        # MK configuration
        mkconfig = ET.SubElement(casedef, "mkconfig", boundcount="240", fluidcount="9")
        mkfluid = ET.SubElement(mkconfig, "mkfluid", mk="0")
        ET.SubElement(mkfluid, "rhop", value=f"{self.params.rho0_kg_m3:.1f}")

        # Geometry
        geometry = ET.SubElement(casedef, "geometry")
        definition = ET.SubElement(
            geometry,
            "definition",
            dp=f"{self.params.dp_m:.4f}",
            units_comment="metres",
        )
        ET.SubElement(
            definition,
            "pointmin",
            x=f"{domain.x_min:.4f}",
            y=f"{domain.y_min:.4f}",
            z=f"{domain.z_min:.4f}",
        )
        ET.SubElement(
            definition,
            "pointmax",
            x=f"{domain.x_max:.4f}",
            y=f"{domain.y_max:.4f}",
            z=f"{domain.z_max:.4f}",
        )

        commands = ET.SubElement(geometry, "commands")
        mainlist = ET.SubElement(commands, "mainlist")

        # Boundary Tank: mkbound=0
        set_bound = ET.SubElement(mainlist, "setshapemk", mk="0")
        ET.SubElement(set_bound, "setdrawmode", mode="full")

        # Draw tank bottom and walls
        draw_box_bound = ET.SubElement(mainlist, "drawbox")
        ET.SubElement(
            draw_box_bound,
            "boxfill",
            bottom="true",
            left="true",
            right="true",
            front="true",
            back="true",
            top="false",
        )
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

        # Fluid Reservoir: mkfluid=0
        set_fluid = ET.SubElement(mainlist, "setshapemk", mk="0")
        ET.SubElement(set_fluid, "setdrawmode", mode="full")
        draw_box_fluid = ET.SubElement(mainlist, "drawbox")
        ET.SubElement(draw_box_fluid, "boxfill", solid="true")
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

        # 2. Solver Execution Parameters
        execution = ET.SubElement(root, "execution")
        parameters = ET.SubElement(execution, "parameters")

        ET.SubElement(parameters, "parameter", key="PosDouble", value="1")
        ET.SubElement(
            parameters, "parameter", key="StepAlgorithm", value=f"{self.params.step_algorithm}"
        )
        ET.SubElement(parameters, "parameter", key="VerletSteps", value="40")
        ET.SubElement(parameters, "parameter", key="Kernel", value=f"{self.params.kernel}")
        ET.SubElement(
            parameters, "parameter", key="ViscoTreatment", value=f"{self.params.visco_treatment}"
        )
        ET.SubElement(parameters, "parameter", key="Visco", value=f"{self.params.visco_alpha:.4f}")
        ET.SubElement(parameters, "parameter", key="ViscoBoundFactor", value="1")
        ET.SubElement(parameters, "parameter", key="DeltaSPH", value=f"{self.params.delta_sph:.4f}")
        ET.SubElement(parameters, "parameter", key="Shifting", value="0")
        ET.SubElement(parameters, "parameter", key="RigidAlgorithm", value="1")
        ET.SubElement(parameters, "parameter", key="FtPause", value="0.0")
        ET.SubElement(parameters, "parameter", key="TimeMax", value=f"{self.params.time_max_s:.4f}")
        ET.SubElement(parameters, "parameter", key="TimeOut", value=f"{self.params.time_out_s:.4f}")
        ET.SubElement(parameters, "parameter", key="IncZ", value="0.5")
        ET.SubElement(parameters, "parameter", key="PartsOutMax", value="1.0")
        ET.SubElement(parameters, "parameter", key="RhopOutMin", value="700")
        ET.SubElement(parameters, "parameter", key="RhopOutMax", value="1300")
        ET.SubElement(
            parameters, "parameter", key="CFLnumber", value=f"{self.params.cfl_number:.2f}"
        )

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

        # Write formatted XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

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
        z_max=dam_height * 1.5,
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
