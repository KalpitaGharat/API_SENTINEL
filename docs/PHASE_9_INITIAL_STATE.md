# Phase 9: Initial State Inspection Report

**Project:** API Sentinel  
**Project Path:** `C:\PROJECTS\api-sentinel`  
**Inspection Date:** 2026-11-11  
**Auditor Role:** Senior Application Security Engineer, Penetration Testing Specialist & Systems Reliability Auditor  

---

## 1. Git Repository State

- **Current Branch:** `feature/api-key-dataset`
- **Head Commit:** `ab08930 docs(audit): add final dataset integrity and benchmark audit report`
- **Working Tree Status:** Cleanly tracking changes from API Key Intelligence and API Onboarding / OpenAPI Discovery phases.

### Staged Changes
None (`git status` reports no staged files).

### Unstaged Tracked Changes
| File Path | Description of Changes |
| :--- | :--- |
| `backend/app/config.py` | Added `TARGET_CREDENTIAL_ENCRYPTION_KEY` configuration field |
| `backend/app/main.py` | Registered `dataset.router` and `targets.router` with lifespan DB initialization |
| `backend/app/models.py` | Added models for `ApiTarget`, `DiscoveredEndpoint`, and `TargetAuthProfile` |
| `backend/app/routes/dataset.py` | Added live testing endpoints and batch test mutex locking |
| `backend/app/schemas.py` | Added request/response schemas for datasets, targets, endpoints, auth profiles |
| `backend/app/services/api_key_benchmark.py` | Shannon entropy, regex explanations, batch evaluator |
| `backend/pytest.ini` | Configured testpaths covering 14 test modules |
| `dashboard/app.py` | Added route for Streamlit `onboarding` and `api_keys` |
| `dashboard/components/sidebar.py` | Added sidebar navigation entries for `onboarding` and `api_keys` |
| `dashboard/views/api_keys.py` | Streamlit single-test, batch test, and benchmark view |
| `docs/API_KEY_BENCHMARK_GUIDE.md` | API Key benchmark guide |
| `docs/API_KEY_DATASET_GUIDE.md` | API Key dataset guide |
| `docs/API_KEY_DATASET_SECURITY.md` | Security and credential isolation guide |
| `frontend/src/App.jsx` | Registered `onboarding` and `api_key_intel` routes & header metadata |
| `frontend/src/components/Sidebar.jsx` | Added sidebar links for Onboarding & API Key Intelligence |
| `frontend/src/services/apiClient.js` | Added target CRUD, spec preview/import, auth profiles, and scan API client methods |
| `frontend/src/views/ApiKeyIntelligence.jsx` | Dedicated React workspace for 10K dataset testing |
| `metadata/benchmark_history.json` | Persistent benchmark execution history |
| `metadata/benchmark_results.json` | Benchmark metrics snapshot |

### Untracked Files
| File Path | Purpose |
| :--- | :--- |
| `backend/app/routes/targets.py` | Target CRUD, OpenAPI import, auth profiles, validation, scan execution bridge |
| `backend/app/services/credential_vault.py` | Fernet authenticated credential encryption and masking service |
| `backend/app/services/openapi_parser.py` | Multi-version OpenAPI 3.0/3.1 and Swagger 2.0 parser with SSRF checks |
| `backend/app/services/target_service.py` | Target management business logic and persistence service |
| `backend/tests/test_dataset_testing.py` | Unit tests for single and batch dataset evaluation |
| `backend/tests/test_openapi_parser.py` | 19 unit tests for OpenAPI parser engine |
| `backend/tests/test_target_routes.py` | 7 end-to-end integration tests for target API routes |
| `backend/tests/test_target_service.py` | 10 unit tests for target management service |
| `dashboard/views/onboarding.py` | Streamlit onboarding, endpoint discovery, and scan launchpad |
| `docs/API_ONBOARDING_GUIDE.md` | Full architecture and user guide for API onboarding |
| `frontend/src/views/ApiOnboarding.jsx` | React workspace for API target catalog, spec import, and BOLA setup |

---

## 2. Environment Configuration & Secrets Safety

- **Environment File:** `C:\PROJECTS\api-sentinel\backend\.env` is present and excluded from version control via `.gitignore`.
- **Environment Keys Defined:**
  - `ENVIRONMENT=development`
  - `DEBUG=True`
  - `PORT=8000`
  - `HOST=0.0.0.0`
  - `CORS_ORIGINS`
  - `DATABASE_URL`
  - `ALLOW_LOCAL_LAB_SCANNING=True`
  - `NVIDIA_API_KEY`
  - `NVIDIA_BASE_URL`
  - `NVIDIA_MODEL`
  - `AI_TIMEOUT_SECONDS`
  - `TARGET_CREDENTIAL_ENCRYPTION_KEY`
- **Exclusion Verification:** `.gitignore` explicitly excludes `.env`, `*.db`, `*.db-wal`, `node_modules`, `*.zip`, and `quarantine/`. No live credentials or Fernet encryption keys are checked into Git.

---

## 3. Active Processes & Port Allocations

- **FastAPI Backend:** Running on `http://127.0.0.1:8000` (PID managed daemon)
- **Healthcare Demo API:** Running on `http://127.0.0.1:8001` (PID managed daemon)
- **React Frontend:** Running on `http://127.0.0.1:5173` (Vite dev server)
- **Baseline Test Suite:** 122 tests passing across 14 test modules in `pytest.ini`.

---

## 4. Preservation Commitments

In accordance with Phase 9 Absolute Preservation Rules:
1. No files will be reset, wiped, or reverted.
2. No working code will be replaced by stubs or mock-only placeholders.
3. Member 1 detection engine (`backend/app/security_engine/member1_engine.py`) remains the single source of truth for vulnerability detection.
4. SSRF controls in `backend/app/security_engine/integration.py` will not be relaxed.
5. All fixes will be surgical, test-backed, and verified with zero regression.
