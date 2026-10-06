"""Unit tests for multi-dam cascade analysis and chained breach triggers (Phase 4)."""

from __future__ import annotations

import pytest

from pravahx.cascade.downstream import (
    CascadeAnalyzer,
    CascadeVerdict,
    ChannelHydrographPoint,
    DamStructure,
)


@pytest.fixture
def initial_upstream_dam() -> DamStructure:
    """Fixture for upstream initial failure dam."""
    return DamStructure(
        id="DAM-UPSTREAM",
        name="Upper Canyon Dam",
        river="Alaknanda",
        chainage_km=0.0,
        dam_height_m=50.0,
        storage_m3=2_000_000.0,  # 2 MCM
        crest_elevation_m=1000.0,
        bed_elevation_m=950.0,
        spillway_capacity_m3s=500.0,
        initial_storage_fraction=0.90,
    )


@pytest.fixture
def sample_upstream_hydrograph() -> list[ChannelHydrographPoint]:
    """Fixture for upstream breach outflow hydrograph."""
    points: list[ChannelHydrographPoint] = []
    # Hydrograph with peak 2,500 m3/s, lasting 3600 seconds
    time_steps = [0.0, 600.0, 1200.0, 1800.0, 2400.0, 3000.0, 3600.0]
    flows = [0.0, 800.0, 2500.0, 2000.0, 1000.0, 300.0, 0.0]

    for t, q in zip(time_steps, flows, strict=True):
        points.append(
            ChannelHydrographPoint(
                time_seconds=t,
                discharge_m3s=q,
                reservoir_head_m=max(0.0, 50.0 * (1.0 - t / 3600.0)),
                breach_width_m=min(60.0, 60.0 * (t / 1200.0)),
                volume_remaining_m3=max(0.0, 2_000_000.0 * (1.0 - t / 3600.0)),
            )
        )
    return points


def test_cascade_channel_routing_lag_and_attenuation(
    sample_upstream_hydrograph: list[ChannelHydrographPoint],
) -> None:
    """Verify channel flood wave routing adds physical lag time and peak attenuation."""
    analyzer = CascadeAnalyzer(celerity_m_s=5.0, attenuation_rate_per_km=0.01)

    dist_km = 10.0
    routed_hg, lag_min = analyzer.route_channel_flood_wave(sample_upstream_hydrograph, dist_km)

    # 10 km at 5 m/s = 2,000 s = 33.33 min lag
    assert pytest.approx(lag_min, rel=1e-2) == 33.33
    assert routed_hg[0].time_seconds == pytest.approx(2000.0, rel=1e-2)

    # Peak flow should attenuate by 10 * 0.01 = 10% (from 2500 to 2250 m3/s)
    peak_in = max(pt.discharge_m3s for pt in sample_upstream_hydrograph)
    peak_out = max(pt.discharge_m3s for pt in routed_hg)
    assert peak_out < peak_in
    assert pytest.approx(peak_out, rel=1e-2) == 2250.0


def test_cascade_single_downstream_dam_safe(
    initial_upstream_dam: DamStructure,
    sample_upstream_hydrograph: list[ChannelHydrographPoint],
) -> None:
    """Verify downstream dam with large capacity safely absorbs arriving flood."""
    large_dam = DamStructure(
        id="DAM-LARGE",
        name="Large Downstream Reservoir",
        river="Alaknanda",
        chainage_km=25.0,
        dam_height_m=100.0,
        storage_m3=50_000_000.0,  # 50 MCM (huge capacity)
        crest_elevation_m=850.0,
        bed_elevation_m=750.0,
        spillway_capacity_m3s=5_000.0,  # Huge spillway
        initial_storage_fraction=0.50,  # 50% empty surcharge storage
    )

    analyzer = CascadeAnalyzer()
    summary = analyzer.evaluate_cascade(
        scenario_id="SCEN-001",
        initial_dam=initial_upstream_dam,
        initial_hydrograph=sample_upstream_hydrograph,
        downstream_dams=[large_dam],
    )

    assert summary.total_dams_evaluated == 1
    assert summary.total_dams_overtopped == 0
    assert summary.cascade_triggered is False
    assert len(summary.links) == 1

    link = summary.links[0]
    assert link.dam_id == "DAM-LARGE"
    assert link.overtopped is False
    assert link.verdict == CascadeVerdict.SAFE
    assert link.freeboard_m > 0
    assert link.chained_scenario_id is None


