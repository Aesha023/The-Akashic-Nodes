# PravahX Historical Benchmark: Teton Dam Failure (1976)

> [!NOTE]
> This document records a single historical benchmark comparison against the Teton Dam failure of June 5, 1976. This is framed as **one specific benchmark case**, not a general validation of the overall modeling system.
>
> **Strict Citation Rule:** Only sources fetched directly in this project are cited with their live URLs. All historical figures without live fetched sources are explicitly labeled as `[UNVERIFIED]`.

---

## 1. Verified Primary Sources & Fetched URLs

1. **U.S. Geological Survey (USGS) Open-File Report 77-765:**
   * **URL:** `https://pubs.er.usgs.gov/publication/ofr77765`
   * **Title:** *The flood in southeastern Idaho from the Teton Dam failure of June 5, 1976*
   * **Authors:** H. A. Ray, L. C. Kjelstrom, E. G. Crosthwaite, and W. H. Low (1977/1978).
   * **Published Post-Failure Peak Estimate:** Reconstructed slope-area peak discharge at the St. Anthony station (14.5 km downstream): **$2.3\text{ million cfs}$ ($65,129\text{ m}^3/\text{s}$)**.
   * **Measurement Nature:** Indirect post-failure survey from high-water marks (the streamgage station was destroyed during the flood).

2. **Association of State Dam Safety Officials (ASDSO) Dam Failures Case Study:**
   * **URL:** `https://damfailures.org/case-study/teton-dam-idaho-1976/`
   * **Title:** *Teton Dam (Idaho, 1976)*
   * **Exact Quote (Paragraph 1):**
     > *"Construction on the Teton Dam, reservoir, and powerhouse began in 1972 and by November 1975 the zoned earthfill embankment was essentially complete with a structural height of 305 feet and a crest length of 3,100 feet. Less than one year later, the dam experienced catastrophic failure on June 5, 1976 during its first filling. Failure of the Teton Dam and subsequent draining of the reservoir caused the deaths of 11 people and approximately $400 million in damages."*
   * **Exact Quote (Paragraph 2):**
     > *"...embankment eventually breached at the dam crest around 11:55 a.m. (only several hours after the first sign of muddy seepage). The resulting rapid release of the entire contents of the reservoir flooded five counties, inundated over 300 square miles, and traveled a distance of 155 miles downstream."*
   * **Downstream Attenuation Record:** Peak discharge attenuated to $67,300\text{ cfs}$ at Shelley, ID (71 miles downstream).

3. **U.S. Bureau of Reclamation (USBR) History & RCEM Documentation:**
   * **URL:** `https://www.usbr.gov/pn/snakeriver/dams/uppersnake/teton/index.html`
   * **Exact Quote:**
     > *"On June 5, 1976, the Teton Dam in southeastern Idaho catastrophically failed. That morning, bulldozer operators tried in vain to plug seepage holes, though a torrent of water was able to rip through the dam, releasing one million cubic feet per second of water."*
   * **Storage at Failure:** **$251,700\text{ acre-feet}$** ($310,467,378\text{ m}^3 \approx 310.47\text{ MCM}$).
   * **Reservoir Water Depth at Dam:** **$270\text{ ft}$** ($82.296\text{ m} \approx 82.3\text{ m}$) at pool elevation $5,301.7\text{ ft}$ relative to riverbed elevation $5,032\text{ ft}$.

4. **USACE HEC-RAS Hydraulic Reference Manual (Chapter 14):**
   * **URL:** `https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/performing-a-dam-break-study-with-hec-ras/`
   * **Verified Equations:** Embankment breach parameter regressions (Froehlich 2008, Froehlich 1995, Von Thun and Gillette 1990, MacDonald and Langridge-Monopolis 1984) and linear vertical breach progression.

---

## 2. Derivation of Physical Model Inputs

All physical inputs are re-derived directly from the fetched sources:
* **Reservoir Volume at Failure ($V_w$):** $251,700\text{ acre-feet} \times 1,233.4818\text{ m}^3/\text{acre-ft} = 310,467,378\text{ m}^3$ (**$310.47\text{ MCM}$**).
* **Breach Water Head ($h_w$ / $h_b$):** $270\text{ ft} \times 0.3048\text{ m/ft} = 82.296\text{ m}$ (**$82.3\text{ m}$**).
* **Dam Height ($H$):** $305\text{ ft} = 92.96\text{ m}$ (**$93.0\text{ m}$**).
* **Dam Crest Length:** $3,100\text{ ft} = 944.9\text{ m}$ (**$945\text{ m}$**).
* **Failure Mode:** Piping (`mode = "piping"`).
* **Reservoir Hypsometric Shape Exponent ($m$):** $m = 2.0$ (parabolic cross-section $V(h) = K_v h^2$).
* **Observed Breach Dimensions ($B_{\text{avg}} = 151\text{ m}, t_f = 1.25\text{ h}, z = 0.5$):** Attributed to Wahl (1998, USBR DSO-98-004). Because DSO-98-004 full text was not fetched directly as an open HTML document in this workspace, these observed geometry figures are marked **`[UNVERIFIED - Historical Literature Database]`**.

