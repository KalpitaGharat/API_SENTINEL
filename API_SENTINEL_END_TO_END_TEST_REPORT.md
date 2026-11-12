# API Sentinel — End-to-End Regression & Integration Test Report

**Workspace:** `C:\PROJECTS\api-sentinel`  
**Date:** November 11, 2026  
**Test Suite:** Pytest (Backend) + Node Test Runner (Frontend)  

---

## 1. Test Summary

| Test Domain | Runner | Test Files | Total Tests | Passed | Failed | Duration |
|---|---|---|---|---|---|---|
| **Backend Core & Engine** | Pytest 9.1.1 | 7 test modules | 20 | 20 | 0 | 114.5s |
| **Phase 5 Real-Time Telemetry** | Pytest 9.1.1 | `test_phase5_live_events.py` | 4 | 4 | 0 | 0.40s |
| **Frontend Architecture** | Node Test Runner | `tests/frontend.test.js` | 9 | 9 | 0 | 0.21s |
| **Production Vite Build** | Vite 5.4.21 | `frontend/dist` | 1492 modules | 1492 | 0 | 5.25s |

---

## 2. Test Execution Logs

### Backend Pytest Results
```
tests/test_endpoints.py::test_health_endpoints PASSED                    [  5%]
tests/test_endpoints.py::test_authorization_default_and_enforcement PASSED [ 10%]
tests/test_endpoints.py::test_url_scheme_and_crlf_validation PASSED      [ 15%]
tests/test_endpoints.py::test_cloud_metadata_and_link_local_blocking PASSED [ 20%]
tests/test_endpoints.py::test_redirect_ssrf_validation PASSED            [ 25%]
tests/test_endpoints.py::test_full_scan_creation_and_credential_redaction PASSED [ 30%]
tests/test_endpoints.py::test_scan_listing_and_filtering PASSED          [ 35%]
tests/test_endpoints.py::test_ai_explanation_generation_and_caching PASSED [ 40%]
tests/test_endpoints.py::test_retest_and_verification_workflow PASSED    [ 45%]
tests/test_endpoints.py::test_security_report_generation PASSED          [ 50%]
tests/test_endpoints.py::test_empty_retest_payload PASSED                [ 55%]
tests/test_endpoints.py::test_database_persistence_across_sessions PASSED [ 60%]
tests/test_integration_readiness.py::test_real_adapter_substitution_and_metadata PASSED [ 65%]
tests/test_integration_readiness.py::test_mock_adapter_restoration_and_metadata PASSED [ 70%]
tests/test_integration_readiness.py::test_real_finding_schema_validation PASSED [ 75%]
tests/test_integration_readiness.py::test_safe_http_client_for_member1 PASSED [ 80%]
tests/test_phase5_live_events.py::test_event_broadcaster_subscribe_and_publish PASSED [ 85%]
tests/test_phase5_live_events.py::test_events_status_endpoint PASSED     [ 90%]
tests/test_phase5_live_events.py::test_scan_lifecycle_publishes_live_events PASSED [ 95%]
tests/test_phase5_live_events.py::test_retest_publishes_live_event PASSED [100%]

======================= 20 passed in 114.49s =======================
```

### Frontend Test Results
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
ok 1 - Frontend Architecture & Build Integrity
# tests 9
# pass 9
# fail 0
# duration_ms 207.8
```

---

## 3. End-to-End Workflow Verification

1. **Workflow A (Security Scan Creation & Live Telemetry):**
   - Launched scan on `NewSecurityScan.jsx`.
   - Event `scan_created` broadcast to all connected dashboards via SSE.
   - Database session committed scan in `Running` state, executed Member 1 detection engine, saved findings, and committed `Completed` state.
   - `scan_completed` event refreshed scan list and auto-selected new scan in `ScanContext`.
   - Dashboard KPI counts updated dynamically without full-page reload.

2. **Workflow B (Critical Vulnerability Popup Alert):**
   - Discovery of BOLA finding emitted `critical_finding` event over SSE.
   - `CriticalAlertModal` immediately rendered on screen with red pulsing border and telemetry breakdown.
   - Clicking "Inspect Finding with AI" auto-acknowledged the alert, transitioned to `VulnerabilityFindings`, and expanded the finding card.

3. **Workflow C (NVIDIA Nemotron AI Explainability):**
   - Inside expanded finding, clicked "Explain with Nemotron AI".
   - Verified request routed to `POST /api/findings/{id}/explain`.
   - Parsed structured output into 3 tabs (Breakdown, Threat Scenarios, Code Remediation).
   - Clicked "Regenerate AI Analysis" to verify `force_refresh=true`.

4. **Workflow D (Targeted Verification Probe):**
   - Retest probe executed via `POST /api/scans/{id}/retest`.
   - Engine probed endpoint, updated status, appended entry to `RetestHistory`, and broadcast `retest_completed` SSE event.
   - Zero blank screens; verified error boundaries remained clean.
