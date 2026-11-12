# API SENTINEL — PHASE 4: COMPREHENSIVE REPOSITORY & ARCHITECTURE AUDIT

**Date:** November 11, 2026  
**Auditor:** Senior FastAPI Integration Engineer, DevSecOps Specialist & Application Security Auditor  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Standalone Copy:** `C:\PROJECTS\api-sentinel-dashboard`  
**Clean Distribution:** `C:\PROJECTS\API_Sentinel_Complete_Platform.zip`

---

## 1. Executive Summary

A comprehensive repository inspection was conducted across the API Sentinel codebase.
The project represents a substantially mature, explainable API security platform developed by a 3-member hackathon team:
- **Member 1:** Vulnerability detection engine (BOLA/IDOR, Broken Auth, Missing Headers) and toggleable Healthcare Demo API.
- **Member 2:** Enterprise dark-theme Cybersecurity Dashboard in Streamlit, supplemented with a React 18 + Vite + Tailwind CSS dashboard.
- **Member 3:** FastAPI core backend, socket-level SSRF defense, SQLite WAL database, and NVIDIA Nemotron AI integration.

The baseline automated test suite contains **57 passing pytest tests** covering endpoints, engine contracts, real HTTP scanning, SSRF mitigations, database concurrency, and AI fallbacks.

The primary gap identified during this inspection was an **integration disconnect between Member 2's dashboard and Member 3's real FastAPI backend**: Member 2 created the dashboard against an isolated mock data layer (`mock_data.py` and a standalone mock server `dashboard/backend/main.py`), rather than connecting to Member 3's OpenAPI endpoints (`/api/scans`, `/api/findings/{id}`, `/api/findings/{id}/explain`, `/api/scans/{id}/retest`, `/api/scans/{id}/report`). Additionally, Nemotron-3.5-lightning live inference required token budget adjustment to accommodate reasoning tokens before generating JSON content.

---

## 2. Complete Repository File Structure

