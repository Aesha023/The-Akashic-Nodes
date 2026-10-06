"""Phase 1 acceptance test script.

Downloads a small DEM patch, computes HAND, generates a Tier 0 envelope,
and exports it to Shapefile, KML, and COG.
"""

import logging
import time
from pathlib import Path

from pravahx.data.dem import fetch_dem
from pravahx.engines.base import RunContext
from pravahx.engines.tier0_hand.adapter import Tier0HandAdapter
from pravahx.export.vector import export_diagnostic_bundle, generate_exports
from pravahx.terrain.hand import compute_hand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    work_dir = Path("test_phase1_output")
    work_dir.mkdir(exist_ok=True)

    # Bounding box for a small reach in India (e.g., somewhere in the Himalayas)
    # Coordinates: min_lon, min_lat, max_lon, max_lat
    # Example: Near Rishikesh, India
    bbox = (78.3, 30.1, 78.35, 30.15)

    start = time.time()

    # 1. Fetch DEM and reproject to metric UTM Zone 44N (EPSG:32644)
    dem_path = fetch_dem(bbox=bbox, cache_dir=work_dir, target_crs="EPSG:32644")

    # 2. Compute HAND
    # With pntr=True, flow accumulation runs properly and max accum is ~27,800.
    # A threshold of 500 cleanly extracts the Ganga main channel and primary tributaries.
    compute_hand(
        dem_path=dem_path,
        out_dir=work_dir,
        accumulation_threshold=500,
    )

    # 3. Tier 0 Engine run
    ctx = RunContext(
        run_id="phase1_test",
        config=None,  # type: ignore
        work_dir=work_dir,
        terrain_dir=work_dir,
        breach_hydrograph_path=None,
    )

    engine = Tier0HandAdapter()
    prepared = engine.prepare(ctx)
    result = engine.run(prepared)
    norm_output = engine.postprocess(result, ctx)

    # 4. Standard exports (COG, Shapefile, filled semi-transparent KML)
    exports_dir = work_dir / "exports"
    exported = generate_exports(norm_output, exports_dir)

    # 5. Diagnostic exports (raw DEM, conditioned DEM, flow accum, stream lines, HAND)
    diagnostic_files = export_diagnostic_bundle(work_dir, exports_dir)
    exported.extend(diagnostic_files)

    total_time = time.time() - start

    logger.info("--- Phase 1 Test Complete ---")
    logger.info(f"Total time: {total_time:.1f} seconds")
    logger.info("Generated exports:")
    for path in exported:
        logger.info(f"  - {path}")


if __name__ == "__main__":
    main()
