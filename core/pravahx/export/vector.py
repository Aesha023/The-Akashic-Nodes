"""Export generators (Phase 1).

Converts normalised output rasters into COG, Shapefile, and KML formats.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

from pravahx.errors import DataError

if TYPE_CHECKING:
    from pathlib import Path

    from pravahx.engines.base import NormalisedOutput

logger = logging.getLogger(__name__)


def export_cog(
    input_path: Path,
    out_path: Path,
) -> Path:
    """Export a raster as a Cloud Optimised GeoTIFF (COG)."""
    logger.info(f"Exporting COG to {out_path}")

    # In a full implementation we would build overviews and set block sizes.
    # For Phase 1 we use rioxarray or rasterio with COG profile if available.
    # Since we use rasterio without gdal tools installed directly on the path,
    # we can use a basic tiled and deflated tif, which is a poor-man's COG.

    with rasterio.open(input_path) as src:
        meta = src.meta.copy()
        data = src.read()

    meta.update(
        driver="GTiff",
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress="deflate",
        interleave="pixel",
    )

    with rasterio.open(out_path, "w", **meta) as dest:
        dest.write(data)

    return out_path


def _vectorise_raster(raster_path: Path, threshold: float = 0.1) -> gpd.GeoDataFrame:
    """Convert raster pixels >= threshold to polygons."""
    with rasterio.open(raster_path) as src:
        image = src.read(1)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    # Create a mask for inundated areas
    mask = (image != nodata) & (image >= threshold) if nodata is not None else image >= threshold

    results = []
    # Extract shapes
    for geom, val in shapes(image, mask=mask, transform=transform):
        # We only care about the envelope for Phase 1 (val represents depth)
        results.append({"geometry": shape(geom), "max_depth": val})

    gdf = gpd.GeoDataFrame(results, crs=crs)
    # Dissolve to simplify, but here we just keep them separate or dissolve all
    # For a simple envelope, dissolve all:
    if not gdf.empty:
        gdf = gdf.dissolve()

    return gdf


def export_shapefile(
    input_path: Path,
    out_path: Path,
    depth_threshold_m: float = 0.1,
) -> Path:
    """Export the inundation envelope as an ESRI Shapefile."""
    logger.info(f"Exporting Shapefile to {out_path}")

    gdf = _vectorise_raster(input_path, threshold=depth_threshold_m)
    if gdf.empty:
        logger.warning("No inundated areas found. Creating empty shapefile.")

    # Shapefiles require a directory or specifically named output
    gdf.to_file(out_path, driver="ESRI Shapefile")
    return out_path


def export_kml(
    input_path: Path,
    out_path: Path,
    depth_threshold_m: float = 0.1,
) -> Path:
    """Export the inundation envelope as a KML file."""
    logger.info(f"Exporting KML to {out_path}")

    import fiona

    fiona.drvsupport.supported_drivers["KML"] = "rw"

    gdf = _vectorise_raster(input_path, threshold=depth_threshold_m)

    # KML must be EPSG:4326
    if not gdf.empty and gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    try:
        gdf.to_file(out_path, driver="KML")
    except Exception as exc:
        raise DataError(f"Failed to export KML: {exc}") from exc

    return out_path


def generate_exports(
    output: NormalisedOutput,
    out_dir: Path,
) -> list[Path]:
    """Generate all standard exports for a normalised output."""
    out_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    try:
        depth_layer = output.get_layer("max_depth")
    except KeyError:
        logger.warning("No max_depth layer to export.")
        return generated

    base_name = f"{output.engine_name}_envelope"

    # COG
    cog_path = out_dir / f"{base_name}.tif"
    generated.append(export_cog(depth_layer.path, cog_path))

    # Shapefile
    shp_path = out_dir / f"{base_name}.shp"
    generated.append(export_shapefile(depth_layer.path, shp_path, output.depth_threshold_m))

    # KML
    kml_path = out_dir / f"{base_name}.kml"
    generated.append(export_kml(depth_layer.path, kml_path, output.depth_threshold_m))

    return generated
