# PravahX

**PravahX** is an automated dam-break and river blockage inundation modelling and disaster impact assessment system.

Built for the Smart India Hackathon 2026 (Problem Statement 26161, NTRO).

---

## Current Operational Status & Real Data Transparency

To maintain rigorous scientific and engineering integrity, the table below documents the exact status of each subsystem, distinguishing components that execute on **real data today** from those that operate on **synthetic test arrays, require external cloud/GPU compute, or await container access**:

| Subsystem | Status Label | Notes & Verification Sources |
| :--- | :--- | :--- |
| **Tier 0 Rapid Inundation (HAND)** | **RAN ON REAL DATA** | Runs on real SRTM 30m / Copernicus GLO-30 elevation models conditioned via WhiteboxTools (D8 flow direction, stream tracing from breach point, down-valley elevation indexing, HAND extraction). |
| **Breach Routing & Ensembles** | **VERIFIED AGAINST A FETCHED REFERENCE** | Level-pool reservoir routing benchmarked against fetched USGS OFR 77-765 ($65,129\text{ m}^3/\text{s}$) and USBR records for Teton Dam failure. Regressions (Froehlich 2008, MacDonald & Langridge-Monopolis 1984, Von Thun & Gillette 1990) and piping orifice equation verified against USACE HEC-RAS Hydraulic Reference Manual (Ch. 14). |
| **Flood Hazard Rating ($HR$)** | **VERIFIED AGAINST A FETCHED REFERENCE** | Implements $HR = d \cdot (v + 0.5) + DF$. Verified against primary Defra / Environment Agency FD2321/TR1 Table 3.1 and FD2320/TR2 guidance. |
| **UN-SPIDER SAR Flood Mapping (Kuttanad)** | **RAN ON REAL DATA, COMPARED QUALITATIVELY** | Executed on live Copernicus Sentinel-1 IW GRD data over Kerala (August 2018). Mapped $40.52\text{ km}^2$ flooded open paddy in Kuttanad / Alappuzha (21 Aug 2018 vs 23 May 2018 pre-monsoon baseline, relative orbit 54). **Area Change Explanation:** An early preliminary test computed $38.94\text{ km}^2$ before applying the HydroSHEDS 5% slope mask and $>8$ pixel connected-component spatial filter. The **$40.52\text{ km}^2$** extent is the **current and official** result exported to `needs_human_check/kuttanad_flood_extent.tif` and `.kml`. Compared qualitatively against Tiwari et al. (2020, *PLOS ONE*). |
| **DualSPHysics 3D SPH Solver** | **RAN ON REAL DATA** | Executed on real hardware: Google Colab NVIDIA Tesla T4 GPU ($dp = 0.02\text{ m}$, 314,801 particles, 2.0 s physical time, 389 s GPU runtime, 41 PARTs). Verified archive SHA-256 (`461646b6...`). **Benchmark not verified** because the 1952 reference values have no fetched open-access primary source. |
| **Delft3D Flexible Mesh (2D)** | **NOT RUN** | Adapter prepares HYDROLIB-core cases and post-processes UGRID NetCDF outputs; solver execution has **NOT RUN** due to pending container access. Public GitHub build plan prepared. |
| **Impact Assessment & Lake Watch** | **SYNTHETIC TESTS ONLY** | Population/asset exposure, economic damage estimation, evacuation clearance windows, and glacial lake time-series anomaly monitoring implemented and verified via unit/integration tests with synthetic test data. All generated maps set `"needs_human_check": true`. |

---

## Architecture & Multi-Tier Modelling

1. **Tier 0 (Rapid Regional Screening):**
   - High-speed screening using Height Above Nearest Drainage (HAND) relative to the scenario reach.
   - Computes flood envelope in seconds over tens of river kilometers on 30m DEMs.
2. **Tier 1 (Far-Field Hydrodynamics — Delft3D-FM):**
   - 2D shallow water flow routing with flexible mesh discretization.
3. **Tier 2 (Near-Field 3D SPH — DualSPHysics):**
   - Full 3D Smoothed Particle Hydrodynamics for turbulent, supercritical dam-break waves and structure impact.
4. **Impact Assessment & Satellite Verification:**
   - Village and critical infrastructure exposure calculation.
   - Evacuation routing and safety clearance window estimation.
   - Sentinel-1 SAR change detection and optical water index validation.

---

## Development & Testing

Run the standard test suite:
```bash
# Run unit tests
pytest tests/unit -v

# Run linter and formatting checks
ruff check .
ruff format --check .

# Run static type checking
mypy --python-version 3.12 core/pravahx backend/app
```

---

## Running Real Earth Engine Flood Mapping (Sentinel-1)

To run UN-SPIDER change detection on a real event (such as Kerala, August 2018):
1. Configure your Google Cloud / Earth Engine service account (see instructions below).
2. Populate `GEE_SERVICE_ACCOUNT_EMAIL`, `GEE_SERVICE_ACCOUNT_KEY_FILE`, and `GEE_PROJECT_ID` in `.env`.
3. PravahX will automatically ingest pre-event and post-event Sentinel-1 GRD scenes, apply orbit correction, thermal noise removal, linear ratio change detection ($\ge 1.25$), HydroSHEDS slope masking ($\le 5\%$), and permanent water subtraction.

---

## Running DualSPHysics on Google Colab GPU

Because local execution requires a CUDA-capable NVIDIA GPU, run Tier 2 near-field simulations on Google Colab:
1. Open `notebooks/dualsphysics_colab_runner.ipynb` in Google Colab.
2. Ensure runtime is set to **GPU (T4 / V100 / A100)**.
3. Upload `dualsphysics_case.tar.gz` exported by PravahX.
4. Execute the simulation and download `dualsphysics_results.tar.gz`.
5. Import back into PravahX (`mode='import'`) with SHA-256 integrity verification.

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
