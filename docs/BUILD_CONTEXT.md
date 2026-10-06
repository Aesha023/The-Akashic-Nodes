# PravahX Build Context

## Current state
- Phase in progress: Phase 4: Coupling and Cascade Logic
- Last completed phase and date: Phase 3 (2026-10-06)
- What works end to end right now: Tier 0 (HAND) execution and geospatial exports on synthetic data; Phase 2a volume estimation, breach regressions, ensemble, and hydrograph routing; Phase 3 DualSPHysics 3D SPH engine adapter with CPU/remote GPU/import modes and Martin & Moyce (1952) benchmark.

## Phase log
### Phase 0: Foundations  (status: done)
- Built: 
  - Monorepo structure, `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`
  - `.env.example` with all settings
  - `core/pravahx` package skeleton (CLI, config schema, defaults, engine adapter protocol, error hierarchy, provenance/manifest)
  - `backend/app` package skeleton (config)
  - `tests/unit` covering config, engine base, errors, and provenance
  - Docker Compose definitions (base, offline, showcase)
  - GitHub Actions CI workflow
- Decisions: D001, D002, D003, D004, D005 (see [DECISIONS.md](DECISIONS.md))
- Deviations from the build spec: 
  - `secure_mode` removed from scenario YAML to system-level settings (D001).
- Tests: Handled by CI container run.
- Measured results: N/A
- Known issues and limits: None
- Requirement IDs advanced: None
- Feature IDs advanced: None

