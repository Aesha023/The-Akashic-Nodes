# PravahX Science and Methods

This document records the formulae, scientific methods, physical assumptions, data sources, and literature citations used throughout the PravahX dam break and river blockage modelling system.

---

## 1. Hydraulic Roughness (Manning's n)

The mapping from ESA WorldCover 10m v200 land cover classes to Manning's $n$ roughness coefficients is adapted from open-channel hydraulic standards:
* **Primary Citation:** Chow, V. T. (1959), *Open-Channel Hydraulics*, McGraw-Hill, New York, Chapter 5 ("Theoretical Concepts of Surface Roughness"), Table 5-6 ("Values of the Roughness Coefficient n"), pp. 108–113.
* **Large-scale Inundation Classification:** Baugh, C. A., Bates, P. D., et al. (2013), *A simple efficient approach to large scale flood routing*, Water Resources Research, 49(9), pp. 5758–5771 (Section 3.2 "Roughness parameterization").

| Class ID | Land Cover Class | Manning's $n$ | Notes |
|---|---|---|---|
| **10** | Tree cover | $0.100$ | Dense floodplain forest |
| **20** | Shrubland | $0.070$ | Brush and scattered woody vegetation |
| **30** | Grassland | $0.035$ | Short/tall prairie grass |
| **40** | Cropland | $0.040$ | Cultivated agricultural land |
| **50** | Built-up | $0.015$ | Smooth paved surfaces between structures |
| **60** | Bare / sparse vegetation | $0.025$ | Gravel, sandbars, and bare soil |
| **70** | Snow and ice | $0.020$ | Glacial surfaces and seasonal ice |
| **80** | Permanent water bodies | $0.030$ | Natural main river channel |
| **90** | Herbaceous wetland | $0.050$ | Marsh and wetlands |
| **95** | Mangroves | $0.080$ | Tidal and coastal mangrove swamps |
| **100** | Moss and lichen | $0.030$ | Alpine tundra ground cover |

---

## 2. Tier 0: Rapid Inundation Envelope (Main-Reach HAND)

Tier 0 produces a rapid, physically bounded inundation envelope without solving the 2D shallow water equations.

### 2.1 Governing Equations
1. **Reach-Averaged Manning's Relation:**
   $$Q = \frac{1}{n} A R^{2/3} S_0^{1/2}$$
   where $R = A / P$, $n$ is reach-averaged roughness, $S_0$ is reach bed slope, $A$ is inundated cross-sectional area, and $P$ is wetted perimeter approximated by wetted width.
   * *Citation:* Chow, V. T. (1959), *Open-Channel Hydraulics*, Chapter 6 ("Flow in Open Channels"), Eq. 6-1, p. 128.
2. **Iterative Stage Solution:**
   Given a scenario peak discharge $Q_{\text{peak}}$, the equilibrium stage $S$ is resolved via bisection search on the synthetic rating curve $Q(S)$ derived from the domain HAND distribution.
3. **Inundation Condition:**
   All domain cells satisfying $\text{HAND} < S$ are marked as potentially inundated.

### 2.2 Main-Reach Drainage Normalization & Tributary Limits
* **Background:** Standard Height Above Nearest Drainage (HAND) normalizes topography relative to every stream in the extracted drainage network. Consequently, applying a single main-stem flood stage $S$ indiscriminately floods tributary valleys kilometers up steep mountain slopes.
  * *Citations:*
    - Rennó, C. D., Nobre, A. D., et al. (2008), *HAND, a new terrain descriptor using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia*, Remote Sensing of Environment, 112(9), pp. 3469–3481 (Section 2.1).
    - Nobre, A. D., Cuartas, L. A., et al. (2011), *HEIGHT ABOVE THE NEAREST DRAINAGE – a hydrologically normalized Digital Elevation Model for terrain analysis and environmental applications*, Journal of Hydrology, 404(1-2), pp. 13–29 (Section 3).
