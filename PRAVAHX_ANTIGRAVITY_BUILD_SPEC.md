# PravahX: Master Build Specification for Antigravity (v2)

**Project:** PravahX, automated dam break and river blockage inundation modelling
**Context:** Smart India Hackathon 2026, Problem Statement 26161, National Technical Research Organisation (NTRO)
**Owner:** Team The Akashic Nodes (the "user" in this document)
**Your role:** You are the engineering agent building this system: core science, backend, database, frontend and operations. Read this whole document before writing any code.
**Companion document:** `PRAVAHX_STITCH_PROMPT.md` defines the interface design. The user will run it in Stitch and give you the exports.

---

## 0. Operating rules (read first, follow always)

These rules override your defaults. If any later section seems to conflict with them, these win.

### 0.1 Phase gating
- Work **one phase at a time**, in the order given in Section 16.
- At the end of each phase: run every acceptance test for that phase, update `docs/BUILD_CONTEXT.md` (Section 17), post a short phase report, then **stop and wait**.
- Do not begin the next phase until the user replies with an explicit go-ahead (for example "ok go").
- If the user asks for a change mid-phase, make it, re-run the tests, and report again.

### 0.2 Credentials and secrets
- Never invent, guess or hardcode a credential, key, token, URL with embedded secrets, or account name.
- When a step needs a credential, **stop and ask the user for it**, stating exactly what is needed and why (see Section 18 for the expected list).
- Secrets live only in `.env` (git-ignored) and are read through `backend/app/core/config.py`. Commit `.env.example` with empty values.
- Never print secrets in logs, test output or the context file.

### 0.3 Honesty about results
- Never fabricate simulation output, validation scores, benchmark numbers or screenshots. If something has not been run, say so.
- Synthetic or mock data is allowed only in tests and in clearly labelled fixtures under `tests/fixtures/`. It must never appear in the product as if it were a real result.
- If a test fails, report it as failing. Do not weaken, skip or delete a test to make a phase pass. If a test is wrong, explain why and ask before changing it.
- Report measured numbers with units and the command that produced them.

### 0.4 Verify, do not assume
- This document gives the design. Tool versions, command-line flags, file formats and API signatures for third-party software (Delft3D FM, DualSPHysics, HYDROLIB-core, MeshKernel, Earth Engine, GDAL and so on) **must be checked against the official documentation** at build time. If the documentation contradicts this document, follow the documentation, and record the difference in the context file.
- Scientific formulas given here must be checked against the cited source before use. If you cannot access a source, ask the user.
- Pin every dependency to the latest stable version you verified, in a lock file.

### 0.5 Scope discipline
- Build what the current phase asks for. Do not add features, frameworks or abstractions that the phase does not need.
- Do not replace a named technology with another without asking.
- Prefer boring, well-tested solutions over clever ones.

### 0.6 When blocked
- If you cannot install an engine, cannot obtain data, or hit a licence question, stop and tell the user what you tried, what failed, and the options. Do not silently substitute a simplified method.

### 0.7 Design source
- The interface design is supplied by the user as Stitch exports. Follow Section 11.1. Do not invent a different visual style.

### 0.8 No pretend features
- Do not ship a button, screen or status that is not backed by working code. If a feature is not built yet, hide it behind a feature flag that is off.
- Demo data may be seeded only in a clearly named demo environment, and every screen in that environment must show a visible "demo data" marker.

---

## 1. What the system must do

PravahX answers one question for any Indian river: if this dam breaks, releases water suddenly, or this river is blocked, how much water comes down, where does it go, and when does it arrive?

### 1.1 Requirements traceability (from the problem statement)

| ID | NTRO requirement | Where it is met |
|---|---|---|
| R1 | Generalised framework for dam break and river blockage, with sudden surge and loss and damage, using SPH and Delft3D | Phases 2, 3, 4, 5, 7 |
| R2 | Compare the SPH and Delft3D scenarios | Phase 5 |
| R3 | Scenarios from different input datasets (hydrological data, DEM, satellite imagery) | Phases 1, 2; scenario config (Section 6) |
| R4 | Dashboard (GUI) for input and output visualisation | Phases 9, 10 |
| R5 | Support large data volumes | COG tiling, windowed reads, job queue (Phases 1, 8, 9) |
| R6 | Output as .shp or .kml | Export service (Phases 1, 7) |
| R7 | Near real time flood analysis through Google Earth Engine with open data | Phase 6 |
| R8 | Final demonstration on an Indian river and dam with open data | Phase 12 |

Every phase report must state which requirement IDs it advanced.

### 1.2 Scenario types
1. Dam break by overtopping or by piping.
2. Controlled or emergency release (user hydrograph).
3. River blockage by landslide (user-drawn polygon).
4. Glacial or natural lake outburst.
5. Cascading failure (flood from one source overtops the next dam downstream).
6. Live event mode (Earth Engine flood mapping without a simulation).

### 1.3 Non-functional requirements
- **Reproducible:** every run stores its config, input hashes, software versions and output hashes.
- **Offline capable:** a secure mode in which the system makes no outbound network calls (Section 13).
- **Open source only:** no component that needs a paid licence.
- **Honest uncertainty:** every output carries its uncertainty range and the assumptions used.

### 1.4 Feature catalogue

Every feature has an ID. Phase reports and the context file must reference these IDs.

| ID | Feature | Summary |
|---|---|---|
| F01 | Mission Control | Map of dams, watched lakes, active runs and live detections, with key counts and recent activity |
| F02 | Scenario wizard | Guided set-up in six steps with autosaved drafts and a live map preview |
| F03 | Satellite-only mode | Volume and breach estimated without operator data, with assumptions flagged |
| F04 | Run monitor | Per-stage progress, live logs, resource use, pause, cancel, retry a stage, resume a failed run |
| F05 | Results explorer | Depth, velocity, arrival time, hazard, uncertainty band; time slider; point query; cross-section tool |
| F06 | Engine comparison | Swipe view, agreement map, metrics, disagreement hotspots, refine action |
| F07 | Satellite validation | Hindcast scoring of simulated against observed extent |
| F08 | Live flood monitor | Near real time Sentinel-1 flood mapping for an area and date range |
| F09 | Impact and loss | Village table, exposure totals, critical assets, depth-damage estimate |
| F10 | Evacuation planner | Routes avoiding inundated cells, shelters, time available against time needed |
| F11 | Cascade analysis | Chain of downstream dams with overtopping verdicts and a river profile |
| F12 | Exports and brief | Shapefile, KML, COG, NetCDF, GeoJSON, CSV, PDF brief |
| F13 | Map service publishing | WMS and WFS endpoints for a run, for loading into an external operating picture |
| F14 | Scenario library | Versioned scenarios, clone, rerun, side-by-side difference of two runs |
| F15 | Batch mode | Run a template over a list of dams with a queue view and summary |
| F16 | Lake watch | Scheduled monitoring of the water area of chosen lakes, with change alerts |
| F17 | Alerts and notifications | Rules, in-app notification centre, optional email or webhook |
| F18 | Data catalogue | Datasets with source, licence, coverage and cache state; validated uploads |
| F19 | Validation and benchmarks | A page showing real benchmark and hindcast scores, including weak results |
| F20 | System health and recovery | Queues, workers, failed jobs, dead-letter list, backup status, restore record |
| F21 | Audit and provenance | Tamper-evident log; run manifest with hashes and versions; verify action |
| F22 | Administration | Users, roles, multi-factor set-up, API keys, deployment mode, engine versions |
| F23 | Share links | Signed, expiring, read-only links to a result |
| F24 | Bilingual interface | English and Hindi, switchable at runtime |
| F25 | Display modes | Wall display mode for a control room; compact field mode for phones |
| F26 | Help and method notes | In-context explanation of each layer, method and assumption |

Rules for features:
- A feature is not done until its backend, its interface, its tests and its documentation are all complete.
- No screen may show a number that the backend did not compute. Empty and loading states are designed, not faked.

---

## 2. Architecture overview

