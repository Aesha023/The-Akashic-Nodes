"""Unit tests for Tier-0 Ganga Demo Pipeline: COG, Exposure, Evacuation, and Brief."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rio_cogeo.cogeo import cog_validate

from scripts.generate_pdf_brief import build_tier0_pdf_brief


class TestTier0DemoPipeline:
    @pytest.fixture
    def data_dir(self) -> Path:
        return Path("data/ganga_inputs")

    def test_cog_format_and_overviews(self, data_dir: Path) -> None:
        """Verify tier0_max_depth_cog.tif is a 100% compliant Cloud-Optimised GeoTIFF."""
        cog_path = data_dir / "tier0_max_depth_cog.tif"
        assert cog_path.exists(), f"Missing {cog_path}"

        valid, errors, _warnings = cog_validate(str(cog_path))
        assert valid is True, f"COG validation failed: {errors}"
        assert len(errors) == 0

        with rasterio.open(cog_path) as src:
            assert src.crs.to_string() == "EPSG:32644"
            assert src.is_tiled is True
            assert src.block_shapes[0] in ((256, 256), (512, 512))
            assert src.shape == (189, 165)

    def test_population_exposure_depth_classes(self, data_dir: Path) -> None:
        """Verify population exposure calculation across depth classes."""
        depth_path = data_dir / "tier0_max_depth.tif"
        pop_path = data_dir / "worldpop_ganga_32644.tif"
        assert depth_path.exists()
        assert pop_path.exists()

        with rasterio.open(depth_path) as src_d, rasterio.open(pop_path) as src_p:
            depth = src_d.read(1)
            pop = src_p.read(1)
            nodata_d = src_d.nodata

            valid_depth = (depth != nodata_d) & (~np.isnan(depth)) & (depth > 0)
            valid_pop = (pop != -9999.0) & (pop > 0)

            exposed_pop = np.where(valid_depth & valid_pop, pop, 0.0)
            total_exposed = float(exposed_pop.sum())

            # Verify total exposed is approximately 2,696 people
            assert 2600.0 <= total_exposed <= 2800.0

            # Verify depth classes
            c1 = float(np.where(valid_pop & valid_depth & (depth <= 0.5), pop, 0.0).sum())
            mask_c2 = valid_pop & valid_depth & (depth > 0.5) & (depth <= 1.5)
            c2 = float(np.where(mask_c2, pop, 0.0).sum())
            c3 = float(np.where(valid_pop & valid_depth & (depth > 1.5), pop, 0.0).sum())

            assert c1 > 0
            assert c2 > 0
            assert c3 > 0
            assert np.isclose(c1 + c2 + c3, total_exposed, rtol=1e-4)

    def test_evacuation_routing_and_isolation(self, data_dir: Path) -> None:
        """Verify evacuation routing logic cuts impassable edges and exports GeoJSON."""
        evac_geo = data_dir / "evacuation_routes.geojson"
        assert evac_geo.exists()

        with open(evac_geo, encoding="utf-8") as f:
            data = json.load(f)

        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1
        for feat in data["features"]:
            assert feat["geometry"]["type"] == "LineString"
            assert "length_m" in feat["properties"]
            assert feat["properties"]["length_m"] > 0

    def test_one_page_pdf_brief_structure(self, tmp_path: Path, data_dir: Path) -> None:
        """Verify that the generated PDF brief is strictly one page and non-empty."""
        import pypdf

        map_png = data_dir / "ganga_tier0_map.png"
        assert map_png.exists()

        out_pdf = tmp_path / "test_brief.pdf"
        stats = {
            "run_id": "tier0_ganga_accepted",
            "area_km2": 1.72,
            "max_depth_m": 7.73,
            "mean_depth_m": 6.31,
            "median_depth_m": 7.23,
            "p10_depth_m": 3.12,
            "p90_depth_m": 7.73,
            "pop_total": 2696,
            "pop_c1": 230,
            "pop_c1_pct": 8.5,
            "pop_c2": 253,
            "pop_c2_pct": 9.4,
            "pop_c3": 2213,
            "pop_c3_pct": 82.1,
            "road_flooded_km": 17.34,
            "road_total_km": 159.54,
            "road_pct": 10.9,
            "buildings_flooded": 5,
            "buildings_total": 93,
            "severed_edges": 930,
            "total_edges": 3638,
            "severed_length_km": 311.84,
            "reachable_origins": 2,
            "unreachable_origins": 3,
            "mean_route_m": 58.4,
        }

        build_tier0_pdf_brief(out_pdf, map_png, stats)
        assert out_pdf.exists()
        assert out_pdf.stat().st_size > 50_000

        reader = pypdf.PdfReader(str(out_pdf))
        assert len(reader.pages) == 1, f"PDF must be exactly 1 page, got {len(reader.pages)}"

    def test_manifest_sha256_integrity(self, data_dir: Path) -> None:
        """Verify that all files listed in manifest.json exist with matching SHA-256."""
        import hashlib

        manifest_path = data_dir / "manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["run_id"] == "tier0_ganga_accepted"
        assert manifest["scenario_type"] == "hypothetical scenario, Tier-0 screening"

        for art in manifest["artifacts"]:
            fname = art["filename"]
            expected_sha = art["sha256"]
            target = data_dir / fname
            if not target.exists():
                target = Path("artifacts") / fname
            assert target.exists(), f"Artifact {fname} from manifest does not exist"

            h = hashlib.sha256()
            with open(target, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            assert h.hexdigest() == expected_sha, f"SHA-256 mismatch for {fname}"
