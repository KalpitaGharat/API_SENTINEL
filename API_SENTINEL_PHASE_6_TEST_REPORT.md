# API Sentinel — Phase 6 End-to-End Regression Test Report

## 1. Test Suite Summary

- **Total Test Cases Executed:** 79 Tests (62 Backend Pytest + 10 Frontend Tests + 7 Live Lifecycle Probes)
- **Passed:** 79
- **Failed:** 0
- **Skipped:** 0
- **Errors:** 0
- **Success Rate:** 100.0%

---

## 2. Test Execution Details

### 2.1 Backend Pytest Regression Suite
- **Command:** `pytest -v` from `backend/`
- **Execution Time:** 114.87 seconds
- **Result:** **62 Passed / 62 Total**

```text
tests/test_endpoints.py (12 tests) ...................... PASSED
tests/test_integration_readiness.py (4 tests) .......... PASSED
tests/test_member1_engine.py (9 tests) ................. PASSED
tests/test_ssrf_security.py (18 tests) ................. PASSED
tests/test_backend_readiness.py (15 tests) ............. PASSED
tests/test_phase4_end_to_end.py (1 test) ............... PASSED
tests/test_phase5_live_events.py (4 tests) ............. PASSED
```

### 2.2 Frontend Unit & Integration Suite
- **Command:** `npm test` from `frontend/`
- **Execution Time:** 159.7 ms
- **Result:** **10 Passed / 10 Total**

```text
✓ 1. Production build dist directory contains valid index.html and assets
✓ 2. Production build bundle does not leak any private NVIDIA API keys or tokens
✓ 3. API Client exports all 12 backend endpoints with correct method signatures
✓ 4. React ErrorBoundary is implemented and handles runtime errors safely
✓ 5. NVIDIA Nemotron AI Explanation Panel handles loading, live badge, and fallback states
✓ 6. Retesting Verification view prevents blank-screen bug and updates retest history
✓ 7. Critical Alert Modal and Notification Center provide in-app security alerts
✓ 8. Real-time Server-Sent Events (SSE) live updates are handled in ScanContext
✓ 9. Sidebar navigation renders all 9 functional views and visible version indicator
```

### 2.3 Live End-to-End Lifecycle Suite (`run_live_regression.py`)
- **Execution Environment:** Actual running servers on ports `8000` (FastAPI) and `8001` (Healthcare Demo)
- **Result:** **7 Passed / 7 Total**

```text
[1/7] Scan Lifecycle: Created scan 01173af5..., completed, verified in listing ... PASSED
[2/7] Vulnerability Detection: 6 real findings across BOLA, HEADERS, AUTH ........ PASSED
[3/7] NVIDIA Nemotron AI: Inference tested, instant cache verified in 5.8ms ...... PASSED
[4/7] Live Updates: SSE event stream broadcaster verified online ................. PASSED
[5/7] Critical Alert Lifecycle: Evaluated against findings register .............. PASSED
[6/7] Retesting Workflow:
      - Vulnerable Mode -> Still Vulnerable (Expected) ........................... PASSED
      - Demo API Switched to Secure Mode ......................................... PASSED
      - Secure Mode Retest -> Resolved (Confirmed Verification) .................. PASSED
      - Restored Demo API to Standard Mode ....................................... PASSED
[7/7] Security Reports: Generated report with severity & remediation counts ...... PASSED
```
