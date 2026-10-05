# PravahX Build Context

## Current state
- Phase in progress: 0
- Last completed phase and date: None yet
- What works end to end right now: Nothing yet (core foundations only)

## Phase log
### Phase 0: Foundations (status: in progress)
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
- Tests: Not yet successfully executed. Docker is not available in the current local terminal. Waiting on GitHub Actions CI run.
- Measured results: N/A
- Known issues and limits: None yet
- Requirement IDs advanced: None yet
- Feature IDs advanced: None yet

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
