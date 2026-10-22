"""Package all Tier-0 Ganga demo exports with SHA-256 manifest."""

import hashlib
import json
from pathlib import Path

export_dir = Path("data/ganga_inputs")
artifacts_dir = Path("artifacts")
artifacts_dir.mkdir(parents=True, exist_ok=True)

files_to_index = [
    ("tier0_max_depth_cog.tif", "Cloud-Optimised GeoTIFF (EPSG:32644) of maximum inundation depth"),
    ("tier0_max_depth.tif", "Standard GeoTIFF (EPSG:32644) of maximum inundation depth"),
    ("tier0_envelope.shp", "ESRI Shapefile of the 1.72 km² inundation envelope"),
    (
        "tier0_envelope.kml",
        "Keyhole Markup Language (KML) vector polygon with semi-transparent blue fill",
    ),
    ("tier0_envelope.geojson", "GeoJSON (EPSG:4326) polygon of the inundation envelope"),
    (
        "evacuation_routes.geojson",
        "GeoJSON (EPSG:4326) LineStrings of computed safe evacuation routes",
    ),
    (
        "worldpop_ganga_32644.tif",
        "Clipped WorldPop 2020 100m population raster for 5x5 km AOI (EPSG:32644)",
    ),
]

manifest_entries = []

for fname, desc in files_to_index:
    fpath = export_dir / fname
    if not fpath.exists():
        print(f"Warning: {fpath} does not exist!")
        continue

    h = hashlib.sha256()
    with open(fpath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    sha256_hash = h.hexdigest()
    size_bytes = fpath.stat().st_size

    manifest_entries.append(
        {
            "filename": fname,
            "format": fpath.suffix.lstrip(".").upper(),
            "size_bytes": size_bytes,
            "sha256": sha256_hash,
            "description": desc,
        }
    )

# Also include the PDF brief if it exists in artifacts
pdf_brief = artifacts_dir / "ganga_tier0_brief.pdf"
if pdf_brief.exists():
    h = hashlib.sha256()
    with open(pdf_brief, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    manifest_entries.append(
        {
            "filename": pdf_brief.name,
            "format": "PDF",
            "size_bytes": pdf_brief.stat().st_size,
            "sha256": h.hexdigest(),
            "description": "Official 1-page PDF executive disaster impact & evacuation brief",
        }
    )

manifest_doc = {
    "run_id": "tier0_ganga_accepted",
    "scenario_name": "Ganga Reach near Rishikesh Tier-0 Screening",
    "scenario_type": "hypothetical scenario, Tier-0 screening",
    "engine": "Tier-0 HAND (Height Above Nearest Drainage)",
    "crs": "EPSG:32644",
    "peak_flow_m3_s": 5000.0,
    "manning_n": 0.035,
    "inundation_area_km2": 1.72,
    "max_depth_m": 7.73,
    "provenance": {
        "dem": "Copernicus GLO-30 (30 m)",
        "population": "WorldPop 2020 Constrained (BSGM IND) 100 m",
        "population_raw_url": "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/IND/ind_ppp_2020_UNadj_constrained.tif",
        "population_raw_sha256": "4fc54bcefe4e23c5f0638f775288375297091d5719d355d85f0820efe9199dbc",
        "infrastructure": "OpenStreetMap contributors (ODbL 1.0)",
        "osm_snapshot_date": "2026-10-22T12:26:58Z",
    },
    "artifacts": manifest_entries,
}

with open(export_dir / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_doc, f, indent=2)

with open(artifacts_dir / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_doc, f, indent=2)

print("Manifest generated successfully with", len(manifest_entries), "artifacts:")
for item in manifest_entries:
    print(
        f"  - {item['filename']} ({item['format']}, {item['size_bytes']:,} bytes): {item['sha256']}"
    )
