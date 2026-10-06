"""Tests for the Tier 0 engine adapter and exports."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import rasterio

from pravahx.engines.base import RunContext
from pravahx.engines.tier0_hand.adapter import Tier0HandAdapter
from pravahx.export.vector import generate_exports

if TYPE_CHECKING:
    from pathlib import Path


def _create_dummy_hand(path: Path) -> None:
    """Create a dummy HAND raster for testing."""
    meta = {
        "driver": "GTiff",
        "height": 10,
        "width": 10,
        "count": 1,
        "dtype": rasterio.float32,
        "nodata": -9999.0,
        "transform": rasterio.transform.from_origin(0, 10, 1, 1),
        "crs": "EPSG:32644",
    }
    # V-shaped valley
    hand = np.zeros((10, 10), dtype=np.float32)
    for i in range(10):
        hand[:, i] = abs(i - 5) * 1.5

    with rasterio.open(path, "w", **meta) as dest:
        dest.write(hand, 1)


class TestTier0HandAdapter:
    def test_tier0_lifecycle(self, tmp_path: Path) -> None:
        """Test prepare, run, and postprocess for Tier 0."""
        hand_path = tmp_path / "hand.tif"
        _create_dummy_hand(hand_path)

        ctx = RunContext(
            run_id="r1",
            config=None,  # type: ignore
            work_dir=tmp_path,
            terrain_dir=tmp_path,
            breach_hydrograph_path=tmp_path / "breach.csv",
        )

        engine = Tier0HandAdapter()

        # Prepare
        prepared = engine.prepare(ctx)
        assert "hand.tif" in prepared.input_file_hashes

        # Run
        # Uses default placeholder peak discharge of 5000.0, will inundate everything.
        result = engine.run(prepared)
        assert result.status == "success"

        out_depth = result.output_dir / "tier0_max_depth.tif"
        assert out_depth.exists()

        # Postprocess
        norm = engine.postprocess(result, ctx)
        assert len(norm.layers) == 1
        assert norm.layers[0].name == "max_depth"

        # Test exports
        exports_dir = tmp_path / "exports"
        exported = generate_exports(norm, exports_dir)

        names = [p.name for p in exported]
        assert "tier0_envelope.tif" in names
        assert "tier0_envelope.shp" in names
        assert "tier0_envelope.kml" in names

        # Verify KML is filled and semi-transparent
        kml_content = (exports_dir / "tier0_envelope.kml").read_text(encoding="utf-8")
        assert "<fill>1</fill>" in kml_content
        assert "<PolyStyle>" in kml_content

    def test_main_channel_cells_inside_envelope(self, tmp_path: Path) -> None:
        """Every reach stream cell (HAND == 0) must be inside the inundation envelope."""
        hand_path = tmp_path / "hand.tif"
        _create_dummy_hand(hand_path)

        ctx = RunContext(
            run_id="r_stream_check",
            config=None,  # type: ignore
            work_dir=tmp_path,
            terrain_dir=tmp_path,
            breach_hydrograph_path=None,
        )

        engine = Tier0HandAdapter()
        prepared = engine.prepare(ctx)
        result = engine.run(prepared)
        assert result.status == "success"

        depth_path = result.output_dir / "tier0_max_depth.tif"
        with rasterio.open(hand_path) as h_src, rasterio.open(depth_path) as d_src:
            hand = h_src.read(1)
            depth = d_src.read(1)
            nodata = d_src.nodata

        # Stream cells are where hand == 0
        stream_mask = hand == 0.0
        assert np.any(stream_mask), "Synthetic HAND must have stream cells"

        # Every stream cell must have positive depth and not be nodata
        valid_depth = (depth > 0) & (depth != nodata)
        missing_stream_cells = stream_mask & (~valid_depth)
        assert not np.any(missing_stream_cells), (
            f"Found {np.sum(missing_stream_cells)} stream cells missing from envelope!"
        )

    def test_envelope_spatially_connected_to_channel(self, tmp_path: Path) -> None:
        """Envelope must be spatially contiguous with channel with no isolated hillside patches."""
        import geopandas as gpd
        from shapely.geometry import LineString

        from pravahx.export.vector import _vectorise_raster

        hand_path = tmp_path / "hand.tif"
        _create_dummy_hand(hand_path)

        ctx = RunContext(
            run_id="r_connect_check",
            config=None,  # type: ignore
            work_dir=tmp_path,
            terrain_dir=tmp_path,
            breach_hydrograph_path=None,
        )

        engine = Tier0HandAdapter()
        prepared = engine.prepare(ctx)
        result = engine.run(prepared)

        depth_path = result.output_dir / "tier0_max_depth.tif"
        gdf_env = _vectorise_raster(depth_path, threshold=0.1)

        # Stream channel line along x=5 (from _create_dummy_hand)
        # Dummy hand transform: from_origin(0, 10, 1, 1). x=5 is at X=5.5
        stream_line = LineString([(5.5, 0.5), (5.5, 9.5)])
        gdf_stream = gpd.GeoDataFrame({"geometry": [stream_line]}, crs=gdf_env.crs)

        # All envelope polygons must intersect the stream line
        stream_geom = gdf_stream.geometry.iloc[0]
        for geom in gdf_env.geometry:
            assert geom.intersects(stream_geom), "Inundation patch is detached from stream channel!"