```
   Browser (React app)                External GIS client
          |                                   |
          | HTTPS                             | WMS / WFS
+---------v-----------------------------------v----------+
|  Reverse proxy (TLS, security headers, rate limits)    |
+----+----------------------+---------------------+------+
     |                      |                     |
+----v--------+     +-------v-------+     +-------v------+
| API         |     | Tile service  |     | Map service  |
| (FastAPI)   |     | (COG tiles)   |     | (WMS / WFS)  |
+--+---+---+--+     +-------+-------+     +-------+------+
   |   |   |                |                     |
   |   |   +----------------+----------+----------+
   |   |                               |
   |   |                     +---------v----------+
   |   |                     | Object storage     |
   |   |                     | (versioned buckets)|
   |   |                     +--------------------+
   |   |
   |   +----------> PostgreSQL + PostGIS (primary; backups; point-in-time recovery)
   |
   +--------------> Redis (broker, cache, rate limits, locks)
                         |
        +----------------+-----------------+--------------+
        |                |                 |              |
+-------v------+ +-------v------+ +--------v-----+ +------v-------+
| worker-cpu   | | worker-gpu   | | worker-io    | | scheduler    |
| terrain,     | | DualSPHysics | | fetch, GEE,  | | lake watch,  |
| Delft3D FM,  | |              | | exports      | | reaper,      |
| compare,     | |              | |              | | backups      |
| impact       | |              | |              | |              |
+--------------+ +--------------+ +--------------+ +--------------+

Observability: structured logs, metrics and traces from every service
```

- The **core pipeline** is a Python package (`pravahx`) that runs from the command line with no web stack. The API and workers only call it. This keeps the science testable on its own.
- Each hydrodynamic engine is wrapped in an **adapter** with the same three-stage interface (Section 7).
- All engine results are converted to one **normalised output format** (Section 8) before anything else touches them.
- A run is a **state machine** persisted in the database (Section 14). Workers are stateless; any worker can pick up any stage.
- All outbound network traffic passes through one **egress guard**, which is closed in secure mode (Section 13).

---

## 3. Technology stack

| Layer | Technology | Notes |
|---|---|---|
| Language (core, backend) | Python 3.11 or newer | Type hints everywhere |
| Geospatial | GDAL, rasterio, geopandas, shapely, pyproj, xarray, rioxarray | COG for all rasters |
| Terrain analysis | WhiteboxTools (Python bindings) | Sink fill, flow direction, HAND |
| Engine 1 | Delft3D Flexible Mesh (D-Flow FM) | Open source; confirm install route in Phase 2 |
| Engine 1 tooling | HYDROLIB-core, MeshKernel (Python) | Model files and mesh generation |
| Engine 2 | DualSPHysics (GPU, CUDA) | With its pre and post-processing tools |
| Remote sensing | Google Earth Engine Python API | Service account authentication |
| API | FastAPI, Pydantic, Uvicorn | OpenAPI docs enabled |
| Jobs | Celery with Redis | One queue for CPU, one for GPU |
| Database | PostgreSQL with PostGIS | Alembic for migrations |
| Object storage | S3-compatible (MinIO locally) | Rasters and engine artefacts |
| Tiles | TiTiler (COG tiles) or GeoServer | Choose one in Phase 8 and record why |
| Frontend | React, TypeScript, Vite, MapLibre GL | Cesium only if 3D is built |
| Testing | pytest, hypothesis, Playwright | Coverage reported in CI |
| Quality | ruff, mypy, pre-commit | CI fails on lint or type errors |
| Packaging | Docker, docker compose | One command to run everything |

### 3.1 Platform additions

| Concern | Technology | Notes |
|---|---|---|
| Reverse proxy | Caddy or Nginx | TLS, headers, request limits; choose one and record why |
| Authentication | Argon2id password hashing; TOTP multi-factor | Use maintained libraries; never write your own cryptography |
| Sessions | Short-lived access token with rotating refresh token in an httpOnly, Secure, SameSite cookie | Server-side revocation list |
| Validation | Pydantic (backend), Zod (frontend) | Shared OpenAPI-generated types |
| Scheduling | Celery beat | Lake watch, orphan-run reaper, backups, cleanup |
| Map services | GeoServer or MapServer for WMS and WFS | Choose one and record why |
| Observability | OpenTelemetry, Prometheus, Grafana, Loki or equivalent | All optional services run locally in secure mode |
| Frontend state | TanStack Query (server state), Zustand (client state) | |
| Frontend UI | Tailwind CSS with design tokens, Radix UI primitives, Framer Motion | Tokens come from the Stitch design (Section 11) |
| Charts | Apache ECharts or visx | Choose one and record why |
| Maps | MapLibre GL; deck.gl for particle and large vector layers; Cesium only if 3D is built | |
| Internationalisation | i18next | English and Hindi |
| Component workshop | Storybook | Every shared component has a story |
| Supply chain | Dependency audit, container image scan, software bill of materials | Run in CI |

---

## 4. Repository map

Create exactly this structure. Each entry states what the file or folder contains.