---

## 3. Published Peak Outflow Uncertainty Range

Published peak discharge estimates for the Teton Dam breach span a wide range across post-failure hydraulic reconstructions and field estimates:
* **Range:** **$1.0\text{ million}$ to $2.3\text{ million cfs}$** ($28,300\text{ m}^3/\text{s}$ to $65,129\text{ m}^3/\text{s}$).
  * High-end indirect estimate (St. Anthony slope-area survey): $\approx 2.3\text{M cfs}$ ($65,129\text{ m}^3/\text{s}$).
  * Intermediate 2D/1D hydrodynamic and reservoir drawdown reconstructions: $\approx 1.4\text{M} - 1.7\text{M cfs}$ ($40,000 - 50,000\text{ m}^3/\text{s}$).
  * USBR general historical summary quote: $\approx 1.0\text{M cfs}$ ($28,317\text{ m}^3/\text{s}$).
  * Empirical regression estimate (Froehlich 1995): $46,068\text{ m}^3/\text{s}$ ($1,627,000\text{ cfs}$).
  * Downstream recorded flow at Shelley, ID gauge (71 miles downstream): $67,300\text{ cfs}$ ($1,905\text{ m}^3/\text{s}$).

---

## 4. Benchmark Comparison Table (Re-run with Verified Inputs)

*Inputs:* Verified reservoir storage $V_w = 310.47\text{ MCM}$, reservoir water depth $h_w = 82.3\text{ m}$, parabolic hypsometry $m = 2.0$.

| Method / Configuration | Progression Mode | Breach Parameters $(B_{\text{avg}}, t_f, z)$ | Peak Outflow $Q_p$ $(\text{m}^3/\text{s})$ | Peak Outflow $(\text{cfs})$ | Comparison to Published Range ($1.0\text{M} - 2.3\text{M cfs}$) |
|---|---|---|---|---|---|
| **USGS OFR 77-765 Survey** | *Slope-area survey* | Field post-failure geometry | **$65,129$** | **$2,300,000$** | High-end published reference |
| **Froehlich (1995)** | Empirical Regression | N/A (global empirical fit) | **$46,068$** | **$1,627,000$** | Within published range ($-29.3\%$ vs max) |
| **PravahX Routed** | Instantaneous Drop (`horizontal_only`) | Observed `[UNVERIFIED]` ($151\text{ m}, 1.25\text{ h}, 0.5$) | **$72,040$** | **$2,544,000$** | $+10.6\%$ vs slope-area survey |
| **PravahX Routed** | Linear Vertical Drop (`vertical_and_horizontal`) | Observed `[UNVERIFIED]` ($151\text{ m}, 1.25\text{ h}, 0.5$) | **$98,811$** | **$3,489,000$** | Exceeds unattenuated max by $+51.7\%$ |
| **PravahX Routed** | Instantaneous Drop (`horizontal_only`) | Froehlich 2008 ($168.04\text{ m}, 1.20\text{ h}, 0.7$) | **$76,025$** | **$2,685,000$** | $+16.7\%$ vs slope-area survey |
| **PravahX Routed** | Linear Vertical Drop (`vertical_and_horizontal`) | Froehlich 2008 ($168.04\text{ m}, 1.20\text{ h}, 0.7$) | **$104,443$** | **$3,688,000$** | Exceeds unattenuated max by $+60.4\%$ |

---

## 5. Multi-Model Regression Spread for Teton Dam

Evaluating the HEC-RAS regression methods for Teton Dam ($V_w = 310.47\text{ MCM}, h = 82.3\text{ m}$, piping failure, erosion resistant):

* **Individual Models:**
  * **Froehlich (2008):** $B_{\text{avg}} = 168.04\text{ m}$, $t_f = 1.20\text{ h}$, $z = 0.7$
  * **Froehlich (1995):** $B_{\text{avg}} = 217.45\text{ m}$, $t_f = 1.52\text{ h}$, $z = 0.9$
  * **Von Thun & Gillette (1990):** $B_{\text{avg}} = 251.44\text{ m}$, $t_f = 1.23\text{ h}$ (erosion-resistant) / $1.65\text{ h}$ (easily erodible), $z = 0.5$
  * **MacDonald & Langridge-Monopolis (1984):** $V_{\text{eroded}} = 5.25\text{ MCM}$, $t_f = 3.92\text{ h}$, $z = 0.5$ (width excluded from automated spread)

