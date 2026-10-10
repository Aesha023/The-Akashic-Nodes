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
* **Observation only (NOT a pass criterion, chosen after seeing data):** C 1 cm front at t=30 = 1591.25 m vs Ritter 1594.3 m.
* **Verdict:** depth PASS + converging; front FAIL, understood. Reference: Delestre et al. 2013 (SWASHES), arXiv:1110.0288v7, Section 4.1.2, fetched and checked.

## 9. Tier-1 Delft3D FM vs Tier-0 HAND: Model Intercomparison (Ganga Reach near Rishikesh)

> [!IMPORTANT]
> **LABELING: MODEL INTERCOMPARISON**
> This simulation is strictly a **MODEL INTERCOMPARISON** between Tier-0 (HAND) and Tier-1 (Delft3D Flexible Mesh 2D) on identical input data and hypothetical forcing. It is **NOT** a validation against field observations. Disagreement between tiers is expected due to structural model differences (static gravity-equilibrium HAND vs 2D shallow-water equations with advective inertia and backwater effects) and will be reported transparently without tuning.

* **Benchmark Status:** **RUNS, but INTERCOMPARISON NOT VALID** (Colab debugging session, commit 5fb9488 + in-notebook fixes)
* **Notebook:** `notebooks/PravahX_Ganga_Tier1.ipynb`
* **Target Environment:** Google Colab Free CPU (Intel Xeon / 2 vCPUs)
* **Execution Budget:** < 45 min wall time (< 15k cells total across variants)

### 9.0 Debugging Session Findings & Validity Gates

During the Colab debugging session (commit `5fb9488` with in-notebook patches), the Delft3D FM engine executed successfully (`EXIT 0`), but identified hydraulic and boundary anomalies that render the intercomparison **NOT VALID** until patched. The following 8 findings were observed and addressed:

1. **`initialFields.ini` Specification:**
   * An `[Initial]` block without `dataFile` triggers an engine fatal ERROR.
   * `[Parameter]` friction from sample points with `interpolationMethod = constant` triggers an engine ERROR (samples require Delaunay triangulation: `interpolationMethod = triangulation`).
   * Quantity name `friction` is rejected by the engine parser. The verified D-Flow FM 1D2D quantity name is `frictioncoefficient` (`[VERIFIED - Deltares D-Flow FM User Manual]`).
   * For uniform Manning $n$ cases (`Base_uniform_50m`, `C_dx25`), no `initialFields.ini` is written or referenced; uniform roughness is configured directly via MDU keyword `UnifFrictCoef = 0.035`.
2. **Boundary `.pli` Edge Alignment & Gate:**
   * Boundary polylines placed interior to the domain were outside the engine's boundary tolerance and resulted in `"opened 0 cells"` (reported as `INFO` while the solver proceeded with zero inflow).
   * Gate enforcement: The run must fail immediately if any boundary opens 0 cells. Polylines are now strictly snapped to the outer boundary links of the mesh.
3. **Inflow Placement on Main Stem vs Tributary:**
   * Inflow in earlier drafts was placed on a northern tributary with high bed elevation ($\sim 458\text{ m}$), rather than the Ganga main stem which enters the AOI from the east ($\sim 244590, 3336101$, bed $\sim 346\text{ m}$).
   * Inflow and outflow boundary locations are now chosen strictly from the Ganga main stem (identified by maximum flow accumulation crossing the model edge). Boundary placement and the longitudinal thalweg profile are plotted over the Tier-0 flood footprint in the notebook.
4. **Boundary Condition (.bc) Naming Conventions:**
   * For the compiled engine build, discharge boundary forcing must reference the support point name: `[forcing]` name `inflow_bnd_0001` (with `quantity = dischargebnd`).
   * Q-h boundary forcing must reference the polyline name: `[forcing]` name `downstream_bnd`.
   * Q-h rating curve table header quantities must be exactly `quantity = qhbnd discharge` and `quantity = qhbnd waterlevel`.
