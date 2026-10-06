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

The HEC-RAS manual documents five empirical regression methods for embankment dam breach parameters:

1. **Froehlich (2008):**
   * Average width: $B_{\text{avg}} = 0.27 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.04}$ ($K_o = 1.3$ overtopping, $1.0$ piping)
   * Formation time: $t_f = 63.2 \cdot \sqrt{\frac{V_w}{g \cdot h_b^2}} / 3600.0$ (hours)
   * Side slope: $z = 1.0$ (overtopping), $0.7$ (piping)
2. **Froehlich (1995a):**
   * Average width: $B_{\text{avg}} = 0.1803 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.19}$ ($K_o = 1.4$ overtopping, $1.0$ piping)
   * Formation time: $t_f = 0.00254 \cdot V_w^{0.53} \cdot h_b^{-0.90}$ (hours)
   * Side slope: $z = 1.4$ (overtopping), $0.9$ (piping)
3. **Von Thun and Gillette (1990):**
   * Average width: $B_{\text{avg}} = 2.5 \cdot h_w + C_b$ (where $C_b$ scales from $6.1\text{ m}$ to $45.7\text{ m}$ with storage $V_w$)
   * Formation time (function of erodibility):
     * Erosion-resistant / standard embankment: $t_f = 0.015 \cdot h_w$ (hours)
     * Easily erodible embankment: $t_f = 0.020 \cdot h_w$ (hours)
   * Side slope: $z = 0.5$ (piping), $1.0$ (overtopping)
4. **MacDonald and Langridge-Monopolis (1984):**
   * Volume of eroded material: $V_{\text{eroded}} = 0.0261 \cdot (V_w \cdot h_w)^{0.77}$ ($\text{m}^3$)
   * Formation time: $t_f = 0.0179 \cdot (V_{\text{eroded}})^{0.364}$ (hours)
   * Side slope: $z = 0.5$
   * *Breach Width Treatment:* In HEC-RAS, MacDonald & Langridge-Monopolis does NOT predict breach width through a standalone direct empirical equation. Instead, width is calculated by equating $V_{\text{eroded}}$ to the physical trapezoidal cross-section volume removed from the embankment ($V_{\text{eroded}} = h_b W_b C_{\text{avg}} + \dots$), which requires the dam's physical cross-section geometry (crest width and upstream/downstream embankment slopes). When dam geometry is not provided, MLM is excluded from the direct width spread and used exclusively in the formation time spread.
5. **Xu and Zhang (2009):**
   * Predicts top width $B_t$, bottom width $B_b$, and failure time $T_f$.
   * *Reason for Omission from Automated Spread:* Requires 5 multi-attribute categorical parameters (dam type, corewall type, foundation type, failure mode, erodibility index $F_r$) not available in standard single-polygon inventories, and its failure time definition incorporates both pre-breach initiation and post-breach enlargement phases, producing non-comparable development times unless individually calibrated.

### 4.1 Multi-Model Ensemble Spread (Min, Median, Max)
Because four empirical regression equations do not constitute a continuous statistical sample for percentiles, the ensemble uncertainty is reported strictly as the **Min**, **Median**, and **Max** of the method spread:
* **Width Spread:** Evaluated across the 3 direct width regression models: Froehlich (2008), Froehlich (1995), and Von Thun & Gillette (1990).
* **Formation Time Spread:** Evaluated across all 4 regression models: Froehlich (2008), Froehlich (1995), Von Thun & Gillette (1990), and MacDonald & Langridge-Monopolis (1984).

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

## 7. Tier 2: 3D Smoothed Particle Hydrodynamics (DualSPHysics)

For complex near-field dam break hydraulics, 3D Smoothed Particle Hydrodynamics (SPH) models free-surface fragmentation, plunging waves, vertical accelerations, and turbulent surge front propagation without mesh distortion.

### 7.1 SPH Governing Equations

1. **Continuity Equation (Mass Conservation):**
   $$\frac{d\rho_a}{dt} = \sum_b m_b (\mathbf{v}_a - \mathbf{v}_b) \cdot \nabla_a W_{ab} + \mathcal{D}_a$$
   where $\rho_a$ is particle density, $m_b$ is particle mass, $\mathbf{v}$ is velocity, $W_{ab}$ is the kernel function, and $\mathcal{D}_a$ is the Molteni & Colagrossi (2009) $\delta$-SPH density diffusion term ($\delta = 0.1$) to stabilize acoustic pressure fluctuations.