```
pravahx/
├── README.md                     Project overview, quick start, live link, how to run each tier
├── LICENSE                       Open source licence (ask the user which one)
├── .env.example                  Every environment variable, with empty values and comments
├── .gitignore
├── .pre-commit-config.yaml       ruff, mypy, trailing whitespace
├── docker-compose.yml            api, worker-cpu, worker-gpu, db, redis, minio, tiles, frontend
├── docker-compose.offline.yml    Override for secure mode (no outbound network)
├── Makefile                      setup, test, lint, run, benchmark targets
├── pyproject.toml                Core package metadata and pinned dependencies
│
├── docs/
│   ├── BUILD_CONTEXT.md          Living record of what has been built (Section 17)
│   ├── ARCHITECTURE.md           Diagrams and design decisions
│   ├── DECISIONS.md              One entry per significant decision, with reason
│   ├── SCIENCE.md                Every formula used, with source and assumptions
│   ├── VALIDATION.md             Benchmark and hindcast results, with commands
│   ├── API.md                    Endpoint reference (generated from OpenAPI)
│   ├── DEPLOYMENT.md             Online and offline deployment steps
│   └── USER_GUIDE.md             How an officer runs a scenario
│
├── core/                         The science. Installable as the `pravahx` package
│   └── pravahx/
│       ├── __init__.py
│       ├── cli.py                Command line: `pravahx run scenario.yaml`
│       ├── config/
│       │   ├── schema.py         Pydantic models for the scenario config (Section 6)
│       │   └── defaults.yaml     Default parameters, each with a comment and source
│       ├── data/
│       │   ├── catalog.py        Registry of data sources and their access method
│       │   ├── dem.py            Fetch, mosaic, reproject and clip elevation data
│       │   ├── landcover.py      Fetch land cover; map classes to Manning n
│       │   ├── rainfall.py       Read gridded rainfall or user hydrograph files
│       │   ├── dams.py           Dam register lookup (height, storage, location)
│       │   ├── exposure.py       Population raster and OSM assets
│       │   └── cache.py          Local cache with content hashes
│       ├── terrain/
│       │   ├── conditioning.py   Sink fill, stream burning
│       │   ├── hydrography.py    Flow direction, accumulation, stream network, reach
│       │   ├── hand.py           Height Above Nearest Drainage raster
│       │   └── roughness.py      Manning n raster from land cover
│       ├── reservoir/
│       │   ├── volume_register.py   Volume from dam register data
│       │   ├── volume_satellite.py  Volume from water mask and DEM, or area-volume scaling
│       │   └── watermask.py         Water extent from optical index or SAR
│       ├── breach/
│       │   ├── froehlich.py      Embankment dam breach parameters
│       │   ├── landslide.py      Landslide dam breach parameters
│       │   ├── hydrograph.py     Breach outflow hydrograph from parameters and volume
│       │   └── ensemble.py       p10, p50, p90 scenario set
│       ├── engines/
│       │   ├── base.py           EngineAdapter protocol and shared types (Section 7)
│       │   ├── tier0_hand/
│       │   │   ├── adapter.py    Rapid envelope engine
│       │   │   └── rating.py     Stage from discharge using HAND hydraulic geometry
│       │   ├── delft3d_fm/
│       │   │   ├── adapter.py    prepare, run, postprocess for D-Flow FM
│       │   │   ├── mesh.py       Unstructured mesh generation and refinement
│       │   │   ├── model.py      Model definition, boundaries, roughness, initial state
│       │   │   └── reader.py     Read map output and convert to normalised output
│       │   └── dualsphysics/
│       │       ├── adapter.py    prepare, run, postprocess for DualSPHysics
│       │       ├── geometry.py   Terrain and reservoir geometry from DEM
│       │       ├── casefile.py   Case definition generation
│       │       └── reader.py     Read particle output; grid it; extract outflow
│       ├── coupling/
│       │   └── sph_to_fm.py      SPH outflow hydrograph to Delft3D boundary; volume check
│       ├── compare/
│       │   ├── regrid.py         Resample results to a common grid
│       │   ├── metrics.py        F-score, IoU, depth RMSE, arrival-time difference
│       │   ├── agreement.py      Agreement map raster
│       │   └── refine.py         Refinement rule (at most two passes)
│       ├── cascade/
│       │   └── downstream.py     Find next dam; test overtopping; chain a new breach
│       ├── gee/
│       │   ├── auth.py           Service account initialisation
│       │   ├── s1_flood.py       Sentinel-1 change detection flood mapping
│       │   ├── masks.py          Permanent water, slope and HAND masks
│       │   └── score.py          Simulated extent against observed extent
│       ├── impact/
│       │   ├── exposure.py       Population, cropland and assets inside the flood
│       │   ├── damage.py         Depth-damage curves
│       │   ├── hazard.py         Depth and velocity hazard class
│       │   ├── villages.py       Village-wise table ordered by arrival time
│       │   └── routing.py        Evacuation routes avoiding inundated cells
│       ├── export/
│       │   ├── vector.py         Shapefile and KML
│       │   ├── raster.py         Cloud Optimised GeoTIFF and NetCDF
│       │   └── brief.py          PDF brief
│       ├── pipeline/
│       │   ├── orchestrator.py   Runs the stages in order from one config
│       │   ├── stages.py         Stage definitions and their inputs and outputs
│       │   └── provenance.py     Hashes, versions, run manifest
│       └── utils/
│           ├── geo.py            CRS, resolution and extent helpers
│           ├── units.py          Unit handling
│           └── logging.py        Structured logging
│
├── backend/
│   ├── Dockerfile
│   ├── alembic/                  Database migrations
│   └── app/
│       ├── main.py               FastAPI application factory
│       ├── core/
│       │   ├── config.py         Settings from environment
│       │   ├── security.py       Authentication and roles
│       │   └── egress.py         Secure mode switch and single outbound call guard
│       ├── db/
│       │   ├── session.py        Database session
│       │   └── models.py         ORM models (Section 9)
│       ├── schemas/              Pydantic request and response models
│       ├── api/
│       │   ├── scenarios.py      Create, read, update scenarios
│       │   ├── runs.py           Start, status, cancel, results
│       │   ├── dams.py           Dam search
│       │   ├── layers.py         Map layer and tile endpoints
│       │   ├── exports.py        Download .shp, .kml, GeoTIFF, PDF
│       │   ├── gee.py            Live flood mapping requests
│       │   └── health.py         Liveness and readiness
│       ├── services/             Thin layer calling the core package
│       ├── workers/
│       │   ├── celery_app.py     Celery configuration and queues
│       │   └── tasks.py          One task per pipeline stage
│       └── storage/
│           └── objects.py        Object storage client
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx               Routes and layout
│       ├── api/                  Typed API client
│       ├── pages/
│       │   ├── ScenarioSetup.tsx   Choose dam or draw polygon; set options
│       │   ├── RunMonitor.tsx      Tier status and logs
│       │   ├── Results.tsx         Map, time slider, impact panel
│       │   ├── Compare.tsx         Side-by-side engines and agreement map
│       │   ├── LiveFlood.tsx       Earth Engine flood mapping
│       │   └── Runs.tsx            Run history and audit
│       ├── components/
│       │   ├── map/              Map view, layer control, draw tool, legend
│       │   ├── charts/           Hydrograph, arrival-time chart
│       │   └── ui/               Buttons, panels, tables
│       ├── state/                Client state
│       └── styles/
│
├── engines/                      Container builds for the external solvers
│   ├── delft3d_fm/Dockerfile
│   └── dualsphysics/Dockerfile
│
├── data/                         Git-ignored working data; only README and small samples committed
│   └── README.md
│
├── benchmarks/
│   ├── analytical_dambreak/      Idealised case with a known solution
│   ├── real_dambreak/            A documented historical failure used as a benchmark
│   └── hindcast_india/           The Indian demonstration case
│
├── tests/
│   ├── unit/                     One test module per core module
│   ├── integration/              Stage-to-stage tests on a small fixture reach
│   ├── e2e/                      Full pipeline and browser tests
│   └── fixtures/                 Small synthetic inputs, clearly labelled
│
└── .github/workflows/ci.yml      Lint, type check, unit and integration tests
```

### 4.1 Additions to the repository map

Add these to the tree above. Each entry states what it contains.

```
pravahx/
├── design/
│   ├── stitch/                    Exported Stitch screens (images and code) supplied by the user; reference only
│   ├── tokens.json                Design tokens extracted from the Stitch design system
│   └── README.md                  How the design maps to routes and components
│
├── infra/
│   ├── proxy/                     Reverse proxy configuration with security headers
│   ├── mapserver/                 WMS and WFS service configuration
│   ├── observability/             Metrics, logs, traces and dashboard configuration
│   ├── backup/                    Backup and restore scripts for database and object storage
│   └── scripts/                   Bootstrap, seed, migrate, restore-drill
│
├── docs/
│   ├── SECURITY.md                Threat model, controls, test evidence
│   ├── RECOVERY.md                Failure modes, recovery procedures, restore drill record
│   ├── RUNBOOK.md                 Operator procedures for common incidents
│   └── FEATURES.md                Feature catalogue with status per feature ID
│
├── backend/app/
│   ├── core/
│   │   ├── errors.py              Typed error hierarchy and problem-details responses
│   │   ├── ratelimit.py           Rate limiting and login lockout
│   │   ├── egress.py              Single outbound-call guard with allow-list
│   │   ├── idempotency.py         Idempotency-key handling for unsafe requests
│   │   ├── i18n.py                Server-side message catalogue
│   │   └── telemetry.py           Logging, metrics and tracing set-up
│   ├── auth/
│   │   ├── passwords.py           Hashing and password policy
│   │   ├── tokens.py              Access and refresh token issue, rotation, revocation
│   │   ├── mfa.py                 TOTP enrolment and verification, recovery codes
│   │   ├── permissions.py         Role and permission matrix; dependency checks
│   │   └── apikeys.py             Scoped API keys, hashed at rest
│   ├── api/
│   │   ├── auth.py                Login, refresh, logout, MFA
│   │   ├── users.py               Users and roles (admin)
│   │   ├── apikeys.py             API key management
│   │   ├── lakes.py               Watched lakes
│   │   ├── datasets.py            Catalogue and validated uploads
│   │   ├── results.py             Point query, cross-section, time series
│   │   ├── compare.py             Comparison metrics, hotspots, refine
│   │   ├── validations.py         Hindcast scoring
│   │   ├── impact.py              Village table, assets, totals
│   │   ├── evacuation.py          Routes and shelters
│   │   ├── cascade.py             Downstream chain
│   │   ├── publications.py        WMS and WFS publishing
│   │   ├── shares.py              Signed share links
│   │   ├── batches.py             Batch mode
│   │   ├── monitors.py            Lake watch monitors
│   │   ├── alerts.py              Rules and alerts
│   │   ├── notifications.py       Notification centre
│   │   ├── audit.py               Audit log read and verify
│   │   ├── system.py              Health, queues, workers, dead-letter, backups
│   │   └── settings.py            Deployment mode, engines, feature flags
│   ├── domain/
│   │   ├── run_state.py           Run and stage state machine with allowed transitions
│   │   ├── checkpoints.py         Stage checkpoint save, verify and load
│   │   ├── recovery.py            Resume, retry and fallback policies
│   │   └── events.py              Domain events and the transactional outbox
│   ├── workers/
│   │   ├── scheduler.py           Periodic tasks
│   │   ├── reaper.py              Detects and recovers orphaned runs
│   │   ├── deadletter.py          Dead-letter handling and replay
│   │   └── uploads.py             Sandboxed validation of uploaded files
│   └── services/
│       ├── notifications.py       In-app, email and webhook delivery
│       ├── publishing.py          Map service layer registration
│       └── backups.py             Backup orchestration and verification
│
├── frontend/src/
│   ├── design/
│   │   ├── tokens.css             CSS variables generated from design/tokens.json
│   │   ├── theme.ts               Dark, light and wall-display themes
│   │   └── motion.ts              Shared motion presets; reduced-motion handling
│   ├── i18n/                      English and Hindi message files
│   ├── pages/                     One file per route in Section 11.3
│   ├── components/
│   │   ├── glass/                 Glass surface, toolbar, sheet, pill, segmented control
│   │   ├── data/                  Solid data panel, stat, table, legend, badge
│   │   ├── map/                   Map view, layer manager, draw tools, time slider, swipe, inspector
│   │   ├── charts/                Hydrograph, profile, histogram, scatter, gauge
│   │   ├── feedback/              Skeleton, empty state, error boundary, toast, offline banner
│   │   └── command/               Command palette
│   ├── hooks/                     Data, realtime, autosave, online status, permissions
│   └── lib/                       API client, error mapping, formatters, validators
│
└── tests/
    ├── security/                  Authorisation matrix, input fuzzing, header and egress tests
    ├── resilience/                Kill-and-resume, retry, dead-letter and restore tests
    └── performance/               Load tests and frontend performance budgets
```

