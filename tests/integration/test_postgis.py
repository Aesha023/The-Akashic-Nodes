"""Integration test for PostGIS database service container (B1. Platform Core)."""

from __future__ import annotations

import os

import pytest
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_Contains, ST_DWithin
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from backend.app.models.asset import CriticalAsset
from backend.app.models.base import Base
from backend.app.models.run import Run
from backend.app.models.scenario import Scenario

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "pravahx_test")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "pravahx_test")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "test_password")

SYNC_PG_URL = (
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def is_postgres_available() -> bool:
    try:
        engine = create_engine(SYNC_PG_URL, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return True
    except Exception:
        return False


@pytest.mark.integration
def test_postgis_spatial_columns_and_queries() -> None:
    """Verify PostGIS geometry columns, spatial indexes, and spatial query execution."""
    if not is_postgres_available():
        pytest.skip(f"PostGIS database container not reachable at {POSTGRES_HOST}:{POSTGRES_PORT}")

    engine = create_engine(SYNC_PG_URL)

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

        # Check postgis version
        result = conn.execute(text("SELECT postgis_full_version();")).scalar()
        assert result is not None
        assert "POSTGIS" in result

    # Create schema tables
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Create a Scenario with AOI geometry
        scenario = Scenario(
            id="scen_postgis_test_01",
            name="Ganga Gorge Test Scenario",
            scenario_type="tier0_screening",
            config_json="{}",
            aoi_geom=WKTElement(
                "POLYGON((78.30 30.10, 78.35 30.10, 78.35 30.15, 78.30 30.15, 78.30 30.10))",
                srid=4326,
            ),
        )
        session.merge(scenario)

        # 2. Create a Run with envelope geometry and validity flag
        run = Run(
            id="run_postgis_test_01",
            scenario_id="scen_postgis_test_01",
            status="succeeded",
            progress_percent=100.0,
            current_stage="completed",
            work_dir="/tmp/test_run",
            is_valid=True,
            envelope_geom=WKTElement(
                "POLYGON((78.31 30.11, 78.34 30.11, 78.34 30.14, 78.31 30.14, 78.31 30.11))",
                srid=4326,
            ),
        )
        session.merge(run)

        # 3. Create Critical Assets (one inside envelope, one outside)
        asset_inside = CriticalAsset(
            id="asset_hospital_01",
            name="Brahmpuri Community Health Centre",
            asset_type="hospital",
            depth_threshold_m=0.30,
            geom=WKTElement("POINT(78.32 30.12)", srid=4326),
        )
        asset_outside = CriticalAsset(
            id="asset_school_02",
            name="Rishikesh Public School",
            asset_type="school",
            depth_threshold_m=0.50,
            geom=WKTElement("POINT(78.45 30.25)", srid=4326),
        )
        session.merge(asset_inside)
        session.merge(asset_outside)
        session.commit()

        # 4. Perform PostGIS spatial query: ST_Intersects / ST_Contains
        stmt = (
            select(CriticalAsset.name)
            .join(Run, Run.id == "run_postgis_test_01")
            .where(ST_Contains(Run.envelope_geom, CriticalAsset.geom))
        )
        intersecting_assets = session.execute(stmt).scalars().all()

        assert "Brahmpuri Community Health Centre" in intersecting_assets
        assert "Rishikesh Public School" not in intersecting_assets

        # 5. Perform distance query with ST_DWithin
        point_probe = WKTElement("POINT(78.32 30.12)", srid=4326)
        stmt_dist = select(CriticalAsset.name).where(
            ST_DWithin(CriticalAsset.geom, point_probe, 0.01)
        )
        near_assets = session.execute(stmt_dist).scalars().all()
        assert "Brahmpuri Community Health Centre" in near_assets
