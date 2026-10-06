# PravahX Build Context

## Current state
- Phase in progress: 2a
- Last completed phase and date: Phase 1 (2026-10-06)
- What works end to end right now: Tier 0 (HAND) execution and geospatial exports on synthetic data.

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

### Phase 2a: Volume, breach and hydrograph (status: in_progress)
- Built / Building:
  - `core/pravahx/reservoir/volume_register.py` and `volume_satellite.py` (Register lookup, new lake DEM-depth integration, and existing lake area-volume scaling relations)
  - `core/pravahx/breach/froehlich.py` (Froehlich 2008 embankment dam breach geometry, formation time, and peak flow)
  - `core/pravahx/breach/ensemble.py` (Breach parameter log-normal uncertainty ensemble for p10, p50, p90)
  - `core/pravahx/breach/hydrograph.py` (Dynamic weir routing through expanding breach with conservation of volume check)
  - Source-point downstream reach extraction in `core/pravahx/terrain/hand.py`
  - Unit tests covering volume estimation, breach relations, ensemble, hydrograph volume integration, and boundary river entry reach tracing
- Decisions: Froehlich (2008) verified against HEC-RAS regression values. Peng and Zhang (2012) logged in BLOCKED.md pending exact Table 4 coefficients.
- Deviations from the build spec: None
- Tests: Unit tests in `tests/unit/test_breach.py`, `tests/unit/test_reservoir.py`, `tests/unit/test_terrain.py`.
- Measured results: N/A
- Known issues and limits: `landslide.py` blocked on user-supplied Table 4 regression coefficients.
- Requirement IDs advanced: R1, R3
- Feature IDs advanced: F03

## Environment
- Dependency versions (pinned):
  - pydantic>=2.10,<3
  - fastapi>=0.115,<1
  - celery[redis]>=5.4,<6
  - sqlalchemy[asyncio]>=2.0.36,<3
  - (see pyproject.toml for full list)
- Solver versions and how they were installed: None yet
- Hardware used for measurements: None yet

## Credentials requested from the user
- None pending.

## Open questions for the user
- None at this time.

## Next steps
- Complete Phase 2a tests and report before proceeding to Phase 2b (Delft3D FM).
