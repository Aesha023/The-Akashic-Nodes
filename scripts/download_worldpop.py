"""Download and clip official WorldPop 100m India population raster.

Provenance:
- URL: https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/IND/ind_ppp_2020_UNadj_constrained.tif
- Dataset: WorldPop 2020 Constrained (Building Settlement Growth Model - BSGM) 100m for India
- Date: 2020-09-20 (Release 2020, Version UNadj_constrained)
- License: Creative Commons Attribution 4.0 International (CC-BY 4.0)
- Raw File Size: 488,818,147 bytes (466.1 MB)
- Raw Expected SHA-256: 4fc54bcefe4e23c5f0638f775288375297091d5719d355d85f0820efe9199dbc
"""

import hashlib
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import Resampling, reproject
from shapely.geometry import box

RAW_URL = "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/IND/ind_ppp_2020_UNadj_constrained.tif"
EXPECTED_SHA256 = "4fc54bcefe4e23c5f0638f775288375297091d5719d355d85f0820efe9199dbc"


def download_and_clip(
    raw_dest: Path = Path("ind_pop_raw.tif"),
    clipped_dest: Path = Path("data/ganga_inputs/worldpop_ganga_32644.tif"),
    reference_depth: Path = Path("data/ganga_inputs/tier0_max_depth.tif"),
    force_download: bool = False,
) -> Path:
    if clipped_dest.exists() and not force_download:
        print(f"Clipped WorldPop raster already exists at {clipped_dest}")
        return clipped_dest

    if not raw_dest.exists():
        print(f"Downloading official WorldPop 100m raster from {RAW_URL}...")
        urllib.request.urlretrieve(RAW_URL, raw_dest)

    # Verify SHA-256
    print(f"Verifying SHA-256 for {raw_dest}...")
    h = hashlib.sha256()
    with open(raw_dest, "rb") as f:
        while chunk := f.read(1024 * 1024 * 8):
            h.update(chunk)
    actual_hash = h.hexdigest()
    assert actual_hash == EXPECTED_SHA256, (
        f"Hash mismatch: expected {EXPECTED_SHA256}, got {actual_hash}"
    )
    print(f"SHA-256 verified: {actual_hash}")

    # Clip to AOI [78.30, 30.10, 78.35, 30.15]
    aoi_geom = [box(78.30, 30.10, 78.35, 30.15)]
    with rasterio.open(raw_dest) as src_raw:
        out_img, out_transform = mask(src_raw, aoi_geom, crop=True)

    with rasterio.open(reference_depth) as src_depth:
        depth_meta = src_depth.meta.copy()

    dst_meta = depth_meta.copy()
    dst_meta.update(dtype=rasterio.float32, nodata=-9999.0)

    pop_reproj = np.zeros((depth_meta["height"], depth_meta["width"]), dtype=np.float32)
    reproject(
        source=out_img,
        destination=pop_reproj,
        src_transform=out_transform,
        src_crs="EPSG:4326",
        dst_transform=depth_meta["transform"],
        dst_crs=depth_meta["crs"],
        resampling=Resampling.bilinear,
        dst_nodata=-9999.0,
    )

    raw_total = float(out_img[out_img > 0].sum()) if np.any(out_img > 0) else 0.0
    valid_reproj = pop_reproj[pop_reproj > 0]
    if len(valid_reproj) > 0 and valid_reproj.sum() > 0:
        pop_reproj = pop_reproj * (raw_total / valid_reproj.sum())

    clipped_dest.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(clipped_dest, "w", **dst_meta) as dst:
        dst.write(pop_reproj, 1)

    print(f"Successfully clipped and saved WorldPop to {clipped_dest}")
    return clipped_dest


if __name__ == "__main__":
    download_and_clip()
