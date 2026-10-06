# PravahX Science and Methods

This document records the formulae, scientific methods, physical assumptions, data sources, and verified citations used throughout the PravahX dam break and river blockage modelling system.

> [!IMPORTANT]
> **Citation Policy:**
> Only sources directly fetched and verified in this project are cited with active URLs and primary content. All other standard textbook relationships and historical literature references are labeled as `[UNVERIFIED - Reference without Live Fetch]` and their mechanisms are stated as explicit physical/mathematical reasoning.

---

## 1. Hydraulic Roughness (Manning's n)

Land cover classes from ESA WorldCover 10m v200 are mapped to empirical Manning's $n$ roughness coefficients.

*Physical Basis:* Hydraulic resistance varies with vegetation density, substrate grain size, and urban obstruction.
*Literature Reference:* Chow (1959), *Open-Channel Hydraulics* `[UNVERIFIED]`.

| Class ID | Land Cover Class | Manning's $n$ | Hydraulic Rationale |
|---|---|---|---|
| **10** | Tree cover | $0.100$ | High flow resistance from trunks and dense foliage |
| **20** | Shrubland | $0.070$ | Intermediate resistance from brush and woody shrubs |
| **30** | Grassland | $0.035$ | Moderate resistance from flexible ground vegetation |
| **40** | Cropland | $0.040$ | Agricultural fields with seasonal soil roughness |
| **50** | Built-up | $0.015$ | Smooth paved ground between structures |
| **60** | Bare / sparse vegetation | $0.025$ | Gravel, exposed alluvium, and sandbars |
| **70** | Snow and ice | $0.020$ | Low-friction packed snow and glacial surfaces |
| **80** | Permanent water bodies | $0.030$ | Natural alluvial riverbed |
| **90** | Herbaceous wetland | $0.050$ | Reeds and emergent marsh plants |
| **95** | Mangroves | $0.080$ | Complex prop-root networks in coastal zones |
| **100** | Moss and lichen | $0.030$ | Low-profile alpine tundra |

---

## 2. Tier 0: Rapid Inundation Envelope (Main-Reach HAND)

Tier 0 produces a rapid, conservative inundation envelope without solving the full 2D shallow water equations.

### 2.1 Governing Relations
1. **Manning's Equation for Channel Conveyance:**
   $$Q = \frac{1}{n} A R^{2/3} S_0^{1/2}$$
   where $R = A / P$, $n$ is reach-averaged roughness, $S_0$ is bed slope, $A$ is inundated cross-sectional area, and $P$ is wetted perimeter approximated by wetted width.
2. **Iterative Stage Solution:**
   Given scenario peak flow $Q_{\text{peak}}$, the stage $S$ is computed using bisection on the synthetic rating curve $Q(S)$ derived from the domain HAND distribution.
3. **Inundation Threshold:**
   Cells satisfying $\text{HAND} < S$ are marked as inundated.

### 2.2 Main-Reach Normalization & Tributary Limits
* **Problem:** Standard hydrologic Height Above Nearest Drainage normalizes elevation relative to every small tributary stream. Applying a uniform main-stem flood stage $S$ floods tributary valleys along their entire length (1–2 km up mountain slopes).
  * *Literature References:* Rennó et al. (2008); Nobre et al. (2011) `[UNVERIFIED]`.
* **PravahX Solution (Main-Stem Relative HAND):**
  1. The primary river reach is traced downstream from the scenario source point (or upstream from the domain outlet along the maximum flow accumulation path).
  2. $\text{HAND}_{\text{main}}(x, y)$ is computed strictly relative to main-reach cells:
     $$\text{HAND}_{\text{main}}(x, y) = z(x, y) - z(\text{nearest main-reach confluence})$$
  3. Near confluences where $z(x, y) \le z_{\text{confluence}} + S$, backwater inundation occurs naturally. As tributary beds climb above $z_{\text{confluence}} + S$, $\text{HAND}_{\text{main}}$ exceeds $S$ and upper tributaries remain dry.
  4. Disconnected fragment rings and local depression sinks are filtered using 8-connectivity flood-fill seeded from the main river corridor.

