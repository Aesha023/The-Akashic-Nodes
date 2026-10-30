"""Database seed and purge utilities for DEMO mode (Full-stack alignment).

Ensures demo rows are strictly tagged with `demo=True` and completely segregated from real runs.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from backend.app.db.session import sync_session_factory
from backend.app.models.alert import Alert, AlertRule
from backend.app.models.batch import Batch, BatchItem
from backend.app.models.scenario import Scenario
from backend.app.models.watched_lake import WatchedLake

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "demo" / "fixtures"


def _load_fixture(filename: str) -> dict[str, Any]:
    file_path = FIXTURES_DIR / filename
    if not file_path.exists():
        return {}
    with open(file_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


def seed_demo_data(session: Session | None = None) -> dict[str, int]:
    """Seed demo rows tagged with demo=True into database."""
    should_close = False
    if session is None:
        session = sync_session_factory()
        should_close = True

    counts: dict[str, int] = {
        "watched_lakes": 0,
        "alerts": 0,
        "alert_rules": 0,
        "batches": 0,
        "scenarios": 0,
    }

    try:
        # 1. Watched Lakes
        lakes_data = _load_fixture("watched_lakes.json").get("items", [])
        for item in lakes_data:
            existing = session.execute(
                select(WatchedLake).where(WatchedLake.id == item["id"])
            ).scalar_one_or_none()
            if not existing:
                lake = WatchedLake(
                    id=item["id"],
                    name=item["name"],
                    lake_type=item.get("lake_type", "glacial"),
                    region=item.get("region", "Himalaya"),
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    elevation_m=item["elevation_m"],
                    area_m2=item["area_m2"],
                    volume_m3=item["volume_m3"],
                    risk_level=item.get("risk_level", "low"),
                    last_observed_at=datetime.datetime.fromisoformat(
                        item["last_observed_at"].replace("Z", "+00:00")
                    )
                    if item.get("last_observed_at")
                    else None,
                    demo=True,
                )
                session.add(lake)
                counts["watched_lakes"] += 1

        # 2. Alert Rules and Alerts
        rule_id = "demo_rule_freeboard"
        existing_rule = session.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        ).scalar_one_or_none()
        if not existing_rule:
            rule = AlertRule(
                id=rule_id,
                name="Demo Freeboard Depletion Trigger",
                rule_type="freeboard_monitoring",
                threshold_value=3.0,
                condition="<",
                channels_json=json.dumps(["email", "webhook"]),
                is_active=True,
                demo=True,
            )
            session.add(rule)
            counts["alert_rules"] += 1

        alerts_data = _load_fixture("alerts.json").get("items", [])
        for item in alerts_data:
            existing_alt = session.execute(
                select(Alert).where(Alert.id == item["id"])
            ).scalar_one_or_none()
            if not existing_alt:
                alt = Alert(
                    id=item["id"],
                    rule_id=rule_id,
                    severity=item["severity"],
                    title=item["title"],
                    message=item["message"],
                    details_json=json.dumps({"target": item.get("target_name")}),
                    status=item.get("status", "active"),
                    demo=True,
                    created_at=datetime.datetime.fromisoformat(
                        item["created_at"].replace("Z", "+00:00")
                    ),
                    resolved_at=datetime.datetime.fromisoformat(
                        item["resolved_at"].replace("Z", "+00:00")
                    )
                    if item.get("resolved_at")
                    else None,
                )
                session.add(alt)
                counts["alerts"] += 1

        # 3. Batches
        batches_data = _load_fixture("batches.json").get("items", [])
        for b_item in batches_data:
            existing_batch = session.execute(
                select(Batch).where(Batch.id == b_item["id"])
            ).scalar_one_or_none()
            if not existing_batch:
                batch = Batch(
                    id=b_item["id"],
                    name=b_item["name"],
                    status=b_item["status"],
                    total_items=b_item["total_items"],
                    completed_items=b_item["completed_items"],
                    failed_items=b_item["failed_items"],
                    created_by=b_item.get("created_by"),
                    demo=True,
                    created_at=datetime.datetime.fromisoformat(
                        b_item["created_at"].replace("Z", "+00:00")
                    ),
                )
                session.add(batch)
                counts["batches"] += 1

                # Add sample batch items
                for idx in range(1, 4):
                    item_id = f"{b_item['id']}_item_{idx}"
                    batch_it = BatchItem(
                        id=item_id,
                        batch_id=b_item["id"],
                        dam_name=f"Demo Fictional Dam {idx}",
                        status="completed" if idx <= 2 else "queued",
                    )
                    session.add(batch_it)

        # 4. Demo Scenario
        demo_scenario_id = "demo_scenario_fictional_reservoir"
        existing_scen = session.execute(
            select(Scenario).where(Scenario.id == demo_scenario_id)
        ).scalar_one_or_none()
        if not existing_scen:
            scen = Scenario(
                id=demo_scenario_id,
                name="Demo Reservoir Alpha — Fictional Screening",
                scenario_type="dam_break",
                failure_mode="overtopping",
                config_json=json.dumps(
                    {
                        "dam": {"name": "Demo Reservoir Alpha", "height_m": 45.0},
                        "demo": True,
                    }
                ),
                created_by="operator@pravahx.org",
                demo=True,
            )
            session.add(scen)
            counts["scenarios"] += 1

        session.commit()
    finally:
        if should_close:
            session.close()

    return counts


def purge_demo_data(session: Session | None = None) -> dict[str, int]:
    """Purge all rows flagged demo=True. Never touches real data."""
    should_close = False
    if session is None:
        session = sync_session_factory()
        should_close = True

    counts: dict[str, int] = {}

    try:
        # Delete demo batch items
        demo_batch_ids = (
            session.execute(
                select(Batch.id).where(Batch.demo == True)  # noqa: E712
            )
            .scalars()
            .all()
        )
        if demo_batch_ids:
            res_items = session.execute(
                delete(BatchItem).where(BatchItem.batch_id.in_(demo_batch_ids))
            )
            counts["batch_items"] = res_items.rowcount  # type: ignore[assignment]
        else:
            counts["batch_items"] = 0

        res_batches = session.execute(delete(Batch).where(Batch.demo == True))  # noqa: E712
        counts["batches"] = res_batches.rowcount  # type: ignore[assignment]

        res_alerts = session.execute(delete(Alert).where(Alert.demo == True))  # noqa: E712
        counts["alerts"] = res_alerts.rowcount  # type: ignore[assignment]

        res_rules = session.execute(delete(AlertRule).where(AlertRule.demo == True))  # noqa: E712
        counts["alert_rules"] = res_rules.rowcount  # type: ignore[assignment]

        res_lakes = session.execute(delete(WatchedLake).where(WatchedLake.demo == True))  # noqa: E712
        counts["watched_lakes"] = res_lakes.rowcount  # type: ignore[assignment]

        res_scenarios = session.execute(delete(Scenario).where(Scenario.demo == True))  # noqa: E712
        counts["scenarios"] = res_scenarios.rowcount  # type: ignore[assignment]

        session.commit()
    finally:
        if should_close:
            session.close()

    return counts
