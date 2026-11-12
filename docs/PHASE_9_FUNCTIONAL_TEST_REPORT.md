# API SENTINEL — PHASE 9 FUNCTIONAL TEST REPORT

**Project:** API Sentinel  
**Target:** Full Platform End-to-End Functionality  
**Audit Date:** November 11, 2026  
**Auditor:** Senior Application Security & Quality Assurance Engineer  
**Branch:** `feature/api-key-dataset`  
**Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. SCOPE OF FUNCTIONAL VERIFICATION

This functional test report documents exhaustive manual and automated testing of all functional subsystems across backend, frontend, and dashboard interfaces:

1. **Target Onboarding & OpenAPI Discovery**
2. **Endpoint Filtering & Granular Selection**
3. **Multi-Account Credential Management**
4. **Member 1 Scan Execution & BOLA/IDOR Detection**
5. **Real-Time Scan Progress & SSE Event Stream**
6. **NVIDIA Nemotron AI Explanations & Rule-Based Fallback**
7. **Retesting Verification Workflow & Status Transitions**
8. **Security Reports & Append-Only Audit History**
9. **API Key Dataset Intelligence & Benchmark Runner**
10. **Dual UI Validation (React Vite Frontend + Streamlit Multi-Page App)**

---

## 2. DETAILED TEST RESULTS BY FUNCTIONAL MODULE

### 2.1 Target Onboarding & OpenAPI Parsing
- **Endpoint:** `POST /api/targets` and `POST /api/targets/preview`
- **Supported Formats:** OpenAPI 3.0, OpenAPI 3.1, and Swagger 2.0 (both JSON and YAML formats).
- **Safety Limits:** 5 MB payload limit, 1,000 endpoint upper bound limit, SSRF checks on remote spec fetching.
- **Parameters & Body Schemas:** Extracts path parameters, query parameters, headers, and request body JSON schemas.
- **Sensitive Operations Detection:** Auto-flags endpoints with sensitive keywords (`/patient`, `/records`, `/users`, `/payments`) and state-changing HTTP verbs (`POST`, `PUT`, `PATCH`, `DELETE`).
- **Status:** **PASS** (Verified across 17 automated tests in `test_openapi_parser.py` and 7 tests in `test_target_routes.py`).

### 2.2 Granular Endpoint Selection & Target Management
- **Endpoint:** `POST /api/targets/{id}/endpoints/select`
- **Capabilities Verified:**
  - Granular toggle via list-of-dicts `[{"endpoint_id": id, "is_selected": true/false}]`.
  - Bulk select/deselect via `deselect_all=True`.
  - Filter selection via `sensitive_only=True` to automatically target high-risk routes.
  - Cascading deletion: deleting a registered target cleans up endpoints and auth profiles while preserving historical scans and findings.
- **Status:** **PASS** (Verified in `test_target_service.py` and `test_target_routes.py`).

### 2.3 Credential Vault & Target Authentication
- **Endpoint:** `POST /api/targets/{id}/auth-profiles`
- **Capabilities Verified:**
  - Dual test accounts: Owner/Primary (`role="owner"`) and Attacker/Foreign (`role="attacker"`).
  - Normalization of frontend payloads (`auth_type` -> `authentication_type`, `token_or_secret` -> `credential_value`).
  - Fernet AES-128 authenticated encryption of tokens, API keys, and HTTP basic auth credentials.
  - Masking verification: all API responses mask credentials (e.g., `eyJh...9xQ`).
- **Status:** **PASS** (Verified in `test_auth_profile_encryption_and_masking`).

### 2.4 Member 1 Security Scan Execution
- **Endpoint:** `POST /api/scans` (with `target_id` or direct URL)
- **Engine Selection:** Automatically discovers and defaults to Member 1 Security Engine.
- **Vulnerabilities Tested:**
  - BOLA / IDOR (Broken Object Level Authorization): Detects when User B can view User A's patient medical records.
  - Broken Authentication: Flags missing tokens or accepted expired/invalid headers.
  - Security Headers: Detects missing `X-Content-Type-Options`, `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`.
- **Status:** **PASS** (Verified against vulnerable Healthcare Demo API).

### 2.5 Real-Time Scan Progress & SSE Streaming
- **Endpoint:** `GET /api/scans/{id}/events` (Server-Sent Events)
- **Event Flow:** Emits structured progress events (`stage_started`, `target_resolved`, `running_checks`, `finding_discovered`, `scan_completed`).
- **Frontend Integration:** React frontend dynamically updates the progress ring, timeline, and discovery feed in real time.
- **Status:** **PASS** (Verified in `test_phase5_live_events.py`).