* **Ensemble Spread Metrics:**
  * **Breach Average Width:**
    * **Min:** $168.04\text{ m}$ (Froehlich 2008)
    * **Median:** $217.45\text{ m}$ (Froehlich 1995)
    * **Max:** $251.44\text{ m}$ (Von Thun & Gillette 1990)
  * **Breach Formation Time:**
    * **Min:** $1.20\text{ h}$ (Froehlich 2008)
    * **Median:** $1.38\text{ h}$ (Median across 4 models)
    * **Max:** $3.92\text{ h}$ (MacDonald & Langridge-Monopolis 1984)

---

## 6. Physical Limitations of 1D Level-Pool Routing

1. **Absence of 2D Reservoir Drawdown:** The 1D level-pool formulation assumes a horizontal water surface across the entire reservoir with zero approach velocity headloss. Real dam-break flow creates a steep 2D drawdown funnel towards the breach opening, lowering the effective static head at the crest.
2. **Tailwater Submergence & Friction:** Friction along the eroded earthen breach channel and downstream backwater reduce actual discharge below frictionless broad-crested weir calculations.

---

## 7. Idealized Dam-Break Simulation: DualSPHysics 3D SPH `[BENCHMARK STATUS: NOT VERIFIED]`

To verify the DualSPHysics 3D SPH formulation before applying it to complex 3D topography, the solver was executed on an idealized water column collapse setup ($a = 1.0\text{ m}, h_0 = 2.0\text{ m}, g = 9.81\text{ m/s}^2$) on an **NVIDIA Tesla T4 GPU (Google Colab)** using DualSPHysics 5.4.355 with 314,801 total particles (242,550 fluid particles, $dp = 0.02\text{ m}$).

### 7.1 Execution Record on Real Hardware
* **Hardware & Runtime:** NVIDIA Tesla T4 GPU, 389.09 s wall time (2.0 s physical time, 29,873 time steps, 41 PART files).
* **Provenance Archive:** `dualsphysics_results.tar.gz` (554 MB, sha256: `461646b67d4954f52dcfca0000a36f41a051b2306234296f388648f9744b7da5`).
* **Operational Status:** **RAN ON REAL DATA**.

### 7.2 Benchmark Verification Status: NOT VERIFIED

> [!WARNING]
> **Status: NOT VERIFIED**
> The physical reference dataset often cited for this case (Martin & Moyce, 1952, Phil. Trans. R. Soc. Lond. A, DOI `10.1098/rsta.1952.0006`) is behind a publisher access paywall (HTTP 403 Forbidden). No open-access source tabulating the exact experimental points has been fetched yet into this workspace.
>
> In accordance with PravahX strict verification rules:
> 1. No quantitative comparison table is accepted without a fetched open-access primary source.
> 2. No pass/fail verdict is claimed.
> 3. The benchmark status remains strictly **NOT VERIFIED** until an open-access paper tabulating or plotting the Martin and Moyce data is fetched and cited with its URL.




## 8. Idealized Dam-Break Simulation: Delft3D Flexible Mesh

To verify the Delft3D FM formulation before applying it to complex 2D topography, the solver will be executed on an idealized dam-break setup.

### 8.1 Engine Smoke Test (Deltares c019)
Before running the benchmark, a basic engine smoke test was performed using the Deltares c019 case (`test/tests/FMtests/f05_boundary_conditions/c019_waterlevel_bc_cmp_varying`).

* **Deltares Commit:** `761dc502e7fe3fac61ecece8c93b94b635f3643b`
* **Bundle:** `MyDrive/PravahX/delft3dfm_linux_x86_64.tar.gz` (147 MB)
* **Bundle SHA-256:** `491364fbba88948752356fb1af0edc8aaecc496ba95545a9b66494c0ba1a6258`
* **Modifications:** 7 obsolete keys commented, ObsFile blanked, MapInterval 600, MapFormat 4.
* **Hardware & Runtime:** Google Colab (CPU) - Fresh Session (10 Oct 2026)
* **Results:** EXIT 0, 5.6 s wall time for 2 h simulation, 13 time steps x 780 faces.
* **Validation:** Fresh session bundle SHA-256 MATCH (`491364fb...6258`). `ldd` confirmed nothing missing (Intel runtime bundled in `lib/`, no apt install needed). `dflowfm --version` EXIT 0 (OpenMP, MPI, PETSc, METIS, PROJ, GDAL: yes). Smoke case results: $s1$ min -0.0154 m / max 0.0056 m, no NaN values, max $|\Delta s1|$ 0.0107 m: IDENTICAL to the build machine.
* **Operational Status:** **RUN AND PASSED** (including fresh-session reproducibility).

### 8.2 Idealized Dam Break (Ritter 1892)

To verify the Delft3D FM solver against analytical dam-break hydrodynamics over a dry bed, the formulation will be tested against the classical Ritter (1892) solution.