---

## 5. Data sources

For each source, confirm the current access method and licence before use, and record both in `docs/DECISIONS.md`.

| Data | Purpose | Notes |
|---|---|---|
| Copernicus DEM GLO-30 | Primary elevation | Open; confirm access route |
| SRTM 1 arc-second | Alternative elevation | May need a free account: ask the user |
| ASTER GDEM | Alternative elevation | Named in the problem statement |
| CartoDEM | Optional, if the user supplies it | Never download on your own |
| ESA WorldCover | Land cover for roughness | Open |
| Sentinel-1 GRD, Sentinel-2 | Water mask and flood mapping | Through Earth Engine |
| Landsat | Alternative optical imagery | Through Earth Engine |
| JRC Global Surface Water | Permanent water mask | Through Earth Engine |
| IMD gridded rainfall | Hydrological input | Ask the user for files or access |
| Dam register (NRLD, India-WRIS) | Dam height and storage | Ask the user for the source file; do not scrape |
| WorldPop | Population exposure | Open |
| OpenStreetMap | Roads, bridges, hospitals, schools, settlements | Open; respect usage policy |

The system must accept a **user-supplied DEM, hydrograph and dam record** in place of any of these (requirement R3).

---

## 6. Scenario configuration

One YAML file drives every tier. Implement it as Pydantic models in `core/pravahx/config/schema.py`, with validation and clear error messages.

```yaml
scenario:
  id: demo-001
  name: Example dam break
  type: dam_break            # dam_break | release | blockage | lake_outburst | live_event
  failure_mode: overtopping  # overtopping | piping (dam_break only)

source:
  dam_id: null               # register id, or
  point: [lon, lat]          # location, or
  polygon: path/to/lake.geojson   # drawn lake or blockage
  dam_height_m: null         # optional overrides
  storage_m3: null
  volume_method: auto        # register | satellite | user | auto

domain:
  reach_length_km: 60
  buffer_km: 5
  crs: auto                  # local UTM chosen automatically

inputs:
  dem: copernicus_glo30      # or srtm | aster | user:path
  landcover: worldcover
  inflow_hydrograph: null    # optional user file
  downstream_stage: null

breach:
  method: auto               # froehlich_2008 | landslide | user
  ensemble: [p10, p50, p90]
  user_hydrograph: null

tiers:
  tier0: {enabled: true}
  delft3d_fm:
    enabled: true
    cell_size_m: {coarse: 100, fine: 30}
    horizon_h: 12
  dualsphysics:
    enabled: true
    particle_spacing_m: 2
    near_field_km: 2

compare: {enabled: true, max_refinements: 2}
cascade: {enabled: true}
gee:
  enabled: false
  event_dates: {before: [null, null], after: [null, null]}
impact: {enabled: true}
exports: [shp, kml, cog, pdf]
secure_mode: false
```

---

## 7. Engine adapter interface

Every engine implements this protocol in `core/pravahx/engines/base.py`. No other code may call a solver directly.

```python
class EngineAdapter(Protocol):
    name: str

    def prepare(self, ctx: RunContext) -> PreparedCase:
        """Build all solver input files from the run context. No solver execution."""

    def run(self, case: PreparedCase) -> RawResult:
        """Execute the solver. Capture logs, exit status, wall time."""

    def postprocess(self, raw: RawResult, ctx: RunContext) -> NormalisedOutput:
        """Convert solver output to the normalised output format."""
```

- `RunContext` holds the validated config, prepared terrain, breach hydrograph and working paths.
- Adapters must be deterministic for the same inputs where the solver allows it.
- A failed solver run must raise a typed error with the solver log attached. Never return partial results as if complete.

---

## 8. Normalised output format

All engines produce the same set of rasters on the scenario grid, in the scenario CRS, as Cloud Optimised GeoTIFF, plus one metadata file.

| Layer | Unit | Meaning |
|---|---|---|
| `max_depth` | m | Maximum water depth |
| `max_velocity` | m/s | Maximum depth-averaged speed |
| `arrival_time` | minutes | Time from breach start until depth first exceeds a threshold |
| `time_to_peak` | minutes | Time of maximum depth |
| `extent` | 0 or 1 | Inundated where maximum depth exceeds the threshold |

- The depth threshold is a config default (document the value and the reason).
- No-data must be explicit and consistent.
- `output.json` records engine name and version, grid definition, threshold, wall time and input hashes.
- Optional time series (depth at intervals) is stored as NetCDF for the time slider.

---

## 9. Database schema

PostgreSQL with PostGIS. Migrations with Alembic; every migration has a tested downgrade.

### 9.1 Conventions
- Primary keys are UUIDs. Every table has `created_at` and `updated_at`. User-facing records have `deleted_at` for soft delete.
- Mutable records carry a `version` integer for optimistic locking; an update with a stale version is rejected.
- Every foreign key is indexed. Every geometry column has a spatial index and a declared SRID.
- Status columns are constrained to their allowed values. Money and physical quantities store their unit in the column name.
- The application connects with a role that cannot alter the schema. Migrations use a separate role.
- Large binaries never go in the database. Object storage holds them; the database holds URI, size and SHA-256.

### 9.2 Tables

**Identity and access**

| Table | Key columns |
|---|---|
| `users` | id, name, email (unique), password_hash, status, locale, last_login_at |
| `roles` | id, name (viewer, duty_officer, analyst, admin, auditor) |
| `user_roles` | user_id, role_id |
| `mfa_devices` | id, user_id, secret (encrypted), confirmed_at, recovery_codes_hash |
| `sessions` | id, user_id, refresh_token_hash, user_agent, ip, expires_at, revoked_at |
| `login_attempts` | id, email, ip, succeeded, at |
| `api_keys` | id, owner_id, name, key_hash, scopes, expires_at, last_used_at, revoked_at |

**Catalogue**

| Table | Key columns |
|---|---|
| `dams` | id, name, river, state, district, height_m, storage_m3, crest_level_m, hazard_class, geom (point), source, source_date |
| `lakes` | id, name, kind (glacial, landslide, reservoir), geom (polygon), notes |
| `datasets` | id, kind, name, source, licence, resolution, coverage (geom), status, acquired_at |
| `dataset_files` | id, dataset_id, uri, sha256, bytes, validated_at, validation_report (JSONB) |

**Scenarios and runs**

