"""Generate HEC-RAS breach hydrograph plot artifact."""

from pathlib import Path

import matplotlib.pyplot as plt

from pravahx.breach.froehlich import compute_froehlich_2008
from pravahx.breach.hydrograph import route_hydrograph


def generate_hec_ras_plot(output_path: Path) -> None:
    # HEC-RAS regression parameters
    vol_m3 = 357.98e6
    h_dam_m = 42.9

    params = compute_froehlich_2008(volume_m3=vol_m3, height_m=h_dam_m, mode="overtopping")

    # Route hydrograph using trapezoidal broad-crested weir formulation (HEC-RAS mode)
    dt_hr = 0.005
    hydrograph = route_hydrograph(
        initial_volume_m3=vol_m3,
        dam_height_m=h_dam_m,
        b_avg_m=params.average_width_m,
        t_f_hr=params.formation_time_hr,
        reservoir_exponent=3.0,
        side_slope_z=params.side_slope_z,
        progression_mode="vertical_and_horizontal",
        dt_hr=dt_hr,
        c_v1=1.70,
        c_v2=1.35,
    )

    times = [p["time_hr"] for p in hydrograph.points]
    discharges = [p["discharge_m3s"] for p in hydrograph.points]
    heads = [p["head_m"] for p in hydrograph.points]

    max_q = hydrograph.peak_discharge_m3s
    t_peak = hydrograph.time_to_peak_hr
    qp_froehlich_1995 = hydrograph.froehlich_1995_peak_m3s

    # Plot
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)

    color_q = "#1f77b4"
    ax1.set_xlabel("Time (hours)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Discharge (m³/s)", color=color_q, fontsize=12, fontweight="bold")
    (line1,) = ax1.plot(
        times,
        discharges,
        color=color_q,
        linewidth=2.5,
        label="Routed Outflow Q(t)",
    )
    ax1.tick_params(axis="y", labelcolor=color_q)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Froehlich 1995 peak line
    line_f95 = ax1.axhline(
        y=qp_froehlich_1995,
        color="#d62728",
        linestyle=":",
        linewidth=2.0,
        label=f"Froehlich (1995) Empirical Q_peak ({qp_froehlich_1995:,.0f} m³/s)",
    )

    # Routed peak marker
    line_peak = ax1.axvline(
        x=t_peak,
        color="#2ca02c",
        linestyle="--",
        linewidth=1.5,
        label=f"Routed Peak Time ({t_peak:.2f} h, {max_q:,.0f} m³/s)",
    )

    # Secondary axis for Head h(t)
    ax2 = ax1.twinx()
    color_h = "#ff7f0e"
    ax2.set_ylabel(
        "Reservoir Head h(t) (m)",
        color=color_h,
        fontsize=12,
        fontweight="bold",
    )
    (line2,) = ax2.plot(
        times,
        heads,
        color=color_h,
        linewidth=2.0,
        linestyle="-.",
        label="Reservoir Head h(t)",
    )
    ax2.tick_params(axis="y", labelcolor=color_h)

    # Title and text annotation
    b_avg_str = f"{params.average_width_m:.1f}"
    t_f_str = f"{params.formation_time_hr:.2f}"
    plt.title(
        f"HEC-RAS Embankment Dam Breach Hydrograph\n"
        f"V_w = 357.98 MCM, h_b = 42.9 m, B_avg = {b_avg_str} m, t_f = {t_f_str} h",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    lines = [line1, line2, line_f95, line_peak]
    labels = [item.get_label() for item in lines]
    ax1.legend(lines, labels, loc="upper right", framealpha=0.9)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Saved hydrograph plot to: {output_path}")


if __name__ == "__main__":
    out_file = Path("artifacts/hec_ras_hydrograph.png")
    generate_hec_ras_plot(out_file)
