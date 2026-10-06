"""Two-pass mesh and particle resolution refinement analyzer (Phase 5)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pydantic import BaseModel, Field
from rasterio.features import shapes
from shapely.geometry import shape

from pravahx.errors import ComparisonError

logger = logging.getLogger(__name__)


class RefinementZone(BaseModel):
    """Spatial zone identified for grid or particle resolution refinement in Pass 2."""

    zone_id: int
    trigger_reason: str = Field(
        ...,
        description="Reason for refinement (e.g., 'depth_gradient', 'supercritical_flow')",
    )
    recommended_resolution_m: float = Field(
        ...,
        description="Target refined cell size in metres",
    )
    refinement_factor: int = Field(
        ...,
        description="Mesh refinement multiplier (e.g. 2x, 4x)",
    )
    area_m2: float = Field(
        ...,
        description="Surface area of the refinement polygon in square metres",
    )
    geojson_geometry: dict[str, Any] = Field(..., description="GeoJSON polygon geometry")


class RefinementPlan(BaseModel):
    """Overall refinement recommendations for second-pass 2D mesh or 3D SPH particles."""

    total_refinement_zones: int
    total_refined_area_km2: float
    base_resolution_m: float
    target_resolution_m: float
    refinement_factor: int
    zones: list[RefinementZone]
    geojson_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def compute_refinement_zones(
    depth_raster_path: Path,
    velocity_raster_path: Path | None = None,
    output_geojson_path: Path | None = None,
    gradient_threshold: float = 0.15,
    froude_threshold: float = 0.9,
    base_resolution_m: float = 50.0,
    refinement_factor: int = 4,
    wet_threshold_m: float = 0.1,
) -> RefinementPlan:
    """Identify hydraulic shock, high-gradient, and supercritical zones for 2-pass mesh refinement.

    Args:
        depth_raster_path: Path to maximum water depth GeoTIFF raster.
        velocity_raster_path: Optional path to maximum velocity GeoTIFF raster.
        output_geojson_path: Optional output path to save refined polygon zones as GeoJSON.
        gradient_threshold: Depth gradient (|grad(d)|) threshold triggering refinement.
        froude_threshold: Froude number (Fr = u / sqrt(g*d)) threshold for shock flow.
        base_resolution_m: Coarse mesh resolution in metres (default: 50 m).
        refinement_factor: Refinement multiplier (default: 4x, giving 50m / 4 = 12.5m).
        wet_threshold_m: Minimum depth in metres to analyze (default: 0.1 m).

    Returns:
        RefinementPlan containing identified zones and geometric boundaries.

    Raises:
        ComparisonError: If depth raster is missing or invalid.
    """
    if not depth_raster_path.exists():
        raise ComparisonError(f"Depth raster not found: {depth_raster_path}")

    with rasterio.open(depth_raster_path) as src_d:
        depth = src_d.read(1).astype(np.float64)
        transform = src_d.transform
        crs = src_d.crs
        cell_x = abs(transform.a)
        cell_y = abs(transform.e)
        if src_d.nodata is not None:
            depth[depth == src_d.nodata] = 0.0
        depth = np.nan_to_num(depth, nan=0.0)

    # 1. Compute spatial depth gradients
    # Use numpy gradient with pixel spacing
    gy, gx = np.gradient(depth, cell_y, cell_x)
    grad_mag = np.sqrt(gx**2 + gy**2)

    # Gradient refinement trigger
    wet_mask = depth >= wet_threshold_m
    high_grad_mask = wet_mask & (grad_mag >= gradient_threshold)

    # 2. Compute Froude number if velocity raster provided
    supercritical_mask = np.zeros_like(depth, dtype=bool)
    if velocity_raster_path is not None and velocity_raster_path.exists():
        with rasterio.open(velocity_raster_path) as src_v:
            vel = src_v.read(1).astype(np.float64)
            if src_v.nodata is not None:
                vel[vel == src_v.nodata] = 0.0
            vel = np.nan_to_num(vel, nan=0.0)

        # Fr = vel / sqrt(9.80665 * depth)
        denom = np.sqrt(np.maximum(depth, 1e-3) * 9.80665)
        froude = np.zeros_like(depth)
        froude[wet_mask] = vel[wet_mask] / denom[wet_mask]
        supercritical_mask = wet_mask & (froude >= froude_threshold)

    # Combined candidate refinement mask
    combined_refine_mask = high_grad_mask | supercritical_mask

    target_res_m = round(base_resolution_m / refinement_factor, 2)
    zones: list[RefinementZone] = []

    # Vectorize refinement mask into polygons
    if np.any(combined_refine_mask):
        mask_uint8 = combined_refine_mask.astype(np.uint8)
        feature_gen = shapes(mask_uint8, mask=combined_refine_mask, transform=transform)

        zone_id = 1
        for geom, val in feature_gen:
            if val == 1:
                poly = shape(geom)
                # Filter out tiny single-pixel slivers smaller than 2 cells
                min_area = 2 * cell_x * cell_y
                if poly.area >= min_area:
                    trigger = "depth_gradient"
                    if np.any(supercritical_mask):
                        trigger = "hydraulic_jump_or_supercritical"

                    zones.append(
                        RefinementZone(
                            zone_id=zone_id,
                            trigger_reason=trigger,
                            recommended_resolution_m=target_res_m,
                            refinement_factor=refinement_factor,
                            area_m2=round(poly.area, 2),
                            geojson_geometry=geom,
                        )
                    )
                    zone_id += 1

    total_area_km2 = sum(z.area_m2 for z in zones) / 1.0e6

    # Save GeoJSON if path provided
    if output_geojson_path is not None and zones:
        output_geojson_path.parent.mkdir(parents=True, exist_ok=True)
        geojson_features = []
        for z in zones:
            geojson_features.append(
                {
                    "type": "Feature",
                    "id": z.zone_id,
                    "geometry": z.geojson_geometry,
                    "properties": {
                        "zone_id": z.zone_id,
                        "trigger_reason": z.trigger_reason,
                        "recommended_resolution_m": z.recommended_resolution_m,
                        "refinement_factor": z.refinement_factor,
                        "area_m2": z.area_m2,
                    },
                }
            )
        geojson_doc = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {"name": crs.to_string() if crs else "EPSG:4326"},
            },
            "features": geojson_features,
        }
        with open(output_geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson_doc, f, indent=2)

    return RefinementPlan(
        total_refinement_zones=len(zones),
        total_refined_area_km2=round(total_area_km2, 4),
        base_resolution_m=base_resolution_m,
        target_resolution_m=target_res_m,
        refinement_factor=refinement_factor,
        zones=zones,
        geojson_path=output_geojson_path if zones else None,
        metadata={
            "gradient_threshold": gradient_threshold,
            "froude_threshold": froude_threshold,
            "depth_raster": str(depth_raster_path.name),
        },
    )