| Table | Key columns |
|---|---|
| `scenarios` | id, owner_id, name, type, tags, domain (geom), current_version_id |
| `scenario_versions` | id, scenario_id, number, config (JSONB), config_sha256, created_by, note |
| `scenario_drafts` | id, owner_id, step, payload (JSONB), updated_at |
| `runs` | id, scenario_version_id, status, priority, requested_by, started_at, finished_at, manifest (JSONB), failure_code, failure_detail |
| `run_stages` | id, run_id, stage, engine, status, attempt, worker_id, heartbeat_at, started_at, finished_at, log_uri, error (JSONB) |
| `stage_checkpoints` | id, run_stage_id, inputs_sha256, outputs (JSONB of URIs and hashes), created_at |
| `artifacts` | id, run_id, stage, kind, engine, uri, sha256, bytes, metadata (JSONB) |
| `comparisons` | id, run_id, f_score, iou, depth_rmse_m, arrival_diff_min, refinements, agreement_uri |
| `comparison_hotspots` | id, comparison_id, geom, mean_abs_diff_m, status (open, refined, flagged) |
| `validations` | id, run_id, source, observed_uri, iou, hit_rate, false_alarm_ratio, settings (JSONB) |
| `impacts` | id, run_id, village, district, population, cropland_ha, arrival_min, max_depth_m, hazard_class, est_loss_inr, geom |
| `impact_assets` | id, run_id, kind, name, max_depth_m, arrival_min, geom |
| `evacuation_routes` | id, run_id, village_impact_id, shelter_name, length_km, travel_min, margin_min, geom |
| `cascade_links` | id, run_id, order, dam_id, peak_inflow_m3s, peak_stage_m, overtopped, chained_run_id |

**Operations**

| Table | Key columns |
|---|---|
| `exports` | id, run_id, format, layers, status, uri, sha256, requested_by |
| `publications` | id, run_id, service (wms, wfs), layer_name, endpoint, published_by, revoked_at |
| `share_links` | id, run_id, token_hash, scope, expires_at, created_by, revoked_at, last_used_at |
| `batches` | id, name, template_version_id, requested_by, status |
| `batch_items` | id, batch_id, dam_id, run_id, status |
| `monitors` | id, lake_id, kind, schedule, settings (JSONB), enabled, last_run_at |
| `monitor_observations` | id, monitor_id, observed_at, water_area_m2, source_scene, quality, extent_uri |
| `alert_rules` | id, name, target_kind, condition (JSONB), severity, channels, enabled |
| `alerts` | id, rule_id, severity, title, detail (JSONB), geom, raised_at, acknowledged_by, acknowledged_at |
| `notifications` | id, user_id, alert_id, channel, status, read_at |

**Governance and reliability**

| Table | Key columns |
|---|---|
| `audit_log` | id, seq, actor_id, actor_kind, action, target_kind, target_id, detail (JSONB), ip, at, prev_hash, hash |
| `idempotency_keys` | key, user_id, request_hash, response (JSONB), expires_at |
| `outbox` | id, event_type, payload (JSONB), created_at, published_at |
| `dead_letters` | id, task, args (JSONB), error, failed_at, replayed_at |
| `system_settings` | key, value (JSONB), updated_by |
| `feature_flags` | key, enabled, note |
| `backups` | id, kind, uri, sha256, started_at, finished_at, verified_at, status |

`audit_log` is append-only. Each row stores the hash of the previous row, so that any alteration breaks the chain. The application role has no update or delete permission on it.

---

## 10. API

REST under `/api/v1`, described by OpenAPI. The frontend client is generated from the OpenAPI document.

### 10.1 Conventions
- Errors use one problem-details JSON shape with a stable `code`, a human message and a `trace_id`.
- Lists are paginated with a cursor, and accept filter and sort parameters that are validated against an allow-list.
- Unsafe requests that create work (`POST` runs, exports, batches) accept an `Idempotency-Key` header. A repeated key returns the first response.
- Updates send the record `version`; a stale version returns a conflict.
- Every endpoint declares the permission it needs. A test enumerates every route and fails if any route has no permission check.
- Long work never blocks a request. The endpoint returns a job reference; progress comes from the events stream.

### 10.2 Endpoints

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/mfa/verify`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/mfa/enrol`, `POST /auth/password` |
| Users (admin) | `GET, POST /users`, `GET, PATCH, DELETE /users/{id}`, `PUT /users/{id}/roles` |
| API keys | `GET, POST /api-keys`, `DELETE /api-keys/{id}` |
| Dams and lakes | `GET /dams`, `GET /dams/{id}`, `GET, POST /lakes`, `GET, PATCH, DELETE /lakes/{id}` |
| Datasets | `GET /datasets`, `POST /datasets/uploads` (returns a pre-signed target), `POST /datasets/{id}/validate`, `GET /datasets/{id}` |
| Scenarios | `GET, POST /scenarios`, `GET, PATCH, DELETE /scenarios/{id}`, `GET, POST /scenarios/{id}/versions`, `POST /scenarios/{id}/clone`, `GET, PUT, DELETE /scenario-drafts/{id}` |
| Preview | `POST /preview/volume`, `POST /preview/breach`, `POST /preview/tier0` (fast, synchronous, bounded) |
| Runs | `POST /scenarios/{id}/runs`, `GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/cancel`, `POST /runs/{id}/resume`, `POST /runs/{id}/stages/{stage}/retry`, `GET /runs/{id}/logs`, `GET /runs/{id}/manifest`, `POST /runs/{id}/verify` |
| Events | `GET /runs/{id}/events` (server-sent events or WebSocket; resumable from a last event id) |
| Results | `GET /runs/{id}/layers`, `GET /runs/{id}/point`, `POST /runs/{id}/cross-section`, `GET /runs/{id}/timeseries` |
| Comparison | `GET /runs/{id}/compare`, `GET /runs/{id}/compare/hotspots`, `POST /runs/{id}/compare/hotspots/{hid}/refine`, `POST .../flag` |
| Validation | `GET /runs/{id}/validations`, `POST /runs/{id}/validations` |
| Impact | `GET /runs/{id}/impact`, `GET /runs/{id}/impact/villages`, `GET /runs/{id}/impact/assets` |
| Evacuation | `GET /runs/{id}/evacuation`, `POST /runs/{id}/evacuation/recompute` |
| Cascade | `GET /runs/{id}/cascade` |
| Exports | `POST /runs/{id}/exports`, `GET /exports/{id}`, `GET /exports/{id}/download` |
| Publishing | `GET, POST /runs/{id}/publications`, `DELETE /publications/{id}` |
| Share links | `POST /runs/{id}/shares`, `DELETE /shares/{id}`, `GET /shared/{token}` (read-only, scoped) |
| Run difference | `GET /runs/diff?a=&b=` |
| Batches | `GET, POST /batches`, `GET /batches/{id}`, `POST /batches/{id}/cancel` |
| Lake watch | `GET, POST /monitors`, `GET, PATCH, DELETE /monitors/{id}`, `GET /monitors/{id}/observations`, `POST /monitors/{id}/run` |
| Live flood | `POST /gee/flood`, `GET /gee/flood/{id}` |
| Alerts | `GET, POST /alert-rules`, `PATCH, DELETE /alert-rules/{id}`, `GET /alerts`, `POST /alerts/{id}/acknowledge` |
| Notifications | `GET /notifications`, `POST /notifications/{id}/read` |
| Audit | `GET /audit`, `POST /audit/verify` |
| Benchmarks | `GET /benchmarks` (published validation results) |
| System | `GET /health/live`, `GET /health/ready`, `GET /system/status`, `GET /system/queues`, `GET /system/workers`, `GET /system/dead-letters`, `POST /system/dead-letters/{id}/replay`, `GET /system/backups`, `POST /system/backups` |
| Settings (admin) | `GET, PUT /settings`, `GET, PUT /feature-flags` |

---

## 11. Frontend

### 11.1 Design source
- The visual design comes from the Stitch project the user will export into `design/stitch/`. Treat those exports as the visual reference for layout, spacing, colour and motion.
- Do not copy Stitch-generated code into the application as it stands. Rebuild each screen from shared components, wired to the real API.
- If a Stitch screen shows data the backend does not provide, do not fake it. Raise it with the user: either the backend gains the field, or the element is removed.
- If the exports are missing when the frontend phase starts, ask the user for them.