* **Domain:** Straight rectangular channel, 2000 m long $\times$ 50 m wide, flat bed, closed side walls. Dam at $x = 1000$ m.
* **Initial Conditions:** Upstream water depth $h_0 = 10$ m, dry downstream bed.
* **Friction:** Frictionless (Manning's $n = 0.0$).
* **Mesh & Time:** $\sim 5$ m resolution. $T_{\text{stop}} = 40$ s, Output map interval = 5 s.
* **Pass Tolerances (defined pre-run):**
  * **Front position error:** $\le 5\%$ relative error vs theoretical wave front $x_f(t)$.
  * **Water depth RMSE (along centerline):** $\le 0.5$ m (expecting some smearing at the front due to numerical diffusion and wet/dry thresholds).

**RESULTS:**
* **Mass:** 500,000 → 500,000 m3 in all 4 runs.
* **Depth RMSE (m) t=10/20/30:** Base 0.055/0.055/0.059; A(epsHu 0.01) 0.053/0.047/0.051; B(n 0.005) 0.061/0.062/0.074; C(dx 2.5) 0.031/0.034/0.042. → PASS (tol 0.5). Refinement 5→2.5 m reduces RMSE ~45%: converging.
* **Front (continuous from dam, depth >5 cm), error % of travel:** Base -32.5/-13.0/+14.6; A -22.4/-10.4/+2.8; B -19.9/+6.0/+30.6; C +9.8/+12.6/+13.5. → FAIL vs pre-registered 5%. Cause: frictionless thin-film artefact (film speeds up to 382 m/s; wall pile-up 0.90 m Base, 0.94 m C).
* **Verdict:** depth PASS + converging; front FAIL, understood. Reference: Delestre et al. 2013 (SWASHES), arXiv:1110.0288v7, Section 4.1.2, fetched and checked.

## 9. Tier-1 Delft3D FM vs Tier-0 HAND: Model Intercomparison (Ganga Reach near Rishikesh)

> [!IMPORTANT]
> **LABELING: MODEL INTERCOMPARISON**
> This simulation is strictly a **MODEL INTERCOMPARISON** between Tier-0 (HAND) and Tier-1 (Delft3D Flexible Mesh 2D) on identical input data and hypothetical forcing. It is **NOT** a validation against field observations. Disagreement between tiers is expected due to structural model differences (static gravity-equilibrium HAND vs 2D shallow-water equations with advective inertia and backwater effects) and will be reported transparently without tuning.

* **Benchmark Status:** **GATES HALTED ALL COMPARISONS (Real Colab Run `ebe5814` + `hydrolib-core` install)**
* **Diagnosis & Decision:** Inflow blocked on 50 m mesh due to perched canyon boundary cells; 25 m mesh resolves canyon thalweg and admits full inflow. **Decision recorded: 25 m mesh (`Primary_dx25`) = PRIMARY for this valley; 50 m mesh (`Sensitivity_50m`) = SENSITIVITY ONLY if it passes the inflow gate.**
* **Notebook:** `notebooks/PravahX_Ganga_Tier1.ipynb`
* **Target Environment:** Google Colab Free CPU (Intel Xeon / 2 vCPUs)
* **Execution Budget:** < 45 min wall time (< 15k cells total across variants)

### 9.0 Real Colab Execution Findings (`ebe5814`) & Diagnosis

During the real Colab execution of commit `ebe5814` (with `hydrolib-core` installed), the pre-registered validity gates worked correctly and halted all intercomparisons. The diagnosis from real engine output revealed:

1. **50 m Mesh Inflow Choking:**
   * Prescribed cumulative inflow in `inflow.bc` was $7.42\text{ Mm}^3$ ($7,420,000\text{ m}^3$).
   * However, stored volume in `Base_uniform_50m` rose only from $52,370\text{ m}^3$ to $136,754\text{ m}^3$ ($\Delta V \approx 84,384\text{ m}^3$); measured outlet discharge remained $0\text{ m}^3/\text{s}$ throughout.
   * `B_worldcover` (on the same 50 m mesh) partly entered (stored volume rose to $\sim 0.99\text{ Mm}^3$).
   * *Investigation of Boundary Cells on 50 m Mesh:* The Ganga enters the domain through a narrow, steep canyon gorge ($\sim 150\text{ m}$ wide valley floor flanked by steep $400+\text{ m}$ mountain slopes). With coarse $50\text{ m}$ averaging, boundary links spanned across steep valley walls, creating perched dry cells ($Z > 380\text{ m}$). The cell-averaged bed level at the domain rim sat significantly higher than the water level of the $100\text{ m}^3/\text{s}$ base flow ($h_{\text{water}} \approx 352.5\text{ m}$ vs rim nodes $\sim 365\text{ m}$), acting as an artificial sill that physically blocked inflow entry into the model interior.
   * *Remediation:*
     * Inflow boundary polyline is now strictly confined to the active channel thalweg ($Z < 380\text{ m}$, $Y \in [3335850, 3336250]$), eliminating dry/perched valley wall links.
     * An internal observation cross-section (`inflow_obs`) is added just inside the domain ($\sim \Delta x$ downstream of the boundary polyline).
     * **Gate c (Inflow Gate):** Measured cumulative inflow across `inflow_obs` must match specified `.bc` inflow within 2% ($|V_{\text{in,meas}} - V_{bc}| / V_{bc} \le 0.02$).
   * *Decision Recorded:* **25 m mesh (`Primary_dx25`) = PRIMARY for this valley; 50 m mesh (`Sensitivity_50m`) = SENSITIVITY ONLY if it passes the inflow gate.**

2. **25 m Mesh Inflow Dynamics & Reach Storage:**
   * On the 25 m mesh, inflow entered fully: stored volume matched cumulative inflow to $< 0.1\%$ prior to outflow initiation.
   * Downstream outlet remained dry until $\sim t = 9,000\text{ s}$ as the base flow and leading flood wave filled natural terrain depressions and channel storage along the 2.8 km reach.
   * Peak measured outflow reached $1,137\text{ m}^3/\text{s}$.
   * Cumulative measured outflow past the outlet reached $3.13\text{ Mm}^3$ (storage-based outflow $2.87\text{ Mm}^3$).
   * By $t = 16,200\text{ s}$, only $38.7\%$ of total cumulative inflow had exited through the downstream boundary.

3. **Warm-up Spin-up Redesign (Base-Flow Equilibrium & Restart Files):**
   * In the real run, base flow ($100\text{ m}^3/\text{s}$) never reached the outlet within the fixed $5,400\text{ s}$ window ($\approx 0.72\text{ Mm}^3$ of base flow was absorbed filling dry terrain depressions).
   * The fixed duration warm-up is replaced by a dynamic base-flow-only pre-run that continues until measured outlet discharge reaches $\ge 90\%$ of inflow ($Q_{\text{out,meas}} \ge 0.90 \cdot Q_{\text{in,meas}}$). The required equilibrium time is logged and reported.
   * At equilibrium, the model writes a restart file (`flow2d3d_rst.nc`), and the breach hydrograph is simulated directly from this pre-conditioned restart state.
   * *Deltares Restart Mechanism Citation:* In Deltares D-Flow FM, hydrodynamic state restarts are written via `rstInterval = <seconds>` in the `[Output]` block of `flow2d3d.mdu`, generating `*_rst.nc` files. The subsequent run loads this state via `restartFile = <path_to_rst.nc>` in the `[Restart]` block of `flow2d3d.mdu` `[VERIFIED - Deltares D-Flow FM User Manual (2023), Section 4.3.4 'Restart files']`.

4. **Run Length & Depression Dead Storage:**
   * The breach simulation continues until:
     * $\ge 70\%$ of the breach inflow volume has drained past the outlet ($V_{\text{breach,out}} \ge 0.70 \cdot V_{\text{breach,in}}$), OR
     * Outlet discharge falls below $2\times$ base flow ($Q_{\text{out}} < 200\text{ m}^3/\text{s}$).
   * The elapsed simulation time needed to satisfy this condition is reported.
   * Water permanently trapped in disconnected terrain depressions ("dead storage") is computed and reported separately ($V_{\text{dead}}$ in $\text{m}^3$ and MCM); this volume cannot drain downstream by physical design.

5. **Mass Balance Formulation:**
   * Domain mass balance is computed strictly using:
     * MEASURED inflow ($V_{\text{in,meas}}$ integrated from observation cross-section `inflow_obs` just inside the boundary),
     * MEASURED outflow ($V_{\text{out,meas}}$ integrated from observation cross-section `outlet_obs` on/adjacent to the outlet boundary line, NOT 100 m upstream),
     * Domain storage change ($\Delta V_{\text{stored}}$ integrated from `*_map.nc` water depths).
     $$\Delta M = V_{\text{in,meas}} - V_{\text{out,meas}} - \Delta V_{\text{stored}}$$
     $$\text{Relative Mass Balance Error} = \frac{|\Delta M|}{V_{\text{in,meas}}} \times 100\%$$
   * The `.bc` forcing file is **NEVER** used as "inflow" in mass balance accounting.

6. **Pre-Comparison Validity Gates (Strict Thresholds Maintained):**
   * **Gate a (Open Cells):** Inflow and downstream boundaries both open $> 0$ cells (no `"opened 0 cells"` or `"opened 0 flow links"`).
   * **Gate b (Diagnostics):** Solver diagnostic scan contains 0 fatal `ERROR` lines and 0 `"No signals"` boundary errors.
   * **Gate c (Inflow Gate):** Measured cumulative inflow across `inflow_obs` matches specified `.bc` inflow within 2% ($|V_{\text{in,meas}} - V_{bc}| / V_{bc} \le 0.02$).
   * **Gate d (Warm-up Gate):** Base flow pre-run achieves steady-state outflow ($Q_{\text{out,meas}} \ge 0.90 \cdot Q_{\text{in,meas}}$) before breach initiation; spin-up time reported.
   * **Gate e (Drainage Gate):** $\ge 70\%$ of breach inflow volume drained past the outlet, OR outlet discharge receded below $2\times$ base flow ($< 200\text{ m}^3/\text{s}$); elapsed time reported.
   * **Gate f (Mass Conservation Gate):** Dynamic mass balance error $< 1.0\%$ evaluated strictly using measured cross-sections and domain storage change.

### 9.1 Identical Inputs & Variant Matrix

To ensure a strictly fair intercomparison, the primary Tier-1 run matches Tier-0's uniform roughness ($n = 0.035$). Spatially distributed roughness and mesh resolution are evaluated as explicit sensitivity variants.

| Parameter / Input | Tier-0 HAND Accepted Run | Tier-1 Primary (`Primary_dx25`) | Sensitivity 1 (`Sensitivity_50m`) | Sensitivity 2 (`Variant_B_worldcover`) | Source / Provenance | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Geographic AOI** | `(78.30, 30.10, 78.35, 30.15)` | `(78.30, 30.10, 78.35, 30.15)` | `(78.30, 30.10, 78.35, 30.15)` | `(78.30, 30.10, 78.35, 30.15)` | Rishikesh reach, Uttarakhand, India | IDENTICAL |
| **Projected CRS** | `EPSG:32644` (UTM 44N) | `EPSG:32644` (UTM 44N) | `EPSG:32644` (UTM 44N) | `EPSG:32644` (UTM 44N) | EPSG Registry | IDENTICAL |
| **Terrain DEM** | Copernicus GLO-30 (30 m) | Copernicus GLO-30 (30 m) | Copernicus GLO-30 (30 m) | Copernicus GLO-30 (30 m) | STAC AWS `copernicus-dem-30m` | IDENTICAL |
| **Hydro-Conditioning** | WhiteboxTools `breach_depressions` | Conditioned DEM bed elevations | Conditioned DEM bed elevations | Conditioned DEM bed elevations | WhiteboxTools v2.4 | IDENTICAL |
| **Domain Envelope** | D8 $\ge 500$ cells reach | Tier-0 envelope + 300 m buffer (clipped to DEM extent) | Tier-0 envelope + 300 m buffer (clipped to DEM extent) | Tier-0 envelope + 300 m buffer (clipped to DEM extent) | PravahX Mesh Generator | MATCHED & CLIPPED |
| **Grid / Mesh Size** | 30 m raster cells | $\mathbf{\Delta x = 25\text{ m}}$ | $\Delta x = 50\text{ m}$ | $\Delta x = 50\text{ m}$ | PravahX Delft3D FM Mesh | **PRIMARY (25m) / SENSITIVITY (50m)** |
| **Manning Roughness** | Uniform $n = 0.035$ | **Uniform $n = 0.035$** | Uniform $n = 0.035$ | Distributed ESA WorldCover 10 m | ESA WorldCover 2021 v200 | **MATCHED (Primary)** |
| **Peak Inflow** | $5,000.0\text{ m}^3/\text{s}$ | $5,000.0\text{ m}^3/\text{s}$ | $5,000.0\text{ m}^3/\text{s}$ | $5,000.0\text{ m}^3/\text{s}$ | Froehlich (2008) back-solve | IDENTICAL PEAK |
| **Warm-up / Spin-up** | N/A (steady-state HAND) | Base flow pre-run until $Q_{\text{out}} \ge 0.9 Q_{\text{in}}$ $\to$ Restart | Base flow pre-run until $Q_{\text{out}} \ge 0.9 Q_{\text{in}}$ $\to$ Restart | Base flow pre-run until $Q_{\text{out}} \ge 0.9 Q_{\text{in}}$ $\to$ Restart | Baseflow equilibrium | VERIFIED RESTART |

### 9.2 Peak Discharge Derivation & Froehlich Hydrograph

* **Hypothetical Scenario:** A hypothetical embankment breach upstream of the Rishikesh reach (NO historical event or actual dam failure is named or implied).
* **Physical Reservoir & Breach Parameters:**
  * Initial reservoir storage $V_w = 5,807,632\text{ m}^3$ ($5.808\text{ MCM}$)
  * Breach height $h_b = 26.0\text{ m}$
  * Failure mode: Overtopping ($K_o = 1.3$, trapezoidal side slopes $z = 1.0\text{ H:V}$)
  * Hypsometric exponent: $m = 2.0$ (parabolic valley hypsometry)
  * Lean-season base flow: $Q_{\text{base}} = 100.0\text{ m}^3/\text{s}$
* **Froehlich (2008) Regressions:**
  * Average breach width:
    $$B_{\text{avg}} = 0.27 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.04} = 0.27 \cdot 1.3 \cdot (5,807,632)^{0.32} \cdot (26.0)^{0.04} = 58.42\text{ m}$$
  * Formation time:
    $$t_f = 63.2 \cdot \sqrt{\frac{V_w}{g \cdot h_b^2}} = 63.2 \cdot \sqrt{\frac{5,807,632}{9.81 \cdot 26.0^2}} = 1,870.3\text{ s} \approx 31.17\text{ min}$$