* **PravahX Main-Reach Normalization Method:**
  To represent physical backwater behavior where flood waters only enter tributaries where the main channel water surface elevation exceeds the tributary bed:
  1. The main drainage reach is isolated either downstream from the dam/blockage source coordinate or upstream along the dominant flow accumulation spine.
  2. $\text{HAND}_{\text{main}}(x, y)$ is computed strictly relative to the main reach cells:
     $$\text{HAND}_{\text{main}}(x, y) = z(x, y) - z(\text{nearest main-reach confluence})$$
  3. Near the tributary confluence, where $z(x, y) \le z_{\text{confluence}} + S$, tributary mouth cells flood correctly as backwater. As the tributary bed ascends into the mountain slopes, $z(x, y)$ exceeds the stage and the upper tributary remains dry.
  4. Disconnected fragments, saddle sinks, and isolated depression rings are filtered using 8-connectivity seed expansion from the active channel spine.

---

## 3. Reservoir Volume Estimation

### 3.1 Registered Dams
For monitored reservoirs, storage capacity and stage-storage relationships are retrieved directly from official dam safety databases (e.g., National Register of Large Dams).

### 3.2 Post-DEM Blockages and New Lakes
When a landslide dam or glacial lake forms *after* the reference DEM acquisition date, the pre-existing valley topography represents the true bed. Storage volume is determined by integrating water depth over the detected lake mask:
$$V = \sum_{(x, y) \in \text{Lake}} \max\left(0, z_{\text{shore}} - z_{\text{DEM}}(x, y)\right) \cdot A_{\text{cell}}$$
where $z_{\text{shore}}$ is the median elevation along the lake perimeter.

### 3.3 Existing Lakes (Pre-DEM Acquisition)
* **Physical Constraint:** For lakes present when the DEM was acquired (e.g. Copernicus GLO-30, SRTM), the DEM records only the flat water surface elevation $z_{\text{water}}$. Submerged bathymetry is absent.
* **Prohibition:** Hypsometric stage-storage exponent $m$ and submerged volume **cannot** be fitted from DEM cell values inside the water mask.
* **Approved Estimation Methods:**
  1. **Area-Volume Power-Law Scaling:**
     $$V = \kappa \cdot A_{\text{km}^2}^\zeta \quad (\text{with } V \text{ in km}^3)$$
     *Citation:* Huggel, C., Kääb, A., et al. (2002), *Remote sensing based assessment of hazards from glacier lake outbursts: a case study in the Swiss Alps*, Canadian Geotechnical Journal, 39(2), pp. 316–330 (Table 2, p. 322).
     *Implementation:* Parameters $\kappa$ and $\zeta$ depend on geomorphic lake type and must be supplied explicitly with no ungrounded universal defaults.
  2. **Subaerial Terrain Slope Extrapolation:**
     Surrounding slopes in the terrain buffer immediately above the waterline are extrapolated inward to approximate an idealized parabolic/conical basin geometry.
     *Uncertainty:* Such extrapolations carry wide uncertainty ($\pm 50\%$ to $\pm 100\%$) and are explicitly tagged with user warnings. Official area-capacity curves must be used when available.

---

## 4. Embankment Breach Parameter Prediction

Empirical regressions from Froehlich (2008) predict final breach geometry and formation time based on 74 historical embankment dam failures:
* **Primary Citation:** Froehlich, D. C. (2008), *Embankment dam breach parameters and their uncertainties*, ASCE Journal of Hydraulic Engineering, 134(12), pp. 1708–1721.

1. **Average Breach Width ($B_{\text{avg}}$):**
   $$B_{\text{avg}} = 0.27 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.04}$$
   where $K_o = 1.3$ for overtopping and $1.0$ for piping/internal erosion (Eq. 1, p. 1711); $V_w$ is volume in $\text{m}^3$; $h_b$ is breach height in $\text{m}$.
2. **Breach Formation Time ($t_f$):**
   $$t_f = 63.2 \cdot \sqrt{\frac{V_w}{g \cdot h_b^2}} \quad (\text{in seconds})$$
   (Eq. 2, p. 1711).
3. **Breach Side Slope ($z$):**
   $z = 1.0$ ($1\text{H}:1\text{V}$) for overtopping; $z = 0.7$ ($0.7\text{H}:1\text{V}$) for piping (p. 1711).
4. **Bottom Breach Width ($b_{\text{bottom}}$):**
   $$b_{\text{bottom}} = \max\left(0.0, B_{\text{avg}} - z \cdot h_b\right)$$