```
C:\PROJECTS\api-sentinel\
│
├── .dockerignore                                   # Ignores .git, .env, __pycache__, node_modules
├── .gitignore                                      # Standard Python & Node ignore rules
├── Dockerfile                                      # Multi-service container specification
├── docker-compose.yml                              # Compose orchestrating backend (:8000) & demo-api (:8001)
├── api_sentinel.db                                 # Persistent SQLite database (WAL journal mode)
├── README.md                                       # Platform overview, architecture diagrams & specs
├── API_SENTINEL_PHASE_2_SSRF_SECURITY_AUDIT.md     # Phase 2 audit on SSRF & DNS rebinding
├── API_SENTINEL_PHASE_3_BACKEND_READINESS_AUDIT.md # Phase 3 audit on DB, Nemotron AI, & Docker
│
├── backend/                                        # FastAPI Application Core
│   ├── .env                                        # Environment configuration (Dev, DB, NVIDIA Key)
│   ├── .env.example                                # Template for environment variables
│   ├── pytest.ini                                  # Pytest configuration covering all 5 test files
│   ├── requirements.txt                            # Backend Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                                 # FastAPI application, CORS, and router registration
│   │   ├── config.py                               # Pydantic BaseSettings environment validation
│   │   ├── database.py                             # SQLAlchemy engine, session maker, WAL & busy PRAGMAs
│   │   ├── models.py                               # Relational ORM models (Scan, Finding, Evidence, History)
│   │   ├── schemas.py                              # Pydantic v2 request/response schemas
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── scans.py                            # POST /api/scans, GET /api/scans, GET /api/scans/{id}
│   │   │   ├── findings.py                         # GET /findings, explain endpoint, /history endpoint
│   │   │   ├── retesting.py                        # POST /api/scans/{id}/retest
│   │   │   └── reports.py                          # GET /api/scans/{id}/report
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scan_service.py                     # Scan coordination & rollback handling
│   │   │   ├── ai_service.py                       # Nemotron LLM integration & offline rule fallback
│   │   │   ├── retest_service.py                   # Verification retesting & state transitions
│   │   │   └── report_service.py                   # Aggregation, compliance, and health scoring
│   │   └── security_engine/
│   │       ├── __init__.py
│   │       ├── integration.py                      # PinnedSyncBackend & BaseSecurityEngineAdapter
│   │       ├── member1_engine.py                   # Real BOLA, Auth, & Headers scanner
│   │       └── MEMBER1_ENGINE_README.md            # Engine technical guide
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                             # Fixtures & in-memory test DB isolation
│       ├── test_endpoints.py                       # Core API & authorization tests (12 tests)
│       ├── test_integration_readiness.py           # Engine adapter discovery & contract (4 tests)
│       ├── test_member1_engine.py                  # Real HTTP vulnerability scanning (9 tests)
│       ├── test_ssrf_security.py                   # SSRF, DNS pinning, & redirect tests (18 tests)
│       ├── test_backend_readiness.py               # WAL, concurrency, AI parsing & Docker (14 tests)
│       └── audit_live_http.py                      # Live TCP socket verification script
│
├── dashboard/                                      # Member 2 Frontend & Dashboard Suite
│   ├── app.py                                      # Streamlit dashboard entrypoint
│   ├── config.py                                   # UI theme colors & typography constants
│   ├── styles.py                                   # Dark navy cybersecurity CSS & keyframe animations
│   ├── utils.py                                    # Formatting & chart helper utilities
│   ├── requirements.txt                            # Streamlit, Plotly, HTTPX dependencies
│   ├── run.bat                                     # Windows launcher script
│   ├── components/
│   │   ├── cards.py                                # KPI posture metric cards
│   │   ├── charts.py                               # Plotly donut & 14-day scan spline chart
│   │   ├── findings_table.py                       # Interactive findings grid
│   │   └── sidebar.py                              # Fixed enterprise sidebar & particle wave
│   ├── views/
│   │   ├── overview.py                             # Security overview posture view
│   │   ├── new_scan.py                             # Scan configurator & terminal monitor
│   │   ├── findings.py                             # Detailed finding explorer & evidence viewer
│   │   ├── retesting.py                            # Verification retesting runner
│   │   ├── history.py                              # Historical scan audit trail
│   │   └── reports.py                              # Compliance scorecards & report exports
│   ├── services/
│   │   ├── api_client.py                           # HTTPX client connecting to backend
│   │   └── mock_data.py                            # Fallback 37-finding test dataset
│   ├── backend/
│   │   └── main.py                                 # Member 2 standalone mock server (to be bypassed)
│   └── frontend/                                   # React 18 + Vite + Tailwind CSS Application
│       ├── package.json
│       ├── vite.config.js
│       ├── tailwind.config.js
│       ├── src/                                    # React components & view pages
│       └── dist/                                   # Production compiled bundle (index.html)
│
└── demo_api/                                       # Target Healthcare Test API
    ├── __init__.py
    ├── main.py                                     # FastAPI application (--vulnerable / --secure)
    ├── config.py                                   # Target settings (ports, modes)
    ├── database.py                                 # Synthetic patient & physician records
    ├── transport.py                                # In-memory transport for unit tests
    └── README.md                                   # Demo target running guide
```

---

## 3. Comparison of Frontend Deliverables

| Aspect | `dashboard/` (Streamlit) | `dashboard/frontend/` (React) | `C:\PROJECTS\api-sentinel-dashboard` |
| :--- | :--- | :--- | :--- |
| **Primary Framework** | Python 3.13 + Streamlit + Plotly | React 18 + Vite + Tailwind CSS | Exact identical duplicate of `dashboard/` |
| **Operational Status** | Fully operational & interactive | Compiled in `dist/`, fully functional | Redundant standalone copy |
| **Suitability for Demo** | **Recommended Primary Demo** (Single Python runtime, native Python backend interop, seamless Streamlit state) | Secondary / Production SPA | Backup copy |
| **Backend Connectivity** | Currently falls back to `mock_data.py` | Standalone UI state | Currently falls back to `mock_data.py` |

---

## 4. Key Findings & Discovered Issues

