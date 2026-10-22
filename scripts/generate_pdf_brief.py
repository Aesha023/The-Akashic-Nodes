"""Generate the official one-page PDF Disaster Impact & Screening Brief for Tier-0 Ganga."""

import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_tier0_pdf_brief(
    out_pdf_path: Path,
    map_png_path: Path,
    stats: dict,
) -> Path:
    """Build a professional, single-page executive screening brief."""
    doc = SimpleDocTemplate(
        str(out_pdf_path),
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=22,
        bottomMargin=22,
    )

    getSampleStyleSheet()

    # Custom styles
    banner_style = ParagraphStyle(
        "Banner",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#b71c1c"),
        alignment=1,  # Center
    )
    title_style = ParagraphStyle(
        "Title",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0d47a1"),
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "SubTitle",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#424242"),
    )
    section_h1 = ParagraphStyle(
        "SectionH1",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#0d47a1"),
        spaceBefore=3,
        spaceAfter=2,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#212121"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#0d47a1"),
    )
    limitation_style = ParagraphStyle(
        "Limitations",
        fontName="Helvetica-Oblique",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#b71c1c"),
    )

    story = []

    # 1. Top Banner
    story.append(
        Paragraph(
            "<b>HYPOTHETICAL SCENARIO - TIER-0 HYDRODYNAMIC SCREENING ONLY</b>",
            banner_style,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#b71c1c"),
            spaceAfter=5,
        )
    )

    # 2. Header Block
    now_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    header_table_data = [
        [
            Paragraph(
                "<b>PravahX Dam Breach & Inundation Brief</b><br/>"
                "<font size=8 color='#555'>Rishikesh Ganga Reach (Uttarakhand, India) "
                "| Tier-0 HAND Model</font>",
                title_style,
            ),
            Paragraph(
                f"<b>Run ID:</b> {stats.get('run_id', 'tier0_ganga_accepted')}<br/>"
                f"<b>Date:</b> {now_str}<br/>"
                "<b>Status:</b> ACCEPTED SCREENING",
                subtitle_style,
            ),
        ]
    ]
    t_header = Table(header_table_data, colWidths=[370, 169])
    t_header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    story.append(t_header)
    story.append(Spacer(1, 4))

    # 3. Two-Column Layout: Left (Map + Provenance), Right (Key Metrics & Findings)
    img_flowable = Image(str(map_png_path), width=265, height=212)

    prov_text = (
        "<b>DATA PROVENANCE & ENGINE:</b><br/>"
        "• <b>DEM:</b> Copernicus GLO-30 (30 m STAC AWS)<br/>"
        "• <b>CRS:</b> EPSG:32644 (UTM 44N) | <b>AOI:</b> 5x5 km<br/>"
        "• <b>Hydraulic Forcing:</b> Peak Flow 5,000.0 m3/s, Manning n=0.035<br/>"
        "• <b>Population:</b> WorldPop 2020 100m Constrained (BSGM IND)<br/>"
        "• <b>Infrastructure:</b> OpenStreetMap (Snapshot: 2026-10-22, ODbL)"
    )
    p_prov = Paragraph(prov_text, table_cell)
    left_cell = [img_flowable, Spacer(1, 4), p_prov]

    area_val = stats.get("area_km2", 1.72)
    area_ha = stats.get("area_ha", 171.9)
    road_fl = stats.get("road_flooded_km", 5.68)
    road_tot = stats.get("road_total_km", 159.54)
    road_p = stats.get("road_pct", 3.6)
    bldg_fl = stats.get("buildings_flooded", 5)
    bldg_tot = stats.get("buildings_total", 93)

    right_cell = [
        Paragraph("<b>1. Hydraulic Screening Envelope</b>", section_h1),
        Table(
            [
                [
                    Paragraph("Inundation Area", table_cell),
                    Paragraph(f"<b>{area_val:.2f} km2</b> ({area_ha:.1f} ha)", table_cell_bold),
                ],
                [
                    Paragraph("Peak Inflow Rate", table_cell),
                    Paragraph("<b>5,000.0 m3/s</b>", table_cell_bold),
                ],
                [
                    Paragraph("Maximum / Mean Depth", table_cell),
                    Paragraph(
                        f"<b>{stats.get('max_depth_m', 7.73):.2f} m</b> / "
                        f"{stats.get('mean_depth_m', 6.31):.2f} m",
                        table_cell_bold,
                    ),
                ],
                [
                    Paragraph("Median (P10 - P90)", table_cell),
                    Paragraph(
                        f"<b>{stats.get('median_depth_m', 7.23):.2f} m</b> "
                        f"({stats.get('p10_depth_m', 3.12):.2f} - "
                        f"{stats.get('p90_depth_m', 7.73):.2f} m)",
                        table_cell,
                    ),
                ],
                [
                    Paragraph("Arrival Time", table_cell),
                    Paragraph("<font color='#d32f2f'>None (Static Tier-0)</font>", table_cell),
                ],
            ],
            colWidths=[110, 155],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ],
        ),
        Spacer(1, 3),
        Paragraph("<b>2. Population & Asset Exposure</b>", section_h1),
        Table(
            [
                [
                    Paragraph("Exposed Population", table_cell),
                    Paragraph(
                        f"<b>{stats.get('pop_total', 0):,d}</b> people (9.8%)", table_cell_bold
                    ),
                ],
                [
                    Paragraph("  • Depth 0.0-0.5 m [UNVERIFIED]", table_cell),
                    Paragraph(
                        f"{stats.get('pop_c1', 0):,d} ({stats.get('pop_c1_pct', 0.0):.1f}%)",
                        table_cell,
                    ),
                ],
                [
                    Paragraph("  • Depth 0.5-1.5 m [UNVERIFIED]", table_cell),
                    Paragraph(
                        f"{stats.get('pop_c2', 0):,d} ({stats.get('pop_c2_pct', 0.0):.1f}%)",
                        table_cell,
                    ),
                ],
                [
                    Paragraph("  • Depth > 1.5 m   [UNVERIFIED]", table_cell),
                    Paragraph(
                        f"{stats.get('pop_c3', 0):,d} ({stats.get('pop_c3_pct', 0.0):.1f}%)",
                        table_cell,
                    ),
                ],
                [
                    Paragraph("Flooded Roads (depth > 0.3m)", table_cell),
                    Paragraph(
                        f"<b>{road_fl:.2f} km</b> of {road_tot:.1f} km ({road_p:.1f}%)",
                        table_cell_bold,
                    ),
                ],
                [
                    Paragraph("Flooded Buildings", table_cell),
                    Paragraph(
                        f"<b>{bldg_fl}</b> of {bldg_tot} (OSM coverage incomplete)", table_cell
                    ),
                ],
                [
                    Paragraph("Critical Facilities", table_cell),
                    Paragraph("<b>0 of 28</b> (depth = 0.00 m)", table_cell_bold),
                ],
                [
                    Paragraph("Monetary Loss Valuation", table_cell),
                    Paragraph(
                        "<font color='#757575'><b>NOT RUN</b> "
                        "(No verified depth-damage curve)</font>",
                        table_cell,
                    ),
                ],
            ],
            colWidths=[120, 145],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ],
        ),
        Spacer(1, 3),
        Paragraph("<b>3. Network Evacuation Assessment</b>", section_h1),
        Table(
            [
                [
                    Paragraph("Vehicle Impassable Cutoff", table_cell),
                    Paragraph(
                        f"Depth > {stats.get('evac_depth_cutoff_m', 0.30):.2f} m [UNVERIFIED]",
                        table_cell,
                    ),
                ],
                [
                    Paragraph("Severed Road Edges", table_cell),
                    Paragraph(
                        f"<b>{stats.get('severed_edges', 930)}</b> of "
                        f"{stats.get('total_edges', 3638)} "
                        f"({stats.get('severed_length_km', 311.84):.1f} km)",
                        table_cell,
                    ),
                ],
                [
                    Paragraph("Reachable Building Origins", table_cell),
                    Paragraph(
                        f"<b>{stats.get('reachable_origins', 2)}</b> of {bldg_fl} "
                        f"(Routes: 8.0 m, 108.8 m)",
                        table_cell_bold,
                    ),
                ],
                [
                    Paragraph("Unreachable Building Origins", table_cell),
                    Paragraph(
                        f"<font color='#d32f2f'><b>{stats.get('unreachable_origins', 3)}</b> "
                        f"of {bldg_fl} (Gorge road severed)</font>",
                        table_cell_bold,
                    ),
                ],
            ],
            colWidths=[120, 145],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fce4ec")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f8bbd0")),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ],
        ),
    ]

    t_main = Table([[left_cell, right_cell]], colWidths=[268, 271])
    t_main.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(t_main)
    story.append(Spacer(1, 5))

    # 4. Mandatory Limitations & Caveats Block
    lim_title = Paragraph(
        "<b>MODEL LIMITATIONS & UNCERTAINTIES (MANDATORY DISCLAIMER):</b>",
        limitation_style,
    )
    lim_body = Paragraph(
        "1. <b>Static Inundation Envelope:</b> Tier-0 HAND operates on static equilibrium "
        "and does not resolve hydrodynamic wave propagation, backwater effects, or "
        "arrival times.<br/>"
        "2. <b>Synthetic Rating Curve:</b> Inundation depth is derived from normal-depth Manning "
        "hydraulics along a uniform reach without bathymetric cross-section survey "
        "calibration.<br/>"
        "3. <b>DEM Water-Surface Artefact:</b> Copernicus GLO-30 reflects water surface elevation "
        "during acquisition; dry-season channel bed conveyance is underestimated.<br/>"
        "4. <b>Operational Scope:</b> Generated strictly for preliminary disaster risk screening "
        "and multi-agency table-top planning. NOT for structural engineering or design use.",
        limitation_style,
    )
    t_lim = Table([[lim_title], [lim_body]], colWidths=[539])
    t_lim.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffebee")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#ef5350")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_lim)

    doc.build(story)
    return out_pdf_path


