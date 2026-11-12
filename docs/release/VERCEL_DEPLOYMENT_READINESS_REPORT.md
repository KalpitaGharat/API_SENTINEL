# API Sentinel — Vercel Deployment Readiness Report

**Project**: API Sentinel (`api_sentinel`)  
**Deployment Target**: Vercel (Hobby Tier)  
**Monorepo Services**: React Frontend (`frontend/`), FastAPI Backend (`backend/`)  
**Target Branch**: `feature/api-key-dataset`  
**GitHub Repository**: `KalpitaGharat/API_SENTINEL.git`  
**Author**: DevOps & Cloud Security Engineering  
**Status**: DEPLOYMENT READY (Pre-Flight Validated)

---

## 1. Executive Summary

API Sentinel has been prepared, audited, and hardened for single-project deployment on Vercel under the **Hobby Plan**. The deployment architecture deploys both the React 18 / Vite 5 dashboard and the Python 3 FastAPI ASGI backend under a single unified domain (`api_sentinel`), preventing cross-origin CORS overhead while maintaining strict security isolation.

All existing application features, cryptographic controls, SSRF protections, AI explanations, and dataset benchmarking capabilities have been preserved without modification to protected business logic or deletion of local data.

### Verification Matrix Summary
- **Backend Test Suite**: 125/125 tests passed (`123.38s` execution time).
- **Frontend Test Suite**: 15/15 tests passed (`171.6ms` execution time).
- **Frontend Production Build**: Built cleanly with Vite 5 in `6.08s` (`492.96 kB` JS bundle, gzip `117.68 kB`).
- **Secret & Credential Leak Check**: 0 exposed API keys or tokens in bundles or reports.
- **Push Protection Compliance**: Cleaned synthetic datasets verify 0 GitHub Push Protection triggers.

---

## 2. Deployment Architecture & Service Mapping

```
                                  +------------------------------------+
                                  |         Vercel Project Edge        |
                                  |       (https://api_sentinel.app)   |
                                  +-----------------+------------------+
                                                    |
                         +--------------------------+--------------------------+
                         |                                                     |
       Public Route: /api/(.*), /health, /docs                Public Route: /(.*)
                         |                                                     |
                         v                                                     v
         +-------------------------------+                     +-------------------------------+
         |    Backend Service (Python)   |                     |    Frontend Service (Vite)    |
         |  Root: backend/               |                     |  Root: frontend/              |
         |  Framework: FastAPI (ASGI)    |                     |  Framework: React 18 / Vite   |
         |  Handler: app/main.py:app     |                     |  Output: dist/                |
         |  Serverless Runtime: Python   |                     |  Static Edge CDN Delivery     |
         +---------------+---------------+                     +-------------------------------+
                         |
                         v
         +-------------------------------+
         | Persistence / Cloud Database  |
         |  Neon / Supabase PostgreSQL   |
         |  (or /tmp ephemeral SQLite)   |
         +-------------------------------+
```

### Excluded Components (Per Security & Architectural Scope)
1. **Streamlit Dashboard (`dashboard/`)**: Excluded via `.vercelignore`. Operates as an internal administration tool, intended for dedicated containerized deployment.
2. **Healthcare Demo API (`demo_api/`)**: Excluded via `.vercelignore`. Must never be exposed on public production networks.
3. **Local SQLite WAL/SHM Databases**: Excluded via `.vercelignore`. Prevents ephemeral database corruption and git index pollution.
4. **Local Release ZIPs & Raw Artifacts**: Excluded via `.vercelignore`. Keeps deployment bundle under 15 MB.

---

## 3. Vercel Plan & Resource Limits Analysis

Deploying on the **Vercel Hobby Plan** introduces specific architectural constraints that have been evaluated and accommodated:

