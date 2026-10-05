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
from pravahx.export.vector import generate_exports
from pravahx.terrain.hand import compute_hand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    work_dir = Path("test_phase1_output")
    work_dir.mkdir(exist_ok=True)

    # Bounding box for a small reach in India (e.g., somewhere in the Himalayas)
    # Just a small patch to make the download and processing fast.
    # Coordinates: min_lon, min_lat, max_lon, max_lat
    # Example: Near Rishikesh, India
    bbox = (78.3, 30.1, 78.35, 30.15)

    start = time.time()

    # 1. Fetch DEM
    dem_path = fetch_dem(bbox=bbox, cache_dir=work_dir)

    # 2. Compute HAND
    compute_hand(
        dem_path=dem_path,
        out_dir=work_dir,
        accumulation_threshold=10,  # Smaller threshold for a small patch
    )

    # 3. Tier 0 Engine run
    ctx = RunContext(
        run_id="phase1_test",
        scenario_id="scen_1",
        config=None,  # type: ignore
        work_dir=work_dir,
    )

    engine = Tier0HandAdapter()
    prepared = engine.prepare(ctx)
    result = engine.run(prepared)
    norm_output = engine.postprocess(result)

    # 4. Export
    exports_dir = work_dir / "exports"
    exported = generate_exports(norm_output, exports_dir)

    total_time = time.time() - start

    logger.info("--- Phase 1 Test Complete ---")
    logger.info(f"Total time: {total_time:.1f} seconds")
    logger.info("Generated exports:")
    for path in exported:
        logger.info(f"  - {path}")


if __name__ == "__main__":
    main()
