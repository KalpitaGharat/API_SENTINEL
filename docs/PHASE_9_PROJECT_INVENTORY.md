# Phase 9: Comprehensive Project Inventory

**Project:** API Sentinel  
**Project Path:** `C:\PROJECTS\api-sentinel`  
**Current Branch:** `feature/api-key-dataset`  
**Inspection Date:** 2026-11-11  

---

## 1. Backend Architecture Inventory

| File Path | Purpose | Dependencies | Related Endpoints | Existing Tests | Status | Known Integration Risks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `backend/app/main.py` | FastAPI application initialization, CORS, lifespan database table setup, routers aggregation | `fastapi`, `sqlalchemy`, `uvicorn` | `/health`, `/api/health`, `/docs` | `test_endpoints.py`, `test_backend_readiness.py` | Active | Lifespan must handle table creations before handling traffic. |
| `backend/app/config.py` | Pydantic Settings configuration, env parsing, CORS origin validation | `pydantic_settings` | N/A | `test_backend_readiness.py` | Active | `TARGET_CREDENTIAL_ENCRYPTION_KEY` must be configured for vault operations. |
| `backend/app/database.py` | SQLite engine creation, WAL mode configuration, SessionLocal, `get_db` dependency | `sqlalchemy` | Dependency injection | `test_backend_readiness.py` | Active | Concurrent SQLite writes handled via WAL mode and busy timeout. |
| `backend/app/models.py` | SQLAlchemy ORM models (`Scan`, `Finding`, `Evidence`, `AiExplanation`, `RetestHistory`, `NotificationAlert`, `ApiTarget`, `DiscoveredEndpoint`, `TargetAuthProfile`) | `sqlalchemy` | All persistence operations | `test_target_service.py`, `test_phase4_end_to_end.py` | Active | Foreign keys and cascade rules must isolate scans from target deletions. |
| `backend/app/schemas.py` | Pydantic v2 schemas for scans, findings, evidence, retesting, reports, datasets, targets, OpenAPI previews | `pydantic` | All route request/response validations | `test_endpoints.py`, `test_target_routes.py` | Active | Field validators ensure URL safety and CRLF sanitization. |
| `backend/app/security_engine/member1_engine.py` | Real security detection engine executing BOLA, Authentication, Security Headers, and Configuration audits | `requests`, `urllib.parse` | `/api/scans`, `/api/targets/{id}/scan`, `/api/scans/{id}/retest` | `test_member1_engine.py`, `test_phase4_end_to_end.py` | Active | Engine baseline must be preserved strictly without alteration. |
| `backend/app/security_engine/integration.py` | SSRF defense engine, destination IP pinning, `validate_target_safety`, `PinnedSyncBackend`, mock adapter override | `ipaddress`, `socket`, `httpcore`, `httpx` | Pre-flight validation on all scanning and retesting | `test_ssrf_security.py`, `test_integration_readiness.py` | Active | Unpinned HTTP transports risk DNS rebinding if safety checks are bypassed. |
| `backend/app/services/scan_service.py` | Orchestrates scan lifecycle, persistence, finding generation, and SSE live broadcasting | `sqlalchemy`, `event_service` | `POST /api/scans`, `GET /api/scans`, `GET /api/scans/{id}` | `test_endpoints.py`, `test_phase4_end_to_end.py` | Active | Credential redaction must redact Authorization and custom headers. |
| `backend/app/services/ai_service.py` | NVIDIA Nemotron client with deterministic offline fallback and SQLite caching | `httpx`, `sqlalchemy` | `POST /api/findings/{id}/explain` | `test_backend_readiness.py`, `test_endpoints.py` | Active | Missing `NVIDIA_API_KEY` must fall back cleanly without breaking. |
| `backend/app/services/retest_service.py` | Verification probing engine executing retests and recording append-only `RetestHistory` | `sqlalchemy`, `member1_engine` | `POST /api/scans/{id}/retest` | `test_endpoints.py`, `test_member1_engine.py` | Active | Status transition must verify true remediation, not merely HTTP 403. |
| `backend/app/services/report_service.py` | Synthesizes executive security reports in JSON and Markdown formats | `sqlalchemy` | `GET /api/scans/{id}/report` | `test_endpoints.py` | Active | Must redact secrets and include sanitized request/response evidence. |
| `backend/app/services/event_service.py` | SSE broadcaster supporting real-time subscriptions and JSON event streaming | `asyncio` | `GET /api/events` | `test_phase5_live_events.py` | Active | Slow SSE consumers must not block scan execution thread. |
| `backend/app/services/openapi_parser.py` | Multi-version parser (OpenAPI 3.0/3.1, Swagger 2.0) with SSRF guard and 5 MB cap | `pyyaml`, `json`, `requests` | `POST /api/targets/preview-spec`, `POST /api/targets/{id}/import-spec` | `test_openapi_parser.py` | Active | Parser must enforce size limits and flag sensitive IDOR candidates. |
| `backend/app/services/target_service.py` | Target lifecycle management, spec persistence, endpoint query/selection, connectivity validation | `sqlalchemy`, `credential_vault` | `/api/targets/*` | `test_target_service.py` | Active | Target deletion must isolate and preserve historical scans. |
| `backend/app/services/credential_vault.py` | Fernet authenticated encryption, decryption, and credential masking | `cryptography.fernet` | `POST /api/targets/{id}/auth-profiles` | `test_target_service.py` | Active | Raw secrets must never be exposed via API responses or logs. |
| `backend/app/services/api_key_benchmark.py` | API key dataset evaluator, Shannon entropy calculation, regex explanations, batch runner | `re`, `math`, `json` | `/api/dataset/*` | `test_api_key_benchmark.py`, `test_dataset_testing.py` | Active | Batch runner must enforce concurrency locks to prevent race conditions. |

