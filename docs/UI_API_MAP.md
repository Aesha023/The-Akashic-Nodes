# PravahX: UI ↔ API ↔ Database Alignment Map

This document establishes the authoritative contract mapping every frontend UI page, view, and component to its backing FastAPI REST endpoints, underlying PostGIS/Alembic database tables, and operational mode (**REAL** vs **DEMO**).

## Core Principle: Two Modes (REAL vs DEMO)
1. **REAL**: Backed by verified computational runs or live infrastructure. Normal status labels apply.
2. **DEMO**: Features illustrating the product vision prior to completed multi-tier runs.
   - Always served via `/api/v1/demo/...` endpoints or flagged with `"demo": true`.
   - Never hard-coded in components; rendered with badge `"DEMO · illustrative data"`.
   - Maps show a subtle "DEMO" watermark.
   - Global "Demo content" toggle in top bar (ON: Presentation mode; OFF: Operational mode).
   - Fictional names only ("Demo Reservoir Alpha", "Demo Glacial Lake 1"). Never invent incidents or alerts for real named dams/lakes.
3. **NEVER DEMO**: Validation/Benchmarks page, Section 11 numbers, certifications, engine status labels.

---

## Detailed Mapping Matrix

| Page / Screen | Sub-Component / Feature | Mode | FastAPI Endpoint(s) | HTTP Method | Database Table(s) | Notes & Data Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Landing Page** | Hero Map Preview | **REAL** | `/api/v1/runs/tier0_ganga_accepted/envelope`<br>`/api/v1/validation/status` | GET | `runs`, `extent_geometries` | Displays real Ganga Tier-0 5x5 km extent ($1.72\text{ km}^2$) |
| | Problem Counter (735 / 6,598) | **REAL** | `/api/v1/validation/status` | GET | (Static cited) | NRLD 2023 CWC Emergency Action Plan count |
| | Three Tiers Architecture | **REAL** | `/api/v1/validation/status` | GET | - | Honest status badges (RUN AND PASSED, RUN AND FAILED, etc.) |
| | Analytical Proof (Ritter Plot) | **REAL** | `/api/v1/validation/benchmarks` | GET | - | Verified Ritter dam break benchmark metrics |
| **Authentication & RBAC (F22)** | Sign-in & Token Exchange | **REAL** | `/api/v1/auth/token`<br>`/api/v1/auth/refresh` | POST | `users` | JWT access token + refresh token rotation |
| | TOTP Multi-Factor Auth (MFA) | **REAL** | `/api/v1/auth/mfa/setup`<br>`/api/v1/auth/mfa/verify` | POST | `users` | RFC 6238 TOTP verification |
| | User & Role Management | **REAL** | `/api/v1/admin/users`<br>`/api/v1/admin/roles` | GET, POST, PUT | `users`, `roles` | RBAC roles: `operator`, `analyst`, `viewer` |
| | API Key Generation | **REAL** | `/api/v1/admin/api-keys` | GET, POST, DELETE | `api_keys` | SHA-256 hashed API key management |
| **Mission Control (F01)** | Operational Run Stream | **REAL** | `/api/v1/runs` | GET | `runs` | Real execution history and status |
| | Infrastructure Health | **REAL** | `/api/v1/system/health` | GET | - | Live PostGIS, Redis, Object storage status |
| | Watched Lakes Stream | **DEMO** | `/api/v1/demo/watched-lakes` | GET | `watched_lakes` (demo=true) | Fictional glacial lakes (Alpha, Beta, Gamma) |
| | Active Alerts Stream | **DEMO** | `/api/v1/demo/alerts` | GET | `alerts` (demo=true) | Fictional early warning advisories |
| **Scenario Wizard (F02/F03)** | Tier-0 Dam & Breach Wizard | **REAL** | `/api/v1/scenarios`<br>`/api/v1/scenarios/validate` | POST | `scenarios` | Froehlich breach geometry + DEM/Landcover selection |
| | Satellite-Only Mode Preview | **DEMO** | `/api/v1/demo/satellite-scoring` | GET | - | Empirical power-law volume scaling preview |
| **Run Monitor (F04)** | Simulation Execution Lifecycle | **REAL** | `/api/v1/runs/{id}`<br>`/api/v1/runs/{id}/events` (SSE)<br>`/api/v1/runs/{id}/ws` (WS) | GET, WS | `runs` | Celery task progress, current stage, logs |
| | Multi-Tier Pipeline Canvas | **DEMO** | `/api/v1/runs/{id}` | GET | `runs` | Visual flow T0 (HAND) $\rightarrow$ T1 (Delft3D) $\rightarrow$ T2 (SPH) |
| **Results Explorer (F05)** | Raster COG Tiles & Inundation | **REAL** | `/api/v1/tiles/{run_id}/cog/tiles/{z}/{x}/{y}.png`<br>`/api/v1/runs/{id}/envelope` | GET | `runs`, `extent_geometries` | True Copernicus GLO-30 HAND depth layer |
| | Point Depth Query | **REAL** | `/api/v1/runs/{id}/depth/point?lat=..&lon=..` | GET | - | Samples `tier0_max_depth_cog.tif` dynamically |
| | Artifact Downloads | **REAL** | `/api/v1/runs/{id}/artifacts/{type}` | GET | `run_artifacts` | COG GeoTIFF, GeoJSON, Shapefile, PDF Brief |
| | Time Scrubber & Isochrones | **DEMO** | `/api/v1/demo/time-series` | GET | - | Labeled "available with Tier-1/Tier-2 runs" |
| | Velocity Vectors & 3D Canyon | **DEMO** | `/api/v1/demo/time-series` | GET | - | Labeled "available with Tier-1/Tier-2 runs" |
| **Engine Comparison (F06)** | Comparison Dashboard | **DEMO** | `/api/v1/demo/engine-comparison` | GET | - | Split map view, agreement heatmap, scatter |
| | Delft3D Status Card | **REAL** | `/api/v1/demo/engine-comparison`<br>`/api/v1/validation/status` | GET | - | "Delft3D Ganga comparison: Pending" with real reason |
| **Satellite Validation (F07)** | Kuttanad Mapped Inundation | **REAL** | `/api/v1/gee/kuttanad-result`<br>`/api/v1/validation/status` | GET | - | Sentinel-1 SAR GRD $40.52\text{ km}^2$ observed flood |
| | Contingency Matrix Scoring | **DEMO** | `/api/v1/demo/satellite-scoring` | GET | - | Synthetic IoU / CSI contingency table preview |
| **Live Flood Monitor (F08)** | Near-Real-Time SAR Feeds | **DEMO** | `/api/v1/demo/live-flood` | GET | - | Simulated radar monitoring stream |
| **Impact Assessment (F09)** | Exposure Metrics & Breakdown | **REAL** | `/api/v1/runs/{id}/exposure` | GET | `exposure_results` | WorldPop 2020 (2,696 exposed), 93 bldgs, 159.5 km roads |
| | Monetary Loss Valuation | **NOT RUN**| - | - | - | "NOT RUN yet: Depth-damage models pending calibration" |
| **Evacuation Planner (F10)** | Evacuation Routes & Marooned | **REAL** | `/api/v1/runs/{id}/evacuation` | GET | `evacuation_routes` | 100 severed roads (14.76 km), 2 reachable, 3 marooned |
| **Cascade Analysis (F11)** | Multi-Dam Domino Wave | **DEMO** | `/api/v1/demo/cascade` | GET | - | Fictional structures Alpha $\rightarrow$ Beta $\rightarrow$ Gamma |
| **Exports & Briefs (F12/F13)** | Operational PDF Brief & GIS | **REAL** | `/api/v1/runs/{id}/artifacts/pdf`<br>`/api/v1/runs/{id}/artifacts/geojson` | GET | `run_artifacts` | 1-page PDF brief (SHA-256 verified) |
| **Share Links (F23)** | Cryptographic Access Link | **REAL** | `/api/v1/share/create`<br>`/api/v1/share/{token}` | POST, GET | `share_links` | HMAC-SHA256 authenticated read-only tokens |
| **Scenario Library (F14)** | Scenario Catalog & Versioning | **REAL** | `/api/v1/scenarios`<br>`/api/v1/scenarios/{id}/versions` | GET, POST, PUT | `scenarios`, `scenario_versions` | Version increments, diff lineage |
| | Visual Run Difference Diff | **DEMO** | `/api/v1/demo/engine-comparison` | GET | - | Difference overlay preview |
| **Batch Mode (F15)** | Batch Scenario Dispatch Queue | **REAL** | `/api/v1/batches`<br>`/api/v1/batches/{id}` | GET, POST | `batches`, `batch_items` | Celery batch processing queue |
| | Sample Batch Run Catalog | **DEMO** | `/api/v1/demo/batches` | GET | `batches` (demo=true) | Illustrative national dam inventory batch |
| **Lake Watch / GLOF (F16)** | Real Scheduler Rules Backend | **REAL** | `/api/v1/lake-watch/rules`<br>`/api/v1/lake-watch/status` | GET, POST | `alert_rules` | Celery beat schedule management |
| | Glacial Lake Catalog & Alerts | **DEMO** | `/api/v1/demo/watched-lakes`<br>`/api/v1/demo/alerts` | GET | `watched_lakes`, `alerts` | Fictional glacial lakes with area expansion rates |
| **Alerts Drawer (F17)** | Notification Rules Configuration | **REAL** | `/api/v1/lake-watch/rules` | GET, POST | `alert_rules` | Webhook, email, threshold configuration |
| | Emergency Notification Stream | **DEMO** | `/api/v1/demo/alerts` | GET | `alerts` (demo=true) | Fictional breach and spillway advisories |
| **Data Catalogue (F18)** | Platform Baseline Datasets | **REAL** | `/api/v1/data-catalog/datasets` | GET, POST | `datasets` | Copernicus GLO-30, WorldCover, WorldPop, OSM AOI |
| **Benchmarks / Validation (F19)**| Ground Truth Engine Evidence | **REAL ONLY**| `/api/v1/validation/benchmarks`<br>`/api/v1/validation/status` | GET | - | Ritter analytical, Deltares c019, Delft3D Ganga, DualSPHysics, GEE |
| **System Health (F20)** | Service Health & Diagnostics | **REAL** | `/api/v1/system/health`<br>`/api/v1/system/health/detailed` | GET | `backups` | DB, Redis, MinIO, Celery worker ping, disk space |
| **Audit Log & Tamper Check (F21)**| Cryptographic Hash Chain | **REAL** | `/api/v1/audit/entries`<br>`/api/v1/audit/verify` | GET | `audit_log_entries` | SHA-256 forward-linked tamper-proof audit trail |
