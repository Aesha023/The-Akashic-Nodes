# PravahX

**PravahX** is an automated dam-break and river blockage inundation modelling and disaster impact assessment system.

Built for the Smart India Hackathon 2026 (Problem Statement 26161, NTRO).

---

## Current Operational Status & Real Data Transparency

To maintain rigorous scientific and engineering integrity, the table below documents the exact status of each subsystem, distinguishing components that execute on **real data today** from those that operate on **synthetic test arrays, require external cloud/GPU compute, or await container access**:

| Subsystem | Operational Mode Today | Real Software / Real Data | Notes & Verification Sources |
| :--- | :--- | :--- | :--- |
| **Tier 0 Rapid Inundation (HAND)** | **RUN & VERIFIED** | **Yes** (Real DEM terrain) | Runs on real SRTM 30m / Copernicus GLO-30 elevation models conditioned via WhiteboxTools (D8 flow direction, stream tracing from breach point, down-valley elevation indexing, HAND extraction). |
| **Breach Routing & Ensembles** | **RUN & VERIFIED** | **Yes** (Published historical records) | Level-pool reservoir routing benchmarked against published Teton Dam failure records. Regressions (Froehlich 2008, MacDonald & Langridge-Monopolis 1984, Von Thun & Gillette 1990) verified against the USACE HEC-RAS Hydraulic Reference Manual. |
| **Flood Hazard Rating ($HR$)** | **RUN & VERIFIED** | **Yes** (UK Defra / EA Standards) | Implements $HR = d \cdot (v + 0.5) + DF$. Verified against primary Defra/Environment Agency FD2321/TR1 Table 3.1 and FD2320/TR2 guidance. |
| **UN-SPIDER SAR Flood Mapping** | **RUN (Offline / Synthetic)** | **Synthetic** (Ready for Live GEE) | Implements the official UN-SPIDER Recommended Practice (linear ratio $\ge 1.25$, slope filter $\le 5\%$, connected-pixel filter $> 8$, permanent water subtraction, plus PravahX HAND filter $\le 15\text{ m}$). Runs offline on rasters today; live execution requires Earth Engine credentials. |
| **DualSPHysics 3D SPH Solver** | **ADAPTER RUN / SOLVER NOT RUN** | **No** (Local machine lacks NVIDIA GPU) | XML generator, packaging scripts, VTK rasterizer, and 1D SPH-Delft3D coupling tested on synthetic data. Physical simulation executable was **NOT RUN** locally; run remotely via Google Colab (`notebooks/dualsphysics_colab_runner.ipynb`). |
| **Delft3D Flexible Mesh (2D)** | **ADAPTER RUN / SOLVER BLOCKED** | **No** (Pending container access) | NetCDF UGRID mesh post-processing and depth/velocity extraction tested on synthetic outputs. Containerized Delft3D engine execution is blocked pending host runtime access. |
| **Depth-Damage & Lake-Watch** | **EMPIRICAL TEMPLATES** | **Empirical Heuristic** | Depth-damage curves and lake expansion (+10% / -20%) anomaly triggers are flagged as empirical templates. All generated maps set `"needs_human_check": true`. |

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