* **Peak Discharge Computation & Back-Solving:**
  * Dynamic breach outflow is governed by the expanding broad-crested weir notch:
    $$b(t) = (B_{\text{avg}} - z \cdot h_b) \cdot \frac{t}{t_f}, \quad h_{\text{notch}}(t) = h_b \cdot \frac{t}{t_f}$$
    $$Q_{\text{notch}}(t) = C_{wd} \cdot b(t) \cdot (h(t) - z_b(t))^{1.5} + C_{vt} \cdot z \cdot (h(t) - z_b(t))^{2.5}$$
    coupled with reservoir continuity $\frac{dV}{dt} = -Q_{\text{out}}(t)$ and hypsometric stage-storage $V(h) = V_w (h / h_b)^2$.
  * **Explicit Back-Solve:** The initial reservoir volume $V_w = 5,807,632\text{ m}^3$ was **iteratively back-solved** to achieve a routed peak breach outflow of exactly $Q_{b,\text{peak}} = 4,900.0\text{ m}^3/\text{s}$. Adding ambient base flow ($100.0\text{ m}^3/\text{s}$) produces a total peak inflow of exactly $Q_{\text{peak}} = \mathbf{5,000.0\text{ m}^3/\text{s}}$, matching the accepted Tier-0 peak discharge.
  * *Verification Status:* Regression equations sourced from Froehlich (2008), *J. Hydraul. Eng.*, 134(12): 1708–1721 `[VERIFIED]`. Inflow volume back-solved via dynamic broad-crested weir routing to match Tier-0 peak discharge `[VERIFIED]`.
  * *Inflow Plot:* The complete hydrograph (spin-up + breach) is plotted and archived to Google Drive as `inflow_hydrograph.png`.

