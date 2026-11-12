# API Sentinel — Core Regression Test Suite Results

**Test Execution Date:** 2026-11-12T10:57:34+05:30  
**Repository:** `C:\PROJECTS\api-sentinel`  
**Branch:** `feature/api-key-dataset`  
**Preserved Baseline Git Commit:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93`  
**Test Harness Environment:** Python 3.13.7 (win32), pytest 9.1.1, SQLite 3 (WAL Mode)

---

## 1. Executive Summary

| Test Suite Category | Suite Target | Total Items | Passed | Failed | Skipped | Pass Rate |
|---|---|---|---|---|---|---|
| **Attack Evidence & Integrity** | `tests/test_attack_evidence_inspector.py` | 7 | 7 | 0 | 0 | 100% |
| **Core Backend & Scans** | `tests/test_backend.py` | 9 | 9 | 0 | 0 | 100% |
| **Backend Readiness & SQLite** | `tests/test_backend_readiness.py` | 14 | 14 | 0 | 0 | 100% |
| **Member 1 Deterministic Engine** | `tests/test_member1_engine.py` | 10 | 10 | 0 | 0 | 100% |
| **Phase 4 Full E2E Lifecycle** | `tests/test_phase4_end_to_end.py` | 1 | 1 | 0 | 0 | 100% |
| **Target Management Routes** | `tests/test_target_routes.py` | 7 | 7 | 0 | 0 | 100% |
| **Target Management Service** | `tests/test_target_service.py` | 12 | 12 | 0 | 0 | 100% |
| **OpenAPI Specification Parser** | `tests/test_openapi_parser.py` | 19 | 19 | 0 | 0 | 100% |
| **SSRF & Network Security** | `tests/test_ssrf_security.py` | 18 | 18 | 0 | 0 | 100% |
| **Total Pytest Suite** | **All Core Suites** | **97** | **97** | **0** | **0** | **100%** |
| **Standalone Forensic Verification** | `scripts/verify_bola_and_retesting.py` | 5 Steps | 5 | 0 | 0 | 100% |
| **Live Multi-Service E2E Test** | `scripts/test_attack_inspector_e2e.py` | 9 Steps | 9 | 0 | 0 | 100% |

---

## 2. Granular Pytest Results Breakdown

### 2.1 Attack Evidence & Integrity Suite (`test_attack_evidence_inspector.py`)
- `test_export_evidence_not_found`: **PASSED** (Returns 404 on invalid finding ID)
- `test_export_evidence_success_and_sha256_integrity`: **PASSED** (Validates RFC 8785 canonical export and SHA-256 digest match)
- `test_sha256_tamper_detection_tampered_response_body`: **PASSED** (Detects payload tampering in response body)
- `test_sha256_tamper_detection_tampered_request_header`: **PASSED** (Detects tampering in headers)
- `test_sha256_tamper_detection_tampered_finding_id`: **PASSED** (Detects tampering in identifier fields)
- `test_evidence_export_secrets_sanitized`: **PASSED** (Confirms passwords and tokens are masked before export)
- `test_ai_service_includes_remediation_disclaimer`: **PASSED** (Verifies mandatory safety disclaimer is appended)

### 2.2 Core Backend & Scans Suite (`test_backend.py`)
- `test_health_endpoints`: **PASSED** (`/health` and `/api/health` connectivity verified)
- `test_scan_requires_authorization`: **PASSED** (Rejects scans without explicit user authorization)
- `test_scan_validates_url_format`: **PASSED** (Rejects invalid URLs with HTTP 422)
- `test_cloud_metadata_blocking`: **PASSED** (Blocks `169.254.169.254` via `TargetSafetyError`)
- `test_create_and_run_scan`: **PASSED** (Full scan execution with redacted config and findings retrieval)
- `test_scan_pagination_and_filter`: **PASSED** (Validates `limit`, `offset`, and `status` query parameters)
- `test_ai_explanation_and_caching`: **PASSED** (Deterministic SQLite caching of generated explanations)
- `test_retest_and_verification_workflow`: **PASSED** (Unremediated target stays `Still Vulnerable`)
- `test_generate_report`: **PASSED** (Generates executive summary and severity breakdown)

### 2.3 Backend Readiness & Persistence Suite (`test_backend_readiness.py`)
- `test_sqlite_pragmas_and_wal_mode`: **PASSED** (Verifies WAL mode and foreign key enforcement)
- `test_database_persistence_across_engine_restart`: **PASSED** (Data preserved across engine teardown)
- `test_concurrent_reads_and_writes_with_wal`: **PASSED** (Concurrent readers do not block writers)
- `test_scan_service_transaction_rollback_on_engine_failure`: **PASSED** (Rolls back failed scan transactions)
- `test_retest_service_transaction_rollback_on_commit_error`: **PASSED** (Rolls back retest on commit error)
- `test_retest_history_append_only_immutability`: **PASSED** (Immutable audit ledger prevents record deletion)
- `test_get_finding_retest_history_endpoint`: **PASSED** (REST endpoint retrieves chronological retest events)
- `test_ai_explanation_output_schema_validation`: **PASSED** (Pydantic validates explanation, impact, remediation)
- `test_ai_service_markdown_fenced_json_parsing`: **PASSED** (Extracts valid JSON from markdown code blocks)
- `test_ai_service_malformed_json_triggers_rule_fallback`: **PASSED** (Gracefully falls back to expert rules)
- `test_ai_service_nvidia_api_errors_trigger_fallback`: **PASSED** (Network/API errors fall back without crashing)
- `test_ai_service_missing_api_key_uses_rule_fallback`: **PASSED** (Missing API keys use rule fallback instantly)
- `test_explain_cache_and_force_refresh`: **PASSED** (Cache hit vs force refresh verified)
- `test_dockerfile_and_compose_static_configuration`: **PASSED** (Dockerfile and docker-compose syntactically valid)

### 2.4 Member 1 Deterministic Engine Suite (`test_member1_engine.py`)
- `test_bola_detection_on_vulnerable_demo_api`: **PASSED** (Detects BOLA on vulnerable Healthcare Demo API)
- `test_bola_prevention_on_secure_mode`: **PASSED** (Zero findings on remediated Demo API)
- `test_generic_200_does_not_trigger_false_positive_bola`: **PASSED** (Generic 200 OK without victim payload ignored)
- `test_missing_security_headers_detection`: **PASSED** (Flags missing CSP, HSTS, X-Content-Type-Options)
- `test_security_headers_remediated_mode`: **PASSED** (Confirms headers pass when properly configured)
- `test_authentication_checks_on_protected_endpoints`: **PASSED** (Flags endpoints missing auth enforcement)
- `test_retesting_lifecycle_vulnerable_then_resolved`: **PASSED** (Status transitions from `Open` to `Resolved`)
- `test_retest_failure_on_unreachable_target`: **PASSED** (Network failure transitions to `Failed` / `Still Vulnerable`)
- `test_bola_retest_returns_needs_review_when_owner_access_is_broken`: **PASSED** (Flags `Needs Review` if owner is blocked)
- `test_backend_discovers_member1_engine_by_default`: **PASSED** (Auto-loads Member 1 engine)

### 2.5 Phase 4 Full E2E Lifecycle Suite (`test_phase4_end_to_end.py`)
- `test_phase4_complete_vulnerable_and_secure_retest_lifecycle`: **PASSED** (Complete vulnerable scan -> evidence -> AI explanation -> secure toggle -> dual-probe retest -> resolved)

### 2.6 Target Management & OpenAPI Suites (`test_target_routes.py`, `test_target_service.py`, `test_openapi_parser.py`)
- **Target Routes:** 7/7 PASSED (Registration, listing, OpenAPI preview, endpoint toggle, Fernet credential encryption, scan bridge)
- **Target Service:** 12/12 PASSED (Validation, search, filtering, cascade deletion, historical scan preservation)
- **OpenAPI Parser:** 19/19 PASSED (OpenAPI 2.0, 3.0, 3.1, YAML/JSON parsing, 5 MB limits, 1,000 endpoint boundary, circular reference protection, SSRF rejection)

### 2.7 SSRF & Network Security Suite (`test_ssrf_security.py`)
- 18/18 PASSED (Unspecified addresses, decimal/hex representations, AWS/GCP/Azure metadata blocking, private network restriction, socket IP pinning, DNS rebinding prevention, TLS SNI preservation, HTTPS-to-HTTP downgrade rejection, redirect loop detection, max hops enforcement, cross-origin header stripping)

---

## 3. Standalone Verification Scripts

### 3.1 Forensic BOLA & Retesting Verification (`scripts/verify_bola_and_retesting.py`)
```
[HEADER] === FORENSIC VERIFICATION: BOLA & RETESTING INTEGRITY ===
[INFO] 1. Authenticating Alice and Bob...
[SUCCESS] Alice token: sentinel_t... | Bob token: sentinel_t...
[INFO] 2. Setting Demo API to VULNERABLE MODE...
[SUCCESS] Alice accessing Alice's record (101): HTTP 200 OK (Legitimate)
[WARN] Alice accessing Bob's record (102): HTTP 200 OK -> LEAKED Bob's diagnosis
[INFO] 3. Setting Demo API to REMEDIATED MODE...
[SUCCESS] Alice accessing Alice's record (101): HTTP 200 OK (Owner access preserved)
[SUCCESS] Alice accessing Bob's record (102): HTTP 403 FORBIDDEN (Access blocked)
[INFO] 4. Verifying False-Positive Prevention logic...
[SUCCESS] Generic HTTP 200 OK without victim payload correctly ignored (NO false positive)
[SUCCESS] Actual victim data payload correctly flags BOLA (True positive confirmed)
[INFO] 5. Testing Dual-Probe Retest Engine behavior on broken owner access...
[SUCCESS] All forensic checks verified successfully!
```

### 3.2 Live Multi-Service E2E Acceptance Test (`scripts/test_attack_inspector_e2e.py`)
```
[HEADER] Starting Live E2E Acceptance Test for Attack & Evidence Inspector...
[INFO] Checking Healthcare Demo API on port 8001...
[SUCCESS] Healthcare Demo API is alive.
[INFO] Setting Demo API to VULNERABLE mode...
[SUCCESS] Demo API mode confirmed: vulnerable=True
[INFO] Submitting scan request to http://127.0.0.1:8000/api/scans...
[SUCCESS] Scan launched successfully with ID: 4c3c6680-d834-4b66-bbe8-c5775e08f8f4
[INFO] Polling scan status until COMPLETED...
[SUCCESS] Scan completed: found 6 findings.
[INFO] Fetching scan findings...
[SUCCESS] Detected BOLA finding ID: ab48ae3c-9954-4d25-87fe-777755c216c1
[INFO] Verifying forensic evidence telemetry structure...
[INFO]   • Latency telemetry: 14.87 ms
[INFO]   • Copyable cURL: curl -X GET "http://127.0.0.1:8001/api/patients/102" ...
[INFO]   • Masked auth header: Bearer sent...__101
[INFO]   • Attack timeline steps: 9
[INFO] Testing GET http://127.0.0.1:8000/api/findings/ab48ae3c-9954-4d25-87fe-777755c216c1/export-evidence...
[SUCCESS] SHA-256 Cryptographic Digest verified: 55fb8ed340f6620c57f36e277816fe9a72339898e9a1cff7de2a2a4106a9576c
[INFO] Switching Demo API to REMEDIATED mode (DEMO_VULNERABLE_MODE=False)...
[SUCCESS] Demo API remediation activated.
[INFO] Triggering verification probe: POST http://127.0.0.1:8000/api/scans/.../retest...
[SUCCESS] Retest result received: previous=Open -> new=Resolved
[INFO] Observed probe status code: HTTP 403 (Expected 403 Forbidden)
[INFO] Checking audit history: GET http://127.0.0.1:8000/api/findings/.../history...
[SUCCESS] Audit record confirmed: id=d8942f43-78cb-4c36-81e8-034c3fd03e16, verified=True
[SUCCESS] ALL ATTACK DEMONSTRATION & EVIDENCE INSPECTOR E2E CHECKS PASSED!
```

---

## 4. Conclusion & Readiness Verdict

The backend core test suite exhibits **zero regressions, zero broken imports, and 100% test pass rate across 97 unit/integration test specifications and 2 full end-to-end multi-service test harnesses**. 

All baseline and core security guarantees remain strictly preserved.
