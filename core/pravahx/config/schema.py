"""Scenario configuration schema.

Pydantic models that validate the scenario YAML (Section 6 of the build spec).
Every field has a description. Validation produces clear, actionable error messages.

Note: secure_mode is a system-level setting (env var PRAVAHX_SECURE_MODE), not
part of the scenario config. See docs/DECISIONS.md #D001.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# ── Enums ────────────────────────────────────────────────────────────────────


class ScenarioType(StrEnum):
    """Allowed scenario types (Section 1.2)."""

    DAM_BREAK = "dam_break"
    RELEASE = "release"
    BLOCKAGE = "blockage"
    LAKE_OUTBURST = "lake_outburst"
    LIVE_EVENT = "live_event"


class FailureMode(StrEnum):
    """Dam-break failure mechanism."""

    OVERTOPPING = "overtopping"
    PIPING = "piping"


class VolumeMethod(StrEnum):
    """How to determine reservoir volume."""

    REGISTER = "register"
    SATELLITE = "satellite"
    USER = "user"
    AUTO = "auto"


class BreachMethod(StrEnum):
    """Breach parameter method."""

    FROEHLICH_2008 = "froehlich_2008"
    LANDSLIDE = "landslide"
    USER = "user"
    AUTO = "auto"


class EnsembleQuantile(StrEnum):
    """Ensemble quantile labels."""

    P10 = "p10"
    P50 = "p50"
    P90 = "p90"


class DEMSource(StrEnum):
    """Built-in DEM sources."""

    COPERNICUS_GLO30 = "copernicus_glo30"
    SRTM = "srtm"
    ASTER = "aster"


class LandcoverSource(StrEnum):
    """Built-in land cover sources."""

    WORLDCOVER = "worldcover"


class ExportFormat(StrEnum):
    """Supported export formats."""

    SHP = "shp"
    KML = "kml"
    COG = "cog"
    NETCDF = "netcdf"
    GEOJSON = "geojson"
    CSV = "csv"
    PDF = "pdf"


class DualSPHysicsMode(StrEnum):
    """SPH adapter execution mode (constraint A)."""

    CPU = "cpu"
    REMOTE_GPU = "remote_gpu"
    PRECOMPUTED = "precomputed"


# ── Sub-models ───────────────────────────────────────────────────────────────


class SourceConfig(BaseModel):
    """Where the water comes from."""

    model_config = ConfigDict(extra="forbid")

    dam_id: str | None = Field(
        default=None,
        description="Dam register ID. Mutually exclusive with point/polygon.",
    )
    point: tuple[float, float] | None = Field(
        default=None,
        description="(longitude, latitude) of the dam or blockage.",
    )
    polygon: Path | None = Field(
        default=None,
        description="Path to a GeoJSON polygon for a lake or blockage.",
    )
    dam_height_m: float | None = Field(
        default=None, gt=0, description="Optional override: dam height in metres."
    )
    storage_m3: float | None = Field(
        default=None, gt=0, description="Optional override: reservoir storage in m³."
    )
    volume_method: VolumeMethod = Field(
        default=VolumeMethod.AUTO,
        description="How to determine reservoir volume.",
    )

    @model_validator(mode="after")
    def _at_least_one_location(self) -> SourceConfig:
        if self.dam_id is None and self.point is None and self.polygon is None:
            msg = "At least one of 'dam_id', 'point' or 'polygon' must be set."
            raise ValueError(msg)
        return self


class DomainConfig(BaseModel):
    """Spatial extent of the simulation."""

    model_config = ConfigDict(extra="forbid")

    reach_length_km: Annotated[float, Field(gt=0, le=500)] = Field(
        default=60,
        description="Length of the river reach downstream of the source, in km.",
    )
    buffer_km: Annotated[float, Field(gt=0, le=50)] = Field(
        default=5,
        description="Buffer width on each side of the reach, in km.",
    )
    crs: str = Field(
        default="auto",
        description="CRS as EPSG code or 'auto' for local UTM.",
    )


class InputsConfig(BaseModel):
    """Data sources for the scenario."""

    model_config = ConfigDict(extra="forbid")

    dem: DEMSource | str = Field(
        default=DEMSource.COPERNICUS_GLO30,
        description="DEM source. Built-in name or 'user:<path>'.",
    )
    landcover: LandcoverSource | str = Field(
        default=LandcoverSource.WORLDCOVER,
        description="Land cover source.",
    )
    inflow_hydrograph: Path | None = Field(
        default=None,
        description="Optional user-supplied inflow hydrograph file.",
    )
    downstream_stage: Path | None = Field(
        default=None,
        description="Optional downstream boundary condition file.",
    )


class BreachConfig(BaseModel):
    """Breach parameter settings."""

    model_config = ConfigDict(extra="forbid")

    method: BreachMethod = Field(
        default=BreachMethod.AUTO,
        description="Breach parameter method.",
    )
    ensemble: list[EnsembleQuantile] = Field(
        default=[EnsembleQuantile.P10, EnsembleQuantile.P50, EnsembleQuantile.P90],
        description="Ensemble quantiles to compute.",
    )
    width_uncertainty_factor: float = Field(
        ...,
        description=(
            "Uncertainty factor for breach width (e.g. standard error in log space). No default."
        ),
    )
    time_uncertainty_factor: float = Field(
        ...,
        description=(
            "Uncertainty factor for breach formation time "
            "(e.g. standard error in log space). No default."
        ),
    )
    user_hydrograph: Path | None = Field(
        default=None,
        description="User-supplied breach hydrograph (overrides computed).",
    )


class Tier0Config(BaseModel):
    """HAND-based rapid envelope settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class Delft3DFMConfig(BaseModel):
    """Delft3D Flexible Mesh engine settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    cell_size_m: dict[str, float] = Field(
        default={"coarse": 100.0, "fine": 30.0},
        description="Mesh cell sizes in metres: 'coarse' for floodplain, 'fine' for channel.",
    )
    horizon_h: Annotated[float, Field(gt=0, le=168)] = Field(
        default=12.0,
        description="Simulation horizon in hours.",
    )

    @field_validator("cell_size_m")
    @classmethod
    def _validate_cell_sizes(cls, v: dict[str, float]) -> dict[str, float]:
        for key in ("coarse", "fine"):
            if key not in v:
                msg = f"cell_size_m must contain '{key}'."
                raise ValueError(msg)
            if v[key] <= 0:
                msg = f"cell_size_m['{key}'] must be positive."
                raise ValueError(msg)
        if v["fine"] >= v["coarse"]:
            msg = "cell_size_m['fine'] must be smaller than cell_size_m['coarse']."
            raise ValueError(msg)
        return v


class DualSPHysicsConfig(BaseModel):
    """DualSPHysics engine settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    particle_spacing_m: Annotated[float, Field(gt=0)] = Field(
        default=2.0,
        description="Inter-particle distance in metres.",
    )
    near_field_km: Annotated[float, Field(gt=0, le=20)] = Field(
        default=2.0,
        description="Near-field domain extent downstream of the dam, in km.",
    )
    mode: DualSPHysicsMode = Field(
        default=DualSPHysicsMode.CPU,
        description="Execution mode: cpu, remote_gpu, or precomputed.",
    )
    precomputed_dir: Path | None = Field(
        default=None,
        description="Directory with precomputed results (when mode=precomputed).",
    )
    precomputed_run_date: str | None = Field(
        default=None,
        description="ISO date when precomputed results were generated.",
    )

    @model_validator(mode="after")
    def _precomputed_needs_dir(self) -> DualSPHysicsConfig:
        if self.mode == DualSPHysicsMode.PRECOMPUTED and self.precomputed_dir is None:
            msg = "precomputed_dir is required when mode is 'precomputed'."
            raise ValueError(msg)
        return self


