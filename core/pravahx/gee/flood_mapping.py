"""Satellite SAR and optical flood extent extraction (Phase 6 / Section 6).

Methods:
1. UN-SPIDER Recommended Practice (Default SAR Method):
   - Linear ratio change detection: Ratio = sigma0_pre_linear / sigma0_post_linear >= 1.25
     (or in dB: sigma0_pre_dB - sigma0_post_dB >= 10 * log10(1.25) ~= +0.9691 dB).
   - Topographic slope filter: excludes terrain with slope > 5 % (PERCENT, not degrees).
     Source: UN-SPIDER Step 9: 'To remove areas with over 5 % slope, a digital elevation model
     (WWF HydroSHEDS) has been chosen'.
   - Connected-pixel filter: eliminates patches connected to 8 or fewer neighbors.
     Source: UN-SPIDER Step 9: 'Furthermore, the connectivity of the flood pixels is assessed
     to eliminate those connected to eight or fewer neighbors.'
   - Permanent water subtraction: excludes permanent rivers/lakes (e.g. JRC surface water).
   - [PravahX Hydrological Addition]: HAND filter <= 15m (Height Above Nearest Drainage).
     Note: HAND is an addition by PravahX and NOT part of the official UN-SPIDER practice.
   Source URL:
     https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping/step-by-step

2. Alternative SAR Backscatter Thresholding (Labelled Alternative):
   - Absolute backscatter threshold: sigma0_post < threshold_db (typically -15.0 dB in VV/VH).

3. Optical Water Index (Sentinel-2 / Landsat):
   - MNDWI = (Green - SWIR) / (Green + SWIR)
   - NDWI = (Green - NIR) / (Green + NIR)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pydantic import BaseModel


class FloodExtractionResult(BaseModel):
    """Satellite-derived flood inundation mapping results."""

    sensor_type: str  # "UN_SPIDER_SAR_Sentinel1", "Absolute_SAR_Sentinel1", "Optical_Sentinel2"
    total_flooded_area_km2: float
    total_permanent_water_km2: float
    flood_mask_path: str
    metadata: dict[str, Any] = {}


def filter_connected_flood_pixels(
    binary_mask: np.ndarray[Any, Any],
    min_connected_pixels: int = 8,
) -> np.ndarray[Any, Any]:
    """Eliminates isolated flood pixels connected to 8 or fewer neighbors.

    Source: UN-SPIDER Recommended Practice Step 9:
    'Furthermore, the connectivity of the flood pixels is assessed to eliminate
     those connected to eight or fewer neighbors. This operation reduces the noise
     of the flood extent product (Fig. 15).'
    """
    if min_connected_pixels <= 0:
        return binary_mask

    try:
        from scipy.ndimage import label  # type: ignore[import-untyped]

        structure = np.ones((3, 3), dtype=int)
        labeled_arr, num_features = label(binary_mask > 0, structure=structure)
        if num_features == 0:
            return binary_mask
        counts = np.bincount(labeled_arr.ravel())
        valid_mask = counts > min_connected_pixels
        valid_mask[0] = False
        res: np.ndarray[Any, Any] = valid_mask[labeled_arr].astype(np.uint8)
        return res
    except ImportError:
        pass

    # Pure NumPy BFS fallback for lightweight or air-gapped environments without scipy
    mask = (binary_mask > 0).astype(bool)
    h, w = mask.shape
    visited = np.zeros((h, w), dtype=bool)
    output = np.zeros((h, w), dtype=np.uint8)

    for r in range(h):
        for c in range(w):
            if mask[r, c] and not visited[r, c]:
                component: list[tuple[int, int]] = []
                queue = [(r, c)]
                visited[r, c] = True
                while queue:
                    curr_r, curr_c = queue.pop()
                    component.append((curr_r, curr_c))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < h and 0 <= nc < w and mask[nr, nc] and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                if len(component) > min_connected_pixels:
                    for cr, cc in component:
                        output[cr, cc] = 1

    return output


def smooth_sar_speckle(
    sar_array: np.ndarray[Any, Any],
    filter_size: int = 5,
) -> np.ndarray[Any, Any]:
    """Apply spatial median filter to reduce SAR speckle noise.

    Source: UN-SPIDER Recommended Practice Step 7:
    'Hence, the code in this Recommended Practice only applies a smoothing filter
     to reduce the inherent speckle-effect of radar imagery (Fig. 13)...
     applied smoothing of 50 m circles.'
    """
    try:
        from scipy.ndimage import median_filter

        res: np.ndarray[Any, Any] = np.asarray(median_filter(sar_array, size=filter_size))
        return res
    except ImportError:
        return np.asarray(sar_array)


def extract_unspider_sar_flood(
    post_event_backscatter_db: np.ndarray[Any, Any],
    pre_event_backscatter_db: np.ndarray[Any, Any],
    ratio_threshold: float = 1.25,
    slope_array_percent: np.ndarray[Any, Any] | None = None,
    slope_array_deg: np.ndarray[Any, Any] | None = None,
    max_slope_percent: float = 5.0,
    hand_array_m: np.ndarray[Any, Any] | None = None,
    max_hand_m: float = 15.0,
    min_connected_pixels: int = 8,
    max_post_backscatter_db: float | None = None,
) -> np.ndarray[Any, Any]:
    """Extract flood water mask following the exact UN-SPIDER recommended practice.

    Exact UN-SPIDER Steps Quoted from Primary Source:
    - Step 2 (Pass Direction):
      'When performing change detection, it is necessary to select the same pass direction
       for the images being compared to avoid false positive signals caused by differences
       of the viewing angle.'
    - Step 7 (Preprocessing & Speckle Smoothing):
      'Hence, the code in this Recommended Practice only applies a smoothing filter to reduce
       the inherent speckle-effect of radar imagery (Fig. 13). applied smoothing of 50 m circles.'
    - Step 8 (Change Detection):
      'This script uses a simple, straight-forward change detection approach, where the
       after-flood mosaic is divided by the before-flood mosaic, resulting in a raster layer
       showing the degree of change per pixel. High values (bright pixels) indicate high change,
       low values (dark pixels) point toward little change. The predefined threshold of 1.25 is
       applied assigning 1 to all values greater than 1.25 and 0 to all values less than 1.25.
       The binary raster layer created by this process shows the potential flood extent (Fig. 14).'
    - Step 9 (Refining the Flood Extent Layer):
      'The JRC Global Surface Water dataset is used to mask out all areas covered by water
       for more than 10 months per year.'
      'To remove areas with over 5 % slope, a digital elevation model (WWF HydroSHEDS)
       has been chosen, which is based on SRTM data, and has a spatial resolution of 3 arc-seconds.'
      'Furthermore, the connectivity of the flood pixels is assessed to eliminate those
       connected to eight or fewer neighbors. This operation reduces the noise of the flood
       extent product (Fig. 15).'

    Note on -12 dB rule:
    - The -12 dB threshold is NOT part of the official UN-SPIDER Recommended Practice.
      It has been removed from the default pipeline. An optional heuristic parameter
      `max_post_backscatter_db` is provided for experimental use, labelled as a non-standard
      addition.

    PravahX Hydrological Additions:
    - HAND filter (max_hand_m <= 15.0 m): Hydrological constraint to remove elevated terrain
      false positives in steep valleys. Labelled as a PravahX addition (NOT part of UN-SPIDER).

    Source URL:
      https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping/step-by-step
    """
    post_db = np.asarray(post_event_backscatter_db, dtype=np.float64)
    pre_db = np.asarray(pre_event_backscatter_db, dtype=np.float64)

    # In linear power scale: Ratio = 10^(pre_dB / 10) / 10^(post_dB / 10) >= ratio_threshold
    # Mathematically: pre_dB - post_dB >= 10 * log10(ratio_threshold)
    db_drop_threshold = 10.0 * math.log10(ratio_threshold)
    db_drop = pre_db - post_db

    # Candidate flooded pixels based on UN-SPIDER ratio threshold (1.25)
    flood_candidate = db_drop >= db_drop_threshold

    # Optional heuristic filter (labelled non-standard addition, NOT part of UN-SPIDER)
    if max_post_backscatter_db is not None:
        flood_candidate = flood_candidate & (post_db <= max_post_backscatter_db)

    # Topographic slope filter (UN-SPIDER Step 9: mask out slopes > 5%)
    if slope_array_percent is not None:
        slope_mask = np.asarray(slope_array_percent, dtype=np.float64) <= max_slope_percent
        flood_candidate = flood_candidate & slope_mask
    elif slope_array_deg is not None:
        # Convert slope degrees to percent: slope_percent = tan(radians(deg)) * 100
        deg_rad = np.radians(np.asarray(slope_array_deg, dtype=np.float64))
        slope_pct = np.tan(deg_rad) * 100.0
        slope_mask = slope_pct <= max_slope_percent
        flood_candidate = flood_candidate & slope_mask

    # [PravahX Addition]: HAND filter (mask out high elevation above nearest drainage)
    if hand_array_m is not None:
        hand_mask = np.asarray(hand_array_m, dtype=np.float64) <= max_hand_m
        flood_candidate = flood_candidate & hand_mask

    # Connected-pixel filter (UN-SPIDER Step 9: eliminate patches connected to <= 8 neighbors)
    res_mask = flood_candidate.astype(np.uint8)
    if min_connected_pixels > 0:
        res_mask = filter_connected_flood_pixels(
            res_mask, min_connected_pixels=min_connected_pixels
        )

    return res_mask


def extract_sar_flood_extent_alternative(
    post_event_backscatter_db: np.ndarray[Any, Any],
    pre_event_backscatter_db: np.ndarray[Any, Any] | None = None,
    threshold_db: float = -15.0,
    diff_threshold_db: float = -3.0,
) -> np.ndarray[Any, Any]:
    """Alternative absolute/difference SAR backscatter thresholding method."""
    post = np.asarray(post_event_backscatter_db, dtype=np.float64)
    water_abs = post < threshold_db

    if pre_event_backscatter_db is not None:
        pre = np.asarray(pre_event_backscatter_db, dtype=np.float64)
        diff = post - pre
        water_diff = diff <= diff_threshold_db
        flood_mask = (water_abs | water_diff) & (post < -12.0)
    else:
        flood_mask = water_abs

    return flood_mask.astype(np.uint8)


# Alias for backward compatibility
extract_sar_flood_extent = extract_sar_flood_extent_alternative


def extract_optical_water_extent(
    green_band: np.ndarray[Any, Any],
    swir_band: np.ndarray[Any, Any] | None = None,
    nir_band: np.ndarray[Any, Any] | None = None,
    threshold: float = 0.0,
) -> np.ndarray[Any, Any]:
    """Extract water mask from optical bands using MNDWI or NDWI."""
    g = np.asarray(green_band, dtype=np.float64)

    if swir_band is not None:
        swir = np.asarray(swir_band, dtype=np.float64)
        mndwi = (g - swir) / np.maximum(1e-6, g + swir)
        water = mndwi > threshold
    elif nir_band is not None:
        nir = np.asarray(nir_band, dtype=np.float64)
        ndwi = (g - nir) / np.maximum(1e-6, g + nir)
        water = ndwi > threshold
    else:
        raise ValueError("Either swir_band or nir_band must be provided.")

    res: np.ndarray[Any, Any] = water.astype(np.uint8)
    return res


def process_satellite_flood_raster(
    post_event_raster_path: str | Path,
    output_mask_path: str | Path,
    sensor_type: str = "UN_SPIDER_SAR_Sentinel1",
    pre_event_raster_path: str | Path | None = None,
    slope_raster_path: str | Path | None = None,
    hand_raster_path: str | Path | None = None,
    permanent_water_mask_path: str | Path | None = None,
    ratio_threshold: float = 1.25,
) -> FloodExtractionResult:
    """Generate satellite flood inundation GeoTIFF following UN-SPIDER change detection."""
    out_p = Path(output_mask_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(post_event_raster_path) as src:
        post_data = src.read(1)

        slope_data = None
        if slope_raster_path:
            with rasterio.open(slope_raster_path) as slp_src:
                slope_data = slp_src.read(1)

        hand_data = None
        if hand_raster_path:
            with rasterio.open(hand_raster_path) as hnd_src:
                hand_data = hnd_src.read(1)

        if sensor_type in ("UN_SPIDER_SAR_Sentinel1", "SAR_Sentinel1") and pre_event_raster_path:
            with rasterio.open(pre_event_raster_path) as pre_src:
                pre_data = pre_src.read(1)
            raw_water = extract_unspider_sar_flood(
                post_event_backscatter_db=post_data,
                pre_event_backscatter_db=pre_data,
                ratio_threshold=ratio_threshold,
                slope_array_deg=slope_data,
                hand_array_m=hand_data,
            )
        elif sensor_type in ("Absolute_SAR_Sentinel1", "SAR_Sentinel1", "UN_SPIDER_SAR_Sentinel1"):
            pre_data = None
            if pre_event_raster_path:
                with rasterio.open(pre_event_raster_path) as pre_src:
                    pre_data = pre_src.read(1)
            raw_water = extract_sar_flood_extent_alternative(
                post_event_backscatter_db=post_data,
                pre_event_backscatter_db=pre_data,
            )
        else:
            raw_water = (post_data > 0).astype(np.uint8)

        # Subtract permanent water if provided
        perm_water_km2 = 0.0
        if permanent_water_mask_path:
            with rasterio.open(permanent_water_mask_path) as perm_src:
                perm_data = perm_src.read(1)
                perm_mask = perm_data > 0
                cell_area_km2 = (abs(src.res[0]) * abs(src.res[1])) / 1e6
                perm_water_km2 = float(np.sum(perm_mask) * cell_area_km2)
                raw_water = np.where(perm_mask, 0, raw_water)

        cell_area_km2 = (abs(src.res[0]) * abs(src.res[1])) / 1e6
        flooded_km2 = float(np.sum(raw_water > 0) * cell_area_km2)

        profile = src.profile.copy()
        profile.update(
            dtype=rasterio.uint8,
            count=1,
            nodata=0,
            compress="deflate",
        )

        with rasterio.open(out_p, "w", **profile) as dst:
            dst.write(raw_water.astype(np.uint8), 1)

    return FloodExtractionResult(
        sensor_type=sensor_type,
        total_flooded_area_km2=round(flooded_km2, 6),
        total_permanent_water_km2=round(perm_water_km2, 6),
        flood_mask_path=str(out_p),
        metadata={
            "resolution_m": float(abs(src.res[0])),
            "crs": str(src.crs),
            "ratio_threshold": ratio_threshold,
            "method": "UN-SPIDER Recommended Practice (change detection)",
        },
    )


def export_binary_mask_to_kml(
    mask: np.ndarray[Any, Any],
    transform: rasterio.Affine,
    kml_path: str | Path,
    event_name: str = "UN-SPIDER Flood Extent",
    description: str = "PravahX UN-SPIDER SAR Flood Mapping",
    folder_name: str = "needs human check",
) -> Path:
    """Export binary flood inundation mask to standard KML vector format."""
    import rasterio.features

    out_p = Path(kml_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    shapes_gen = rasterio.features.shapes(
        mask.astype(np.uint8), mask=(mask > 0), transform=transform
    )
    placemarks: list[str] = []
    poly_idx = 0

    for geom, val in shapes_gen:
        if val > 0 and geom["type"] in ("Polygon", "MultiPolygon"):
            poly_idx += 1
            coords_list = (
                [geom["coordinates"]]
                if geom["type"] == "Polygon"
                else geom["coordinates"]
            )
            for poly_coords in coords_list:
                ext_ring = poly_coords[0]
                coord_str = " ".join([f"{lon},{lat},0" for lon, lat in ext_ring])
                placemark = f"""    <Placemark>
      <name>Flooded Area #{poly_idx}</name>
      <styleUrl>#floodStyle</styleUrl>
      <Polygon>
        <extrude>0</extrude>
        <altitudeMode>clampToGround</altitudeMode>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coord_str}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>"""
                placemarks.append(placemark)

    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{event_name}</name>
    <description><![CDATA[{description}]]></description>
    <Style id="floodStyle">
      <LineStyle>
        <color>ff0000ff</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <color>7fff8000</color>
        <fill>1</fill>
        <outline>1</outline>
      </PolyStyle>
    </Style>
    <Folder>
      <name>{folder_name}</name>
      <open>1</open>
{chr(10).join(placemarks)}
    </Folder>
  </Document>
</kml>
"""
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(kml_content)
    return out_p