2. **Momentum Equation (Navier-Stokes SPH):**
   $$\frac{d\mathbf{v}_a}{dt} = -\sum_b m_b \left(\frac{P_a}{\rho_a^2} + \frac{P_b}{\rho_b^2} + \Pi_{ab}\right) \nabla_a W_{ab} + \mathbf{g}$$
   where $P$ is pressure, $\mathbf{g} = (0, 0, -9.81)\text{ m/s}^2$, and $\Pi_{ab}$ is Monaghan artificial viscosity ($\alpha = 0.01$).

3. **Tait's Weakly Compressible Equation of State (EOS):**
   $$P = B \left[\left(\frac{\rho}{\rho_0}\right)^\gamma - 1\right], \quad B = \frac{c_0^2 \rho_0}{\gamma}$$
   with $\gamma = 7.0$, $\rho_0 = 1000\text{ kg/m}^3$, and numerical sound speed $c_0 \approx 10 \cdot \sqrt{g h_{\text{max}}}$ ensuring density variations remain under $1\%$ ($\text{Mach} < 0.1$).

4. **Kernel Function & Time Integration:**
   * **Kernel:** Wendland quintic kernel (Kernel = 2) with compact support radius $2h$.
   * **Time Integrator:** Symplectic Position Verlet (StepAlgorithm = 2) with dynamic CFL condition ($\text{CFL} = 0.2$).

---

## 8. Idealized Dam-Break Reference Solution: Martin & Moyce (1952)

* *Literature Reference:* Martin & Moyce (1952), *An Experimental Study of the Collapse of Liquid Columns on a Rigid Horizontal Plane*, Phil. Trans. R. Soc. Lond. A `[UNVERIFIED - Standard SPHERIC Benchmark 2 Reference]`.

### 8.1 Non-Dimensional Scaling
For a rectangular water column of initial base width $a$ and height $h_0 = 2a$:
* Non-dimensional time: $t^* = t \cdot \sqrt{\frac{2g}{a}}$
* Non-dimensional surge front position: $x^* = \frac{x}{a}$

### 8.2 Surge Front Kinematics
1. **Initial Hydrostatic Acceleration Phase ($t^* < 1.0$):**
   $$x^*(t^*) = 1.0 + 0.5 \cdot (t^*)^2$$
2. **Asymptotic Constant-Surge Propagation ($t^* \ge 1.0$):**
   $$x^*(t^*) = 1.0 + 2.0 \cdot (t^* - 0.4)$$

---

---

## 9. Multi-Tier Coupling & Multi-Dam Cascade Formulations

### 9.1 SPH-to-Delft3D Flux Handoff & Volume Conservation
At the spatial boundary where 3D SPH terminates and 2D SWE begins, the cumulative water volume $V(T)$ passing through the downstream measurement plane is integrated via the trapezoidal rule:
$$V_{\text{SPH}} = \int_0^T Q_{\text{SPH}}(t)\,dt \approx \sum_{k=1}^N \frac{Q_k + Q_{k-1}}{2} (t_k - t_{k-1})$$

The generated Delft3D FM `.bc` boundary condition time-series $Q_{\text{FM}}(t)$ must satisfy strict mass conservation:
$$\text{Relative Error} = \frac{|V_{\text{FM}} - V_{\text{SPH}}|}{V_{\text{SPH}}} \le \epsilon_{\text{tol}} \quad (\epsilon_{\text{tol}} = 0.01 = 1.0\%)$$

### 9.2 Cascade Dam Failure & Overtopping Analysis
For cascading reservoirs connected by river reaches:
1. **Wave Celerity & Channel Lag:** Flood wave transit time over channel distance $L$ at mean celerity $c = \sqrt{g \bar{d}} + \bar{u}$:
   $$\Delta t_{\text{lag}} = \frac{L}{c}$$
2. **Channel Routing Attenuation:** Peak discharge attenuation based on channel roughness and length:
   $$Q_{\text{arriving, peak}} = Q_{\text{upstream, peak}} \cdot \exp\left(-\frac{\alpha \cdot L}{1000}\right)$$