---

## 3. Reservoir Volume Estimation

### 3.1 Registered Dams
Monitored reservoirs retrieve storage capacity and stage-storage relationships from official dam registers (e.g. National Register of Large Dams).

### 3.2 Post-DEM Formed Blockages (New Lakes)
When a landslide dam or glacial lake forms *after* reference DEM acquisition, the DEM captures the exposed valley floor. Volume is calculated by integrating depth across the water mask:
$$V = \sum_{(x, y) \in \text{Lake}} \max\left(0, z_{\text{shore}} - z_{\text{DEM}}(x, y)\right) \cdot A_{\text{cell}}$$
where $z_{\text{shore}}$ is the median perimeter elevation.

### 3.3 Existing Lakes (Pre-DEM Acquisition)
* **Physical Constraint:** For water bodies present during DEM acquisition, the DEM records the flat water surface elevation $z_{\text{water}}$. Bed topography is invisible. Fitting a hypsometric exponent $m$ or volume below the waterline directly from DEM elevations inside the lake mask is physically impossible.
* **Approved Estimation Methods:**
  1. **Area-Volume Power-Law Scaling:** $V = \kappa \cdot A_{\text{km}^2}^\zeta$ ($V$ in $\text{km}^3$, $A$ in $\text{km}^2$). Parameters $\kappa$ and $\zeta$ must be supplied explicitly by the user (no defaults).
  2. **Terrain Slope Extrapolation:** Average terrain slope within a subaerial buffer around the lake perimeter is projected inward under an assumed valley hypsometry. This produces an order-of-magnitude estimate with high uncertainty ($\pm 50\%$ to $\pm 100\%$) and is flagged with an explicit warning.

---

## 4. Embankment Breach Regressions (HEC-RAS Manual)

* **Verified Source:** USACE HEC-RAS Hydraulic Reference Manual (Chapter 14):
  `https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/performing-a-dam-break-study-with-hec-ras/`

The HEC-RAS manual incorporates four empirical regression equations for embankment dam breach parameters:

1. **Froehlich (2008):**
   * Average width: $B_{\text{avg}} = 0.27 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.04}$ ($K_o = 1.3$ overtopping, $1.0$ piping)
   * Formation time: $t_f = 63.2 \cdot \sqrt{\frac{V_w}{g \cdot h_b^2}} / 3600.0$ (hours)
   * Side slope: $z = 1.0$ (overtopping), $0.7$ (piping)
2. **Froehlich (1995):**
   * Average width: $B_{\text{avg}} = 0.1803 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.19}$ ($K_o = 1.4$ overtopping, $1.0$ piping)
   * Formation time: $t_f = 0.00254 \cdot V_w^{0.53} \cdot h_b^{-0.90}$ (hours)
   * Side slope: $z = 1.4$ (overtopping), $0.9$ (piping)
3. **Von Thun and Gillette (1990):**
   * Average width: $B_{\text{avg}} = 2.5 \cdot h_w + C_b$ (where $C_b$ scales from $6.1\text{m}$ to $45.7\text{m}$ with storage $V_w$)
   * Formation time: $t_f = 0.015 \cdot h_w$ (hours)
   * Side slope: $z = 0.5$
4. **MacDonald and Langridge-Monopolis (1984):**
   * Eroded volume: $V_{\text{eroded}} = 0.0261 \cdot (V_w \cdot h_w)^{0.77}$ ($\text{m}^3$)
   * Formation time: $t_f = 0.0179 \cdot (V_{\text{eroded}})^{0.364}$ (hours)
   * Average width: $B_{\text{avg}} \approx \sqrt{V_{\text{eroded}} / h_b}$, side slope $z = 0.5$