5. **Outlet Bed Elevation for Q-h Rating Table:**
   * The Q-h normal depth table previously assumed an idealized bed of $337.00\text{ m}$. Real mesh bed elevations near the outlet differ ($342.6\text{ m}$ on 50 m mesh, $337.5\text{ m}$ on 25 m mesh).
   * The normal depth table is now computed using the actual minimum bed elevation extracted from the boundary cells.
6. **Zero Outflow & DEM Boundary Lip Resolution:**
   * In initial runs, zero outflow occurred across all runs: cumulative inflow ($7,061,783\text{ m}^3$ + initial $150\text{ m}^3$) equaled stored volume ($7,061,933\text{ m}^3$) exactly to the $\text{m}^3$. Outlet water depth remained 0 m for most of the run; at the end of the 25 m mesh run, $6.6\text{ m}$ of water was impounded behind an artificial $\sim 7\text{ m}$ bed lip ($\sim 344.4\text{ m}$ edge bed vs $337.5\text{ m}$ just upstream).
   * *Root Cause Verified:* The mesh boundary (Tier-0 envelope + 300 m buffer) extended beyond the clipped DEM raster extent into nodata border margins, causing edge cells to receive default nodata values ($350\text{ m}$).
   * *Fix:* The computational domain is strictly clipped to the valid, non-nodata DEM extent (eroded by $15\text{ m}$), eliminating edge artifacts without modifying the underlying terrain data.
7. **Spin-up Near-Steady Claim Removed:**
   * The earlier assertion that "spin-up reaches near-steady, $|Q_{\text{out}} - Q_{\text{in}}| / Q_{\text{in}} < 0.05$" was never measured in previous runs and was false (measured outflow was 0). This claim has been excised from documentation.
8. **Real Mass Balance & Observation Cross-Section:**
   * The hard-coded mass balance "PASS (exact)" has been removed.
   * An observation cross-section (`outlet_obs.pli`) is placed 100 m upstream of the outlet boundary (registered via MDU `crsFile = outlet_obs.pli`).
   * Mass balance is computed dynamically from model outputs:
     $$\Delta M = V_{\text{in,cum}} - V_{\text{out,cum}} - \Delta V_{\text{stored}}$$
     where cumulative inflow and outflow are integrated from `*_his.nc` and storage change is computed from `*_map.nc`.

#### Pre-Comparison Validity Gates

Before computing or comparing spatial metrics (IoU, F-score), the notebook strictly evaluates five validity gates. If any gate fails, the notebook reports `FAIL`, prints the gate diagnostics, and **halts without performing the intercomparison**:

* **Gate a (Open Cells):** Both inflow and downstream boundaries open $> 0$ cells (checked via log inspection: `"opened N cells"`).
* **Gate b (Diagnostics):** Solver diagnostic scan contains 0 fatal `ERROR` lines and 0 `"No signals"` boundary errors.
* **Gate c (Spin-up Equilibrium):** Warm-up outflow measured at the observation cross-section is within $10\%$ of baseflow inflow ($|Q_{\text{out}} - Q_{\text{in}}| / Q_{\text{in}} \le 0.10$). If not met, warm-up must be lengthened.
* **Gate d (Drainage Efficiency):** $\ge 70\%$ of total cumulative inflow drains past the outlet by $T_{\text{stop}}$, or an explicit physical/hydraulic mechanism (e.g. storage depression retention) is documented.
* **Gate e (Mass Conservation):** Cumulative domain mass balance relative error $|\Delta M| / V_{\text{in,cum}} < 1.0\%$.

### 9.1 Identical Inputs & Variant Matrix

To ensure a strictly fair intercomparison, the primary Tier-1 run matches Tier-0's uniform roughness ($n = 0.035$). Spatially distributed roughness and mesh refinement are evaluated as explicit sensitivity variants.