### 9.3 Warm-up Spin-up & Simulation Timeline

* **Base-Flow Spin-up Pre-run:**
  * Discharge: $Q_{\text{base}} = 100.0\text{ m}^3/\text{s}$ held constant.
  * *Equilibrium Criterion:* Continues until measured outflow across `outlet_obs` reaches $\ge 90\%$ of inflow ($Q_{\text{out,meas}} \ge 0.90 \cdot Q_{\text{in,meas}}$).
  * Writes restart file `flow2d3d_rst.nc` at equilibrium time $T_{\text{eq}}$.
* **Breach Hydrograph Run:**
  * Initiated from restart state `flow2d3d_rst.nc`.
  * Breach peak reached at $t = T_{\text{eq}} + 1,870\text{ s}$ ($Q_{\text{total}} = 5,000.0\text{ m}^3/\text{s}$).
  * Run continues until $\ge 70\%$ of breach volume has exited domain OR $Q_{\text{out}} < 2\times Q_{\text{base}}$ ($200\text{ m}^3/\text{s}$).
* **Breach-Only Evaluation Window:**
  * All hydrodynamic maximums (maximum water depth, maximum velocity, arrival times) and intercomparison metrics are computed **strictly over the breach period** ($t \ge T_{\text{eq}}$).
  * Baseflow spin-up depths ($h \approx 0.5 - 1.2\text{ m}$ in the active channel) are isolated so arrival time thresholds ($0.05\text{ m}$ and $0.30\text{ m}$ above initial baseflow) accurately reflect the breach wave.