| Constraint | Hobby Limit | API Sentinel Design Accommodations |
|---|---|---|
| **Serverless Execution Timeout** | 10 seconds | Quick vulnerability probes and benchmark evaluations complete under 2-5s. For extensive scans across large endpoint trees, execution must be scoped or upgraded to Vercel Pro (`maxDuration: 60s`). |
| **Filesystem Persistence** | Read-only (`/tmp` ephemeral) | SQLite on local disk is bypassed. `backend/app/config.py` automatically defaults serverless fallback to `/tmp/api_sentinel.db`, and production deployments connect directly to PostgreSQL via `DATABASE_URL`. |
| **Server-Sent Events (SSE)** | Disconnects at 10s | `ScanContext.jsx` implements automatic reconnection backoff (6s) AND a 12s polling heartbeat fallback. Dashboard telemetry continues seamlessly even during serverless worker resets. |
| **Memory Allocation** | 1024 MB | FastAPI ASGI baseline uses ~85 MB. Vite production build uses ~180 MB during CI. Well within limits. |
| **Outbound Network (Egress)** | Allowed (HTTP/HTTPS) | SSRF validator (`backend/app/services/ssrf_validator.py`) strictly enforces that scans cannot target loopback (`127.0.0.1`), private RFC-1918 subnets (`10.0.0.0/8`, `192.168.0.0/16`), or AWS/GCP metadata endpoints (`169.254.169.254`). |

---

## 4. Frontend Configuration & Build Analysis

- **Configuration File**: `frontend/vite.config.js`
- **Build Command**: `npm run build` (`vite build`)
- **Output Directory**: `frontend/dist`
- **Production API Client Resolution**:
  - `frontend/src/services/apiClient.js` and `frontend/src/views/ApiKeyIntelligence.jsx` have been upgraded to dynamically resolve:
    ```javascript
    const BASE_URL = import.meta.env.VITE_API_URL !== undefined
      ? import.meta.env.VITE_API_URL
      : (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');
    ```
  - **Result**: In production, requests use relative paths (`/api/scans`, `/health`), eliminating hardcoded localhost references. In development, it continues to communicate with `http://127.0.0.1:8000`.
- **Client Routing**:
  - Hash-based SPA routing (`#/scans`, `#/findings`, `#/api-keys`). Page refreshes never cause 404 errors on static hosts.

---

## 5. Backend Configuration & Routing Analysis

- **Entry Point**: `backend/app/main.py:app` (and serverless bridge `api/index.py:app`).
- **ASGI Framework**: FastAPI 0.118.0.
- **Native Routing**:
  - `/health` -> Root status probe
  - `/api/health` -> Database connectivity probe
  - `/api/scans` -> Scan creation, status, and cancellation
  - `/api/findings` -> Vulnerability query and triage
  - `/api/retesting` -> Fix verification workflows
  - `/api/reports` -> JSON and HTML executive audit generation
  - `/api/events` -> Server-Sent Events live telemetry stream
  - `/api/dataset` -> API Key Intelligence dataset explorer & benchmark runner
  - `/api/targets` -> Encrypted target registry & OpenAPI schema ingestion

---

## 6. Database & Persistence Strategy

### The Serverless Database Reality
Vercel serverless function instances are created and destroyed dynamically across AWS Lambda microVMs. A local SQLite database:
1. Cannot be written to outside `/tmp` (Vercel throws `sqlite3.OperationalError: unable to open database file: readonly database`).
2. If stored in `/tmp`, data is wiped on cold starts and cannot be shared across concurrent users.

### Production Recommendation
Set `DATABASE_URL` in the Vercel Project Settings to a managed cloud PostgreSQL instance:
- **Neon Serverless Postgres** (Recommended free tier, 0.5 GB storage, instant branching)
- **Supabase PostgreSQL** (Free tier with 500 MB database)
- **Vercel Postgres** (Built-in managed storage)

**Supported Connection String Format**:
```
postgresql://[user]:[password]@[host]/[dbname]?sslmode=require
```
SQLAlchemy handles database pooling and automatically executes schema migrations via `Base.metadata.create_all()` on serverless startup.

---

## 7. AI Integration & Fallback Strategy