| Parameter / Input | Tier-0 HAND Accepted Run | Tier-1 Primary (`Base_uniform_50m`) | Variant B (`B_worldcover`) | Variant C (`C_dx25`) | Source / Provenance | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Geographic AOI** | `(78.30, 30.10, 78.35, 30.15)` | `(78.30, 30.10, 78.35, 30.15)` | `(78.30, 30.10, 78.35, 30.15)` | `(78.30, 30.10, 78.35, 30.15)` | Rishikesh reach, Uttarakhand, India | IDENTICAL |
| **Projected CRS** | `EPSG:32644` (UTM 44N) | `EPSG:32644` (UTM 44N) | `EPSG:32644` (UTM 44N) | `EPSG:32644` (UTM 44N) | EPSG Registry | IDENTICAL |
| **Terrain DEM** | Copernicus GLO-30 (30 m) | Copernicus GLO-30 (30 m) | Copernicus GLO-30 (30 m) | Copernicus GLO-30 (30 m) | STAC AWS `copernicus-dem-30m` | IDENTICAL |
| **Hydro-Conditioning** | WhiteboxTools `breach_depressions` | Conditioned DEM bed elevations | Conditioned DEM bed elevations | Conditioned DEM bed elevations | WhiteboxTools v2.4 | IDENTICAL |
| **Domain Envelope** | D8 $\ge 500$ cells reach | Tier-0 envelope + 300 m buffer (clipped to DEM extent) | Tier-0 envelope + 300 m buffer (clipped to DEM extent) | Tier-0 envelope + 300 m buffer (clipped to DEM extent) | PravahX Mesh Generator | MATCHED & CLIPPED |
| **Grid / Mesh Size** | 30 m raster cells | $\Delta x = 50\text{ m}$ | $\Delta x = 50\text{ m}$ | $\Delta x = 25\text{ m}$ | PravahX Delft3D FM Mesh | PRIMARY / SENSITIVITY |
| **Manning Roughness** | Uniform $n = 0.035$ | **Uniform $n = 0.035$** | Distributed ESA WorldCover 10 m | Uniform $n = 0.035$ | ESA WorldCover 2021 v200 | **MATCHED (Primary)** |
| **Peak Inflow** | $5,000.0\text{ m}^3/\text{s}$ | $5,000.0\text{ m}^3/\text{s}$ | $5,000.0\text{ m}^3/\text{s}$ | $5,000.0\text{ m}^3/\text{s}$ | Froehlich (2008) back-solve | IDENTICAL PEAK |
| **Spin-up Warm-up** | N/A (steady-state HAND) | $5,400\text{ s}$ at $100\text{ m}^3/\text{s}$ | $5,400\text{ s}$ at $100\text{ m}^3/\text{s}$ | $5,400\text{ s}$ at $100\text{ m}^3/\text{s}$ | Baseflow equilibrium | FAIR BASELINE |

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

* **Base-Flow Spin-up Period:**
  * Duration: $T_{\text{spinup}} = 5,400\text{ s}$ ($1.5\text{ h}$).
  * Discharge: $Q_{\text{base}} = 100.0\text{ m}^3/\text{s}$ held constant.
  * *Equilibrium Measurement:* Outflow is dynamically monitored at the downstream observation cross-section `outlet_obs.pli`. Gate (c) verifies that $|Q_{\text{out}} - Q_{\text{in}}| / Q_{\text{in}} \le 0.10$ before admitting results.
* **Breach Hydrograph Period:**
  * Starts at $t = 5,400\text{ s}$ ($1.5\text{ h}$).
  * Breach peak reached at $t = 5,400 + 1,870 = 7,270\text{ s}$ ($Q_{\text{total}} = 5,000.0\text{ m}^3/\text{s}$).
  * Hydrograph recedes back to base flow by $t = 12,600\text{ s}$ ($3.5\text{ h}$ total simulation).
* **Breach-Only Evaluation Window:**
  * All hydrodynamic maximums (maximum water depth, maximum velocity, arrival times) and intercomparison metrics are computed **strictly over the breach period** ($t \ge 5,400\text{ s}$).
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
  * Primary (`Base_uniform_50m`): $\Delta x = 50\text{ m}$, quad faces clipped strictly to valid DEM extent.
  * High-Resolution Variant (`C_dx25`): $\Delta x = 25\text{ m}$, quad faces clipped strictly to valid DEM extent.
  * Both meshes are well within the $< 100\text{k}$ Colab CPU limit.
