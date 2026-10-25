# PravahX Offline & Air-Gapped Deployment Guide

## 1. Executive Summary & Architectural Overview

PravahX is engineered for critical infrastructure and disaster response operations in sensitive or disconnected environments. When operating in an air-gapped security boundary (Constraint C / National Critical Infrastructure), all outbound network connectivity is physically or logically severed.

In **Secure / Air-Gapped Mode** (`PRAVAHX_SECURE_MODE=secure`):
1. **Zero Outbound Network Egress**: Docker containers are bound to an isolated bridge network (`internal: true`). Packets attempting egress to the public internet are rejected at the kernel firewall level.
2. **Deterministic Pre-Staged Data**: All external data dependencies (elevation, population, land use, infrastructure) are read exclusively from pre-staged local storage mounts (`/app/data/`).
3. **External API Circuit Breaking**: Remote satellite calls (Google Earth Engine), OpenStreetMap Overpass live queries, remote elevation downloads (Copernicus GLO-30), and external SMTP gateways are deactivated. If called, they fall back to local cached snapshots or fail fast with explicit air-gap error notices.

---

## 2. Platform Architecture & Services

The complete PravahX backend stack consists of seven interconnected core services that operate independently of external SaaS or cloud infrastructure:

| Service | Container Image | Internal Role | Port | Healthcheck |
| :--- | :--- | :--- | :--- | :--- |
| **`postgis`** | `postgis/postgis:16-3.4` | Spatial relational storage & GeoAlchemy2 geometries | 5432 | `pg_isready -U pravahx` |
| **`redis`** | `redis:7-alpine` | Celery task queue broker, locks & rate limiting | 6379 | `redis-cli ping` |
| **`minio`** | `minio/minio:latest` | S3-compatible local object storage for rasters & exports | 9000, 9001 | `mc ready local` |
| **`titiler`** | `ghcr.io/developmentseed/titiler:latest` | Dynamic Cloud-Optimised GeoTIFF (COG) XYZ tile renderer | 8080 (ext) / 8000 (int) | `curl -f /healthz` |
| **`api`** | `pravahx-backend:latest` | FastAPI REST API, RBAC, audit log, scenario lifecycle | 8000 | `curl -f /api/v1/health` |
| **`worker`** | `pravahx-backend:latest` | Celery CPU worker: hydrographs, HAND, exposure, routes | — | Celery ping |
| **`beat`** | `pravahx-backend:latest` | Celery periodic task scheduler: Lake Watch alerts | — | Celery beat heartbeat |

---

## 3. Data Pre-Staging Protocols

In air-gapped environments, the following datasets must be pre-populated in `./data` prior to starting simulations:

### 3.1 Digital Elevation Models (DEM)
- **Path**: `data/dem/` or `data/ganga_inputs/dem_ganga_32644.tif`
- **Source**: Copernicus GLO-30 or local LiDAR/drone surveys.
- **Format**: Cloud-Optimised GeoTIFF (COG), projected in the appropriate UTM zone (e.g., `EPSG:32644`).
- **Validation**: Verify elevation values are in metres Above Sea Level with valid NoData masks.

### 3.2 Population Density
- **Path**: `data/worldpop/` or `data/ganga_inputs/worldpop_ganga_32644.tif`
- **Source**: WorldPop 2020 100m Constrained (BSGM IND).
- **Format**: Sum-preserving resampled GeoTIFF matching the simulation domain bounds.
- **Integrity**: Check that the sum matches known regional census totals within 1%.

### 3.3 Land Cover / Manning's $n$
- **Path**: `data/landcover/` or `data/ganga_inputs/worldcover_ganga_32644.tif`
- **Source**: ESA WorldCover 10m.
- **Lookup**: Classified according to the PravahX hydraulic roughness table (`core/pravahx/landcover/manning.py`).

### 3.4 Infrastructure Vector Data
- **Path**: `data/osm/` or `data/ganga_inputs/osm_aoi.osm`
- **Source**: OpenStreetMap `.osm` XML or `.pbf` extracts.
- **Attributes**: Highway ways (primary, secondary, residential) and building footprints/relations.

---

## 4. Container Image Bundling for Offline Transfer

To deploy into an air-gapped facility via secure optical or USB media:

### 4.1 On an Connected Staging Machine
```bash
# 1. Pull third-party images
docker pull postgis/postgis:16-3.4
docker pull redis:7-alpine
docker pull minio/minio:latest
docker pull ghcr.io/developmentseed/titiler:latest

# 2. Build PravahX backend image
docker compose build api

# 3. Export all images into a compressed archive
docker save \
  postgis/postgis:16-3.4 \
  redis:7-alpine \
  minio/minio:latest \
  ghcr.io/developmentseed/titiler:latest \
  pravahx-api:latest \
| gzip > pravahx_airgap_bundle.tar.gz

# 4. Generate SHA-256 manifest
sha256sum pravahx_airgap_bundle.tar.gz > pravahx_airgap_bundle.tar.gz.sha256
```

### 4.2 On the Air-Gapped Host
```bash
# 1. Verify cryptographic hash
sha256sum -c pravahx_airgap_bundle.tar.gz.sha256

# 2. Load images into the local Docker daemon
gunzip -c pravahx_airgap_bundle.tar.gz | docker load
```

---

## 5. Startup & Operational Procedures

### 5.1 Initialize Environment
```bash
# Copy template configuration
cp .env.example .env

# Configure environment for offline mode
sed -i 's/PRAVAHX_SECURE_MODE=online/PRAVAHX_SECURE_MODE=secure/g' .env
sed -i 's/SECRET_KEY=/SECRET_KEY='$(openssl rand -hex 32)'/g' .env
sed -i 's/S3_ACCESS_KEY=/S3_ACCESS_KEY=pravahx_minio_admin/g' .env
sed -i 's/S3_SECRET_KEY=/S3_SECRET_KEY='$(openssl rand -hex 16)'/g' .env
```

### 5.2 Launch Stack with Air-Gap Network Enforcement
```bash
# Launch with the offline override compose file
docker compose -f docker-compose.yml -f docker-compose.offline.yml up -d
```

### 5.3 Verify Service Health
```bash
# Inspect running containers
docker compose ps

# Check detailed platform health via the REST API
curl -s http://localhost:8000/api/v1/system/health/detailed | jq .
```

---

## 6. End-to-End Smoke Test Verification

Execute the automated end-to-end smoke test script against the air-gapped stack:

```bash
# Run against the live API
python scripts/smoke_test_api.py --base-url http://localhost:8000
```

The smoke test validates:
- [x] Database, Redis, and MinIO storage connectivity
- [x] Analyst registration, JWT issuance, and RBAC authentication
- [x] Tier-0 Ganga scenario creation and run execution
- [x] Inundation envelope polygon geometry (`tier0_envelope.geojson`)
- [x] Point depth query calibration at coordinate `(78.305, 30.125)`
- [x] Sum-preserving population exposure calculation (2,696 / 9.84%)
- [x] Road network severance depth cutoff ($> 0.30\text{ m}$)
- [x] Origin-to-safety evacuation graph routing (2 reachable, 3 unreachable)
- [x] 1-page executive disaster impact PDF generation (`ganga_tier0_brief.pdf`)
- [x] Artifact bundle packaging (`.zip`)
