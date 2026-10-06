"""DualSPHysics 3D Smoothed Particle Hydrodynamics (SPH) engine adapter package (Phase 3)."""

from pravahx.engines.dualsphysics.adapter import DualSPHysicsAdapter
from pravahx.engines.dualsphysics.benchmark import (
    BenchmarkResult,
    DualSPHysicsBenchmark,
    run_idealized_dam_break_benchmark,
)
from pravahx.engines.dualsphysics.builder import (
    DualSPHysicsBuilder,
    SPHDomainBounds,
    SPHFluidBlock,
    SPHSimulationParams,
    build_dualsphysics_case,
)
from pravahx.engines.dualsphysics.colab import export_colab_case_package
from pravahx.engines.dualsphysics.reader import read_dualsphysics_output
from pravahx.engines.dualsphysics.runner import (
    DualSPHysicsExecutionMode,
    DualSPHysicsRunner,
)

__all__ = [
    "BenchmarkResult",
    "DualSPHysicsAdapter",
    "DualSPHysicsBenchmark",
    "DualSPHysicsBuilder",
    "DualSPHysicsExecutionMode",
    "DualSPHysicsRunner",
    "SPHDomainBounds",
    "SPHFluidBlock",
    "SPHSimulationParams",
    "build_dualsphysics_case",
    "export_colab_case_package",
    "read_dualsphysics_output",
    "run_idealized_dam_break_benchmark",
]
