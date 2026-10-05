# PravahX

**PravahX** is an automated dam break and river blockage inundation modelling system.

This project is built for the Smart India Hackathon 2026 (Problem Statement 26161, NTRO).

## Overview
PravahX answers one question for any Indian river: if a dam breaks, releases water suddenly, or a river is blocked, how much water comes down, where does it go, and when does it arrive?

It supports a multi-tier modelling approach:
- **Tier 0:** Rapid envelope (HAND based)
- **Tier 1:** Delft3D Flexible Mesh (far-field)
- **Tier 2:** DualSPHysics (near-field GPU SPH)

## Quick Start
*Instructions for running the application will be added in Phase 12.*

## Development
See the [Makefile](Makefile) for development commands:
- `make setup`: Install dependencies and pre-commit hooks
- `make ci`: Run linting, type checks, and tests
- `make run-dev`: Start the local Docker Compose stack
- `make run-offline`: Start in secure, air-gapped mode
- `make run-showcase`: Start in read-only showcase mode

## Documentation
- [Build Context](docs/BUILD_CONTEXT.md)
- [Architecture](docs/ARCHITECTURE.md) (coming soon)
- [Decisions](docs/DECISIONS.md)

## License
Licensed under the [Apache License, Version 2.0](LICENSE).