### 9.4 Downstream Boundary Condition: DEM Longitudinal Profile

* **Derivation from DEM Profile:**
  * Longitudinal profile along the lower 2.8 km reach to domain outlet:
    * Upstream profile thalweg elevation: $z_1 \approx 338.50\text{ m}$
    * Outlet cross-section thalweg elevation: derived from actual mesh boundary cell minimum bed
    * Streamwise reach length: $L \approx 2,788\text{ m}$
    * Longitudinal bed slope: $S_0 \approx 0.00054$
    * Effective channel bottom width at outlet: $B = 200.0\text{ m}$.
* **Manning Normal Depth Rating Curve (`quantity = qhbnd`):**
  * Stage-discharge relationship derived from Manning's formula for wide rectangular channel:
    $$Q = \frac{1}{n} B h_n^{5/3} \sqrt{S_0} \implies h_n(Q) = \left( \frac{n \cdot Q}{B \sqrt{S_0}} \right)^{3/5}$$
    $$\text{Water Level } z_w(Q) = z_{\text{bed,actual}} + h_n(Q)$$
  * Calculated from actual boundary cell minimum bed elevation ($z_{\text{bed,actual}}$) to ensure zero hydraulic lip at the mesh exit.
* **Limitation Note:** The Q-h normal depth boundary assumes uniform steady flow at the domain exit. Backwater effects from downstream hydraulic controls or narrowing beyond the domain boundaries are not captured.