class TiersConfig(BaseModel):
    """Engine tier settings."""

    model_config = ConfigDict(extra="forbid")

    tier0: Tier0Config = Field(default_factory=Tier0Config)
    delft3d_fm: Delft3DFMConfig = Field(default_factory=Delft3DFMConfig)
    dualsphysics: DualSPHysicsConfig = Field(default_factory=DualSPHysicsConfig)


class CompareConfig(BaseModel):
    """Engine comparison settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    max_refinements: Annotated[int, Field(ge=0, le=2)] = Field(
        default=2,
        description="Maximum mesh/particle refinement iterations.",
    )


class CascadeConfig(BaseModel):
    """Cascade analysis settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class GEEConfig(BaseModel):
    """Google Earth Engine settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    event_dates: dict[str, list[str | None]] | None = Field(
        default=None,
        description="Before and after ranges: {'before': [start, end], 'after': [start, end]}.",
    )


class ImpactConfig(BaseModel):
    """Impact analysis settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class ScenarioHeader(BaseModel):
    """Top-level scenario identification."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
        description="Unique scenario identifier (alphanumeric, hyphens, underscores).",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Human-readable scenario name.",
    )
    type: ScenarioType = Field(
        ...,
        description="Scenario type.",
    )
    failure_mode: FailureMode | None = Field(
        default=None,
        description="Failure mechanism (required for dam_break type only).",
    )

    @model_validator(mode="after")
    def _dam_break_needs_failure_mode(self) -> ScenarioHeader:
        if self.type == ScenarioType.DAM_BREAK and self.failure_mode is None:
            msg = "failure_mode is required when type is 'dam_break'."
            raise ValueError(msg)
        if self.type != ScenarioType.DAM_BREAK and self.failure_mode is not None:
            msg = "failure_mode is only valid when type is 'dam_break'."
            raise ValueError(msg)
        return self


# ── Root config ──────────────────────────────────────────────────────────────


class ScenarioConfig(BaseModel):
    """Complete scenario configuration (Section 6 of the build spec).

    Drives every tier. Loaded from YAML, validated with clear errors.
    secure_mode is NOT included here — it is a system-level env var.
    See docs/DECISIONS.md #D001.
    """

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioHeader
    source: SourceConfig
    domain: DomainConfig = Field(default_factory=DomainConfig)
    inputs: InputsConfig = Field(default_factory=InputsConfig)
    breach: BreachConfig = Field(...)
    tiers: TiersConfig = Field(default_factory=TiersConfig)
    compare: CompareConfig = Field(default_factory=CompareConfig)
    cascade: CascadeConfig = Field(default_factory=CascadeConfig)
    gee: GEEConfig = Field(default_factory=GEEConfig)
    impact: ImpactConfig = Field(default_factory=ImpactConfig)
    exports: list[ExportFormat] = Field(
        default=[ExportFormat.SHP, ExportFormat.KML, ExportFormat.COG, ExportFormat.PDF],
        description="Export formats to produce.",
    )


def load_scenario_config(path: Path) -> ScenarioConfig:
    """Load and validate a scenario config from a YAML file.

    Raises ``pydantic.ValidationError`` with clear, actionable messages
    if the config is invalid.
    """
    import yaml
    from yaml.error import YAMLError

    text = path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(text)
    except YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}") from e
    if not isinstance(raw, dict):
        msg = f"Expected a YAML mapping at the top level, got {type(raw).__name__}."
        raise ValueError(msg)
    return ScenarioConfig.model_validate(raw)