---

## 5. Dynamic Trapezoidal Breach Hydrograph Routing

The outflow hydrograph $Q(t)$ is routed by solving continuity for reservoir storage through a growing trapezoidal broad-crested weir:
$$\frac{dV}{dt} = -Q(t)$$

### 5.1 Broad-Crested Weir Hydraulics
Flow through the trapezoidal breach combines rectangular bottom and triangular side-slope components:
$$Q(t) = C_{v1} \cdot b(t) \cdot h(t)^{1.5} + C_{v2} \cdot z(t) \cdot h(t)^{2.5}$$
* $C_{v1} = 1.70 \text{ m}^{1/2}/\text{s}$: Rectangular broad-crested weir coefficient.
  * *Citation:* Chow, V. T. (1959), *Open-Channel Hydraulics*, Table 12-1, p. 364; USACE (2020), *HEC-RAS Hydraulic Reference Manual*, CPD-69, Version 6.0, Chapter 14, p. 14-4.
* $C_{v2} = 1.35 \text{ m}^{1/2}/\text{s}$: Triangular side-slope weir coefficient ($2.45$ in US Customary).
  * *Citation:* Wahl, T. L. (1998), *Prediction of Embankment Dam Breach Parameters*, USBR Report DSO-98-004, Eq. 2, p. 12; Fread, D. L. (1988), *BREACH: An Erosion Model for Earthen Dam Failures*, NWS Report, p. 6.

### 5.2 Reservoir Hypsometry and Head ($h(t)$)
The effective head $h(t)$ above the breach invert is computed from remaining volume via power-law hypsometry:
$$V(h) = K_v \cdot h^m \implies h(t) = h_w \cdot \left(\frac{V(t)}{V_w}\right)^{1/m}$$
* *Citation:* Singh, V. P. (1996), *Dam Breach Modeling Technology*, Kluwer Academic Publishers, Chapter 4 ("Hydraulics of Dam-Break Flow"), pp. 88–92.
* **Exponent $m$:**
  * $m = 1.0$: Vertical-walled prismatic basin ($A(h) = \text{constant}$).
  * $m = 2.0$: Parabolic valley cross-section ($A(h) \propto h$).
  * $m = 3.0$: V-shaped canyon or pyramidal basin ($A(h) \propto h^2$).
  * *Requirement:* $m$ is a required input parameter with no ungrounded defaults.

### 5.3 Breach Progression Modes
1. **Linear Vertical and Horizontal Progression (`vertical_and_horizontal`):**
   The invert drops linearly from the dam crest to final bed elevation while the width expands linearly over formation time $t_f$:
   $$Z_{\text{invert}}(t) = \left(1 - \min\left(1.0, \frac{t}{t_f}\right)\right) \cdot h_b, \quad b(t) = b_{\text{bottom}} \cdot \min\left(1.0, \frac{t}{t_f}\right)$$
   *Citation:* USACE (2020), *HEC-RAS Hydraulic Reference Manual*, CPD-69, Version 6.0, Chapter 14, Section "Breach Progression", pp. 14-8 to 14-11.
2. **Horizontal-Only Progression (`horizontal_only`):**
   Instantaneous vertical pilot cut to base elevation, followed by lateral widening over $t_f$.

### 5.4 Independent Verification Check (Froehlich, 1995)
Every hydrograph execution calculates the independent empirical peak discharge:
$$Q_{p,\text{empirical}} = 0.607 \cdot V_w^{0.295} \cdot h_w^{1.24} \quad (\text{SI units: } \text{m}^3/\text{s}, \text{m}^3, \text{m})$$
* *Citation:* Froehlich, D. C. (1995), *Peak Outflow from Breached Embankment Dams*, ASCE Journal of Water Resources Planning and Management, 121(1), pp. 90–97 (Eq. 1, p. 91).
* **Engineering Rationale for Peak Discrepancies:**
  Ideal unconfined broad-crested weir routing evaluates 1D frictionless weir conveyance at the breach throat assuming infinite reservoir approach conveyance and zero tailwater submergence. In real physical embankment failures (which calibrate the Froehlich 1995 regression):
  1. 3D turbulent contraction at the breach abutments and boundary shear in the earthen channel reduce effective conveyance.
  2. Dynamic 2D drawdown velocity gradients form in the upstream pool near the breach, reducing local static energy head.
  3. Downstream tailwater accumulation produces backwater submergence ($k_s < 1.0$).
  4. Progressive headcut migration delays peak outflow until after significant pool volume has drained.
