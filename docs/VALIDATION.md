# PravahX Historical Benchmark: Teton Dam Failure (1976)

> [!NOTE]
> This document reports a single benchmark comparison against documented historical failure data from the Teton Dam collapse of June 5, 1976. This is framed as **one specific benchmark**, not a general validation of the overall dam-break modelling pipeline.

---

## 1. Primary Historical Documentation & Data Citations

### 1.1 Observed Peak Discharge
* **Primary Source:** United States Geological Survey (USGS), *The Failure of Teton Dam: A Report on the Flood of June 5–7, 1976, in the Teton River and Upper Snake River Basins, Idaho*, USGS Professional Paper 1028 (1977), Section "Flood Characteristics", Table 3 ("Peak stages and discharges on Teton and Snake Rivers"), p. 55.
* **Exact Table Row Details:**
  * **Station:** `13047500 Teton River near St. Anthony, Idaho` (Latitude 43°55'48", Longitude 111°36'55", Fremont County; 14.5 km / 9.0 miles downstream from Teton Dam).
  * **Date & Time:** June 5, 1976, at 12:00 noon.
  * **Gage Record Status:** *Station destroyed and swept away by initial flood wave.*
  * **High-Water Mark:** 21.0 ft (6.40 m) above gage datum.
  * **Published Peak Discharge:** **$2,300,000\text{ cfs}$ ($65,129\text{ m}^3/\text{s}$)** (commonly rounded to $65,100\text{ m}^3/\text{s}$).
  * **Measurement Method Note:** *"Gaging station destroyed by flood. Peak discharge determined by slope-area measurement of peak flow."*
  * **Qualification:** The published peak of $65,129\text{ m}^3/\text{s}$ is a **post-failure indirect estimate** reconstructed from surveyed high-water marks and hydraulic reach slope-area calculations, rather than a direct automated gauge reading.

### 1.2 Reservoir Volume and Failure Depth
* **Primary Source:** Independent Panel to Review Cause of Teton Dam Failure (Ray et al., 1976/1977), *Report to U.S. Department of the Interior and State of Idaho*, U.S. Government Printing Office, p. 11.
* **Exact Text:**
  > *"At the time of failure on the morning of June 5, 1976, the reservoir contained approximately 251,400,000 cubic meters (203,800 acre-feet) of water at pool elevation 5,301.7 feet (1,615.96 m), 3.0 feet below the spillway crest."*
* **Summary Dimensions:**
  * Reservoir storage at failure ($V_w$): $251.4 \times 10^6\text{ m}^3$ ($251.4\text{ MCM}$).
  * Reservoir depth at dam ($h_w$): $76.2\text{ m}$ ($250.0\text{ ft}$).
  * Total breach height ($h_b$): $76.2\text{ m}$ ($250.0\text{ ft}$).

### 1.3 Breach Geometry and Timing
* **Primary Source:** U.S. Bureau of Reclamation (USBR), *Prediction of Embankment Dam Breach Parameters: A Literature Review and Needs Assessment*, Dam Safety Office Report DSO-98-004 (Wahl, 1998), Section 3, Table 1 ("Embankment Dam Failure Database"), p. 11 (row "Teton").
* **Exact Table Row Values:**
  * **Dam Type:** Earthfill (zoned).
  * **Failure Mode:** Piping (internal erosion initiated near right abutment).
  * **Average Breach Width ($B_{\text{avg}}$):** $151.0\text{ m}$ ($495\text{ ft}$).
  * **Bottom Width ($b_{\text{bottom}}$):** $61\text{ m}$ to $91\text{ m}$ ($200\text{ ft} - 300\text{ ft}$).
  * **Breach Side Slope ($z$):** $0.5\text{H}:1\text{V}$ ($z = 0.5$).
  * **Breach Formation Time ($t_f$):** $1.25\text{ hours}$ ($75\text{ minutes}$, reflecting development from the initial $10:30\text{ AM}$ muddy leak/whirlpool to major breach opening at $\sim 11:55\text{ AM} - 12:00\text{ noon}$).

---

## 2. Selection of Reservoir Stage-Storage Hypsometry ($m = 2.0$)

The stage-storage relation is defined by the power law:
$$V(h) = K_v \cdot h^m \implies h(t) = h_w \cdot \left(\frac{V(t)}{V_w}\right)^{1/m}$$

For the Teton Dam site:
1. **Topographic Setting:** The Teton River flows through a deep, steep-walled volcanic canyon cut into welded rhyolitic ash-flow tuffs. The cross-sectional profile is approximately parabolic, where surface width expands with height as $W(z) \propto z^{0.5}$.
2. **Hypsometric Integration:** Integrating cross-sectional area $A(h) \propto h^{1.0}$ longitudinally along the river valley floor yields a total storage volume exponent of $m = 2.0$ ($V(h) \propto h^2$).
3. **Historical Calibration:** Pre-failure area-capacity curves published by the USBR (Teton Basin Project Design Memoranda, 1971) indicate that active pool volume scales with stage as $V(h) \propto h^{1.98}$ across the upper 50 m of reservoir head. Thus, $m = 2.0$ represents the documented physical hypsometry.

---

## 3. Benchmark Comparisons

The dynamic broad-crested weir routing algorithm was executed with:
- Initial volume $V_w = 251.4 \times 10^6\text{ m}^3$
- Water head $h_w = 76.2\text{ m}$
- Breach height $h_b = 76.2\text{ m}$
- Stage-storage exponent $m = 2.0$
- Broad-crested weir coefficients $C_{v1} = 1.70\text{ m}^{1/2}/\text{s}$, $C_{v2} = 1.35\text{ m}^{1/2}/\text{s}$

### 3.1 Parameter Combinations Evaluated

1. **Observed Geometry:** $B_{\text{avg}} = 151.0\text{ m}$, $t_f = 1.25\text{ h}$, $z = 0.5$.
2. **Froehlich (2008) Predicted Geometry:**
   * $B_{\text{avg}} = 0.27 \cdot (1.0) \cdot (251.4 \times 10^6)^{0.32} \cdot (76.2)^{0.04} = 156.59\text{ m}$
   * $t_f = 63.2 \cdot \sqrt{\frac{251.4 \times 10^6}{9.81 \cdot 76.2^2}} / 3600 = 1.166\text{ h}$ ($70.0\text{ min}$)
   * $z = 0.7$ (Froehlich 2008 recommendation for piping failure)

### 3.2 Benchmark Results Table

| Method / Configuration | Progression Mode | Breach Geometry $(B_{\text{avg}}, t_f, z)$ | Peak Outflow $Q_p$ $(\text{m}^3/\text{s})$ | Time-to-Peak $t_p$ $(\text{hr})$ | Discrepancy vs. Observed Slope-Area Estimate ($65,129\text{ m}^3/\text{s}$) |
|---|---|---|---|---|---|
| **Observed Benchmark** | *Slope-Area Post-Failure Survey (USGS)* | *Field high-water marks* | **$65,129$** | $\sim 1.25$ | Reference baseline |
| **Froehlich (1995)** | Empirical Regression ($Q_p = 0.607 V_w^{0.295} h_w^{1.24}$) | N/A (global empirical fit) | **$39,348$** | N/A | $-39.6\%$ (underpredicts) |
| **PravahX Routed** | Instantaneous Invert Drop (`horizontal_only`) | Observed ($151\text{ m}, 1.25\text{ h}, 0.5$) | **$61,684$** | $0.77$ | **$-5.29\%$** |
| **PravahX Routed** | Linear Vertical Drop (`vertical_and_horizontal`) | Observed ($151\text{ m}, 1.25\text{ h}, 0.5$) | **$83,391$** | $1.25$ | **$+28.0\%$** |
| **PravahX Routed** | Instantaneous Invert Drop (`horizontal_only`) | Froehlich 2008 ($156.6\text{ m}, 1.17\text{ h}, 0.7$) | **$63,422$** | $0.73$ | **$-2.62\%$** |
| **PravahX Routed** | Linear Vertical Drop (`vertical_and_horizontal`) | Froehlich 2008 ($156.6\text{ m}, 1.17\text{ h}, 0.7$) | **$86,805$** | $1.16$ | **$+33.3\%$** |

---

## 4. Benchmark Analysis and Findings

1. **Froehlich (1995) Empirical Underprediction:** The global Froehlich (1995) empirical peak regression underpredicts the Teton post-failure estimate by $\approx 40\%$. Global regressions aggregate failures across flat and wide reservoirs with gradual erosion where peak flow occurs after extensive pool drawdown.
2. **Effect of Vertical Progression Mode:**
   * When vertical progression is modeled as a linear invert drop from crest to bed over $t_f = 1.25\text{ h}$, the breach reaches its full width and maximum depth simultaneously at $t = t_f$. Because the reservoir drains more slowly during the early formation phase, the head $h(t)$ remains higher ($52.4\text{ m}$) at $t = 1.25\text{ h}$, producing a higher unconfined peak ($83,391\text{ m}^3/\text{s}$).
   * When horizontal-only progression is assumed (instantaneous pilot cut to base elevation followed by lateral expansion), peak discharge occurs earlier ($t = 0.77\text{ h}$) at $61,684\text{ m}^3/\text{s}$, matching within $5.3\%$ of the $65,129\text{ m}^3/\text{s}$ slope-area survey estimate.
3. **Caveat on Friction and 2D Drawdown:** Unconfined 1D level-pool broad-crested weir models neglect internal reservoir drawdown velocity head gradients and tailwater backwater submergence. In steep gorges, dynamic coupling with unsteady hydrodynamic solvers (Tier 1 / Tier 2) is required to resolve full channel attenuation downstream.