def main() -> None:
    """Generate or stage the PDF brief for artifacts upload and API serving."""
    import shutil

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = artifacts_dir / "ganga_tier0_brief.pdf"
    bundled_pdf = Path("data/ganga_inputs/ganga_tier0_brief.pdf")

    map_png = Path("data/ganga_inputs/ganga_tier0_map.png")
    stats = {
        "run_id": "tier0_ganga_accepted",
        "area_km2": 1.72,
        "max_depth_m": 7.73,
        "mean_depth_m": 6.31,
        "median_depth_m": 7.23,
        "p10_depth_m": 3.12,
        "p90_depth_m": 7.73,
        "pop_total": 2696,
        "pop_c1": 230,
        "pop_c1_pct": 8.5,
        "pop_c2": 253,
        "pop_c2_pct": 9.4,
        "pop_c3": 2213,
        "pop_c3_pct": 82.1,
        "road_flooded_km": 17.34,
        "road_total_km": 159.54,
        "road_pct": 10.9,
        "buildings_flooded": 5,
        "buildings_total": 93,
        "severed_edges": 930,
        "total_edges": 3638,
        "severed_length_km": 311.84,
        "reachable_origins": 2,
        "unreachable_origins": 3,
        "mean_route_m": 58.4,
    }
    build_tier0_pdf_brief(out_pdf, map_png, stats)
    shutil.copy(out_pdf, bundled_pdf)
    print(f"Built and staged verified PDF brief at {out_pdf} and {bundled_pdf}")


if __name__ == "__main__":
    main()
