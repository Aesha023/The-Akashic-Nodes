# PravahX Build Context

## Current state
- Phase in progress: 0
- Last completed phase and date: None yet
- What works end to end right now: Nothing yet (core foundations only)

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
  - `core/pravahx/pipeline/data.py` (STAC-based Copernicus DEM downloading/caching)
  - `core/pravahx/pipeline/terrain.py` (WhiteboxTools HAND model)
  - `core/pravahx/pipeline/roughness.py` (Manning's n from landcover)
  - `core/pravahx/pipeline/rating.py` (Manning's based discharge-to-stage solver)
  - `core/pravahx/engines/tier0.py` (Tier 0 engine adapter)
  - `core/pravahx/pipeline/exports.py` (COG, Shapefile, KML generation)
  - `tests/unit/test_rating.py` and `tests/unit/test_tier0.py`
  - `scripts/test_phase1.py` for end-to-end small patch extraction
- Decisions: Used Element84 Earth Search STAC API for open access to Copernicus GLO-30 DEM without needing user credentials.
- Deviations from the build spec: None.
- Tests: Unit tests for rating geometry and tier0 adapter. `test_phase1.py` script provided for user validation.
- Measured results: N/A (Pending user run on target environment)
- Known issues and limits: Tier 0 assumes a synthetic uniform rating curve based on reach-averaged HAND.
- Requirement IDs advanced: R3 (Multi-tier capability started)
- Feature IDs advanced: F11 (Export formats)

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
- Complete Phase 0 by verifying `make ci` passes.
- Stop and request approval to begin Phase 1.