---

## 2. Frontend Inventory (React + Vite)

| File Path | Purpose | Dependencies | Related Backend API | Status | Known Integration Risks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `frontend/src/App.jsx` | Main application container, hash router, layout, header metadata, error boundaries | React 18, `lucide-react` | N/A | Active | All 10 views must be cleanly registered in hash routing. |
| `frontend/src/components/Sidebar.jsx` | Vertical navigation bar with cyber glow aesthetic, active pills, unread alert counters | `lucide-react` | N/A | Active | Active route styling must remain visible and accessible. |
| `frontend/src/services/apiClient.js` | Centralized typed HTTP client with timeout safeguards and error parsing | `fetch` | All `/api/*` endpoints | Active | Must handle network disconnection with descriptive error objects. |
| `frontend/src/context/ScanContext.jsx` | Global state for scans, findings, SSE event listener, active alerts, audio notifications | React Context, EventSource | `/api/scans`, `/api/events` | Active | EventSource must handle auto-reconnect and reconnect backoff. |
| `frontend/src/views/SecurityOverview.jsx` | Executive KPI overview, severity donut, scan activity chart, recent findings table | React, Lucide | `/api/scans` | Active | Charts must handle empty states gracefully. |
| `frontend/src/views/ApiOnboarding.jsx` | Target catalog, OpenAPI upload/preview/URL, 1-click Demo setup, endpoint discovery, BOLA auth | React, Lucide | `/api/targets/*` | Active | Must allow granular endpoint selection and test account saving. |
| `frontend/src/views/NewSecurityScan.jsx` | Target URL configuration, category selector, scan profile, live scan execution logs | React, Lucide | `POST /api/scans` | Active | Must enforce authorization confirmation checkbox. |
| `frontend/src/views/ScanHistory.jsx` | Chronological list of historical scans with status pills, target details, and action buttons | React, Lucide | `GET /api/scans` | Active | Pagination and status filtering must work smoothly. |
| `frontend/src/views/VulnerabilityFindings.jsx` | Findings explorer with severity badges, category filtering, evidence viewer, AI trigger | React, Lucide | `GET /api/scans/{id}/findings` | Active | Finding details must display sanitized evidence. |
| `frontend/src/views/AiSecurityAnalysis.jsx` | NVIDIA Nemotron analysis view with impact, remediation code, and explanation breakdown | React, Lucide | `POST /api/findings/{id}/explain` | Active | Must indicate whether explanation is AI-generated or fallback. |
| `frontend/src/views/ApiKeyIntelligence.jsx` | 10,000-sample dataset explorer, single sample tester, batch benchmark runner, session logs | React, Lucide | `/api/dataset/*` | Active | Must mask API key samples in all UI tables and test cards. |
| `frontend/src/views/RetestingVerification.jsx` | Retest launchpad, before/after evidence comparison, append-only history audit trail | React, Lucide | `POST /api/scans/{id}/retest` | Active | Must display immutable timestamped retest records. |
| `frontend/src/views/NotificationsView.jsx` | Live SSE notification feed with severity indicators and dismissal controls | React, Lucide | `GET /api/events` | Active | Notifications must not duplicate indefinitely. |
| `frontend/src/views/Reports.jsx` | Security compliance reports, executive summaries, Markdown & JSON export | React, Lucide | `GET /api/scans/{id}/report` | Active | Exported reports must be downloadable without secrets. |
| `frontend/src/views/SettingsView.jsx` | Node health monitor, database status, SSE connection diagnostics, build identity | React, Lucide | `/health`, `/api/health` | Active | Real-time health polling with graceful error states. |

