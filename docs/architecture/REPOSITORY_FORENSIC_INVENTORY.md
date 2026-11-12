# API Sentinel — Repository Forensic Inventory

**Inventory Version:** 1.0.0 Production Baseline  
**Branch:** `feature/api-key-dataset`  
**Preserved Baseline Git Commit:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93`  
**Audit Date:** 2026-11-12

---

## 1. Directory Tree & Classification Overview

| Directory / Subsystem | Primary Function | Architecture Tier |
|---|---|---|
| `backend/app/` | Core FastAPI application & business logic | Core Backend |
| `backend/app/security_engine/` | Member 1 deterministic testing engine & transport | Core Scanner |
| `backend/app/routes/` | REST API routes & endpoints | Core API / Deferred Routes |
| `backend/app/services/` | Business logic services | Core Services / Deferred Services |
| `backend/tests/` | Pytest regression & integration test suites | Test Engineering |
| `frontend/src/` | React 18 single-page application | Preserved Frontend |
| `demo_api/` | Controlled vulnerable/remediated Healthcare Demo API | Controlled Testbed |
| `dashboard/` | Streamlit secondary demonstration dashboard | Demonstration / Secondary UI |
| `scripts/` | Forensic verification & automated demonstration scripts | Verification Tooling |
| `docs/` | System architecture, audit logs, and guides | Documentation Suite |

---

## 2. Component Forensic Catalog

### 2.1 Core Backend (`backend/app/`)

| File Path | Description | Status |
|---|---|---|
| `backend/app/main.py` | FastAPI application initialization, lifespan handlers, CORS middleware, router registration, and static frontend dist mounting. | Core Active |
| `backend/app/config.py` | Pydantic BaseSettings loading environment configurations, secret masking, lab mode, and AI timeouts. | Core Active |
| `backend/app/database.py` | SQLAlchemy database engine, session factory, connection pragmas (`WAL`, `foreign_keys=ON`, `busy_timeout=5000`). | Core Active |
| `backend/app/models.py` | SQLAlchemy ORM models: `Scan`, `Finding`, `AIExplanation`, `RetestHistory`, `Target`, `TargetEndpoint`, `AuthProfile`. | Core Active |
| `backend/app/schemas.py` | Pydantic request/response validation schemas, including `ScanResponse`, `FindingResponse`, `TargetCreateRequest`, and evidence structures. | Core Active |

---

### 2.2 Core Scanner Engine (`backend/app/security_engine/`)

| File Path | Description | Status |
|---|---|---|
| `backend/app/security_engine/member1_engine.py` | The deterministic security testing engine: `_check_bola` (BOLA/IDOR), `_check_authentication`, `_check_headers_and_config`, `_retest_bola`, and `PinnedHTTPTransport` SSRF controls. | Core Active |
| `backend/app/security_engine/integration.py` | Security engine adapter interface connecting the FastAPI scan service to Member 1 engine. | Core Active |
| `backend/app/services/scan_service.py` | Coordinates scan lifecycles, database transactions, SSE event dispatches, and finding persistence. | Core Active |
| `backend/app/services/retest_service.py` | Executes single-finding or batch retesting, dual-probe verification, status transitions, and audit logging. | Core Active |

---

### 2.3 Target Management & Onboarding (`backend/app/routes/` & `backend/app/services/`)

| File Path | Description | Status |
|---|---|---|
| `backend/app/routes/targets.py` | REST endpoints for target registration, listing, deletion, OpenAPI spec import, endpoint toggling, and auth profiles. | Core Active |
| `backend/app/services/target_service.py` | Target lifecycle management, endpoint filtering, cascade deletion, and historical scan preservation. | Core Active |
| `backend/app/services/openapi_parser.py` | Robust parser for OpenAPI 2.0/3.0/3.1 specs (JSON/YAML) with size limits (5 MB max), cycle detection, and SSRF prevention. | Core Active |
| `backend/app/services/credential_vault.py` | Fernet symmetric encryption and decryption for target credentials and authorization tokens. | Core Active |

---

### 2.4 Evidence Inspector & Finding Management

| File Path | Description | Status |
|---|---|---|
| `backend/app/routes/findings.py` | Endpoints for listing findings, viewing details, requesting AI explanations, exporting RFC 8785 canonical evidence with SHA-256 digests, and retrieving retest history. | Core Active |
| `backend/app/services/ai_service.py` | NVIDIA Nemotron integration with strict schema validation, timeout protection, secret masking, and deterministic rule-based fallback. | Core Active |
| `backend/app/routes/reports.py` | Aggregated scan security report generation with severity breakdown and compliance metrics. | Core Active |
| `backend/app/routes/events.py` | SSE real-time scan event streaming endpoint. | Core Active |
| `backend/app/services/event_service.py` | In-memory pub/sub broker for SSE events. | Core Active |

---

### 2.5 Controlled Demo Environment (`demo_api/`)

| File Path | Description | Status |
|---|---|---|
| `demo_api/main.py` | FastAPI application exposing synthetic Healthcare endpoints (`/api/patients/{id}`, `/api/prescriptions/{id}`, `/api/appointments/{id}`). | Testbed Active |
| `demo_api/config.py` | Configuration toggles for `DEMO_VULNERABLE_MODE` and `ENABLE_SECURITY_HEADERS`. | Testbed Active |
| `demo_api/models.py` | Synthetic in-memory patient database for Alice (ID 101) and Bob (ID 102). | Testbed Active |

---

### 2.6 Deferred & Secondary Features

| File Path | Description | Status |
|---|---|---|
| `backend/app/routes/dataset.py` | Endpoints for API key intelligence datasets, leak pattern analysis, and validation statistics. | Deferred / Optional |
| `backend/app/services/api_key_benchmark.py` | Benchmarking engine comparing regex patterns against LLM models for API key detection accuracy. | Deferred / Optional |
| `dashboard/views/api_keys.py` | Streamlit UI view for exploring API key intelligence and benchmark runs. | Deferred / Optional |
| `dashboard/app.py` | Secondary Streamlit dashboard for alternative presentations. | Secondary UI |

---

### 2.7 Frontend Application (`frontend/`) — *Preserved Completely*

| File Path | Description | Status |
|---|---|---|
| `frontend/src/App.jsx` | Main application shell with client-side routing, navigation bar, and toast alerts. | Preserved |
| `frontend/src/components/AttackEvidenceInspector.jsx` | Forensic evidence modal displaying HTTP telemetry, masked secrets, copyable cURL, and attack diagrams. | Preserved |
| `frontend/src/views/ApiOnboarding.jsx` | Target management and OpenAPI specification importer UI. | Preserved |
| `frontend/src/views/VulnerabilityFindings.jsx` | Finding explorer with severity badges, AI explanation modals, and retest triggers. | Preserved |
| `frontend/src/views/RetestingVerification.jsx` | Remediation verification dashboard tracking `Resolved` vs. `Still Vulnerable` status. | Preserved |
| `frontend/src/views/Reports.jsx` | Printable security audit summary report view. | Preserved |

---

### 2.8 Verification Tooling & Test Suites

| Directory / Script | Coverage Scope | Status |
|---|---|---|
| `backend/tests/test_attack_evidence_inspector.py` | 7 tests: Evidence export, SHA-256 tamper-detection, credential sanitization, AI remediation disclaimer. | Active Verified |
| `backend/tests/test_backend.py` | 9 tests: Health, target authorization, metadata blocking, scan creation, pagination, AI explain, retest workflow, report generation. | Active Verified |
| `backend/tests/test_backend_readiness.py` | 14 tests: SQLite WAL mode, database persistence, transaction rollbacks, retest history immutability, AI fallback. | Active Verified |
| `backend/tests/test_member1_engine.py` | 10 tests: BOLA detection, false-positive prevention, security headers, authentication checks, retest lifecycle. | Active Verified |
| `backend/tests/test_phase4_end_to_end.py` | 1 test: Full end-to-end lifecycle on live demo API. | Active Verified |
| `backend/tests/test_target_routes.py` | 7 tests: Target CRUD, spec preview/import, endpoint toggles, credential encryption, scan bridge. | Active Verified |
| `backend/tests/test_target_service.py` | 12 tests: Target validation, filtering, spec persistence, cascade deletion, scan preservation. | Active Verified |
| `backend/tests/test_openapi_parser.py` | 19 tests: Spec versions 2.0/3.0/3.1, JSON/YAML, size limits, cycle detection, SSRF protection. | Active Verified |
| `backend/tests/test_ssrf_security.py` | 18 tests: IPv4/IPv6 private ranges, decimal/hex IP representations, cloud metadata, TLS SNI, redirect loops. | Active Verified |
| `scripts/verify_bola_and_retesting.py` | Standalone script verifying BOLA exploitability and dual-probe retesting logic. | Active Verified |
| `scripts/test_attack_inspector_e2e.py` | Live E2E script launching scan on port 8000 against demo API on port 8001, verifying SHA-256 export and retest. | Active Verified |