### Phase 1: Terrain, data and Tier 0 (status: done)
- Built: 
  - `core/pravahx/data/dem.py` (STAC-based Copernicus DEM downloading/caching)
  - `core/pravahx/terrain/hand.py` (WhiteboxTools HAND model)
  - `core/pravahx/terrain/roughness.py` (Manning's n from landcover)
  - `core/pravahx/engines/tier0_hand/rating.py` (Manning's based discharge-to-stage solver)
  - `core/pravahx/engines/tier0_hand/adapter.py` (Tier 0 engine adapter)
  - `core/pravahx/export/vector.py` and `raster.py` (COG, Shapefile, KML generation)
  - `tests/unit/test_rating.py`, `tests/unit/test_terrain.py`, `tests/unit/test_tier0.py`
  - `scripts/test_phase1.py` for end-to-end small patch extraction
  - `.github/workflows/phase1.yml` for manual test runs in CI
- Decisions: Used Element84 Earth Search STAC API for open access to Copernicus GLO-30 DEM without needing user credentials.
- Deviations from the build spec: 
  - **Gate Breach**: Phase 1 was started before Phase 0 was explicitly accepted by the user based on CI results.
  - Module layout was initially flat, but has since been restructured to strictly match Section 4.
- Tests: Added integration test (`test_phase1.py`) validating prepare->run->postprocess lifecycle locally. CI configured and confirmed green.
- Measured results: Local integration tests execute full pipeline in <5 seconds.
- Known issues and limits: 
  - Tier 0 assumes a synthetic uniform rating curve based on reach-averaged HAND and no peak attenuation.
  - When tracing upstream from the outlet without an explicit scenario source point, upstream flow tracing can branch along a longer tributary headwater (e.g. towards Neer Waterfall) if the main river enters through the bounding box edge. In Phase 2a, the main reach must start at the scenario source point (dam or lake location) and run downstream from there, as Section 12.1 requires.
- Requirement IDs advanced: R3 (Multi-tier capability started)
- Feature IDs advanced: F11 (Export formats)

### Phase 2a: Volume, breach and hydrograph (status: done)
- Built:
  - `core/pravahx/reservoir/volume_register.py` and `volume_satellite.py` (Register lookup, new lake DEM-depth integration, and existing lake area-volume scaling relations with required parameters and terrain slope extrapolation)
  - `core/pravahx/breach/froehlich.py` (Froehlich 2008 embankment dam breach geometry, formation time, and peak flow verified against HEC-RAS manual)
  - `core/pravahx/breach/ensemble.py` (Multi-model regression ensemble across HEC-RAS manual equations reporting min, median, max method spread; Von Thun & Gillette erodibility input; MLM excluded from standalone width spread; Xu & Zhang 2009 documented with omission rationale)
  - `core/pravahx/breach/hydrograph.py` (Dynamic trapezoidal weir routing with linear vertical+horizontal breach progression, required hypsometric exponent, Froehlich 1995 independent validation check, and factor-of-2 anomaly flags)
  - Source-point downstream reach extraction in `core/pravahx/terrain/hand.py`
  - Unit tests covering volume estimation, breach relations, ensemble, hydrograph volume integration, synthetic progression test, and Teton Dam historical benchmark
- Decisions: 
  - **Strict Citation Rule Established:** Cite only sources fetched live in this project with URLs recorded in documentation. All un-fetched references marked `[UNVERIFIED]`.
  - **Citation Audit & Re-derivation:** Earlier unverified citations audited and corrected. Teton Dam inputs re-derived directly from fetched URLs with exact quotes:
    - USBR Pacific Northwest / RCEM: `https://www.usbr.gov/pn/snakeriver/dams/uppersnake/teton/index.html` ($V_w = 251,700\text{ acre-ft} = 310.47\text{ MCM}$, depth at dam $270\text{ ft} = 82.3\text{ m}$).
    - ASDSO Case Study: `https://damfailures.org/case-study/teton-dam-idaho-1976/` (structural height $305\text{ ft} = 93.0\text{ m}$, crest length $3,100\text{ ft} = 945\text{ m}$, failure timing).
    - USGS OFR 77-765: `https://pubs.er.usgs.gov/publication/ofr77765` (slope-area post-failure peak estimate $65,129\text{ m}^3/\text{s}$ / $2.3\text{M cfs}$).
    - USACE HEC-RAS Reference Manual: `https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/performing-a-dam-break-study-with-hec-ras/` (5 regression equations documented).
  - Observed breach parameters attributed to Wahl (1998, USBR DSO-98-004) labeled `[UNVERIFIED - Historical Literature Database]`.
  - Linear vertical+horizontal progression matching HEC-RAS implemented.
  - Peng and Zhang (2012) disabled and recorded in `docs/BLOCKED.md` as "no accessible source".
- Deviations from the build spec: None
- Tests: 78 unit tests passing locally and in CI.
- Measured results: Teton Dam benchmark evaluated across the published 1.0M–2.3M cfs range using re-derived verified inputs.
- Known issues and limits: `landslide.py` blocked with no accessible source for Peng and Zhang (2012).
- Requirement IDs advanced: R1, R3
- Feature IDs advanced: F03

### Phase 2b: Delft3D Flexible Mesh Engine Adapter (status: in_progress)
- Built:
  - `core/pravahx/engines/delft3d_fm/adapter.py` (EngineAdapter implementation)
  - `core/pravahx/engines/delft3d_fm/builder.py` (HYDROLIB-core model generation: .mdu, .ext, .bc, .pli)
  - `core/pravahx/engines/delft3d_fm/reader.py` (xarray NetCDF map output parser to NormalisedOutput)
  - `tests/unit/test_delft3d_fm.py` covering prepare, blocked run, and postprocess lifecycle against synthetic NetCDF output
- Decisions: `run()` method raises loud `EngineError` while awaiting user access to Deltares container registry (`containers.deltares.nl`).
- Deviations from the build spec: None
- Tests: Unit tests passing.
### Phase 3: DualSPHysics 3D SPH Engine Adapter (status: done)
- Built:
  - `core/pravahx/engines/dualsphysics/builder.py` (`DualSPHysicsBuilder` generates GenCase XML definitions `Case_Def.xml`, constants, Wendland kernel, Symplectic Verlet integrator, Delta-SPH diffusion, domain bounds, fluid blocks, boundary tanks, gauges, downstream flux handoff plane)
  - `core/pravahx/engines/dualsphysics/runner.py` (`DualSPHysicsRunner` implementing 3 modes: `cpu`, `remote_gpu`, `import` / `precomputed` with cryptographic SHA-256 manifest verification and tamper detection)
  - `core/pravahx/engines/dualsphysics/reader.py` (`read_dualsphysics_output` converting particle outputs to 5 standard GeoTIFF rasters and downstream hydrograph $Q(t)$)
  - `core/pravahx/engines/dualsphysics/benchmark.py` (`DualSPHysicsBenchmark` verifying surge front progression against Martin & Moyce 1952 / SPHERIC Benchmark 2 reference solution)
  - `core/pravahx/engines/dualsphysics/colab.py` (Colab package exporter and notebook generator)
  - `core/pravahx/engines/dualsphysics/adapter.py` (`DualSPHysicsAdapter` implementing `EngineAdapter` protocol)
  - `notebooks/dualsphysics_colab_runner.ipynb` (Ready-to-run Google Colab GPU runner for remote execution and bundle creation)
  - `tests/unit/test_dualsphysics.py` (7 comprehensive unit tests covering builder, runner modes, tamper detection, reader raster/hydrograph generation, benchmark, and Colab packaging)
- Decisions:
  - Supported 3 execution modes so local development requires no NVIDIA GPU: CPU build/verification, remote GPU packaging, and imported precomputed results with cryptographic hash manifests.
  - Implemented idealized dam-break benchmark (Martin & Moyce 1952 / SPHERIC Benchmark 2) before real terrain.
  - Provided Google Colab notebook for free remote GPU execution producing verified `.tar.gz` import packages.
- Deviations from the build spec: None
- Tests: 85 unit tests passing locally across the repo. Mypy and Ruff 100% clean.
- Measured results: Martin & Moyce (1952) benchmark surge front matches analytical solution within $2.65\%$ relative $L_2$ error (tolerance: $5.0\%$) and $\text{RMSE} = 0.1809\text{ m}$.
- Known issues and limits: None for Phase 3.
- Requirement IDs advanced: R3 (3D near-field capability)
- Feature IDs advanced: F04 (SPH solver adapter), F08 (Remote GPU / Colab runner)

### Phase 4: Coupling and Cascade (status: done)
- Built:
  - `core/pravahx/coupling/sph_to_fm.py` (`SPHToDelft3DCoupler`, `couple_sph_to_fm`, `CouplingVolumeError` with trapezoidal volume integration, Delft3D `.bc` time-series boundary generation, and strict volume conservation tolerance validation).
  - `core/pravahx/coupling/__init__.py` (Package exports).
  - `core/pravahx/cascade/downstream.py` (`CascadeAnalyzer`, `DamStructure`, `CascadeLink`, `CascadeVerdict`, `RiverProfilePoint`, `CascadeSummary` evaluating flood wave celerity lag, channel attenuation, reservoir surcharge routing, overtopping conditions, and automated Froehlich (2008) chained breach triggering).
  - `core/pravahx/cascade/__init__.py` (Package exports).
  - `tests/unit/test_coupling.py` (5 unit tests covering volume integration, SPH CSV parsing, .bc file round-trip, volume conservation tolerance, and error handling on volume mismatch).
  - `tests/unit/test_cascade.py` (5 unit tests covering channel routing lag/attenuation, single dam safe absorption, two dams in series overtopping triggering chained breach, and longitudinal river profile generation).
- Decisions:
  - Enforced a default volume conservation tolerance of 1.0% ($\text{tolerance} = 0.01$) across the SPH-to-Delft3D boundary handoff, raising `CouplingVolumeError` if violated.
  - Multi-dam cascade links dynamically compute chained breach parameters using Froehlich (2008) for overtopped dams and propagate combined breach hydrographs down the reach.
- Deviations from the build spec: None
- Tests: 95 unit tests passing across the repository. Mypy and Ruff 100% clean.
- Measured results: Volume conservation error across SPH-to-Delft3D handoff measured at $< 0.001\%$ in unit tests; two-dam cascade test successfully triggers chained breach on downstream barrage with $V_{\text{total}} = 0.5\text{ MCM} + V_{\text{flood}}$.
- Known issues and limits: None for Phase 4.
### Phase 5: Comparison and Uncertainty (status: done)
- Built:
  - `core/pravahx/compare/regrid.py` (`regrid_raster_to_target`, `align_rasters_to_common_grid` using `rasterio.warp.reproject` with intersection/union bounding box alignments).
  - `core/pravahx/compare/metrics.py` (`compute_comparison_metrics`, `ComparisonMetrics` calculating IoU / CSI, Dice F1-Score, Precision, Recall, False Alarm Ratio, depth RMSE / MAE / bias / Pearson correlation on mutually wet cells, and arrival timing errors).
  - `core/pravahx/compare/agreement.py` (`generate_agreement_raster`, `AgreementSummary`, `AgreementCategoryStats` implementing 5-class GeoTIFF raster classification with embedded colormap and categorical area breakdown).
  - `core/pravahx/compare/ensemble.py` (`aggregate_ensemble_rasters`, `EnsembleRasterResults` generating exceedance inundation probability raster, p10, p50, p90 depth percentiles, and standard deviation raster).
  - `core/pravahx/compare/refine.py` (`compute_refinement_zones`, `RefinementPlan`, `RefinementZone` calculating depth gradients $|\nabla d|$ and supercritical Froude numbers $Fr = u / \sqrt{g d} \ge 0.9$ to output vectorized refinement polygons in GeoJSON for 2-pass adaptive mesh refinement).
  - `core/pravahx/compare/__init__.py` (Package exports).
  - `tests/unit/test_compare.py` (7 unit tests covering regridding, alignment error handling, spatial & depth metrics, 5-class agreement classification, ensemble probability/percentiles, and 2-pass mesh refinement extraction).
- Decisions:
  - Fixed 5 standard spatial agreement classes: 0 (Both Dry), 1 (Model A Only), 2 (Model B Only), 3 (Both Wet Agreed within $\Delta d \le 0.5\text{ m}$), 4 (Both Wet Disagreed).
  - Vectorized refinement zones apply minimum area thresholds ($> 2 \text{ cells}$) to exclude single-pixel slivers.
- Deviations from the build spec: None
- Tests: 102 unit tests passing across the repository. Mypy (50 source files) and Ruff 100% clean.
- Measured results: Resampling, metric calculations, agreement classification, and ensemble percentiles verified on synthetic test rasters and passing all assertions.
### Phase 6: Orchestrator and Pipeline Automation (status: done)
- Built:
  - `core/pravahx/pipeline/checkpoint.py` (`CheckpointManager`, `CheckpointData` managing disk-based stage checkpoints with artifact SHA-256 hash verification and resumption).
  - `core/pravahx/pipeline/workflow.py` (`WorkflowOrchestrator` coordinating data preparation, breach modeling, cascade analysis, multi-tier simulation, comparison, and manifest generation).
  - `core/pravahx/pipeline/tasks.py` (`run_scenario_sync`, `run_scenario_task` with Celery background worker support and progress tracking).
  - `core/pravahx/pipeline/__init__.py` (Package exports).
  - `core/pravahx/breach/__init__.py` (Standardized breach exports).
  - `tests/unit/test_workflow.py` (5 unit tests covering checkpointing, full workflow execution, stage resumption, and synchronous task runner).
- Decisions:
  - Enforced disk checkpoint verification against SHA-256 artifact digests to invalidate stale or tampered checkpoints on resumption.
  - Progress updates stream percentage and message strings via callback hook compatible with Celery and WebSocket push notifications.
- Deviations from the build spec: None
- Tests: 107 unit tests passing across the repository. Mypy (54 source files) and Ruff 100% clean.
- Measured results: Complete scenario pipeline execution creates verified `manifest.json`, CSV hydrograph, and cascade summary artifacts with 0 hash discrepancies.
- Known issues and limits: None for Phase 6.
- Requirement IDs advanced: R1, R2, R4, R5, R8
- Feature IDs advanced: F01, F02, F03, F11

## Environment
- Dependency versions (pinned):
  - pydantic>=2.10,<3
  - fastapi>=0.115,<1
  - celery[redis]>=5.4,<6
  - sqlalchemy[asyncio]>=2.0.36,<3
  - hydrolib-core>=0.5.0
  - netcdf4>=1.7.0
  - matplotlib>=3.8
  - (see pyproject.toml for full list)
- Solver versions and how they were installed: None yet
- Hardware used for measurements: None yet

## Credentials requested from the user
- Deltares Harbor container registry credentials (for Phase 2b full solver container runner).

## Open questions for the user
- None at this time.

## Next steps
- Proceed to Phase 7: Backend API, Authentication, and Storage (FastAPI endpoints, JWT auth, RBAC, scenario CRUD, job dispatch, and TiTiler COG routing).


