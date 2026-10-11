"""Test headless end-to-end execution of PravahX_Ganga_Tier1.ipynb notebook."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.show = lambda *args, **kwargs: None


def test_ganga_tier1_notebook_headless(tmp_path: Path) -> None:
    """Execute all code cells of PravahX_Ganga_Tier1.ipynb in headless mode."""
    nb_path = Path("notebooks/PravahX_Ganga_Tier1.ipynb").resolve()
    assert nb_path.exists(), f"Notebook not found at {nb_path}"

    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)

    # Prepare isolated content environment
    content_dir = tmp_path / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PRAVAHX_CONTENT_DIR"] = str(content_dir)
    os.environ["PRAVAHX_STUB_DFLOWFM"] = "1"

    drive_dir = content_dir / "drive" / "MyDrive" / "PravahX"
    ganga_in_dir = drive_dir / "ganga_inputs"
    ganga_in_dir.mkdir(parents=True, exist_ok=True)

    repo_inputs = Path("data/ganga_inputs").resolve()
    if repo_inputs.exists():
        for f in repo_inputs.iterdir():
            if f.is_file():
                shutil.copy(f, ganga_in_dir / f.name)
    else:
        import geopandas as gpd
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        from shapely.geometry import Polygon

        transform = from_origin(239800.0, 3338500.0, 30.0, 30.0)
        meta = {
            "driver": "GTiff",
            "height": 190,
            "width": 166,
            "count": 1,
            "dtype": "float32",
            "crs": "EPSG:32644",
            "transform": transform,
            "nodata": -9999.0,
        }
        # DEM: monotonic gradient along reach
        dem_arr = np.linspace(337.0, 450.0, 190 * 166, dtype=np.float32).reshape((190, 166))
        with rasterio.open(ganga_in_dir / "dem_ganga_32644.tif", "w", **meta) as dst:
            dst.write(dem_arr, 1)

        # Depth raster
        d_arr = np.full((190, 166), 1.5, dtype=np.float32)
        with rasterio.open(ganga_in_dir / "tier0_max_depth.tif", "w", **meta) as dst:
            dst.write(d_arr, 1)

        # WorldCover raster
        wc_meta = meta.copy()
        wc_meta.update(dtype="uint8", nodata=0)
        wc_arr = np.full((190, 166), 40, dtype=np.uint8)
        with rasterio.open(ganga_in_dir / "worldcover_ganga_32644.tif", "w", **wc_meta) as dst:
            dst.write(wc_arr, 1)

        # Valley envelope polygon
        poly = Polygon(
            [
                (239900.0, 3332900.0),
                (244600.0, 3332900.0),
                (244600.0, 3337800.0),
                (239900.0, 3337800.0),
            ]
        )
        gdf = gpd.GeoDataFrame({"geometry": [poly]}, crs="EPSG:32644")
        gdf.to_file(ganga_in_dir / "tier0_envelope.shp")

    # Engine stub directory
    bin_dir = content_dir / "delft3d_bin" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dflowfm_bin = bin_dir / "dflowfm"
    dflowfm_bin.write_text("#!/bin/sh\nexit 0\n")

    ns = {
        "__name__": "__main__",
    }

    executed_cells = 0
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue

        src = "".join(cell["source"])
        first_line = cell["source"][0].strip() if cell["source"] else f"Cell {i}"
        try:
            exec(src, ns)
            executed_cells += 1
        except Exception as e:
            pytest.fail(f"Cell {i} ({first_line}) failed with {type(e).__name__}: {e}")

    assert executed_cells >= 10, f"Expected at least 10 code cells, executed {executed_cells}"
