"""Executive disaster impact and evacuation brief generator (Phase 7 / Section 9)."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pravahx.impact.damage import DamageEstimate
    from pravahx.impact.evacuation import EvacuationPlanSummary
    from pravahx.impact.exposure import ExposureSummary


def generate_impact_brief_markdown(
    scenario_id: str,
    scenario_name: str,
    exposure: ExposureSummary,
    damage: DamageEstimate,
    evacuation: EvacuationPlanSummary,
) -> str:
    """Generate a structured Markdown disaster brief for emergency responders."""
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# PravahX Disaster Impact & Evacuation Brief",
        f"**Scenario:** {scenario_name} (`{scenario_id}`)",
        f"**Generated At:** {timestamp}",
        "**Classification:** Emergency Planning Document (NTRO / SDMA)",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        f"- **Total Population Exposed:** {exposure.total_population_exposed:,} people",
        (
            f"- **Inundated Settlements:** {exposure.inundated_villages} of "
            f"{exposure.total_villages} analyzed"
        ),
        (
            "- **Agricultural Land Inundated:** "
            f"{exposure.total_cropland_inundated_ha:,.2f} hectares"
        ),
        f"- **Critical Assets at Risk:** {exposure.critical_assets_at_risk}",
        f"- **Estimated Total Direct Loss:** ₹{damage.grand_total_loss_inr:,.2f} INR",
        (
            "- **Evacuation Clearance Status:** "
            f"{evacuation.trapped_settlements} Trapped, "
            f"{evacuation.critical_settlements} Critical (< 60m margin)"
        ),
        "",
        "## 2. Economic Loss Breakdown",
        "| Sector | Estimated Loss (INR) | % of Total |",
        "|---|---|---|",
    ]

    tot = damage.grand_total_loss_inr or 1.0
    res_pct = damage.total_residential_loss_inr / tot * 100
    lines.append(
        f"| Residential Structures & Contents | ₹{damage.total_residential_loss_inr:,.2f} | "
        f"{res_pct:.1f}% |"
    )
    agri_pct = damage.total_agricultural_loss_inr / tot * 100
    lines.append(
        f"| Standing Crops & Agriculture | ₹{damage.total_agricultural_loss_inr:,.2f} | "
        f"{agri_pct:.1f}% |"
    )
    infra_pct = damage.total_infrastructure_loss_inr / tot * 100
    lines.append(
        f"| Critical & Public Infrastructure | ₹{damage.total_infrastructure_loss_inr:,.2f} | "
        f"{infra_pct:.1f}% |"
    )
    lines.append(f"| **Grand Total** | **₹{damage.grand_total_loss_inr:,.2f}** | **100.0%** |")

    lines.extend(
        [
            "",
            "## 3. Village Exposure and Evacuation Priority",
            (
                "| Village | District | Affected Pop | Inundated Crop (ha) "
                "| Max Depth (m) | Arrival Time (min) | Evac Margin (min) | Urgency |"
            ),
            "|---|---|---|---|---|---|---|---|",
        ]
    )

    evac_dict = {r.village_name: r for r in evacuation.routes}

    for v in exposure.villages:
        if not v.is_inundated:
            continue
        ev = evac_dict.get(v.village_name)
        margin_str = f"{ev.safety_margin_min:.1f}" if ev else "N/A"
        urgency_str = ev.urgency_level if ev else "N/A"

        row_str = (
            f"| {v.village_name} | {v.district} | {v.affected_population:,} | "
            f"{v.inundated_cropland_ha:.1f} | {v.max_depth_m:.2f} | "
            f"{v.arrival_time_min:.1f} | {margin_str} | **{urgency_str}** |"
        )
        lines.append(row_str)

    lines.extend(
        [
            "",
            "## 4. Critical Infrastructure Exposure",
            (
                "| Asset Name | Type | Max Inundation Depth (m) "
                "| Flood Arrival Time (min) | Hazard Severity |"
            ),
            "|---|---|---|---|---|",
        ]
    )

    for a in exposure.critical_assets:
        if a.is_inundated:
            row_asset = (
                f"| {a.asset_name} | {a.asset_type} | {a.max_depth_m:.2f} | "
                f"{a.arrival_time_min:.1f} | {a.hazard_class.upper()} |"
            )
            lines.append(row_asset)

    lines.extend(
        [
            "",
            "## 5. Model Uncertainty & Operational Caveats",
            "> [!IMPORTANT]",
            (
                "> - **Terrain Resolution:** High-gradient mountain terrain flood "
                "extents are conditioned on available DEM resolution."
            ),
            (
                "> - **Manning Roughness:** Channel and floodplain friction values "
                "are estimated from regional landcover classifications."
            ),
            (
                "> - **Breach Timing:** Flood wave arrival assumes instantaneous "
                "initiation following breach trigger criteria."
            ),
            (
                "> - **Ground Truth:** Field verification and live gauge monitoring "
                "must supersede numerical model projections."
            ),
        ]
    )

    return "\n".join(lines)


def export_impact_brief(
    scenario_id: str,
    scenario_name: str,
    exposure: ExposureSummary,
    damage: DamageEstimate,
    evacuation: EvacuationPlanSummary,
    output_path: str | Path,
) -> Path:
    """Write impact brief to disk."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    md_content = generate_impact_brief_markdown(
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        exposure=exposure,
        damage=damage,
        evacuation=evacuation,
    )
    out_p.write_text(md_content, encoding="utf-8")
    return out_p
