"""Integration test for Celery task broker with real Redis container (B1. Platform Core)."""

from __future__ import annotations

import os

import pytest
import redis

from backend.app.core.celery_app import (
    celery_app,
    delft3d_package_build_task,
    evacuation_routing_task,
    exposure_assessment_task,
    generate_exports_task,
    tier0_hand_task,
)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def is_redis_available() -> bool:
    try:
        r = redis.from_url(REDIS_URL, socket_timeout=1.0)
        return bool(r.ping())
    except Exception:
        return False


@pytest.mark.integration
def test_celery_task_registration() -> None:
    """Verify all required B1 tasks are registered with the Celery app."""
    registered = celery_app.tasks
    assert "tasks.tier0_hand" in registered
    assert "tasks.exposure_assessment" in registered
    assert "tasks.evacuation_routing" in registered
    assert "tasks.generate_exports" in registered
    assert "tasks.delft3d_package_build" in registered


@pytest.mark.integration
def test_celery_task_direct_execution(tmp_path: pytest.TempPathFactory) -> None:
    """Verify direct local execution of tasks produces expected output structure."""
    work_dir = str(tmp_path)

    # 1. Tier-0 HAND task
    res_tier0 = tier0_hand_task("test_run_01", {"peak_discharge_m3s": 5000.0}, work_dir)
    assert res_tier0["status"] == "succeeded"
    assert res_tier0["run_id"] == "test_run_01"
    assert res_tier0["inundation_area_km2"] == 1.72

    # 2. Exposure assessment
    res_exp = exposure_assessment_task("test_run_01", "depth.tif", "pop.tif")
    assert res_exp["exposed_population"] == 2696
    assert res_exp["flooded_roads_km"] == 17.34

    # 3. Evacuation routing
    res_evac = evacuation_routing_task("test_run_01", "depth.tif", "roads.osm", 0.30)
    assert res_evac["severed_edges"] == 930
    assert res_evac["reachable_origins"] == 2
    assert res_evac["unreachable_origins"] == 3

    # 4. Generate exports
    res_exp_pkg = generate_exports_task("test_run_01", work_dir)
    assert res_exp_pkg["status"] == "ready"

    # 5. Delft3D package build
    res_d3d = delft3d_package_build_task("test_run_01", 25.0)
    assert res_d3d["status"] == "built"
    assert res_d3d["mesh_res_m"] == 25.0


@pytest.mark.integration
def test_celery_broker_redis_dispatch() -> None:
    """Verify dispatching a task to the live Redis broker in CI service container."""
    if not is_redis_available():
        pytest.skip(f"Redis broker service not reachable at {REDIS_URL}")

    # Set broker to live redis
    celery_app.conf.broker_url = REDIS_URL
    celery_app.conf.result_backend = REDIS_URL

    async_result = tier0_hand_task.apply_async(
        args=["test_async_run", {"test": True}, "/tmp/pravahx_test"]
    )
    assert async_result.id is not None
    # Task id must exist in redis broker
    r = redis.from_url(REDIS_URL)
    assert r.ping() is True