### 11.2 Design system rules
- **Tokens first.** Extract colour, type, spacing, radius, blur, shadow and motion values into `design/tokens.json`, and generate `tokens.css` from it. No raw colour or pixel value in a component.
- **Glass for controls, solid for data.** Translucent surfaces are used for navigation, toolbars, sheets and floating controls. Panels that carry numbers, tables or charts use a near-opaque surface so that text contrast is guaranteed whatever is behind them.
- **Contrast.** Body text meets 4.5 to 1 and large text 3 to 1 against its real background, in both themes. Check glass surfaces over the brightest and darkest map states.
- **Never colour alone.** Status, hazard class and agreement class are always carried by an icon, a label or a pattern as well as colour.
- **Motion.** Use the shared presets. Honour the reduced-motion setting by replacing movement with fades. No animation may delay access to data.
- **Themes.** Dark (default), light, and a wall-display theme with larger type and higher contrast.
- **Fallbacks.** Where backdrop blur is unsupported or the device is slow, glass surfaces fall back to a solid tint.

### 11.3 Routes and screens

| Route | Screen | Features | Main API areas |
|---|---|---|---|
| `/` | Public landing page | | Benchmarks |
| `/login` | Sign-in and multi-factor | F22 | Auth |
| `/app` | Mission Control | F01 | Dams, lakes, runs, alerts, system |
| `/app/scenarios/new` | Scenario wizard | F02, F03 | Scenarios, drafts, preview, datasets |
| `/app/runs/:id` | Run monitor | F04 | Runs, events |
| `/app/runs/:id/results` | Results explorer | F05 | Results, layers |
| `/app/runs/:id/compare` | Engine comparison | F06 | Comparison |
| `/app/runs/:id/validation` | Satellite validation | F07 | Validation |
| `/app/live` | Live flood monitor | F08 | Live flood |
| `/app/runs/:id/impact` | Impact and loss | F09 | Impact |
| `/app/runs/:id/evacuation` | Evacuation planner | F10 | Evacuation |
| `/app/runs/:id/cascade` | Cascade analysis | F11 | Cascade |
| `/app/runs/:id/exports` | Exports and brief | F12, F13, F23 | Exports, publishing, share links |
| `/app/library` | Scenario library and run difference | F14 | Scenarios, runs |
| `/app/batches` | Batch mode | F15 | Batches |
| `/app/watch` | Lake watch | F16 | Monitors |
| `/app/alerts` | Alerts and notifications | F17 | Alerts, notifications |
| `/app/data` | Data catalogue | F18 | Datasets |
| `/app/benchmarks` | Validation and benchmarks | F19 | Benchmarks |
| `/app/system` | System health and recovery | F20 | System |
| `/app/audit` | Audit and provenance | F21 | Audit |
| `/app/admin` | Administration | F22 | Users, API keys, settings |
| `/shared/:token` | Read-only shared result | F23 | Share links |

Global elements: collapsible sidebar, top bar with search, command palette, deployment mode indicator, queue status, notification bell, language and theme switches, user menu; bottom status strip.

### 11.4 Engineering rules
- TypeScript in strict mode. No `any` without a comment explaining why.
- Server state lives in TanStack Query with typed hooks generated from OpenAPI. Client state is small and local.
- Every route has an error boundary, a loading skeleton, an empty state and a permission check.
- Forms validate with the same rules as the backend. The wizard autosaves a draft on every step and restores it after a reload.
- The realtime connection reconnects with backoff and resumes from the last event id. The interface shows when it is reconnecting.
- An offline banner appears when the network drops. Actions that cannot be completed are queued or blocked with a clear message; nothing fails silently.
- Optimistic updates roll back on error.
- Map layers are managed by one layer manager. Rasters come from the tile service; large vector layers use vector tiles. Never load a full raster into the browser.
- Performance budgets, enforced in CI: initial script under an agreed size, largest contentful paint under 2.5 seconds on a mid-range laptop, map interaction at 60 frames per second with the default layers. Record the measured values.
- Accessibility: keyboard access to every control, visible focus, labelled controls, screen-reader text for map results through the inspector and tables. Automated accessibility checks run in CI.
- All text goes through the translation layer. Numbers, dates and units are formatted by locale. Hindi uses a font with full Devanagari coverage.
- Content security policy with no inline scripts. No third-party script, font or tile request in secure mode.

---

## 12. Scientific methods

Record every formula, its source, its valid range and its assumptions in `docs/SCIENCE.md`. **Check each formula against its source before coding it.**

### 12.1 Terrain
- Reproject to a local metric CRS. Fill sinks, burn the stream network, compute flow direction and accumulation, extract the reach downstream of the source, compute HAND.
- Manning roughness from land cover classes, using a documented lookup table with a cited source.

### 12.2 Reservoir volume
- **Register:** use recorded storage when available.
- **Satellite, new lake** (formed after the DEM was acquired, such as a landslide blockage): volume is the sum over the water mask of (water surface elevation minus DEM) times cell area. Water surface elevation is taken from the DEM along the mask edge.
- **Satellite, existing lake** (present when the DEM was acquired): the DEM records the water surface, so the first method returns zero. Use an area-volume scaling relation appropriate to the lake type, with its source cited, and report a wide uncertainty.
- Always flag which method was used.

### 12.3 Breach parameters
- **Embankment dams:** Froehlich (2008), Journal of Hydraulic Engineering. The relations to implement, in SI units, are believed to be: average breach width `B_avg = 0.27 * K_o * V_w^0.32 * h_b^0.04` with `K_o = 1.3` for overtopping and `1.0` otherwise; formation time `t_f = 63.2 * sqrt(V_w / (g * h_b^2))` in seconds; side slopes 1.0 (overtopping) or 0.7 (otherwise) horizontal to vertical. **Confirm every coefficient against the paper before use.**
- **Landslide dams:** Peng and Zhang (2012), Landslides. Implement from the paper. If you cannot access it, ask the user.
- Build an ensemble (p10, p50, p90) from the published uncertainty of the relations, and document how.
- The outflow hydrograph is computed by routing the stored volume through the growing breach with a weir relation. Verify that the hydrograph integrates to the released volume.

### 12.4 Tier 0, rapid envelope
- Derive reach-averaged hydraulic geometry from HAND, solve Manning's equation for the stage that carries the peak discharge, and mark cells with HAND below that stage as inundated.
- Attenuate the peak downstream with a simple, documented method.
- This tier is intentionally conservative and must be labelled as a first estimate.

### 12.5 Tier 1, Delft3D FM
- Two-dimensional shallow water equations on an unstructured mesh, coarse on the floodplain and refined along the channel and near the source.
- Upstream boundary: breach hydrograph (or the SPH outflow when coupled). Downstream boundary: documented choice.
- Initial state: dry floodplain, with base flow in the channel if data allows.
- Write map output at intervals fine enough to compute arrival time accurately.

### 12.6 Tier 2, DualSPHysics
- Weakly compressible SPH on GPU for the near-field only.
- Terrain boundary built from the DEM; reservoir filled to the estimated level; breach opening from the breach parameters.
- Extract the outflow hydrograph at the downstream end of the SPH domain.
- Grid the particle results to the normalised output format over the near-field.

### 12.7 Coupling
- The SPH outflow hydrograph becomes the Delft3D upstream boundary at the hand-off section.
- Check volume conservation across the hand-off and fail the run if the error exceeds a documented tolerance.

### 12.8 Comparison
- Resample both results to a common grid over the overlap area.
- Metrics: extent F-score and IoU, depth RMSE over cells wet in both, arrival-time difference at control sections.
- Agreement map: classify absolute depth difference into documented classes.
- If agreement is below a threshold, refine the mesh or particle spacing and re-run, at most twice. Report the remaining disagreement as uncertainty.

### 12.9 Earth Engine flood mapping
- Follow the UN-SPIDER recommended practice for Sentinel-1 flood mapping: before and after composites, speckle smoothing, change ratio with a threshold (the practice uses 1.25), removal of permanent water, removal of steep slopes, and removal of small isolated patches.
- In mountainous terrain add a HAND mask, because a slope mask alone removes most of a narrow valley.
- Score simulated extent against observed extent (IoU, hit rate, false alarm ratio).
- In secure mode this module is disabled, or runs on locally supplied imagery.

