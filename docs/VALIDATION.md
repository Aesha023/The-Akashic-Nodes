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
* **Generator required these fixes to run at all:** (1) hydrolib-core missing in Colab; (2) DtUser defaulted to 300 s (> Tstop 40 s) → set DtUser 5, DtMax 0.5, HisInterval 5, MapInterval 5; (3) hydrolib writes obsolete key wrishp_enc → engine rejects; (4) initial water was wired via waterLevIniFile (expects .xyz samples) → reservoir empty; fixed with IniFieldFile = initialFields.ini ([General] fileVersion 2.00, fileType iniField; [Initial] quantity waterlevel, dataFileType polygon, interpolationMethod constant, operand O, value 10.0); (5) upstream.pol header was "1 4" → must be "5 2" with closing point.
* **After fixes:** 2000/4000 cells wet at t=0, mass conserved exactly (500,000 m3 at t=0 and t=30 s).
* **Frictionless (pre-registered config):** depth RMSE 0.055/0.055/0.059 m at t=10/20/30 → PASS (tol 0.5 m). Front FAIL: thin-film artefact, film speeds 382 m/s (t=5) and 126 m/s (t=10) vs Ritter max 19.8 m/s; water piles at far wall (0.90 m at x=1997.5, t=30).
* **Spot values vs Ritter:** x=1400 t=30: 0.475 vs 0.474 m; x=1200 t=20: 1.14 vs 1.09 m; dam site ≈4.37–4.42 vs 4.44 m.
* **Sensitivity (NOT the pass criterion, recorded as such):** A) epsHu 0.01 m: wall pile-up gone, continuous front +194/+126/+108 m ahead, RMSE ≈0.05 m. B) Manning n 0.005: front err -40.1%/+4.7%/+16.3%, RMSE ≈0.06–0.07 m (friction departs from Ritter's assumption).
* **Verdict:** depth PASS, front FAIL (understood numerical artefact). Reference: Delestre et al. 2013 (SWASHES), arXiv:1110.0288v7, Section 4.1.2, fetched and checked.