---

## 3. Streamlit Dashboard Inventory

| File Path | Purpose | Dependencies | Related Backend API | Status | Known Integration Risks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dashboard/app.py` | Streamlit entrypoint, page routing, and theme styling | `streamlit` | N/A | Active | Must route cleanly between all views. |
| `dashboard/components/sidebar.py` | Navigation bar with brand logo, SVG icons, and routing pills | `streamlit` | N/A | Active | Query parameter routing (`?page=...`) must synchronize with state. |
| `dashboard/views/overview.py` | Executive security overview and KPI metrics | `streamlit`, `requests` | `/api/scans` | Active | Fast failure if backend offline. |
| `dashboard/views/onboarding.py` | Streamlit target catalog, spec import, endpoint explorer, BOLA auth, scan launch | `streamlit`, `requests` | `/api/targets/*` | Active | Synchronized with FastAPI as single source of truth. |
| `dashboard/views/new_scan.py` | Scan launcher with target input and authorization checkbox | `streamlit`, `requests` | `POST /api/scans` | Active | Must respect SSRF rules on local lab scanning. |
| `dashboard/views/findings.py` | Discovered vulnerability inspection with technical evidence | `streamlit`, `requests` | `/api/findings` | Active | Displays sanitized evidence. |
| `dashboard/views/api_keys.py` | Single sample tester, batch tester, and benchmark results viewer | `streamlit`, `requests` | `/api/dataset/*` | Active | In-memory evaluation and masked credentials. |
| `dashboard/views/retesting.py` | Targeted regression probe trigger and verification status | `streamlit`, `requests` | `/api/scans/{id}/retest` | Active | Evidence preservation. |
| `dashboard/views/history.py` | Historical scan audit table | `streamlit`, `requests` | `/api/scans` | Active | Read-only audit log. |
| `dashboard/views/reports.py` | Report generation and Markdown export | `streamlit`, `requests` | `/api/scans/{id}/report` | Active | Download button for audit reports. |

---

## 4. Test Suite Inventory

| Test Module Path | Test Focus | Test Count | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `backend/tests/test_endpoints.py` | Core endpoints, health checks, scan creation, findings, AI caching | 12 | PASS | In-memory SQLite with mock engine adapter |
| `backend/tests/test_integration_readiness.py` | Real/mock engine substitution, adapter isolation | 4 | PASS | Tests engine pluggability |
| `backend/tests/test_member1_engine.py` | BOLA detection, header checks, auth verification, secure mode | 9 | PASS | Tests against demo API fixtures |
| `backend/tests/test_ssrf_security.py` | Destination IP pinning, rebinding, IPv4/IPv6, cloud metadata, redirects | 18 | PASS | Strict SSRF defense validation |
| `backend/tests/test_backend_readiness.py` | SQLite WAL mode, concurrency, transaction rollback, Nemotron fallback | 14 | PASS | Database stability and AI error handling |
| `backend/tests/test_phase4_end_to_end.py` | Complete vulnerable-to-secure retest lifecycle | 1 | PASS | Full lifecycle with live demo API |
| `backend/tests/test_phase5_live_events.py` | SSE event broadcaster, subscription, lifecycle events | 4 | PASS | Async queue pub/sub testing |
| `backend/tests/test_api_key_dataset.py` | Master dataset schema, balance, leakage, isolation | 5 | PASS | 10,000-sample dataset integrity |
| `backend/tests/test_api_key_benchmark.py` | Detection formulas, metrics, masking, Shannon entropy | 5 | PASS | Benchmark evaluation formulas |
| `backend/tests/test_dataset_endpoints.py` | Dataset API routes, overview, providers, stats, pagination | 6 | PASS | FastAPI dataset endpoints |
| `backend/tests/test_dataset_testing.py` | Single sample test, batch test, concurrency lock, history | 8 | PASS | Live testing engine validation |
| `backend/tests/test_openapi_parser.py` | OpenAPI 3.0/3.1, Swagger 2.0, YAML, size cap, sensitive IDOR markers | 19 | PASS | Specification parsing engine |
| `backend/tests/test_target_service.py` | Target CRUD, spec persistence, endpoint query, Fernet vault, cascade delete | 10 | PASS | Target management service |
| `backend/tests/test_target_routes.py` | End-to-end target routes, live preview, auth masking, scan bridge | 7 | PASS | Full target HTTP lifecycle |
| **Total Automated Tests** | | **122** | **100% PASS** | **117.8s execution time** |
