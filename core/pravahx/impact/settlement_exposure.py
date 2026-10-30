"""Real settlement exposure from OSM features, Tier-0 depth, and WorldPop rasters."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask


def compute_settlement_exposure(
    osm_path: str | Path = "data/ganga_inputs/osm_aoi.osm",
    depth_raster_path: str | Path = "data/ganga_inputs/tier0_max_depth.tif",
    worldpop_raster_path: str | Path = "data/ganga_inputs/worldpop_ganga_32644.tif",
    buffer_radius_m: float = 500.0,
) -> dict[str, Any]:
    """Compute empirical settlement flood exposure using spatial raster overlays.

    Methodology:
        1. Extract OSM place features inside AOI with place in
           {city, town, village, hamlet, suburb, neighbourhood}.
        2. Area per settlement: OSM polygon if present (from multipolygons layer),
           else a buffer around the node (radius configurable, default 500m).
        3. All geometries reprojected to EPSG:32644 (UTM 44N matching hydrodynamic raster).
        4. Calculate exposed population by summing WorldPop 2020 cells intersecting both
           the settlement area and wet cells (depth > 0) of the Tier-0 depth raster.
        5. Extract peak flood depth as the maximum water depth within wet cells in that area.
        6. Assign standardized depth classes from PravahX design system:
           '0.0 - 0.5m', '0.5 - 1.5m', '1.5 - 3.0m', '3.0 - 5.0m', '5.0 - 8.0m', '> 8.0m',
           or 'Dry / Uninundated'.
        7. Real OSM IDs formatted as node/..., way/..., relation/...
        8. Settlement figures overlap and are not additive.

    Returns:
        Structured exposure dictionary with metadata and settlement records.
    """
    osm_path = Path(osm_path)
    depth_raster_path = Path(depth_raster_path)
    worldpop_raster_path = Path(worldpop_raster_path)

    if not osm_path.exists():
        raise FileNotFoundError(f"OSM file not found: {osm_path}")
    if not depth_raster_path.exists():
        raise FileNotFoundError(f"Depth raster not found: {depth_raster_path}")
    if not worldpop_raster_path.exists():
        raise FileNotFoundError(f"WorldPop raster not found: {worldpop_raster_path}")

    place_types = {"city", "town", "village", "hamlet", "suburb", "neighbourhood"}

    # Collect candidate settlement features (polygons first, then points)
    candidate_features: list[dict[str, Any]] = []

    # 1. Check OSM multipolygons layer for place polygons
    try:
        polys = gpd.read_file(str(osm_path), layer="multipolygons")
        if "place" in polys.columns:
            place_polys = polys[polys["place"].isin(place_types)].copy()
            if not place_polys.empty:
                place_polys = place_polys.to_crs("EPSG:32644")
                for _, row in place_polys.iterrows():
                    osm_way_id = row.get("osm_way_id")
                    osm_rel_id = row.get("osm_id")
                    if osm_rel_id:
                        osm_id_str = f"relation/{osm_rel_id}"
                    elif osm_way_id:
                        osm_id_str = f"way/{osm_way_id}"
                    else:
                        osm_id_str = f"way/{row.name}"

                    name_val = str(row.get("name", "")).strip()
                    display_name = (
                        name_val
                        if name_val and name_val != "None"
                        else "Settlement name unavailable (OSM)"
                    )

                    candidate_features.append(
                        {
                            "osm_id": osm_id_str,
                            "name": display_name,
                            "place_type": str(row["place"]),
                            "geometry": row.geometry,
                            "method": "OSM polygon boundary",
                        }
                    )
    except Exception:
        # Layer missing or unreadable
        pass

    # 2. Check OSM points layer for place nodes
    try:
        pts = gpd.read_file(str(osm_path), layer="points")
        if "place" in pts.columns:
            place_pts = pts[pts["place"].isin(place_types)].copy()
            if not place_pts.empty:
                place_pts = place_pts.to_crs("EPSG:32644")
                for _, row in place_pts.iterrows():
                    node_id = row.get("osm_id")
                    osm_id_str = f"node/{node_id}" if node_id else f"node/{row.name}"
                    name_val = str(row.get("name", "")).strip()
                    display_name = (
                        name_val
                        if name_val and name_val != "None"
                        else "Settlement name unavailable (OSM)"
                    )

                    # 500m planar buffer around node
                    buffered_geom = row.geometry.buffer(buffer_radius_m)
                    candidate_features.append(
                        {
                            "osm_id": osm_id_str,
                            "name": display_name,
                            "place_type": str(row["place"]),
                            "geometry": buffered_geom,
                            "method": f"{buffer_radius_m:.0f}m radial buffer around OSM node",
                        }
                    )
    except Exception:
        pass

    if not candidate_features:
        return {
            "methodology": (
                f"Radial buffer ({buffer_radius_m:.0f}m) around OSM place nodes "
                "or OSM polygon boundaries."
            ),
            "buffer_radius_m": buffer_radius_m,
            "non_additive_note": (
                "Settlement figures overlap and are not additive. "
                "Total AOI exposed population is computed separately without double-counting."
            ),
            "total_settlements_evaluated": 0,
            "inundated_settlements_count": 0,
            "settlements": [],
        }

    settlement_records: list[dict[str, Any]] = []

    with (
        rasterio.open(depth_raster_path) as d_src,
        rasterio.open(worldpop_raster_path) as wp_src,
    ):
        depth_arr = d_src.read(1)
        wp_arr = wp_src.read(1)
        transform = d_src.transform
        nodata = d_src.nodata if d_src.nodata is not None else -9999.0

        # Wet cells: depth > 0 and valid non-nodata
        wet_mask = (depth_arr > 0.0) & (depth_arr != nodata) & (~np.isnan(depth_arr))

        for feat in candidate_features:
            geom = feat["geometry"]
            in_geom_mask = geometry_mask(
                [geom], out_shape=depth_arr.shape, transform=transform, invert=True
            )
            wet_in_geom = in_geom_mask & wet_mask
            has_wet = bool(np.any(wet_in_geom))

            pop_exposed = (
                float(np.nansum(np.where(wet_in_geom & (wp_arr > 0), wp_arr, 0.0)))
                if has_wet
                else 0.0
            )
            peak_d = float(np.nanmax(depth_arr[wet_in_geom])) if has_wet else 0.0

            # PravahX design system depth ramp:
            # 0 - 0.5, 0.5 - 1.5, 1.5 - 3, 3 - 5, 5 - 8, > 8
            if not has_wet or peak_d <= 0.0:
                d_class = "Dry / Uninundated"
            elif peak_d <= 0.5:
                d_class = "0.0 - 0.5m"
            elif peak_d <= 1.5:
                d_class = "0.5 - 1.5m"
            elif peak_d <= 3.0:
                d_class = "1.5 - 3.0m"
            elif peak_d <= 5.0:
                d_class = "3.0 - 5.0m"
            elif peak_d <= 8.0:
                d_class = "5.0 - 8.0m"
            else:
                d_class = "> 8.0m"

            settlement_records.append(
                {
                    "osm_id": feat["osm_id"],
                    "name": feat["name"],
                    "place_type": feat["place_type"],
                    "method": feat["method"],
                    "population_exposed": round(pop_exposed),
                    "population_exposed_exact": round(pop_exposed, 2),
                    "peak_depth_m": round(peak_d, 2),
                    "depth_class": d_class,
                    "is_inundated": has_wet,
                }
            )

    # Sort: inundated first by exposed population descending, then by peak depth descending
    settlement_records.sort(
        key=lambda r: (
            r["is_inundated"],
            r["population_exposed"],
            r["peak_depth_m"],
        ),
        reverse=True,
    )

    return {
        "methodology": (
            "OSM polygon boundary when available, else "
            f"{buffer_radius_m:.0f}m planar buffer around place node in EPSG:32644; "
            "population_exposed = WorldPop 2020 sum where depth > 0; "
            "peak_depth_m = maximum Tier-0 water depth within area."
        ),
        "buffer_radius_m": buffer_radius_m,
        "non_additive_note": (
            "Settlement figures overlap and are not additive. "
            "Total AOI exposed population is computed separately without double-counting."
        ),
        "total_settlements_evaluated": len(settlement_records),
        "inundated_settlements_count": sum(1 for r in settlement_records if r["is_inundated"]),
        "settlements": settlement_records,
    }


def save_settlement_exposure_artifact(
    out_dir: str | Path = "data/ganga_inputs",
    buffer_radius_m: float = 500.0,
) -> tuple[Path, Path, str]:
    """Execute computation and save JSON output along with SHA-256 hash."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = compute_settlement_exposure(buffer_radius_m=buffer_radius_m)

    out_json = out_dir / "settlements_exposure.json"
    json_bytes = json.dumps(result, indent=2).encode("utf-8")
    out_json.write_bytes(json_bytes)

    sha256_hash = hashlib.sha256(json_bytes).hexdigest()
    out_sha = out_dir / "settlements_exposure.json.sha256"
    out_sha.write_text(f"{sha256_hash}  settlements_exposure.json\n", encoding="utf-8")

    return out_json, out_sha, sha256_hash


if __name__ == "__main__":
    json_path, sha_path, digest = save_settlement_exposure_artifact()
    print(f"Generated verified settlements exposure at {json_path}")
    print(f"SHA-256: {digest}")