### 2.6 Explainable AI (NVIDIA Nemotron + Rule-Based Fallback)
- **Endpoint:** `POST /api/findings/{id}/explain`
- **Integration:** OpenAI-compatible client connecting to `https://integrate.api.nvidia.com/v1/chat/completions`.
- **Output Validation:** Pydantic validation guarantees structured sections: plain-language explanation, attack impact, and concrete remediation steps.
- **Fallback Verification:** If the NVIDIA API key is omitted, invalid, or times out, the system seamlessly serves comprehensive rule-based explanations without failing the user experience.
- **Caching:** Responses are cached in SQLite `ai_explanations` table; subsequent requests are served instantaneously without redundant API calls.
- **Status:** **PASS** (Verified in `test_ai_explanation_generation_and_caching` and `test_explain_cache_and_force_refresh`).

### 2.7 Verification Retesting Workflow
- **Endpoint:** `POST /api/scans/{id}/retest`
- **Dual-Check Verification:**
  - Probes User A (Owner) first to ensure resource availability.
  - Probes User B (Attacker) second to test authorization enforcement.
  - If target endpoint is down or owner access fails -> Marks `Needs Review` (not `Resolved`).
  - If owner access succeeds and attacker receives HTTP 403 Forbidden -> Marks `Resolved`.
  - If attacker still accesses data -> Marks `Still Vulnerable`.
- **Status:** **PASS** (Verified in `test_member1_engine.py` and `test_phase4_end_to_end.py`).

### 2.8 Append-Only Audit History & Security Reports
- **Endpoints:** `GET /api/reports/{scan_id}` and `GET /api/findings/{id}/retest-history`
- **Audit Preservation:** Every retest invocation appends a permanent record to `retest_history` with timestamp, tester, old status, new status, and technical HTTP evidence.
- **Report Synthesis:** Generates full executive summaries, severity breakdown, CVSS estimates, and remediation action items.
- **Status:** **PASS** (Verified in `test_retest_history_append_only_immutability`).

### 2.9 Dataset Intelligence & Benchmark Runner
- **Endpoints:** `GET /api/dataset/overview`, `GET /api/dataset/benchmark`, `POST /api/dataset/test/single`, `POST /api/dataset/test/batch`
- **Capabilities:**
  - Indexes 10,000 samples across 25 providers and 3 source categories.
  - Single-sample live detection testing with Shannon entropy calculation and structural pattern breakdown.
  - Batch evaluation against custom splits with live metrics calculation (Precision, Recall, F1, Accuracy, Specificity).
  - Concurrency lock protection to guarantee resource stability.
- **Status:** **PASS** (Verified across 18 dataset and benchmark tests).

### 2.10 User Interface Functional Verification
1. **React Single Page Application (`http://localhost:5173`)**:
   - Navigation across Dashboard, API Onboarding, Scans, Live Scan Progress, Findings & AI Remediation, Retest History, API Key Intelligence, and Reports.
   - Production build compiles cleanly with zero syntax or bundling errors (`npm run build`).
2. **Streamlit Multi-Page Dashboard (`http://localhost:8501`)**:
   - Python 3.13 bytecode compilation succeeds (`python -m py_compile dashboard/app.py dashboard/views/onboarding.py`).
   - All interactive views render with responsive metrics, graphs, and action triggers.

---

## 3. FUNCTIONAL TEST MATRIX SUMMARY

| Module / Workflow | Execution Mode | Expected Result | Observed Result | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| OpenAPI Spec Preview | API & UI | Parse 3 endpoints, show methods & parameters | Exact 3 endpoints displayed with methods | **PASS** |
| Target Registration | SQLite & Vault | Store target, encrypt credentials | Encrypted in DB, masked in UI | **PASS** |
| Endpoint Selection | API & UI | Filter sensitive routes, granular toggle | Correctly toggles without clearing others | **PASS** |
| BOLA Vulnerability Scan | Demo API (Port 8001) | Detect patient record data leakage | HTTP 200 + Foreign record detected | **PASS** |
| AI Finding Explanation | Nemotron / Fallback | Produce Explainable remediation | Complete explanation + cached in SQLite | **PASS** |
| Retest Vulnerable Mode | Demo API | Attacker still receives 200 OK | Retest marks "Still Vulnerable" | **PASS** |
| Retest Remediated Mode | Demo API Secure | Attacker receives 403 Forbidden | Retest marks "Resolved" | **PASS** |
| Broken Owner Retest | Mock 500 / Down | Owner access fails | Retest marks "Needs Review" | **PASS** |
| Executive Report Gen | Reporting API | Summary metrics + findings list | Detailed PDF/Markdown summary rendered | **PASS** |
| Dataset Batch Test | Dataset Engine | Calculate confusion matrix & metrics | Full metrics generated without secret leaks | **PASS** |

---

## 4. FUNCTIONAL READINESS VERDICT

All functional requirements for API Sentinel are fully validated, verified against live endpoints, and operating in accordance with specification.
