"""Data fetching and caching (Phase 1).

Retrieves DEM and landcover data via STAC API, merges tiles and crops
to the requested bounding box. Uses local caching based on BBOX hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING

import geopandas as gpd
import pystac_client
import rasterio
import rioxarray
from rasterio.merge import merge
from shapely.geometry import box

from pravahx.errors import DataError

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# STAC endpoint for open Copernicus DEM
STAC_API_URL = "https://earth-search.aws.element84.com/v1"
DEM_COLLECTION = "cop-dem-glo-30"


def _hash_bbox(bbox: tuple[float, float, float, float]) -> str:
    """Hash a bounding box to create a cache key."""
    # Round to 3 decimal places (~100m) to reuse cache for very similar bounds
    rounded = [round(c, 3) for c in bbox]
    s = json.dumps(rounded, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def fetch_dem(
    bbox: tuple[float, float, float, float],
    cache_dir: Path,
    crs: str = "EPSG:4326",
) -> Path:
    """Fetch and crop Copernicus GLO-30 DEM for a bounding box.

    Args:
        bbox: (minx, miny, maxx, maxy) in the given CRS.
        cache_dir: Directory to store the downloaded and merged DEM.
        crs: CRS of the bounding box (default EPSG:4326).

    Returns:
        Path to the cached, cropped GeoTIFF.

    Raises:
        DataError: If the STAC search fails or no tiles are found.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    # If the bbox is not WGS84, we must project it for the STAC search.
    if crs != "EPSG:4326":
        bounds_gdf = gpd.GeoDataFrame({"geometry": [box(*bbox)]}, crs=crs)
        wgs_bounds = tuple(bounds_gdf.to_crs("EPSG:4326").total_bounds)
    else:
        wgs_bounds = bbox

    cache_key = _hash_bbox(wgs_bounds)
    out_path = cache_dir / f"dem_{cache_key}.tif"

    if out_path.exists():
        logger.info(f"Using cached DEM: {out_path}")
        return out_path

    logger.info(f"Searching STAC API for DEM tiles in {wgs_bounds}...")
    try:
        catalog = pystac_client.Client.open(STAC_API_URL)
        search = catalog.search(
            collections=[DEM_COLLECTION],
            bbox=wgs_bounds,
        )
        items = list(search.items())
    except Exception as exc:
        raise DataError(f"Failed to query STAC API: {exc}") from exc

    if not items:
        raise DataError(f"No DEM tiles found for bounding box {wgs_bounds}")

    # Extract HTTP URLs for the 'data' asset (GeoTIFFs on AWS S3)
    urls = []
    for item in items:
        if "data" in item.assets:
            urls.append(item.assets["data"].href)

    if not urls:
        raise DataError("STAC items found, but missing 'data' asset URLs.")

    logger.info(f"Found {len(urls)} DEM tiles. Downloading and merging...")

    # Use rasterio to open all remote URLs and merge them
    try:
        src_files_to_mosaic = []
        for url in urls:
            src_files_to_mosaic.append(rasterio.open(url))

        mosaic, out_trans = merge(src_files_to_mosaic, bounds=wgs_bounds)
        out_meta = src_files_to_mosaic[0].meta.copy()

        # Close remote sources
        for src in src_files_to_mosaic:
            src.close()

    except Exception as exc:
        raise DataError(f"Failed to download or merge DEM tiles: {exc}") from exc

    # Update metadata for the cropped mosaic
    out_meta.update(
        {
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "compress": "deflate",
            "tiled": True,
        }
    )

    # Write merged mosaic to disk (WGS84)
    wgs_path = cache_dir / f"dem_{cache_key}_wgs84.tif"
    with rasterio.open(wgs_path, "w", **out_meta) as dest:
        dest.write(mosaic)

    # If original request was in another CRS, reproject it
    if crs != "EPSG:4326":
        logger.info(f"Reprojecting DEM to {crs}...")
        ds = rioxarray.open_rasterio(wgs_path)
        if isinstance(ds, list):
            raise ValueError("Expected a single DataArray or Dataset")
        ds_proj = ds.rio.reproject(crs)
        # Crop exactly to the requested projected bbox
        ds_proj = ds_proj.rio.clip_box(*bbox)
        ds_proj.rio.to_raster(out_path, compress="deflate", tiled=True)
        wgs_path.unlink(missing_ok=True)  # Clean up intermediate WGS84 file
    else:
        wgs_path.rename(out_path)

    logger.info(f"DEM cached successfully at {out_path}")
    return out_path
