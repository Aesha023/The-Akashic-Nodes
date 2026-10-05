"""Tests for the Tier 0 engine adapter and exports."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio

from pravahx.engines.base import RunContext, compute_file_hash, NormalisedOutput, NormalisedLayer
from pravahx.engines.tier0_hand.adapter import Tier0HandAdapter
from pravahx.export.vector import generate_exports


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
            scenario_id="s1",
            config=None, # type: ignore
            work_dir=tmp_path,
        )
        
        engine = Tier0HandAdapter()
        
        # Prepare
        prepared = engine.prepare(ctx)
        assert "hand.tif" in prepared.input_hashes
        
        # Run
        # Uses default placeholder peak discharge of 5000.0, will inundate everything.
        result = engine.run(prepared)
        assert result.success is True
        
        out_depth = result.output_dir / "tier0_max_depth.tif"
        assert out_depth.exists()
        
        # Postprocess
        norm = engine.postprocess(result)
        assert len(norm.layers) == 1
        assert norm.layers[0].name == "max_depth"
        
        # Test exports
        exports_dir = tmp_path / "exports"
        exported = generate_exports(norm, exports_dir)
        
        names = [p.name for p in exported]
        assert "tier0_envelope.tif" in names
        assert "tier0_envelope.shp" in names
        assert "tier0_envelope.kml" in names