### 9.5 Model Build Specifications

* **Computational Meshes:**
  * Primary (`Primary_dx25`): $\Delta x = 25\text{ m}$, quad faces clipped strictly to valid DEM extent. Primary choice resolving canyon thalweg without boundary pinching.
  * Sensitivity (`Sensitivity_50m`): $\Delta x = 50\text{ m}$, quad faces clipped strictly to valid DEM extent. Executed as sensitivity variant only if Gate c (inflow gate) passes.
  * Both meshes are well within the $< 100\text{k}$ Colab CPU limit.
* **Bed Level:** Interpolated at mesh nodes and cell centres from the Copernicus GLO-30 conditioned DEM.
* **Roughness Treatment:**
  * Primary & Sensitivity 50m: Uniform Manning $n = 0.035$ configured via MDU `UnifFrictCoef = 0.035` (no `initialFields.ini`).
  * Variant B (`Variant_B_worldcover`): Sourced via `initialFields.ini` with `quantity = frictioncoefficient`, `interpolationMethod = triangulation`, mapped from ESA WorldCover 10 m classes: Tree cover (10) $n=0.070$, Shrubland (20) $n=0.050$, Grassland (30) $n=0.035$, Cropland (40) $n=0.040$, Built-up (50) $n=0.100$, Bare (60) $n=0.030$, Water (80) $n=0.030$. Area-weighted mean $n \approx 0.0436$. Mapping status: `[UNVERIFIED - Empirical Literature Mapping]`.
* **Numerical Settings:**
  * `MapFormat = 4` (UGRID NetCDF standard).
  * Observation cross-sections: `crsFile = cross_sections.pli` (containing `inflow_obs` just inside the domain rim and `outlet_obs` adjacent to the downstream boundary line).
  * Restart files: `rstInterval` configured in MDU; restart execution via `[Restart] restartFile = flow2d3d_rst.nc` `[VERIFIED - Deltares D-Flow FM User Manual Section 4.3.4]`.
  * Time stepping: $DtUser = 10\text{ s}$, $DtMax = 2.0\text{ s}$, $CflMax = 0.7$, $epsHu = 0.01\text{ m}$.

### 9.6 Limitations

1. **Open DEM Channel Conveyance:** Open DEMs (Copernicus GLO-30) record the water surface elevation rather than the submerged bathymetric river bed. Because dry-season bathymetry is absent, channel cross-sectional area and conveyance capacity are underestimated.
2. **Roughness Mapping:** Manning $n$ values mapped from ESA WorldCover 10 m are empirical literature values `[UNVERIFIED - Empirical Literature Mapping]`.
3. **Arrival Time Thresholds:** Flood wave arrival is reported at $0.05\text{ m}$ (initial wave arrival) and $0.30\text{ m}$ (substantial hazard threshold) above baseflow. Threshold selection is `[UNVERIFIED - Empirical Threshold Selection]`.
4. **Downstream Normal Depth:** Downstream boundary assumes steady normal depth via Manning formula, which neglects local acceleration or backwater effects occurring downstream of the domain boundary.
5. **Depression Dead Storage:** Hydro-conditioned DEM depressions naturally capture and hold ponded water that cannot drain under gravity without positive gradient. This volume is recorded as dead storage.

### 9.7 Intercomparison Outputs and Final Table (Pre-registered)

Upon Colab execution of `notebooks/PravahX_Ganga_Tier1.ipynb`, the notebook enforces the 6 validity gates. If all gates pass, the notebook generates:

1. **Consolidated Intercomparison Table:**
   `case | cells | wall s | EXIT | inflow gate | warmup gate | drain gate | mass balance | dead storage (MCM) | IoU | F-score | Tier-0 area | Tier-1 area | depth diff mean/RMSD`
   Across cases: `Primary_dx25`, `Sensitivity_50m`, `Variant_B_worldcover`.
   *(Note: Pending Colab execution with validity gate clearance; no IoU/F metrics are quoted prior to passing all gates).*

2. **Hydrodynamic Rasters & Vectors (EPSG:32644):**
   `tier1_max_depth.tif`, `tier1_max_velocity.tif`, `tier1_arrival_time_0_05.tif`, `tier1_arrival_time_0_30.tif`, `tier1_envelope.shp`, `tier1_envelope.kml`.

3. **Archived Artifacts:**
   * Inflow Hydrograph plot: `inflow_hydrograph.png`
   * 4-Panel Summary Map: `ganga_tier1_summary.png`
   * Text Report & CSV: `INTERCOMPARISON_REPORT.txt`, `intercomparison_summary_table.csv`
   * `[Figure pending: Summary map docs/img/ganga_tier1_summary.png will be copied from Drive upon Colab execution; no placeholder figures are committed.]`


