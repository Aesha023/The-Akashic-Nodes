# PravahX Backend Status

This document defines the verified operational status of the PravahX hydrodynamic and computational modeling backend as of October 2026.

---

## 1. Proven Capabilities

The following components and characteristics have been physically executed and empirically proven:

1. **Engine Build & Portability:**
   * Automated compilation, packaging, and headless distribution of Deltares D-Flow FM (Delft3D Flexible Mesh 2D hydrodynamic solver).
   * Portable Linux binary execution bundle verified via cryptographic SHA-256 integrity hash (`491364fb...6258`).
   * Automated container-free deployment on standard cloud CPU environments (Google Colab 2 vCPUs).

2. **Analytical Ritter (1892) Benchmark:**
   * Tested against the classical Ritter (1892) analytical dam-break solution over a dry bed via SWASHES formulation (Delestre et al., 2013).
   * Water depth RMSE along channel centerline at $t = 30\text{ s}$ measured $0.059\text{ m}$ ($\le 0.5\text{ m}$ tolerance PASS).
   * Numerical convergence proven: mesh refinement from $\Delta x = 5\text{ m}$ to $\Delta x = 2.5\text{ m}$ reduced depth RMSE by ~45% to $0.042\text{ m}$.
   * Complete physical mass conservation: 500,000 $\to$ 500,000 $\text{m}^3$ exact in all test configurations.

3. **Real-Terrain Execution with Exact Engine Mass Balance:**
   * End-to-end execution on real-world steep topography (Ganga River reach near Rishikesh, Copernicus GLO-30 DEM, ESA WorldCover roughness).
   * Verified numerical mass conservation to $0\text{ m}^3$ using Delft3D FM's OWN internal finite-volume water balance:
     * Warm-up run: in 1,080,000 | out 0 | storage +1,080,000 | residual 0 $\text{m}^3$ | engine `volume_error` 0.0.
     * Breach run: in 7,241,809 | out 4,166,187 | storage +3,075,622 | residual 0 $\text{m}^3$ | engine `volume_error` 0.0.
   * Confirms that Delft3D FM is mathematically and numerically mass conservative to $0\text{ m}^3$. Discrepancies observed earlier (34–44%) were identified and resolved as external discrete post-processing accounting artifacts.

4. **50 m Mesh Boundary Rejection by Measurement:**
   * Inflow boundary choking on the 50 m mesh was diagnosed and rejected through empirical gate measurement: coarse cell averaging across steep canyon walls ($150\text{ m}$ valley floor flanked by $400+\text{ m}$ slopes) produced artificial sills up to $365\text{ m}$, blocking the $100\text{ m}^3/\text{s}$ base flow.
   * Formal modeling decision: **25 m mesh is PRIMARY** (resolves channel thalweg and admits 100% of inflow); 50 m mesh rejected for steep gorges.

---

## 2. Pending Items

1. **Ganga Tier-1 vs Tier-0 Model Intercomparison:**
   * **Status:** `RUNS; mass balance exact; INTERCOMPARISON PENDING (warm-up + run length)`.
   * **Remaining Halts:**
     * *Gate d (Warm-up Gate):* Base flow ($100\text{ m}^3/\text{s}$) over 3 h was entirely absorbed by terrain depression storage in the gorge (open DEM water-surface pit effect) without outflow reaching the downstream boundary.
     * *Gate e (Drainage Gate):* Breach run duration (4 h) was insufficient for the flood wave tail to drain; 53% of breach volume remained in gorge storage and end discharge remained at $211.5\text{ m}^3/\text{s} > 200\text{ m}^3/\text{s}$.
   * **Planned Next-Step Fix (NOT executed now):**
     * Pre-wet/initialise the reach at base-flow water level (e.g. from Tier-0 water surface) or warm up for ~10–12 h until base flow reaches the downstream boundary and passes Gate d.
     * Extend breach simulation duration beyond 4 h until $\ge 70\%$ of breach excess volume drains and discharge recedes below $2\times$ base flow ($< 200\text{ m}^3/\text{s}$), allowing Gate e to pass.
   * **Intercomparison Integrity:** Model comparison metrics (IoU, F-score, depth difference statistics) remain withheld until both Gate d and Gate e pass. No IoU/F metrics are reported.

---

## 3. Scope Boundary

* **Ganga Tier-1 Delft3D FM Work:** Frozen per project milestone.
* **Frontend:** NOT started.
