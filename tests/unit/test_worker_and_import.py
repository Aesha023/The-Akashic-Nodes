"""Unit tests for run importer and worker adapter API (Item 14)."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from core.pravahx.importer.run_importer import calculate_sha256, import_run


def test_calculate_sha256(tmp_path: Path) -> None:
    test_file = tmp_path / "sample.txt"
    test_file.write_text("pravahx integrity test content", encoding="utf-8")
    h = calculate_sha256(test_file)
    assert len(h) == 64
    assert h == calculate_sha256(test_file)


def test_import_run_delft3d(tmp_path: Path) -> None:
    run_dir = tmp_path / "delft3d_test_run"
    run_dir.mkdir(parents=True)
    mdu = run_dir / "flow2d3d.mdu"
    mdu.write_text("[geometry]\nNetFile=mesh.nc\n", encoding="utf-8")

    manifest = import_run(engine="delft3d", folder_path=run_dir, run_id="test_delft3d_01")
    assert manifest["engine"] == "delft3d"
    assert manifest["run_id"] == "test_delft3d_01"
    assert manifest["status"] == "completed"
    assert len(manifest["artifacts"]) == 1
    assert manifest["artifacts"][0]["name"] == "flow2d3d.mdu"


@pytest.mark.asyncio
async def test_worker_adapter_api() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Status query
        res = await client.get("/api/v1/workers/status")
        assert res.status_code == 200
        data = res.json()
        assert "queues" in data
        assert "counts" in data

        # 2. Register a Delft3D worker
        reg_payload = {
            "worker_id": "test-colab-worker-01",
            "engine": "delft3d",
            "hostname": "colab-gpu-instance-12",
            "capabilities": {"cores": 4, "ram_gb": 16},
        }
        res_reg = await client.post("/api/v1/workers/register", json=reg_payload)
        assert res_reg.status_code == 200
        assert res_reg.json()["status"] == "registered"

        # 3. Pull jobs
        res_pull = await client.get("/api/v1/workers/jobs/pull?engine=delft3d")
        assert res_pull.status_code == 200

        # 4. Stream progress
        prog_payload = {
            "progress_percent": 45.0,
            "stage": "2D SWE Hydrodynamic Computation",
            "log_line": "[00:15:30] Time step 1800s completed",
        }
        res_prog = await client.post(
            "/api/v1/workers/jobs/test_run_99/progress",
            json=prog_payload,
        )
        assert res_prog.status_code == 200
        assert res_prog.json()["status"] == "recorded"