### Issue 1: Frontend API Client Disconnect (High Priority)
* **Finding:** `dashboard/services/api_client.py` was implemented by Member 2 to query mock endpoints (`/metrics/summary`, `/scans/trigger`, `/findings`, `/scans/last`), rather than Member 3's real FastAPI backend routes (`/api/scans`, `/api/findings/{id}`, `/api/findings/{id}/explain`, `/api/scans/{id}/retest`, `/api/scans/{id}/report`).
* **Impact:** The Streamlit dashboard defaults to `mock_data.py` even when the real FastAPI backend is running.
* **Remediation:** Update `SentinelAPIClient` to default `base_url="http://127.0.0.1:8000"`, map to real `/api/*` endpoints, parse real scan and finding records from SQLite, and retain `mock_data.py` strictly as an offline fallback when the backend is offline.

### Issue 2: Streamlit Views Simulation Loops (High Priority)
* **Finding:** In `dashboard/views/new_scan.py` and `dashboard/views/retesting.py`, button clicks executed purely local `time.sleep()` loops with static logs rather than calling `api_client.trigger_scan()` or `api_client.retest()`. Furthermore, `findings.py` lacked an "Explain with Nemotron" button.
* **Impact:** A user running a scan or retest in the dashboard would see simulated progress rather than triggering Member 1's real security engine and Member 3's real verification retest engine.
* **Remediation:** Connect `new_scan.py` to `api_client.trigger_scan()`, connect `retesting.py` to `api_client.retest_scan()`, display real HTTP evidence telemetry, and add live AI explanation invocation in `findings.py`.

### Issue 3: Nemotron Token Budget & Reasoning Interaction (Medium Priority)
* **Finding:** NVIDIA Nemotron-3.5-lightning utilizes internal thinking/reasoning tokens. When `max_tokens` was configured to 1024 with a separate system message, reasoning tokens exhausted the budget, resulting in `finish_reason: length` and `content: None`.
* **Impact:** Remote LLM calls returned `None`, forcing the system to fall back to the deterministic rule engine despite having an active API key.
* **Remediation:** Increased `max_tokens=3072`, configured `max_retries=1`, and unified instructions into a single user message. Tested and verified: Nemotron now produces structured JSON explanations directly.

### Issue 4: CORS Configuration for React Frontend (Low Priority)
* **Finding:** `CORS_ORIGINS` in `config.py` permitted ports 8501 and 3000, but omitted Vite's default port 5173 (`http://localhost:5173`).
* **Remediation:** Add `http://localhost:5173,http://127.0.0.1:5173` to `CORS_ORIGINS`.

---

## 5. Security Posture Assessment

1. **SSRF Defense:** Solid. Socket-level IP pinning (`PinnedSyncBackend`) and zero-keepalive connection pooling prevent DNS rebinding attacks. URL normalization, dual-stack DNS, and cloud metadata blocking (`169.254.169.254`) are fully enforced.
2. **Credential Protection:** Synthetic demo passwords (`demo_password_a`, `demo_password_b`) are strictly prevented from leaving the local lab environment via `is_authorized_demo_target()`. User credentials in scan payloads are redacted prior to database persistence.
3. **Database Concurrency:** SQLite in WAL mode with a 30s busy timeout and foreign keys enabled handles concurrent reading and writing without database locks.
4. **AI Safety:** The security engine alone determines vulnerability verdicts. AI output is constrained to explaining verified findings and suggesting remediation. Non-empty string schemas are strictly enforced via Pydantic.

---

## 6. Execution Plan for Remaining Phases

1. **Phase 2 & 4:** Wire `dashboard/services/api_client.py` and Streamlit views (`new_scan.py`, `findings.py`, `retesting.py`, `reports.py`) directly to Member 3's real FastAPI endpoints while preserving graceful offline fallback.
2. **Phase 5:** Execute an end-to-end live HTTP test against the Healthcare Demo API (vulnerable scan -> finding detection -> Nemotron AI explain -> secure toggle -> verification retest -> status promotion to Resolved).
3. **Phase 7:** Audit Docker Compose configurations and verify container networking status.
4. **Phase 8:** Add integration tests for frontend client connectivity and end-to-end workflows.
5. **Phase 9 & 10:** Produce the final demonstration runbook (`API_SENTINEL_FINAL_DEMO_GUIDE.md`) and final verification report.