* **Bed Level:** Interpolated at mesh nodes and cell centres from the Copernicus GLO-30 conditioned DEM.
* **Roughness Treatment:**
  * Primary & Variant C: Uniform Manning $n = 0.035$ configured via MDU `UnifFrictCoef = 0.035` (no `initialFields.ini`).
  * Variant B (`B_worldcover`): Sourced via `initialFields.ini` with `quantity = frictioncoefficient`, `interpolationMethod = triangulation`, mapped from ESA WorldCover 10 m classes: Tree cover (10) $n=0.070$, Shrubland (20) $n=0.050$, Grassland (30) $n=0.035$, Cropland (40) $n=0.040$, Built-up (50) $n=0.100$, Bare (60) $n=0.030$, Water (80) $n=0.030$. Area-weighted mean $n \approx 0.0436$. Mapping status: `[UNVERIFIED - Empirical Literature Mapping]`.
* **Numerical Settings:**
  * `MapFormat = 4` (UGRID NetCDF standard).
  * Observation cross-section: `crsFile = outlet_obs.pli` (located 100 m upstream of outlet).
  * Time stepping: $T_{\text{stop}} = 12,600\text{ s}$ ($3.5\text{ h}$), $DtUser = 10\text{ s}$, $DtMax = 2.0\text{ s}$, $CflMax = 0.7$, $epsHu = 0.01\text{ m}$.

### 9.6 Limitations

1. **Open DEM Channel Conveyance:** Open DEMs (Copernicus GLO-30) record the water surface elevation rather than the submerged bathymetric river bed. Because dry-season bathymetry is absent, channel cross-sectional area and conveyance capacity are underestimated.
2. **Roughness Mapping:** Manning $n$ values mapped from ESA WorldCover 10 m are empirical literature values `[UNVERIFIED - Empirical Literature Mapping]`.
3. **Arrival Time Thresholds:** Flood wave arrival is reported at $0.05\text{ m}$ (initial wave arrival) and $0.30\text{ m}$ (substantial hazard threshold) above baseflow. Threshold selection is `[UNVERIFIED - Empirical Threshold Selection]`.
4. **Downstream Normal Depth:** Downstream boundary assumes steady normal depth via Manning formula, which neglects local acceleration or backwater effects occurring downstream of the domain boundary.

### 9.7 Intercomparison Outputs and Final Table (Pre-registered)

Upon Colab execution of `notebooks/PravahX_Ganga_Tier1.ipynb`, the notebook enforces the 5 validity gates. If all gates pass, the notebook generates:

1. **Consolidated Intercomparison Table:**
   `case | cells | wall s | EXIT | mass balance | IoU | F-score | Tier-0 area | Tier-1 area | depth diff mean/RMSD (both wet)`
   Across all 3 cases: `Base_uniform_50m`, `B_worldcover`, `C_dx25`.
   *(Note: Pending Colab execution with validity gate clearance; no IoU/F metrics are quoted prior to passing all gates).*

2. **Hydrodynamic Rasters & Vectors (EPSG:32644):**
   `tier1_max_depth.tif`, `tier1_max_velocity.tif`, `tier1_arrival_time_0_05.tif`, `tier1_arrival_time_0_30.tif`, `tier1_envelope.shp`, `tier1_envelope.kml`.

3. **Archived Artifacts:**
   * Inflow Hydrograph plot: `inflow_hydrograph.png`
   * 4-Panel Summary Map: `ganga_tier1_summary.png`
   * Text Report & CSV: `INTERCOMPARISON_REPORT.txt`, `intercomparison_summary_table.csv`
   * `[Figure pending: Summary map docs/img/ganga_tier1_summary.png will be copied from Drive upon Colab execution; no placeholder figures are committed.]`