### 4.1 Multi-Model Ensemble Uncertainty
Instead of arbitrary statistical multipliers, the ensemble uncertainty quantiles ($p10, p50, p90$) are derived directly from the distribution of predictions across these four HEC-RAS regression equations for a given dam geometry and storage volume.

---

## 5. Dynamic Trapezoidal Breach Hydrograph Routing

The outflow hydrograph $Q(t)$ is routed by integrating volume conservation through a time-varying trapezoidal broad-crested weir:
$$\frac{dV}{dt} = -Q(t)$$

### 5.1 Broad-Crested Weir Flow
Flow combines rectangular bottom and triangular side-slope components:
$$Q(t) = C_{v1} \cdot b(t) \cdot h(t)^{1.5} + C_{v2} \cdot z(t) \cdot h(t)^{2.5}$$
* $C_{v1} = 1.70 \text{ m}^{1/2}/\text{s}$: Rectangular broad-crested weir coefficient.
* $C_{v2} = 1.35 \text{ m}^{1/2}/\text{s}$: Triangular side-slope weir coefficient.
* *Verified Source:* USACE HEC-RAS Hydraulic Reference Manual Chapter 14.

### 5.2 Stage-Storage Hypsometry $h(t)$
Effective head $h(t)$ above the breach invert is computed from remaining storage volume:
$$V(h) = K_v \cdot h^m \implies h(t) = h_w \cdot \left(\frac{V(t)}{V_w}\right)^{1/m}$$
* $m = 1.0$: Vertical-walled prismatic basin ($A(h) = \text{const}$).
* $m = 2.0$: Parabolic cross-section valley ($A(h) \propto h$).
* $m = 3.0$: V-shaped canyon or pyramidal basin ($A(h) \propto h^2$).
* *Requirement:* $m$ must be supplied explicitly with no ungrounded defaults.

### 5.3 Breach Progression Modes
1. **Linear Vertical and Horizontal Progression (`vertical_and_horizontal`):**
   Breach invert drops linearly from dam crest to bed over formation time $t_f$ while width expands linearly:
   $$Z_{\text{invert}}(t) = \left(1 - \min\left(1.0, \frac{t}{t_f}\right)\right) \cdot h_b, \quad b(t) = b_{\text{bottom}} \cdot \min\left(1.0, \frac{t}{t_f}\right)$$
   *Verified Source:* USACE HEC-RAS Hydraulic Reference Manual Chapter 14.
2. **Horizontal-Only Progression (`horizontal_only`):**
   Instantaneous vertical notch incision to bed elevation, followed by lateral widening over $t_f$.

### 5.4 Independent Verification & Discrepancy Flagging
Every routed run computes the empirical Froehlich (1995) peak discharge:
$$Q_{p,\text{empirical}} = 0.607 \cdot V_w^{0.295} \cdot h_w^{1.24} \quad (\text{SI units})$$
* *Physical Reasons for Discrepancies:*
  1D unconfined weir routing assumes zero reservoir drawdown velocity gradients, no approach friction, and unconfined tailwater. Physical dam breaches experience 3D abutment contraction headlosses, earthen channel friction, tailwater backwater submergence ($k_s < 1.0$), and progressive headcut erosion lag.
* *Warning Threshold:* If $Q_{p,\text{routed}} / Q_{p,\text{empirical}} > 2.0$ or $< 0.5$, an operator warning is attached to the output.

---

## 6. Verified Project Sources

1. **USACE HEC-RAS Hydraulic Reference Manual (Chapter 14):**
   `https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/performing-a-dam-break-study-with-hec-ras/`
2. **USGS Open-File Report 77-765:**
   `https://pubs.er.usgs.gov/publication/ofr77765`
3. **ASDSO Dam Failures Case Study (Teton Dam):**
   `https://damfailures.org/case-study/teton-dam-idaho-1976/`
