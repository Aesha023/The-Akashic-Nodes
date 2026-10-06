"""Export generators (Phase 1).

Converts normalised output rasters into COG, Shapefile, and KML formats.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import geopandas as gpd
import numpy as np
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


def _style_kml_polygons(
    kml_path: Path,
    fill_color: str = "80ff5500",  # Semi-transparent blue/cyan in aabbggrr hex (50% alpha)
    line_color: str = "ff0000ff",  # Red border outline
    line_width: float = 1.5,
) -> None:
    """Ensure KML polygons are filled and semi-transparent, not just outlines."""
    if not kml_path.exists():
        return
    text = kml_path.read_text(encoding="utf-8")
    style_xml = (
        f'<Style id="inundation_style">'
        f"<LineStyle><color>{line_color}</color><width>{line_width}</width></LineStyle>"
        f"<PolyStyle><color>{fill_color}</color><fill>1</fill><outline>1</outline></PolyStyle>"
        f"</Style>"
    )

    if "<PolyStyle>" in text:
        text = re.sub(
            r"<PolyStyle>.*?</PolyStyle>",
            f"<PolyStyle><color>{fill_color}</color><fill>1</fill><outline>1</outline></PolyStyle>",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"<LineStyle>.*?</LineStyle>",
            f"<LineStyle><color>{line_color}</color><width>{line_width}</width></LineStyle>",
            text,
            flags=re.DOTALL,
        )
    else:
        text = re.sub(r"(<Document[^>]*>)", r"\1" + style_xml, text, count=1)
        text = re.sub(r"(<Placemark[^>]*>)", r"\1<styleUrl>#inundation_style</styleUrl>", text)

    kml_path.write_text(text, encoding="utf-8")


def export_lines_kml(
    gdf: gpd.GeoDataFrame,
    out_path: Path,
    line_color: str = "ffff0000",  # Blue in aabbggrr hex
    line_width: float = 2.5,
) -> Path:
    """Export line geometries to KML with styling."""
    logger.info(f"Exporting Lines KML to {out_path}")
    import fiona

    fiona.drvsupport.supported_drivers["KML"] = "rw"

    if not gdf.empty:
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

    gdf.to_file(out_path, driver="KML")

    if out_path.exists():
        text = out_path.read_text(encoding="utf-8")
        styled = re.sub(
            r"<LineStyle>.*?</LineStyle>",
            f"<LineStyle><color>{line_color}</color><width>{line_width}</width></LineStyle>",
            text,
            flags=re.DOTALL,
        )
        out_path.write_text(styled, encoding="utf-8")

    return out_path


def export_raster_overlay_kmz(
    raster_path: Path,
    out_kmz_path: Path,
    layer_name: str,
) -> Path:
    """Export a raster as a georeferenced KMZ GroundOverlay for Google Earth."""
    logger.info(f"Exporting KMZ overlay to {out_kmz_path}")
    import io
    import zipfile

    from PIL import Image

    with rasterio.open(raster_path) as src:
        data = src.read(1)
        bounds = src.bounds
        nodata = src.nodata

    valid = (data != nodata) & (~np.isnan(data)) if nodata is not None else ~np.isnan(data)
    rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)

    if np.any(valid):
        val_min = float(np.min(data[valid]))
        val_max = float(np.max(data[valid]))
        norm = np.zeros_like(data, dtype=np.uint8)
        if val_max > val_min:
            norm[valid] = ((data[valid] - val_min) / (val_max - val_min) * 255).astype(np.uint8)

        rgba[valid, 0] = norm[valid]
        rgba[valid, 1] = norm[valid]
        rgba[valid, 2] = 255 - norm[valid]
        rgba[valid, 3] = 180  # 70% opacity

    img = Image.fromarray(rgba)
    png_name = f"{layer_name}.png"
    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Folder>
    <name>{layer_name}</name>
    <GroundOverlay>
      <name>{layer_name}</name>
      <Icon><href>{png_name}</href></Icon>
      <LatLonBox>
        <north>{bounds.top}</north>
        <south>{bounds.bottom}</south>
        <east>{bounds.right}</east>
        <west>{bounds.left}</west>
      </LatLonBox>
    </GroundOverlay>
  </Folder>
</kml>"""

    out_kmz_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_kmz_path, "w") as zf:
        zf.writestr("doc.kml", kml)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        zf.writestr(png_name, buf.getvalue())

    return out_kmz_path


def export_kml(
    input_path: Path,
    out_path: Path,
    depth_threshold_m: float = 0.1,
) -> Path:
    """Export the inundation envelope as a filled, semi-transparent KML file."""
    logger.info(f"Exporting KML to {out_path}")

    import fiona

    fiona.drvsupport.supported_drivers["KML"] = "rw"

    gdf = _vectorise_raster(input_path, threshold=depth_threshold_m)

    # KML must be EPSG:4326
    if not gdf.empty and gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    try:
        gdf.to_file(out_path, driver="KML")
        # Ensure polygons are filled and semi-transparent
        _style_kml_polygons(out_path)
    except Exception as exc:
        raise DataError(f"Failed to export KML: {exc}") from exc

    return out_path


def export_diagnostic_bundle(
    work_dir: Path,
    exports_dir: Path,
) -> list[Path]:
    """Export diagnostic COGs, stream lines, and KML GroundOverlays."""
    exports_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    # Map of intermediate files to standard names
    candidates = [
        ("raw_dem", list(work_dir.glob("dem_*.tif"))),
        ("conditioned_dem", [work_dir / "filled.tif"]),
        ("flow_accumulation", [work_dir / "d8_accum.tif"]),
        ("streams", [work_dir / "streams.tif"]),
        ("hand", [work_dir / "hand.tif"]),
    ]

    for label, paths in candidates:
        valid_paths = [p for p in paths if p.exists() and not p.name.endswith("_wgs84.tif")]
        if not valid_paths:
            continue
        src_path = valid_paths[0]
        # 1. COG
        cog_path = exports_dir / f"{label}.tif"
        generated.append(export_cog(src_path, cog_path))
        # 2. KMZ GroundOverlay
        kmz_path = exports_dir / f"{label}.kmz"
        generated.append(export_raster_overlay_kmz(src_path, kmz_path, label))

    # 3. Stream network as vector lines KML
    streams_shp = work_dir / "streams.shp"
    if streams_shp.exists():
        gdf_streams = gpd.read_file(streams_shp)
        stream_kml = exports_dir / "stream_network.kml"
        generated.append(export_lines_kml(gdf_streams, stream_kml))

    return generated


def generate_exports(
    output: NormalisedOutput,
    out_dir: Path,
) -> list[Path]:
    """Generate all standard exports for a normalised output."""
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

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

    # KML (filled and semi-transparent)
    kml_path = out_dir / f"{base_name}.kml"
    generated.append(export_kml(depth_layer.path, kml_path, output.depth_threshold_m))

    return generated
