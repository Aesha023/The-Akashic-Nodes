# PravahX — Architectural and Technical Decisions

This document records significant decisions made during the build of PravahX.

| ID | Title | Date | Status | Phase |
|---|---|---|---|---|
| D001 | Secure mode as a system-level setting | 2026-10-05 | Accepted | 0 |
| D002 | Tile server vs Map server | 2026-10-05 | Accepted | 0 |
| D003 | SPH execution modes (GPU constraint) | 2026-10-05 | Accepted | 0 |
| D004 | Showcase deployment mode | 2026-10-05 | Accepted | 0 |
| D005 | Linux container for local CI checks | 2026-10-05 | Accepted | 0 |

---

## D001: Secure mode as a system-level setting

**Context:** The problem statement and specs require a "secure mode" with no outbound network calls. The original scenario config schema included `secure_mode: false` at the scenario level.

**Decision:** Remove `secure_mode` from the scenario config schema. It is now a system-wide setting controlled by the `PRAVAHX_SECURE_MODE` environment variable (`online` or `secure`) and enforced by the egress guard and Docker network topology. The mode in effect during a run is recorded in its `manifest.json`.

**Reasoning:** Security posture should not be determined by user input (a scenario config file). If the system is air-gapped, a user should not be able to bypass it by setting `secure_mode: false`.

## D002: Tile server vs Map server

**Context:** Section 3 asks to choose a tile service (TiTiler or GeoServer) and Section 3.1 asks to choose a map server (GeoServer or MapServer).

**Decision:** We will use two separate services:
1. **TiTiler (COG tiles):** For the application's internal map layers (Phase 8), serving Cloud Optimised GeoTIFFs directly from object storage.
2. **MapServer (WMS/WFS):** For publishing results to external clients (feature F13, Phase 10).

**Reasoning:** The deployment target is a single small Linux VM (constraint B). TiTiler is lightweight and designed specifically for COG. MapServer is generally lighter on memory than GeoServer (which runs on the JVM), making it a better fit for a constrained environment.

## D003: SPH execution modes (GPU constraint)

**Context:** The SPH engine (DualSPHysics) requires a CUDA GPU, but the development environment does not have one (constraint A).

**Decision:** The `DualSPHysicsConfig` schema supports a `mode` field with three options: `cpu`, `remote_gpu`, and `precomputed`. The `precomputed` mode requires a directory containing precomputed results and their original run date, which will be imported and verified by hash, then flagged as precomputed in the run manifest and UI.

**Reasoning:** This allows end-to-end testing of the pipeline without a local GPU, while maintaining provenance and honesty about results.

## D004: Showcase deployment mode

**Context:** Constraint C requires a read-only showcase mode for the frontend and API.

**Decision:** A new system setting `PRAVAHX_DEPLOYMENT_MODE` (`full` or `showcase`) is introduced. In `showcase` mode, all workers and schedulers are disabled (via `docker-compose.showcase.yml`), the API blocks mutating operations, and the frontend displays a banner.

**Reasoning:** Minimises compute usage on the student cloud subscription while allowing interactive demonstrations of precomputed results.

## D005: Linux container for local CI checks

**Context:** Running tests locally on a Windows host caused C compilation failures (e.g., `numpy` builds blocked by Application Control policies), masking whether the Python code was actually sound.

**Decision:** The local test runner (`make ci-docker` or `make test-docker`) builds a lightweight Linux container (`Dockerfile.test`) containing all dependencies and runs the linter, type checker, and tests inside it.

**Reasoning:** Ensures that local tests run in the same Linux environment as the GitHub Actions CI pipeline and the ultimate deployment target, eliminating host-OS quirks and preventing false negatives during development.

## D002: Module-specific MyPy Ignore for PySTAC Client

**Date:** 2026-10-05
**Context:** pystac_client currently lacks type stubs, causing mypy strict checking to fail.
**Decision:** We ignore missing imports for pystac_client.* explicitly in pyproject.toml. Global ignores are strictly forbidden.

