"""Unit tests for flood hazard classification, exposure, damage, and evacuation (Phase 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import rasterio
from affine import Affine

from pravahx.impact.brief import export_impact_brief
from pravahx.impact.damage import (
    agricultural_damage_factor,
    estimate_flood_damage,
    infrastructure_damage_factor,
    residential_damage_factor,
)
from pravahx.impact.evacuation import EvacuationShelter, plan_evacuation_routes
from pravahx.impact.exposure import (
    compute_asset_exposure,
    compute_village_exposure,
)
from pravahx.impact.hazard import (
    HazardClass,
    calculate_hazard_rating,
    classify_hazard,
    generate_hazard_raster,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def synthetic_impact_rasters(tmp_path: Path) -> dict[str, Path]:
    """Create small synthetic depth, velocity, and arrival time GeoTIFFs."""
    width, height = 20, 20
    transform = Affine.translation(500000.0, 3300000.0) @ Affine.scale(10.0, -10.0)
    crs = "EPSG:32644"

    depth_arr = np.zeros((height, width), dtype=np.float32)
    vel_arr = np.zeros((height, width), dtype=np.float32)
    arr_arr = np.full((height, width), 999.0, dtype=np.float32)

    # Inundate middle region
    depth_arr[5:15, 5:15] = 2.5
    vel_arr[5:15, 5:15] = 3.0
    arr_arr[5:15, 5:15] = 45.0  # 45 minutes arrival

    # Shallow edge
    depth_arr[3:5, 5:15] = 0.4
    vel_arr[3:5, 5:15] = 0.5
    arr_arr[3:5, 5:15] = 60.0

    depth_path = tmp_path / "max_depth.tif"
    vel_path = tmp_path / "max_velocity.tif"
    arr_path = tmp_path / "arrival_time.tif"

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": rasterio.float32,
        "crs": crs,
        "transform": transform,
        "nodata": -9999.0,
    }

    with rasterio.open(depth_path, "w", **profile) as dst:
        dst.write(depth_arr, 1)

    with rasterio.open(vel_path, "w", **profile) as dst:
        dst.write(vel_arr, 1)

    with rasterio.open(arr_path, "w", **profile) as dst:
        dst.write(arr_arr, 1)

    return {
        "depth": depth_path,
        "velocity": vel_path,
        "arrival": arr_path,
    }


def test_hazard_rating_and_classification() -> None:
    # Test zero depth
    hr_zero = calculate_hazard_rating(0.0, 0.0)
    assert hr_zero == 0.0
    assert classify_hazard(0.0, 0.0) == HazardClass.LOW

    # Shallow water: depth=0.2, vel=0.5 -> HR = 0.2*(0.5 + 0.5) + 0.5 = 0.2 + 0.5 = 0.70 -> LOW
    hr_shallow = calculate_hazard_rating(0.2, 0.5)
    assert pytest.approx(hr_shallow, abs=0.01) == 0.70
    assert classify_hazard(0.2, 0.5) == HazardClass.LOW

    # Moderate water: depth=0.5, vel=1.0 -> HR = 0.5*(1.0 + 0.5) + 1.0 = 1.75 -> HIGH
    hr_high = calculate_hazard_rating(0.5, 1.0)
    assert pytest.approx(hr_high, abs=0.01) == 1.75
    assert classify_hazard(0.5, 1.0) == HazardClass.HIGH

    # Deep water: depth=3.0, vel=2.0 -> HR = 3.0*(2.0 + 0.5) + 1.0 = 8.5 -> EXTREME
    hr_extreme = calculate_hazard_rating(3.0, 2.0)
    assert hr_extreme >= 2.0
    assert classify_hazard(3.0, 2.0) == HazardClass.EXTREME

    # Defra Table 3.1 Land Use tests:
    # Shallow water (0.2m, 0.5m/s):
    # Pasture: DF=0 -> HR = 0.2*(0.5+0.5) + 0 = 0.20
    assert pytest.approx(calculate_hazard_rating(0.2, 0.5, land_use="pasture"), abs=0.01) == 0.20
    # Woodland: DF=0 for d<=0.25 -> HR = 0.20
    assert pytest.approx(calculate_hazard_rating(0.2, 0.5, land_use="woodland"), abs=0.01) == 0.20
    # Woodland moderate depth (0.5m, 1.0m/s): DF=0.5 -> HR = 0.5*1.5 + 0.5 = 1.25
    assert pytest.approx(calculate_hazard_rating(0.5, 1.0, land_use="woodland"), abs=0.01) == 1.25
    # Urban moderate depth (0.5m, 1.0m/s): DF=1.0 -> HR = 0.5*1.5 + 1.0 = 1.75
    assert pytest.approx(calculate_hazard_rating(0.5, 1.0, land_use="urban"), abs=0.01) == 1.75

    # Array classification
    d_arr = np.array([0.0, 0.2, 0.5, 3.0])
    v_arr = np.array([0.0, 0.5, 1.0, 2.0])
    classes = classify_hazard(d_arr, v_arr)
    assert isinstance(classes, np.ndarray)
    assert list(classes) == [0, 1, 3, 4]


def test_hazard_raster_generation(
    synthetic_impact_rasters: dict[str, Path], tmp_path: Path
) -> None:
    out_hazard = tmp_path / "hazard_classified.tif"
    res = generate_hazard_raster(
        depth_raster_path=synthetic_impact_rasters["depth"],
        velocity_raster_path=synthetic_impact_rasters["velocity"],
        output_raster_path=out_hazard,
    )
    assert res.exists()
    with rasterio.open(res) as src:
        data = src.read(1)
        assert src.dtypes[0] == "uint8"
        # Check colormap exists
        cmap = src.colormap(1)
        assert 1 in cmap
        assert 4 in cmap
        # Middle should be extreme (class 4: depth=2.5, vel=3.0)
        assert data[10, 10] == 4


def test_village_and_asset_exposure(synthetic_impact_rasters: dict[str, Path]) -> None:
    # Coordinate of cell (10, 10): x = 500000 + 10.5*10 = 500105, y = 3300000 - 10.5*10 = 3299895
    villages_data: list[dict[str, Any]] = [
        {
            "name": "Devprayag Village",
            "district": "Tehri Garhwal",
            "population": 1200,
            "cropland_ha": 45.0,
            "x": 500100.0,
            "y": 3299900.0,
        },
        {
            "name": "Safe Hill Village",
            "district": "Pauri Garhwal",
            "population": 800,
            "cropland_ha": 30.0,
            "x": 500010.0,
            "y": 3299990.0,  # Dry corner (row 0, col 1)
        },
    ]

    assets_data: list[dict[str, Any]] = [
        {
            "name": "Primary Health Centre",
            "type": "Hospital",
            "x": 500100.0,
            "y": 3299900.0,
        }
    ]

    v_exp = compute_village_exposure(
        villages_data=villages_data,
        depth_raster_path=synthetic_impact_rasters["depth"],
        arrival_raster_path=synthetic_impact_rasters["arrival"],
        velocity_raster_path=synthetic_impact_rasters["velocity"],
    )

    assert len(v_exp) == 2
    devprayag = next(v for v in v_exp if v.village_name == "Devprayag Village")
    safe = next(v for v in v_exp if v.village_name == "Safe Hill Village")

    assert devprayag.is_inundated is True
    assert devprayag.max_depth_m == 2.5
    assert devprayag.arrival_time_min == 45.0
    assert devprayag.affected_population == 1200
    assert devprayag.inundated_cropland_ha == 45.0
    assert devprayag.hazard_class == "extreme"

    assert safe.is_inundated is False
    assert safe.affected_population == 0

    a_exp = compute_asset_exposure(
        assets_data=assets_data,
        depth_raster_path=synthetic_impact_rasters["depth"],
        arrival_raster_path=synthetic_impact_rasters["arrival"],
        velocity_raster_path=synthetic_impact_rasters["velocity"],
    )
    assert len(a_exp) == 1
    assert a_exp[0].is_inundated is True
    assert a_exp[0].hazard_class == "extreme"


def test_damage_estimation() -> None:
    assert residential_damage_factor(0.0) == 0.0
    assert residential_damage_factor(0.5) == 0.30
    assert residential_damage_factor(3.5) == 1.00

    assert agricultural_damage_factor(0.0) == 0.0
    assert agricultural_damage_factor(0.2) == 0.40
    assert agricultural_damage_factor(1.5) == 1.00

    assert infrastructure_damage_factor(0.0) == 0.0
    assert infrastructure_damage_factor(0.4) == 0.25

    from pravahx.impact.exposure import CriticalAssetExposure, VillageExposure

    v_list = [
        VillageExposure(
            village_name="Flooded Hamlet",
            district="Uttarkashi",
            population=450,
            cropland_ha=20.0,
            is_inundated=True,
            max_depth_m=1.0,  # 50% res, 100% agri
            arrival_time_min=30.0,
            hazard_class="high",
            affected_population=450,
            inundated_cropland_ha=20.0,
        )
    ]

    a_list = [
        CriticalAssetExposure(
            asset_name="District Substation",
            asset_type="Substation",
            is_inundated=True,
            max_depth_m=1.0,  # 60% infra
            arrival_time_min=30.0,
            hazard_class="high",
        )
    ]

    dmg = estimate_flood_damage(village_exposures=v_list, asset_exposures=a_list)
    assert dmg.total_residential_loss_inr > 0
    assert dmg.total_agricultural_loss_inr > 0
    assert dmg.total_infrastructure_loss_inr > 0
    assert dmg.grand_total_loss_inr == pytest.approx(
        dmg.total_residential_loss_inr
        + dmg.total_agricultural_loss_inr
        + dmg.total_infrastructure_loss_inr
    )


def test_evacuation_routing() -> None:
    from pravahx.impact.exposure import VillageExposure

    v_list = [
        VillageExposure(
            village_name="Near Village",
            district="Rudraprayag",
            population=500,
            cropland_ha=10.0,
            is_inundated=True,
            max_depth_m=2.0,
            arrival_time_min=45.0,  # Arrives in 45 min
            geom={"type": "Point", "coordinates": [500000.0, 3300000.0]},
        ),
        VillageExposure(
            village_name="Far Village",
            district="Rudraprayag",
            population=300,
            cropland_ha=5.0,
            is_inundated=True,
            max_depth_m=2.0,
            arrival_time_min=180.0,  # Arrives in 3 hours
            geom={"type": "Point", "coordinates": [500000.0, 3300000.0]},
        ),
    ]

    shelters = [
        EvacuationShelter(
            shelter_id="S1",
            name="Hilltop Community Centre",
            capacity=1000,
            x=501000.0,  # 1 km away -> road dist 1.3 km
            y=3300000.0,
        )
    ]

    plan = plan_evacuation_routes(village_exposures=v_list, shelters=shelters)
    assert plan.total_settlements == 2

    # Near village: travel time ~ (1.3/3.5*60*0.6 + 1.3/25*60*0.4) + 30 = ~44.5 min
    # arrival 45 min -> margin ~ 0.5 min -> CRITICAL
    near_r = next(r for r in plan.routes if r.village_name == "Near Village")
    assert near_r.urgency_level in ["CRITICAL", "TRAPPED"]

    far_r = next(r for r in plan.routes if r.village_name == "Far Village")
    assert far_r.urgency_level in ["HIGH_PRIORITY", "VIABLE"]


def test_impact_brief_generation(tmp_path: Path) -> None:
    from pravahx.impact.damage import DamageEstimate
    from pravahx.impact.evacuation import EvacuationPlanSummary
    from pravahx.impact.exposure import ExposureSummary, VillageExposure

    exp = ExposureSummary(
        total_villages=5,
        inundated_villages=2,
        total_population_exposed=1500,
        total_cropland_inundated_ha=50.0,
        critical_assets_at_risk=1,
        villages=[
            VillageExposure(
                village_name="Rishikesh Basti",
                district="Dehradun",
                population=1500,
                cropland_ha=50.0,
                is_inundated=True,
                max_depth_m=1.8,
                arrival_time_min=55.0,
                hazard_class="high",
                affected_population=1500,
                inundated_cropland_ha=50.0,
            )
        ],
    )

    dmg = DamageEstimate(
        total_residential_loss_inr=5_000_000.0,
        total_agricultural_loss_inr=2_000_000.0,
        total_infrastructure_loss_inr=10_000_000.0,
        grand_total_loss_inr=17_000_000.0,
    )

    evac = EvacuationPlanSummary(
        total_settlements=1,
        trapped_settlements=0,
        critical_settlements=1,
        viable_settlements=0,
    )

    out_file = tmp_path / "disaster_brief.md"
    res_path = export_impact_brief(
        scenario_id="scen_tehri_001",
        scenario_name="Tehri Dam Overtopping",
        exposure=exp,
        damage=dmg,
        evacuation=evac,
        output_path=out_file,
    )
    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")
    assert "Tehri Dam Overtopping" in content
    assert "₹17,000,000.00" in content
    assert "Rishikesh Basti" in content