def test_cascade_two_dams_in_series_triggers_chained_breach(
    initial_upstream_dam: DamStructure,
    sample_upstream_hydrograph: list[ChannelHydrographPoint],
) -> None:
    """Verify test with two dams in series triggers cascade failure when second dam overtop."""
    # Downstream small barrage with high initial storage and low crest freeboard
    barrage_dam = DamStructure(
        id="DAM-BARRAGE-01",
        name="Valley Run-of-River Barrage",
        river="Alaknanda",
        chainage_km=15.0,
        dam_height_m=18.0,
        storage_m3=500_000.0,  # 0.5 MCM (small storage, easily overwhelmed)
        crest_elevation_m=820.0,
        bed_elevation_m=802.0,
        spillway_capacity_m3s=400.0,  # Spillway cannot handle 2,000+ m3/s
        initial_storage_fraction=0.95,  # 95% full
    )

    analyzer = CascadeAnalyzer()
    summary = analyzer.evaluate_cascade(
        scenario_id="SCEN-CASCADE-TEST",
        initial_dam=initial_upstream_dam,
        initial_hydrograph=sample_upstream_hydrograph,
        downstream_dams=[barrage_dam],
    )

    assert summary.total_dams_evaluated == 1
    assert summary.total_dams_overtopped == 1
    assert summary.cascade_triggered is True

    link = summary.links[0]
    assert link.dam_id == "DAM-BARRAGE-01"
    assert link.overtopped is True
    assert link.verdict == CascadeVerdict.OVERTOPPED
    assert link.freeboard_m < 0  # Water elevation exceeded crest

    # Verify chained breach parameters were automatically computed
    assert link.chained_scenario_id == "SCEN-CASCADE-TEST_cascade_DAM-BARRAGE-01"
    assert link.chained_peak_outflow_m3s is not None
    assert link.chained_peak_outflow_m3s > 0
    assert link.chained_breach_width_m is not None
    assert link.chained_breach_width_m > 0
    assert link.chained_formation_time_h is not None
    assert link.chained_formation_time_h > 0


def test_cascade_longitudinal_profile(
    initial_upstream_dam: DamStructure,
    sample_upstream_hydrograph: list[ChannelHydrographPoint],
) -> None:
    """Verify river profile generation records chainage, bed elevation, and crest levels."""
    dam2 = DamStructure(
        id="DAM-MID",
        name="Middle Dam",
        river="Alaknanda",
        chainage_km=20.0,
        dam_height_m=30.0,
        storage_m3=1_000_000.0,
        crest_elevation_m=800.0,
        bed_elevation_m=770.0,
        spillway_capacity_m3s=300.0,
    )
    dam3 = DamStructure(
        id="DAM-LOW",
        name="Lower Dam",
        river="Alaknanda",
        chainage_km=45.0,
        dam_height_m=25.0,
        storage_m3=800_000.0,
        crest_elevation_m=650.0,
        bed_elevation_m=625.0,
        spillway_capacity_m3s=250.0,
    )

    analyzer = CascadeAnalyzer()
    summary = analyzer.evaluate_cascade(
        scenario_id="SCEN-PROFILE",
        initial_dam=initial_upstream_dam,
        initial_hydrograph=sample_upstream_hydrograph,
        downstream_dams=[dam2, dam3],
    )

    assert len(summary.profile) == 3  # Initial + dam2 + dam3
    assert summary.profile[0].dam_id == "DAM-UPSTREAM"
    assert summary.profile[0].chainage_km == 0.0
    assert summary.profile[1].dam_id == "DAM-MID"
    assert summary.profile[1].chainage_km == 20.0
    assert summary.profile[2].dam_id == "DAM-LOW"
    assert summary.profile[2].chainage_km == 45.0