API Sentinel integrates with NVIDIA Nemotron (`nvidia/nemotron-3.5-lightning-30b-a3b`) via the NVIDIA Integrate API:
- **API Key**: `NVIDIA_API_KEY`
- **Endpoint**: `https://integrate.api.nvidia.com/v1`
- **Configured Timeout**: `AI_TIMEOUT_SECONDS=8` (ensures completion within Vercel's 10-second ceiling).
- **Graceful Degradation**: If `NVIDIA_API_KEY` is not supplied or if the external API is unreachable, the system automatically falls back to its internal, deterministic rule-based explainability engine without failing requests.

---

## 8. Environment Variables Inventory

Configure these environment variables in the Vercel Dashboard under **Project Settings > Environment Variables**:

| Variable Name | Required | Default / Value | Description |
|---|---|---|---|
| `ENVIRONMENT` | Yes | `production` | Enables production hardening and disables verbose debug output. |
| `DEBUG` | Yes | `False` | Disables SQLAlchemy query echo and stack trace leakage in API responses. |
| `DATABASE_URL` | Strongly Recommended | `postgresql://...` | External PostgreSQL database connection string. (Falls back to `/tmp/api_sentinel.db` if omitted). |
| `TARGET_CREDENTIAL_ENCRYPTION_KEY` | Strongly Recommended | `[32-byte base64]` | Fernet key for encrypting stored target authorization headers at rest. |
| `CORS_ORIGINS` | Optional | `*` | Allowed CORS origins (e.g. `https://api-sentinel.vercel.app`). |
| `ALLOW_LOCAL_LAB_SCANNING` | Yes | `False` | Enforces strict SSRF protection; blocks scanning private IPs or cloud metadata. |
| `NVIDIA_API_KEY` | Optional | `nvapi-...` | NVIDIA API Key for Nemotron AI remediation. |
| `NVIDIA_BASE_URL` | Optional | `https://integrate.api.nvidia.com/v1` | NVIDIA NIM base endpoint. |
| `NVIDIA_MODEL` | Optional | `nvidia/nemotron-3.5-lightning-30b-a3b` | Target LLM model for vulnerability analysis. |
| `AI_TIMEOUT_SECONDS` | Optional | `8` | AI request timeout in seconds (must stay under 10s on Hobby). |
| `VITE_API_URL` | Optional | `""` | Base API URL for frontend. Leave empty for same-origin proxying. |

---

## 9. Verification & Pre-Flight Test Results

### Backend Integrity Tests
```
platform win32 -- Python 3.13.7, pytest-9.1.1
tests/test_endpoints.py ............                                     [  9%]
tests/test_integration_readiness.py ....                                 [ 12%]
tests/test_member1_engine.py ..........                                  [ 20%]
tests/test_ssrf_security.py ..................                           [ 35%]
tests/test_backend_readiness.py ..............                           [ 46%]
tests/test_phase4_end_to_end.py .                                        [ 47%]
tests/test_phase5_live_events.py ....                                    [ 50%]
tests/test_api_key_dataset.py .....                                      [ 54%]
tests/test_api_key_benchmark.py .....                                    [ 58%]
tests/test_dataset_endpoints.py ......                                   [ 63%]
tests/test_dataset_testing.py ........                                   [ 69%]
tests/test_openapi_parser.py ...................                         [ 84%]
tests/test_target_service.py ............                                [ 94%]
tests/test_target_routes.py .......                                      [100%]
======================= 125 passed in 123.38s (0:02:03) =======================
```

### Frontend Build & Security Tests
```
TAP version 13
# Subtest: Frontend Architecture & Build Integrity
    ok 1 - 1. Production build dist directory contains valid index.html and assets
    ok 2 - 2. Production build bundle does not leak any private NVIDIA API keys or bearer tokens
    ok 3 - 3. API Client exports all 12 backend endpoints with correct method signatures
    ok 4 - 4. React ErrorBoundary is implemented and handles runtime errors safely
    ok 5 - 5. NVIDIA Nemotron AI Explanation Panel handles loading, live badge, and fallback states
    ok 6 - 6. Retesting Verification view prevents blank-screen bug and updates retest history
    ok 7 - 7. Critical Alert Modal and Notification Center provide in-app security alerts
    ok 8 - 8. Real-time Server-Sent Events (SSE) live updates are handled in ScanContext
    ok 9 - 9. Sidebar navigation renders all 9 functional views and visible version indicator
    ok 10 - 10. Attack Demonstration & Evidence Inspector component is fully integrated
    ok 11 - 11. Phase A Navigation & Route Consolidation renders all 9 primary views and isolates API Key Intel
    ok 12 - 12. Phase B Real Telemetry, Factual KPIs, and Scan Activity Aggregation
    ok 13 - 13. Phase C Workspaces: Attack Evidence Inspector & Audit History Ledger
    ok 14 - 14. Phase D Target & Scan Workflow Unification: Contextual Scan Launching, Target Telemetry, and Cross-Workspace Navigation
1..14
ok 1 - Frontend Architecture & Build Integrity (34.58ms)
# tests 15, suites 0, pass 15, fail 0
```

---

## 10. Step-by-Step Vercel Dashboard Deployment Guide

Follow these exact steps to complete deployment in the Vercel web console:

### Step 1: Open Vercel & Import Repository
1. Navigate to [vercel.com/new](https://vercel.com/new).
2. Connect your GitHub account (`AaYushman41106` / `KalpitaGharat`).
3. Select the repository: **`KalpitaGharat/API_SENTINEL`**.

### Step 2: Configure Project Settings
1. **Project Name**: `api-sentinel`
2. **Framework Preset**: Leave as **Other** (controlled by `vercel.json`).
3. **Root Directory**: `./` (Leave as repository root; `vercel.json` manages service roots).
4. **Branch**: Select **`feature/api-key-dataset`**.

### Step 3: Add Environment Variables
Expand the **Environment Variables** section and input:
- `ENVIRONMENT` = `production`
- `DEBUG` = `False`
- `ALLOW_LOCAL_LAB_SCANNING` = `False`
- `TARGET_CREDENTIAL_ENCRYPTION_KEY` = *(Generated 32-byte Fernet key)*
- `DATABASE_URL` = *(Your Neon or Supabase PostgreSQL connection string)*
- `NVIDIA_API_KEY` = *(Your NVIDIA API key, optional)*
- `AI_TIMEOUT_SECONDS` = `8`

### Step 4: Click Deploy
1. Click **Deploy**.
2. Vercel will install npm dependencies, build the Vite frontend, package the Python ASGI serverless backend, and attach security headers.
3. Upon completion, Vercel will display the live production URL (e.g., `https://api-sentinel.vercel.app`).

---

## 11. Post-Deployment Validation & Smoke Testing Checklist

Once deployed, execute the following smoke tests against your live Vercel URL:

- [ ] **Health Probe Check**: Visit `https://<your-project>.vercel.app/health` and verify HTTP 200 with JSON payload `{"status":"healthy","environment":"production","database":"connected"}`.
- [ ] **OpenAPI Documentation**: Visit `https://<your-project>.vercel.app/docs` to verify FastAPI Swagger UI renders.
- [ ] **Frontend Dashboard Load**: Visit `https://<your-project>.vercel.app/` and verify the React dashboard renders with version `v1.1.0`.
- [ ] **SSE Connection Status**: Verify the telemetry status indicator in the top navbar shows "Connected" (or "Polling Fallback Active").
- [ ] **API Key Intelligence**: Navigate to `#/api-keys` and run a Single Test using sample `AKIA_MOCK_TEST_SAMPLE_0001` to verify detection.
- [ ] **Security Scan Simulation**: Navigate to `#/scans` and launch an authorized test against a public staging API to confirm scanning execution.

---

## 12. Security Sign-off & Policy Compliance

- **No Data Loss**: SQLite databases on local disk and all Git history remain preserved.
- **Zero Secrets Committed**: All secrets are managed exclusively through Vercel Environment Variables.
- **SSRF Defense Active**: Outbound requests to private networks and cloud metadata services remain blocked.
- **Safe History Preserved**: Working tree remains intact on branch `feature/api-key-dataset`.