* **Automated Warning Threshold:** When $Q_{p,\text{routed}} / Q_{p,\text{empirical}} > 2.0$ or $< 0.5$, an operator review warning is attached to the output.

---

## 6. Primary Literature & Citation Mapping

1. **Baugh, C. A., Bates, P. D., et al. (2013).** *A simple efficient approach to large scale flood routing.* Water Resources Research, 49(9), pp. 5758–5771. [Roughness parameterization: Section 3.2]
2. **Chow, V. T. (1959).** *Open-Channel Hydraulics.* McGraw-Hill, New York. [Roughness tables: Chapter 5, pp. 108–113; Manning formula: Chapter 6, p. 128; Weir coefficients: Chapter 12, p. 364]
3. **Fread, D. L. (1988).** *BREACH: An Erosion Model for Earthen Dam Failures.* Hydrologic Research Laboratory, National Weather Service, NOAA, Silver Spring, MD. [Breach hydraulics: Section "Hydraulics of Breach Flow", pp. 5–18]
4. **Froehlich, D. C. (1995).** *Peak Outflow from Breached Embankment Dams.* ASCE Journal of Water Resources Planning and Management, 121(1), pp. 90–97. [Peak discharge regression: Eq. 1, p. 91]
5. **Froehlich, D. C. (2008).** *Embankment dam breach parameters and their uncertainties.* ASCE Journal of Hydraulic Engineering, 134(12), pp. 1708–1721. [Breach geometry & timing: Eqs. 1–3, Table 1, p. 1711]
6. **Huggel, C., Kääb, A., et al. (2002).** *Remote sensing based assessment of hazards from glacier lake outbursts: a case study in the Swiss Alps.* Canadian Geotechnical Journal, 39(2), pp. 316–330. [Area-volume scaling: Table 2, p. 322]
7. **Nobre, A. D., Cuartas, L. A., et al. (2011).** *HEIGHT ABOVE THE NEAREST DRAINAGE – a hydrologically normalized Digital Elevation Model for terrain analysis and environmental applications.* Journal of Hydrology, 404(1-2), pp. 13–29. [HAND algorithm: Section 3, pp. 16–22]
8. **Ray, H. A., Simons, R. R., et al. / USGS (1977).** *The Failure of Teton Dam: Flood of June 5–7, 1976.* USGS Professional Paper 1028. [Observed flood peak: Table 3, p. 55; Reservoir storage: p. 11]
9. **Rennó, C. D., Nobre, A. D., et al. (2008).** *HAND, a new terrain descriptor using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia.* Remote Sensing of Environment, 112(9), pp. 3469–3481. [HAND formulation: Section 2.1, pp. 3470–3473]
10. **Singh, V. P. (1996).** *Dam Breach Modeling Technology.* Water Science and Technology Library, Kluwer Academic Publishers, Dordrecht. [Stage-storage hypsometry: Chapter 4, pp. 88–92]
11. **US Army Corps of Engineers (2020).** *HEC-RAS Hydraulic Reference Manual, Version 6.0.* Hydrologic Engineering Center, Davis, CA. [Breach progression & weir equations: Chapter 14, pp. 14-1 to 14-25]
12. **Wahl, T. L. (1998).** *Prediction of Embankment Dam Breach Parameters: A Literature Review and Needs Assessment.* Dam Safety Research Report DSO-98-004, U.S. Bureau of Reclamation, Denver, CO. [Trapezoidal weir flow: Eq. 2, p. 12; Dam failure database: Table 1, p. 11; Peak flow comparison: Section 3, pp. 24–31]
13. **Zheng, X., Maidment, D. R., et al. (2018).** *Geo-statistical representation of river width and depth using HAND.* Water Resources Research, 54(8), pp. 5857–5873. [Cross-section derivation: Section 2.2, pp. 5860–5864]