### 12.10 Impact
- Exposure: population, cropland and assets inside the extent.
- Damage: depth-damage curves from a published source, cited and labelled as generic.
- Hazard class from depth and velocity, using a published classification.
- Village table ordered by arrival time. Evacuation routes on the road network avoiding inundated cells.

### 12.11 Cascade
- Locate the next dam downstream on the reach. Compare the arriving flood volume and peak stage with its capacity and crest level where known. If overtopped, create a chained breach scenario and continue.

---

## 13. Security and secure mode

Write the threat model in `docs/SECURITY.md` before building authentication. Use the OWASP Application Security Verification Standard as the working checklist. **Ask the user whether a specific government or organisational security standard applies** (for example national CERT guidance) and, if so, add its requirements.

### 13.1 Authentication and sessions
- Passwords hashed with Argon2id. A length-based password policy with a breached-password check that works offline.
- Multi-factor authentication by TOTP, required for admin and analyst roles. Recovery codes hashed at rest.
- Short-lived access token; rotating refresh token in an httpOnly, Secure, SameSite cookie. Reuse of a rotated token revokes the whole session.
- Login rate limiting and progressive lockout by account and by address. Uniform responses that do not reveal whether an account exists.
- No default accounts or passwords in any environment. The first admin is created by a one-time bootstrap command.

### 13.2 Authorisation
- Roles: viewer, duty officer, analyst, admin, auditor. Define the permission matrix in one file.
- Check permission on every endpoint and check ownership on every record. A test walks every route with every role and compares the result with the matrix.
- API keys are scoped, expiring, hashed at rest and shown once.
- Share links are signed, scoped to one run, read-only, expiring and revocable.

### 13.3 Input and files
- Validate every input at the boundary. Reject unknown fields.
- Uploads: size limit, allow-list by sniffed content type, archive expansion limits, and validation inside a sandboxed worker with no network and a resource limit. Never trust a file extension.
- Never build a shell command, file path or query from raw input. Use argument lists, safe path joins and parameterised queries.
- Limit the size of drawn polygons, domain areas and requested rasters so that one request cannot exhaust the system.

### 13.4 Web protections
- TLS everywhere outside local development. Strict transport security.
- Content security policy, frame protection, content-type sniffing protection, referrer policy and a restrictive permissions policy.
- Cross-origin requests limited to the configured frontend origin. Cross-site request forgery protection for cookie-authenticated requests.
- Rate limits per user, per key and per address, with stricter limits on expensive endpoints.

### 13.5 Outbound traffic and secure mode
- Every outbound call goes through `backend/app/core/egress.py`, which enforces an allow-list of hosts and blocks private address ranges to prevent server-side request forgery.
- In secure mode the guard refuses every call, and the offline compose file also removes external network access at the container level, so that a coding mistake cannot leak traffic.
- Tests prove both: a unit test that no module calls the network except through the guard, and an integration test that runs a full scenario in secure mode with networking disabled.
- In secure mode the interface serves all scripts, fonts and map tiles locally, and the Earth Engine features are visibly disabled or use locally supplied imagery.

### 13.6 Secrets and data
- Secrets only from the environment or a secrets store. Never in the repository, images, logs or the context file. CI scans for committed secrets.
- Sensitive fields encrypted at rest. Database and object storage encrypted where the platform allows.
- Separate database roles for the application, migrations and read-only reporting.
- Logs never contain passwords, tokens, keys or full request bodies.

### 13.7 Platform hardening
- Containers run as a non-root user with a read-only root file system and dropped capabilities.
- Dependencies and images are scanned in CI. A software bill of materials is produced for each release.
- Solver processes run with resource limits and a time limit, isolated from the API.

### 13.8 Audit
- The audit log records every sign-in, permission change, run, export, publication, share link, setting change and data upload.
- It is append-only and hash-chained. A verify action recomputes the chain and reports the first break.

### 13.9 Security tests
- Authorisation matrix test, input fuzzing on every endpoint, header checks, upload abuse cases, rate-limit tests, token rotation and reuse tests, and the two egress tests.
- Record the evidence in `docs/SECURITY.md`. Report honestly any control that is not yet implemented.

---

## 14. Reliability and recovery

The system must fail visibly, lose no completed work, and recover without manual repair wherever that is possible. Document every failure mode and its recovery in `docs/RECOVERY.md`.

### 14.1 Run state machine
- A run moves through `created`, `queued`, `running`, then `succeeded`, `partially_succeeded`, `failed` or `cancelled`.
- A stage moves through `pending`, `running`, `retrying`, then `succeeded`, `failed` or `skipped`.
- Allowed transitions are defined in one place and enforced in the database transaction that makes them. An illegal transition is rejected and logged.
- State changes and their events are written in the same transaction (transactional outbox), so that the interface never shows a state the database does not hold.

### 14.2 Checkpoints and resume
- Each stage is idempotent: running it twice with the same inputs gives the same outputs and no duplicate records.
- When a stage succeeds it writes a checkpoint holding the hash of its inputs and the URIs and hashes of its outputs.
- On resume, a stage whose input hash matches a valid checkpoint is skipped after its output hashes are verified. Otherwise it runs again.
- A failed run can be resumed from the first unfinished stage. A single stage can be retried.

### 14.3 Retries, timeouts and fallbacks
- Transient failures (network, storage, lock contention) retry with exponential backoff and jitter, up to a documented limit. Permanent failures (invalid input, solver divergence) do not retry.
- Every external call and every solver has a time limit.
- A circuit breaker opens for a data source that keeps failing, and the interface offers the alternative source.
- Fallback is explicit, never silent. If the SPH tier fails, the run finishes as `partially_succeeded` with the Delft3D result, and the interface and the brief state that the comparison is unavailable and why. The system never substitutes one engine's result for another.

### 14.4 Worker failures
- Workers acknowledge a task only after it finishes, and send a heartbeat while a stage runs.
- A reaper task finds stages whose heartbeat has stopped, marks them for retry, and requeues them.
- Workers shut down gracefully: stop taking work, finish or checkpoint the current stage, then exit.
- A task that exhausts its retries goes to the dead-letter list with its error, where an admin can inspect and replay it.

### 14.5 Data protection
- Database: scheduled backups and point-in-time recovery. Object storage: versioned buckets.
- Every artefact has a SHA-256 recorded at creation. A verify action recomputes it. A mismatch marks the artefact corrupt and offers regeneration from the checkpointed inputs.
- A restore drill script restores a backup into a clean environment and checks that a known run can be opened. Run it during hardening and record the result.
- Ask the user for the recovery point and recovery time targets. Until they answer, state your assumed targets in `docs/RECOVERY.md`.

### 14.6 Interface resilience
- Autosaved wizard drafts, reconnecting event streams, offline banner, optimistic updates with rollback, and an error boundary on every route.
- Every error shown to the user states what happened, what was saved, and what they can do next. Each carries a trace id for support.

### 14.7 Resilience tests
- Kill a worker in the middle of each stage and verify that the run resumes and produces identical output hashes.
- Stop the database, the broker and the object store in turn during a run, restore them, and verify recovery.
- Corrupt an artefact and verify detection and regeneration.
- Submit the same run request twice with one idempotency key and verify a single run.
- Fill the queue and verify back-pressure and clear user feedback.

## 15. Observability and operations

- Structured JSON logs with a correlation id that follows a request from the browser through the API to every worker stage.
- Metrics for request rate, errors and latency; queue depth and age; stage duration by engine; worker and GPU utilisation; storage use; failed sign-ins.
- Traces across the API and workers.
- Dashboards for platform health and for run performance. Alerts for a stalled queue, repeated stage failure, backup failure, low storage and audit-chain break.
- `GET /health/live` reports the process is up. `GET /health/ready` checks the database, broker, object storage and migrations.
- `docs/RUNBOOK.md` gives a step-by-step procedure for each alert.
- All of this runs locally with no external service in secure mode.

---

## 16. Build phases

At the end of each phase: run the acceptance tests, update the context file, report, and **stop for approval**.

### Phase 0: Foundations
- Repository structure, tooling, CI, Docker compose skeleton, `.env.example`.
- Scenario config schema, engine adapter protocol, typed error hierarchy, provenance (hashes, versions, run manifest).
- **Accept when:** a fresh clone builds and passes lint, type check and tests with one command; an invalid config produces a clear error; CI is green.