3. **Downstream Reservoir Surcharge Routing:**
   $$h(t) = \left(\frac{V(t)}{K_v}\right)^{1/m}$$
   If peak reservoir stage exceeds the dam crest ($z_{\text{peak}} > z_{\text{crest}}$), an overtopping failure is triggered. Chained breach geometry and hydrograph are computed using the verified Froehlich (2008) formulation with combined storage $V_{\text{combined}} = V_{\text{storage}} + V_{\text{flood wave}}$.

---

## 10. Multi-Tier Comparison, Agreement Mapping, and Uncertainty

### 10.1 Spatial Extent Metrics
Comparing Model A against Model B over binary inundated masks ($d \ge d_{\text{thresh}}$):
- **Critical Success Index / IoU:** $\text{IoU} = \frac{TP}{TP + FP + FN}$
- **Dice F1-Score:** $F_1 = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$
- **Precision (Hit Rate):** $\text{Precision} = \frac{TP}{TP + FP}$
- **Recall (Sensitivity):** $\text{Recall} = \frac{TP}{TP + FN}$
- **False Alarm Ratio:** $\text{FAR} = \frac{FP}{TP + FP}$

### 10.2 Depth and Arrival-Time Differences (Mutually Wet Cells)
- **Depth RMSE:** $\text{RMSE}_d = \sqrt{\frac{1}{N_{TP}} \sum (d_A - d_B)^2}$
- **Depth MAE:** $\text{MAE}_d = \frac{1}{N_{TP}} \sum |d_A - d_B|$
- **Depth Bias:** $\text{Bias}_d = \frac{1}{N_{TP}} \sum (d_A - d_B)$
- **Arrival Time MAE:** $\text{MAE}_t = \frac{1}{N_{\text{arr}}} \sum |t_{\text{arr}, A} - t_{\text{arr}, B}|$

### 10.3 5-Class Spatial Agreement Categorization
Grid cells are classified into 5 discrete categories:
- **Class 0 (Both Dry):** $d_A < d_{\text{thresh}}$ and $d_B < d_{\text{thresh}}$
- **Class 1 (Model A Only):** $d_A \ge d_{\text{thresh}}$ and $d_B < d_{\text{thresh}}$
- **Class 2 (Model B Only):** $d_A < d_{\text{thresh}}$ and $d_B \ge d_{\text{thresh}}$
- **Class 3 (Agreed Wet):** $d_A \ge d_{\text{thresh}}$, $d_B \ge d_{\text{thresh}}$, and $|d_A - d_B| \le \Delta d_{\text{thresh}}$ ($\Delta d_{\text{thresh}} = 0.5\text{ m}$)
- **Class 4 (Disagreed Wet):** $d_A \ge d_{\text{thresh}}$, $d_B \ge d_{\text{thresh}}$, and $|d_A - d_B| > \Delta d_{\text{thresh}}$

### 10.4 Ensemble & Uncertainty Aggregation
Across $M$ stochastic / parameter spread scenarios:
- **Inundation Exceedance Probability:** $P(\text{depth} \ge d_{\text{thresh}}) = \frac{1}{M} \sum_{k=1}^M \mathbb{I}(d_k \ge d_{\text{thresh}})$
- **Percentile Depth Fields:** p10 (optimistic/minimum), p50 (median/expected), p90 (conservative/maximum) calculated cell-by-cell.

### 10.5 Two-Pass Mesh & Particle Refinement Criteria
Identifies high-resolution candidate sub-domains for Pass 2 based on:
1. **Depth Gradient:** $|\nabla d| = \sqrt{\left(\frac{\partial d}{\partial x}\right)^2 + \left(\frac{\partial d}{\partial y}\right)^2} \ge \tau_{\text{grad}}$ ($\tau_{\text{grad}} = 0.15\text{ m/m}$)
2. **Supercritical Flow / Hydraulic Jump Vicinity:** $Fr = \frac{u}{\sqrt{g d}} \ge 0.90$

---

## 11. Verified Project Sources

1. **USACE HEC-RAS Hydraulic Reference Manual (Chapter 14):**
   `https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/performing-a-dam-break-study-with-hec-ras/`
2. **USGS Open-File Report 77-765:**
   `https://pubs.er.usgs.gov/publication/ofr77765`
3. **ASDSO Dam Failures Case Study (Teton Dam):**
   `https://damfailures.org/case-study/teton-dam-idaho-1976/`
4. **USBR Teton History & Facility Documentation:**
   `https://www.usbr.gov/pn/snakeriver/dams/uppersnake/teton/index.html`


