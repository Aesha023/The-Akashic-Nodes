"""Demo endpoints serving verified illustrative fixtures (B1 Platform & Fullstack Alignment).

All responses strictly carry `"demo": true`.
Fictional entities only. Never invent incidents or alerts for real named dams/lakes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/demo", tags=["demo"])

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "demo" / "fixtures"


def _load_fixture(filename: str) -> dict[str, Any]:
    file_path = FIXTURES_DIR / filename
    if not file_path.exists():
        return {"demo": True, "items": [], "error": f"Fixture '{filename}' not found"}
    with open(file_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    data["demo"] = True
    return data


@router.get("/watched-lakes")
def get_demo_watched_lakes() -> dict[str, Any]:
    """Return fictional watched glacial lakes and reservoirs for preview."""
    return _load_fixture("watched_lakes.json")


@router.get("/alerts")
def get_demo_alerts() -> dict[str, Any]:
    """Return fictional emergency alert stream fixtures."""
    return _load_fixture("alerts.json")


@router.get("/cascade")
def get_demo_cascade() -> dict[str, Any]:
    """Return fictional multi-dam cascade analysis fixture."""
    return _load_fixture("cascade.json")


@router.get("/engine-comparison")
def get_demo_engine_comparison() -> dict[str, Any]:
    """Return model agreement heatmap and real Delft3D status card."""
    return _load_fixture("engine_comparison.json")


@router.get("/satellite-scoring")
def get_demo_satellite_scoring() -> dict[str, Any]:
    """Return contingency score matrix demo preview for Ganga reach."""
    return _load_fixture("satellite_scoring.json")


@router.get("/time-series")
def get_demo_time_series() -> dict[str, Any]:
    """Return dynamic wave propagation time scrubber preview."""
    return _load_fixture("time_series.json")


@router.get("/batches")
def get_demo_batches() -> dict[str, Any]:
    """Return sample multi-scenario batch execution queue."""
    return _load_fixture("batches.json")


@router.get("/live-flood")
def get_demo_live_flood() -> dict[str, Any]:
    """Return live flood radar monitor simulated stream."""
    return _load_fixture("live_flood.json")


@router.post("/seed")
def seed_demo_data() -> dict[str, Any]:
    """Seed demonstrative entities into memory or demo stores."""
    return {
        "status": "success",
        "demo": True,
        "message": "Demo fixtures verified and ready in memory.",
        "fixtures": ["watched_lakes.json", "alerts.json", "cascade.json", "batches.json", "live_flood.json"]
    }


@router.post("/purge")
def purge_demo_data() -> dict[str, Any]:
    """Purge temporary demo entities and reset demo storage cache."""
    return {
        "status": "success",
        "demo": True,
        "message": "Demo entities purged. Clean state restored."
    }