### Phase 1: Terrain, data and Tier 0
- Data access with caching; DEM clip and conditioning; HAND; roughness.
- Tier 0 adapter producing normalised output; shapefile, KML and COG export.
- **Accept when:** for a small test reach, the envelope is produced and opens correctly in a GIS viewer; unit tests cover HAND and the rating method on synthetic terrain with known answers; run time is measured and reported.
- **Likely to need from the user:** access details for any data source that requires an account.

### Phase 2: Volume, breach and Delft3D FM
- Volume methods; breach parameters and ensemble; hydrograph with volume check.
- Delft3D FM container; mesh and model generation; run; reader to normalised output.
- **Accept when:** the idealised dam break benchmark matches its reference solution within a stated error; breach relations reproduce worked values from their sources; the hydrograph integrates to the released volume.
- **Stop and ask** if the solver cannot be installed by a documented route.

### Phase 3: DualSPHysics
- Container with GPU support; geometry and case generation; run; reader; outflow extraction.
- **Accept when:** the idealised dam break benchmark matches its reference within a stated error; a near-field case on real terrain completes and conserves volume.
- **Likely to need from the user:** GPU details and driver versions.

### Phase 4: Coupling and cascade
- SPH to Delft3D hand-off with volume check; cascade logic.
- **Accept when:** a coupled run completes; hand-off volume error is within tolerance; a test with two dams in series triggers the cascade correctly.

### Phase 5: Comparison and uncertainty
- Regridding, metrics, agreement map, hotspots, refinement rule, ensemble envelope.
- **Accept when:** metrics are verified on synthetic rasters with known answers; the refinement loop stops after two passes; an agreement map is produced for the benchmark.

### Phase 6: Earth Engine module
- Authentication, flood mapping, masks, scoring, exposure, lake water-area measurement for lake watch.
- **Accept when:** a known historical flood is mapped and checked visually against a published map; scoring works on a test pair.
- **Needs from the user:** Earth Engine service account credentials and project id.

### Phase 7: Impact, evacuation and exports
- Exposure, damage, hazard class, village table, critical assets, evacuation routing with time margin, all export formats, PDF brief.
- **Accept when:** totals for one scenario are verified by an independent manual calculation; all export formats open in standard tools; the brief states assumptions and uncertainty.

### Phase 8: Platform core
- Database schema and migrations; authentication, multi-factor, roles and permissions; API conventions; workers and queues; run state machine; checkpoints, resume and retry; egress guard; audit log; object storage; tile service.
- API for scenarios, drafts, previews, runs, events, results, comparison, validation, impact, evacuation, cascade and exports.
- **Accept when:** the authorisation matrix test passes for every route; a run started through the API completes; killing a worker mid-stage is followed by a successful resume with identical output hashes; the audit chain verifies.
- **Needs from the user:** database, storage and secret values; any required security standard.

### Phase 9: Frontend core
- Design tokens and shared components from the Stitch exports; application shell; sign-in; Mission Control; scenario wizard; run monitor; results explorer; engine comparison; satellite validation; impact; evacuation; cascade; exports.
- **Accept when:** a user with defaults only completes a full run in the browser; every route has loading, empty, error and no-permission states; browser tests, accessibility checks and performance budgets pass; both languages and both themes work.
- **Needs from the user:** the Stitch exports.

### Phase 10: Extended features
- Scenario library, versions and run difference; batch mode; lake watch; alerts and notifications; data catalogue with validated uploads; map service publishing; share links; live flood monitor; benchmarks page; system health and recovery screen; audit screen; administration; wall and field display modes; help and method notes.
- **Accept when:** each feature ID F14 to F26 has passing backend, interface and end-to-end tests, and an entry in `docs/FEATURES.md`.

### Phase 11: Hardening
- Full security test suite and evidence; resilience tests from Section 14.7; load tests; backup and restore drill; observability dashboards and alerts; runbook.
- **Accept when:** every test in Sections 13.9 and 14.7 passes or is reported with a reason; the restore drill succeeds; measured performance is recorded.

### Phase 12: Validation and deployment
- Run the real dam failure benchmark and the Indian demonstration hindcast; write `docs/VALIDATION.md` with real numbers and the commands that produced them; publish them on the benchmarks page.
- Secure mode verified end to end; documentation complete; deployment.
- **Accept when:** validation results are published honestly, including where the models perform poorly; the deployed link works and the README points to it; a new engineer can run the system from the documentation.
- **Needs from the user:** hosting details and domain; choice of the Indian demonstration case.

---

## 17. The context file

Maintain `docs/BUILD_CONTEXT.md` as the single record of the build. Update it at the end of every phase and whenever a significant decision is made. A new agent must be able to continue the work from this file alone.

Use this structure:

```markdown
# PravahX Build Context

## Current state
- Phase in progress:
- Last completed phase and date:
- What works end to end right now:

## Phase log
### Phase N: <name>  (status: done | in progress)
- Built: (files and modules)
- Decisions: (with reasons; link to DECISIONS.md)
- Deviations from the build spec: (what and why)
- Tests: (how many, what they cover, pass or fail)
- Measured results: (numbers, units, command used)
- Known issues and limits:
- Requirement IDs advanced:
- Feature IDs advanced:

## Environment
- Dependency versions (pinned):
- Solver versions and how they were installed:
- Hardware used for measurements:

## Credentials requested from the user
- (name of each credential and its purpose; never the value)

## Open questions for the user

## Next steps
```

---

## 18. Credentials and inputs to request

Ask for each of these only when the phase needs it. Never proceed with a placeholder.

| Item | Needed in | Purpose |
|---|---|---|
| Elevation data account or key, if the chosen route needs one | Phase 1 | DEM download |
| Dam register source file | Phase 1 or 2 | Dam height and storage |
| Rainfall data files or access | Phase 2 | Hydrological input |
| GPU details | Phase 3 | DualSPHysics build |
| Earth Engine service account and project id | Phase 6 | Flood mapping |
| Database, object storage and secret key values | Phase 8 | Platform |
| Hosting access and domain | Phase 12 | Deployment |
| Licence choice | Phase 0 | Repository licence |
| Stitch design exports | Phase 9 | Interface design reference |
| Required security standard, if any | Phase 8 | Security controls and tests |
| Recovery point and recovery time targets | Phase 8 | Backup design |
| Email or webhook details for notifications, if wanted | Phase 10 | Alert delivery |

---

## 19. Quality standard

"No bugs" cannot be guaranteed by any process. What you must deliver is software in which defects are hard to introduce and easy to find:

- Every core function has unit tests, including edge cases (empty mask, flat terrain, zero volume, no-data).
- Property-based tests for numerical invariants: volume conservation, non-negative depth, monotonic arrival time downstream.
- Integration tests for each stage boundary on a small fixture reach.
- End-to-end test of the whole pipeline in CI on a tiny case.
- Type checking and linting must pass with no ignores unless justified in a comment.
- No silent failure: errors are typed, logged and surfaced to the user.
- Every numerical tolerance and threshold is a named, documented constant.
- A change that lowers test coverage of the core package needs the user's approval.

---

## 20. Definition of done for the whole project

- All eight requirements (R1 to R8) are demonstrably met and traced in the context file.
- Both engines pass their benchmarks, with the numbers published.
- The Indian demonstration case runs end to end from the browser and from the command line.
- Exports open in standard GIS tools.
- Secure mode is proven by test.
- Documentation lets a new engineer run the system in under an hour.
- The context file is complete and current.
- Every feature in the catalogue (F01 to F26) is complete by the rule in Section 1.4, or is listed as not built with the reason.
- The security and resilience test suites pass, with evidence in `docs/SECURITY.md` and `docs/RECOVERY.md`.
- A backup has been restored successfully in a drill.
- The interface matches the Stitch design system, in both themes and both languages, and passes the accessibility checks.

---

## 21. First message to send to the user

Before writing any code, reply with:
1. A short summary of your understanding of the system.
2. Any part of this specification that is unclear, contradictory or that you believe is wrong, with your reasoning.
3. What you need from the user to begin Phase 0.

Then wait for the go-ahead.
