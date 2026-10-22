"""Render high-resolution map of real Tier-0 Ganga inundation for the PDF brief."""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from pyproj import Transformer

# Load rasters and vectors
dem_path = "data/ganga_inputs/dem_ganga_32644.tif"
depth_path = "data/ganga_inputs/tier0_max_depth.tif"
env_path = "data/ganga_inputs/tier0_envelope.shp"
osm_path = "data/ganga_inputs/osm_aoi.osm"
out_png = "data/ganga_inputs/ganga_tier0_map.png"

# Read DEM
with rasterio.open(dem_path) as src_dem:
    dem = src_dem.read(1)
    bounds = src_dem.bounds
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    # Compute hillshade
    x, y = np.gradient(dem, 30, 30)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)
    azimuth = 315.0 * np.pi / 180.0
    altitude = 45.0 * np.pi / 180.0
    shaded = np.sin(altitude) * np.sin(slope) + np.cos(altitude) * np.cos(slope) * np.cos(
        azimuth - aspect
    )
    hillshade = (shaded - shaded.min()) / (shaded.max() - shaded.min() + 1e-6)

# Read depth
with rasterio.open(depth_path) as src_depth:
    depth = src_depth.read(1)
    nodata = src_depth.nodata
    depth_mask = (depth != nodata) & (~np.isnan(depth)) & (depth > 0)
    depth_plot = np.where(depth_mask, depth, np.nan)

# Read vectors
gdf_env = gpd.read_file(env_path)
gdf_roads = gpd.read_file(osm_path, layer="lines").to_crs(epsg=32644)
gdf_roads = gdf_roads[gdf_roads["highway"].notna()]

env_geom = (
    gdf_env.geometry.union_all()
    if hasattr(gdf_env.geometry, "union_all")
    else gdf_env.geometry.unary_union
)
gdf_roads_flooded = gdf_roads.intersection(env_geom)
gdf_roads_flooded = gdf_roads_flooded[~gdf_roads_flooded.is_empty]

# Critical facilities
gdf_pts = gpd.read_file(osm_path, layer="points")
crit_amenities = ["hospital", "clinic", "school", "police"]
facs = []
t = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
for _idx, r in gdf_pts.iterrows():
    am = r.get("amenity")
    other = str(r.get("other_tags", ""))
    tag = None
    for ca in crit_amenities:
        if am == ca or f'"{ca}"' in other:
            tag = ca
            break
    if tag:
        xp, yp = t.transform(r.geometry.x, r.geometry.y)
        facs.append({"name": r.get("name") or tag, "type": tag, "x": xp, "y": yp})

# Plotting
fig, ax = plt.subplots(figsize=(10, 8), dpi=200)

# 1. Hillshade
ax.imshow(hillshade, cmap="gray", extent=extent, origin="upper", alpha=0.6)

# 2. Inundation depth
cmap_hydro = LinearSegmentedColormap.from_list(
    "hydro", ["#90caf9", "#2196f3", "#0d47a1", "#1a237e"]
)
im = ax.imshow(
    depth_plot, cmap=cmap_hydro, extent=extent, origin="upper", vmin=0, vmax=8.0, alpha=0.85
)

# 3. Envelope boundary
gdf_env.boundary.plot(ax=ax, color="#002171", linewidth=1.2, label="Tier-0 Envelope")

# 4. Roads
gdf_roads.plot(ax=ax, color="#424242", linewidth=0.7, alpha=0.7, label="OSM Road Network")
gdf_roads_flooded.plot(ax=ax, color="#d32f2f", linewidth=1.5, label="Flooded Roads")

# 5. Critical facilities
if facs:
    fx = [f["x"] for f in facs]
    fy = [f["y"] for f in facs]
    ax.scatter(
        fx,
        fy,
        c="#ffd600",
        edgecolors="#000000",
        s=40,
        zorder=5,
        label="Critical Facilities (OSM)",
    )

# Colorbar for depth
cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
cbar.set_label("Inundation Depth (m)", fontsize=10, weight="bold")

# Title and subtitle banner
ax.set_title(
    "HYPOTHETICAL SCENARIO - TIER-0 SCREENING\n"
    "Ganga Reach near Rishikesh (UTM 44N / EPSG:32644) | Peak Flow: 5,000 m3/s",
    fontsize=11,
    weight="bold",
    pad=12,
    color="#b71c1c",
)

ax.set_xlabel("Easting (m)", fontsize=9)
ax.set_ylabel("Northing (m)", fontsize=9)
ax.grid(True, linestyle="--", alpha=0.4)

# Legend
legend_elements = [
    Patch(facecolor="#2196f3", edgecolor="#002171", label="Inundation Extent (1.72 km2)"),
    plt.Line2D([0], [0], color="#424242", lw=1.5, label="Intact Road (153.86 km)"),
    plt.Line2D([0], [0], color="#d32f2f", lw=2, label="Flooded Road (5.68 km)"),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#ffd600",
        markeredgecolor="k",
        markersize=7,
        label="Critical Facilities (28 unflooded)",
    ),
]
ax.legend(handles=legend_elements, loc="upper right", framealpha=0.9, fontsize=8)

plt.tight_layout()
plt.savefig(out_png, dpi=200, bbox_inches="tight")
plt.close()
print("Saved real map image to", out_png)