def execute_unspider_sar_gee(
    bbox: tuple[float, float, float, float],
    pre_start: str,
    pre_end: str,
    post_start: str,
    post_end: str,
    output_dir: str | Path,
    pass_direction: str = "DESCENDING",
    polarization: str = "VH",
    ratio_threshold: float = 1.25,
    max_slope_percent: float = 5.0,
    min_connected_pixels: int = 8,
    event_name: str = "Kerala August 2018",
) -> FloodExtractionResult:
    """Execute live UN-SPIDER change detection on Google Earth Engine.

    Parameters
    ----------
    bbox : tuple
        (min_lon, min_lat, max_lon, max_lat)
    pre_start, pre_end : str
        Pre-event date range (YYYY-MM-DD).
    post_start, post_end : str
        Post-event date range (YYYY-MM-DD).
    output_dir : Path
        Directory where GeoTIFF and KML will be exported.
    pass_direction : str
        Identical orbit direction (Step 2: 'DESCENDING' or 'ASCENDING').
    polarization : str
        SAR polarization (typically 'VH').
    ratio_threshold : float
        Change ratio threshold (Step 8: default 1.25).
    max_slope_percent : float
        WWF HydroSHEDS slope mask threshold (Step 9: default 5.0%).
    min_connected_pixels : int
        Connectivity filter threshold (Step 9: default 8 pixels).
    """
    import ee
    from rasterio.transform import from_bounds

    from pravahx.gee.client import GEEClient

    client = GEEClient()
    if not client.initialize():
        raise RuntimeError(f"Earth Engine authentication failed: {client.last_error}")

    min_lon, min_lat, max_lon, max_lat = bbox
    roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(roi)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", polarization))
        .filter(ee.Filter.eq("orbitProperties_pass", pass_direction))
    )

    pre_col = s1.filterDate(pre_start, pre_end)
    post_col = s1.filterDate(post_start, post_end)

    pre_dates = (
        pre_col.aggregate_array("system:time_start")
        .map(lambda t: ee.Date(t).format("YYYY-MM-dd HH:mm"))
        .getInfo()
    )
    post_dates = (
        post_col.aggregate_array("system:time_start")
        .map(lambda t: ee.Date(t).format("YYYY-MM-dd HH:mm"))
        .getInfo()
    )

    pre_img = pre_col.select(polarization).mosaic()
    post_img = post_col.select(polarization).mosaic()

    # Step 7: Speckle smoothing (50m circular median filter)
    pre_filtered = pre_img.focal_median(50, "circle", "meters")
    post_filtered = post_img.focal_median(50, "circle", "meters")

    # Step 8: Change ratio
    diff = post_filtered.divide(pre_filtered)
    flood_raw = diff.gt(ratio_threshold)

    # Step 9: Slope filter (WWF HydroSHEDS <= 5%)
    dem = ee.Image("WWF/HydroSHEDS/03CONDEM")
    slope_deg = ee.Terrain.slope(dem)
    slope_mask = (
        slope_deg.multiply(math.pi / 180.0).tan().multiply(100.0).lte(max_slope_percent)
    )

    # Step 9: JRC permanent water mask (seasonality >= 10 months)
    jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    perm_water = jrc.select("seasonality").gte(10)

    # Step 9: Connected pixel filter
    refined = flood_raw.updateMask(slope_mask).updateMask(perm_water.Not())
    conn = refined.connectedPixelCount(25)
    final_flood = refined.updateMask(conn.gt(min_connected_pixels))

    # Calculate area in km2
    pixel_area = ee.Image.pixelArea()
    flood_area_img = final_flood.multiply(pixel_area)
    stats = flood_area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=30,
        maxPixels=1e9,
    ).getInfo()
    area_m2 = stats.get(polarization, 0) or 0
    area_km2 = area_m2 / 1e6

    # Sample raster via 2x2 tiling to respect 262,144 pixel limit per sample
    mid_lon = (min_lon + max_lon) / 2.0
    mid_lat = (min_lat + max_lat) / 2.0
    roi_nw = ee.Geometry.Rectangle([min_lon, mid_lat, mid_lon, max_lat])
    roi_ne = ee.Geometry.Rectangle([mid_lon, mid_lat, max_lon, max_lat])
    roi_sw = ee.Geometry.Rectangle([min_lon, min_lat, mid_lon, mid_lat])
    roi_se = ee.Geometry.Rectangle([mid_lon, min_lat, max_lon, mid_lat])

    final_img = final_flood.unmask(0).toByte().reproject("EPSG:4326", None, 30)

    arr_nw = np.array(
        final_img.sampleRectangle(region=roi_nw).getInfo()["properties"][polarization],
        dtype=np.uint8,
    )
    arr_ne = np.array(
        final_img.sampleRectangle(region=roi_ne).getInfo()["properties"][polarization],
        dtype=np.uint8,
    )
    arr_sw = np.array(
        final_img.sampleRectangle(region=roi_sw).getInfo()["properties"][polarization],
        dtype=np.uint8,
    )
    arr_se = np.array(
        final_img.sampleRectangle(region=roi_se).getInfo()["properties"][polarization],
        dtype=np.uint8,
    )

    min_c = min(arr_nw.shape[1], arr_sw.shape[1])
    min_c2 = min(arr_ne.shape[1], arr_se.shape[1])
    top_row = np.hstack([arr_nw[:, :min_c], arr_ne[:, :min_c2]])
    bot_row = np.hstack([arr_sw[:, :min_c], arr_se[:, :min_c2]])
    min_w = min(top_row.shape[1], bot_row.shape[1])
    arr = np.vstack([top_row[:, :min_w], bot_row[:, :min_w]])

    nrows, ncols = arr.shape
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, ncols, nrows)

    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    tif_path = out_p / "kerala_flood_2018.tif"
    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        height=nrows,
        width=ncols,
        count=1,
        dtype=rasterio.uint8,
        crs="EPSG:4326",
        transform=transform,
        compress="deflate",
        nodata=0,
    ) as dst:
        dst.write(arr, 1)

    kml_check_path = out_p / "needs_human_check" / "kerala_flood_2018.kml"
    kml_main_path = out_p / "kerala_flood_2018.kml"

    export_binary_mask_to_kml(
        mask=arr,
        transform=transform,
        kml_path=kml_check_path,
        event_name=f"{event_name} Flood Extent",
        folder_name="needs human check",
    )
    export_binary_mask_to_kml(
        mask=arr,
        transform=transform,
        kml_path=kml_main_path,
        event_name=f"{event_name} Flood Extent",
        folder_name="needs human check",
    )

    return FloodExtractionResult(
        sensor_type="UN_SPIDER_SAR_Sentinel1",
        total_flooded_area_km2=round(area_km2, 4),
        total_permanent_water_km2=0.0,
        flood_mask_path=str(tif_path),
        metadata={
            "event": event_name,
            "orbit_direction": pass_direction,
            "polarization": polarization,
            "pre_event_dates": pre_dates,
            "post_event_dates": post_dates,
            "ratio_threshold": ratio_threshold,
            "kml_path_needs_human_check": str(kml_check_path),
            "kml_path": str(kml_main_path),
            "status": "needs human check",
            "needs_human_check": True,
        },
    )
