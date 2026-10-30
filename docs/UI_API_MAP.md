# PravahX: UI ↔ API ↔ Database Alignment Map

This document establishes the authoritative contract mapping every frontend UI page, view, and component to its backing FastAPI REST endpoints, underlying PostGIS/Alembic database tables, operational mode (**REAL** vs **DEMO**), and backing Playwright test suite.

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

## Authoritative Alignment Matrix

| Page | Question | Endpoints | DB Tables | REAL/DEMO | Playwright Test Name |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Landing** | "Where does the water go before it gets there?" | `GET /api/v1/runs/tier0_ganga_accepted/envelope`<br>`GET /api/v1/validation/status`<br>`GET /api/v1/validation/benchmarks` | `runs`, `extent_geometries` | **REAL** | `test_landing_page_smoke` |
| **Home (F00)** | "What would you like to do today?" | `GET /api/v1/runs` | `runs` | **REAL** | `test_home_page_smoke` |
| **Sign In** | "Enter credentials to access operational flood intelligence" | `POST /api/v1/auth/token`<br>`POST /api/v1/auth/refresh`<br>`POST /api/v1/auth/mfa/verify` | `users` | **REAL** | `test_auth_signin_smoke` |
| **Mission Control (F01)** | "What needs my attention now?" | `GET /api/v1/runs`<br>`GET /api/v1/system/health/detailed`<br>`GET /api/v1/demo/watched-lakes`<br>`GET /api/v1/demo/alerts`<br>`GET /api/v1/demo/cascade` | `runs`, `users`, `watched_lakes` (demo), `alerts` (demo) | **REAL + DEMO** | `test_mission_control_smoke` |
| **New Scenario Wizard (F02/F03)** | "Where and how does the hypothetical dam breach occur?" | `POST /api/v1/scenarios`<br>`POST /api/v1/scenarios/validate`<br>`GET /api/v1/demo/satellite-scoring` | `scenarios`, `scenario_versions` | **REAL (T0) + DEMO (Sat)** | `test_scenario_wizard_smoke` |
| **Run Monitor (F04)** | "Is my run progressing?" | `GET /api/v1/runs/{id}`<br>`GET /api/v1/runs/{id}/events` (SSE)<br>`WS /api/v1/runs/{id}/ws` | `runs` | **REAL** | `test_run_monitor_smoke` |
| **Results Explorer (F05)** | "Which areas flood if this dam breaks?" | `GET /api/v1/runs/{id}/summary`<br>`GET /api/v1/runs/{id}/exposure`<br>`GET /api/v1/runs/{id}/depth/point`<br>`GET /api/v1/tiles/{id}/cog/tiles/{z}/{x}/{y}.png`<br>`GET /api/v1/runs/{id}/artifacts/{type}`<br>`POST /api/v1/share/runs/{id}` | `runs`, `exposure_results`, `extent_geometries`, `run_artifacts`, `share_links` | **REAL (data) + DEMO (time slider)** | `test_results_explorer_smoke` |
| **Engine Comparison (F06)** | "How do Tier-0 and Tier-1 hydrodynamics compare on the same reach?" | `GET /api/v1/demo/engine-comparison`<br>`GET /api/v1/validation/status` | `runs` | **DEMO (splits) + REAL (status)** | `test_engine_comparison_smoke` |
| **Satellite Validation (F07)** | "How well does the flood simulation match Sentinel-1 satellite radar?" | `GET /api/v1/gee/kuttanad-result`<br>`GET /api/v1/validation/status`<br>`GET /api/v1/demo/satellite-scoring` | (GEE cache) | **REAL (Kuttanad) + DEMO (scoring)** | `test_satellite_validation_smoke` |
| **Live Flood Monitor (F08)** | "Where is flood water actively rising right now?" | `GET /api/v1/demo/live-flood` | `alerts` (demo) | **DEMO** | `test_live_flood_smoke` |
| **Impact Assessment (F09)** | "Who and what is affected?" | `GET /api/v1/runs/{id}/exposure` | `exposure_results` | **REAL** | `test_impact_assessment_smoke` |
| **Evacuation Router (F10)** | "How do people get out safely?" | `GET /api/v1/runs/{id}/evacuation` | `evacuation_routes` | **REAL** | `test_evacuation_router_smoke` |
| **Cascade Modeling (F11)** | "Will the failure of this dam trigger a domino breach downstream?" | `GET /api/v1/demo/cascade` | `cascade_runs` (demo) | **DEMO** | `test_cascade_modeling_smoke` |
| **Exports & Share (F12/F13/F23)** | "How do I securely share and export verifiable flood intelligence?" | `GET /api/v1/runs/{id}/artifacts/{type}`<br>`POST /api/v1/share/runs/{id}`<br>`GET /api/v1/share/{token}` | `run_artifacts`, `share_links` | **REAL** | `test_exports_share_smoke` |
| **Scenario Library (F14)** | "Which historical and precomputed breach scenarios are archived?" | `GET /api/v1/scenarios`<br>`GET /api/v1/scenarios/{id}/versions`<br>`POST /api/v1/scenarios/{id}/clone` | `scenarios`, `scenario_versions` | **REAL** | `test_scenario_library_smoke` |
| **Batch Processing (F15)** | "Can we screen all 6,598 registered large dams concurrently?" | `GET /api/v1/batches`<br>`POST /api/v1/batches`<br>`GET /api/v1/demo/batches` | `batches`, `batch_items` | **REAL (queue) + DEMO (samples)** | `test_batch_processing_smoke` |
| **Lake Watch / GLOF (F16)** | "Are glacial lakes expanding dangerously in upstream catchments?" | `GET /api/v1/lake-watch/rules`<br>`POST /api/v1/lake-watch/rules`<br>`GET /api/v1/demo/watched-lakes` | `alert_rules`, `watched_lakes` (demo) | **REAL (scheduler) + DEMO (lakes)** | `test_lake_watch_smoke` |
| **Alert Rules (F17)** | "Who needs to be warned immediately when water levels rise?" | `GET /api/v1/lake-watch/rules`<br>`POST /api/v1/lake-watch/rules`<br>`GET /api/v1/demo/alerts` | `alert_rules`, `alerts` (demo) | **REAL (rules) + DEMO (alerts)** | `test_alert_rules_smoke` |
| **Data Catalogue (F18)** | "Which elevation models and hydrological datasets are verified in storage?" | `GET /api/v1/data-catalog/datasets`<br>`POST /api/v1/data-catalog/datasets` | `datasets` | **REAL** | `test_data_catalogue_smoke` |
| **Validation & Benchmarks (F19)** | "Are these hydrodynamic calculations scientifically proven?" | `GET /api/v1/validation/benchmarks`<br>`GET /api/v1/validation/status` | (Analytical & empirical records) | **REAL ONLY (NO DEMO)** | `test_validation_benchmarks_smoke` |
| **System Health (F20)** | "Are all cluster nodes and solver engines healthy?" | `GET /api/v1/system/health`<br>`GET /api/v1/system/health/detailed` | `backups` | **REAL** | `test_system_health_smoke` |
| **Audit Hash Chain (F21)** | "Has any record or simulation hash been modified?" | `GET /api/v1/audit/entries`<br>`GET /api/v1/audit/verify` | `audit_log_entries` | **REAL** | `test_audit_log_smoke` |
| **Admin & Security (F22)** | "Who has permission to launch or approve simulation runs?" | `GET /api/v1/admin/users`<br>`POST /api/v1/admin/users/invite`<br>`GET /api/v1/admin/api-keys`<br>`POST /api/v1/admin/api-keys` | `users`, `roles`, `api_keys` | **REAL** | `test_admin_security_smoke` |
