# API Sentinel — Complete Backend Integration Audit

**Date:** November 11, 2026  
**Auditor / Engineer:** Senior Backend Integration Engineer & DevSecOps Auditor  
**Master Repository:** `C:\PROJECTS\api-sentinel`  
**Frontend Path:** `C:\PROJECTS\api-sentinel\frontend`  
**API Client:** [`frontend/src/services/apiClient.js`](file:///C:/PROJECTS/api-sentinel/frontend/src/services/apiClient.js)

---

## 1. Executive Summary

This integration audit verifies the wiring between the React 18 frontend and the FastAPI backend. Every backend endpoint defined in the control plane was mapped against its corresponding API client method, UI component, request payload structure, response schema, and error handling mechanisms.

**Audit Verdict:** 12 out of 12 backend endpoints are fully integrated and verified with zero mock bypasses in the active path.

---

## 2. Comprehensive Endpoint Integration Matrix

| # | HTTP Method | Backend Route | API Client Method | Connected React Component | Request Schema / Params | Response Schema / Validated Fields | Integration Status |
|:---:|:---:|---|---|---|---|---|:---:|
| 1 | `GET` | `/health` | `apiClient.getHealth()` | `ScanContext.jsx` | None | `HealthResponse`: `status`, `timestamp`, `environment`, `database`, `version` | **VERIFIED** |
| 2 | `GET` | `/api/health` | `apiClient.getApiHealth()` | `ScanContext.jsx` | None | `HealthResponse`: `status`, `timestamp`, `environment`, `database` | **VERIFIED** |
| 3 | `POST` | `/api/scans` | `apiClient.createScan(data)` | `NewSecurityScan.jsx` | `ScanCreateRequest`: `target_url`, `scan_profile`, `user_authorized`, `categories` | `ScanResponse`: `id`, `target_url`, `status`, `total_findings`, `created_at` | **VERIFIED** |
| 4 | `GET` | `/api/scans` | `apiClient.getScans(params)` | `ScanHistory.jsx`, `ScanContext.jsx` | Query: `skip=0`, `limit=20`, `status_filter=...` | `ScanListResponse`: `total`, `items: List[ScanResponse]` | **VERIFIED** |
| 5 | `GET` | `/api/scans/{id}` | `apiClient.getScan(id)` | `LastScanSummary.jsx`, `ScanContext.jsx` | Path: `scan_id: str` | `ScanResponse`: `id`, `target_url`, `status`, `total_findings`, `completed_at` | **VERIFIED** |
| 6 | `GET` | `/api/scans/{id}/findings` | `apiClient.getScanFindings(id, filters)` | `VulnerabilityFindings.jsx`, `RecentFindingsTable.jsx` | Path: `scan_id: str`<br>Query: `severity`, `category`, `status` | `List[FindingResponse]`: `id`, `vulnerability`, `category`, `endpoint`, `severity`, `evidence`, `ai_explanation` | **VERIFIED** |
| 7 | `GET` | `/api/findings/{id}` | `apiClient.getFinding(id)` | `AiExplanationPanel.jsx` | Path: `finding_id: str` | `FindingResponse`: full finding with nested `EvidenceResponse` & `AIExplanationResponse` | **VERIFIED** |
| 8 | `POST` | `/api/findings/{id}/explain` | `apiClient.explainFinding(id, false)` | `AiExplanationPanel.jsx` | Path: `finding_id: str`<br>Query: `force_refresh=false` | `AIExplanationResponse`: `id`, `explanation`, `impact`, `remediation`, `model_name`, `created_at` | **VERIFIED** |
| 9 | `POST` | `/api/findings/{id}/explain?force_refresh=true` | `apiClient.explainFinding(id, true)` | `AiExplanationPanel.jsx` | Path: `finding_id: str`<br>Query: `force_refresh=true` | `AIExplanationResponse`: fresh explanation bypassing SQLite cache | **VERIFIED** |
| 10 | `GET` | `/api/findings/{id}/history` | `apiClient.getFindingHistory(id)` | `RetestingVerification.jsx` | Path: `finding_id: str` | `RetestHistoryListResponse`: `finding_id`, `total_retests`, `history: List[RetestHistoryItemResponse]` | **VERIFIED** |
| 11 | `POST` | `/api/scans/{id}/retest` | `apiClient.retestScan(id, findingId)` | `RetestingVerification.jsx` | Path: `scan_id: str`<br>Body: `{ "finding_id": "..." }` | `RetestResponse`: `scan_id`, `retested_at`, `results: List[RetestResultItem]` | **VERIFIED** |
| 12 | `GET` | `/api/scans/{id}/report` | `apiClient.getScanReport(id)` | `Reports.jsx` | Path: `scan_id: str` | `ReportResponse`: `scan`, `summary`, `findings`, `generated_at` | **VERIFIED** |

---

## 3. Detailed Data Flow Analysis

### 3.1 Scan Creation Flow (`POST /api/scans`)
1. User enters `http://127.0.0.1:8001`, selects profile, confirms authorization, and clicks **"Launch Automated Security Scan"**.
2. `NewSecurityScan.jsx` validates input syntax and invokes `apiClient.createScan(...)`.
3. Backend performs pre-flight SSRF check (`validate_target_safety`), sets up `EngineAdapter`, and dispatches security checks.
4. Scan record and findings are committed to SQLite with WAL mode.
5. Frontend receives `ScanResponse`, updates `ScanContext.scans`, selects the new `id`, and renders finding summary with one-click navigation.

### 3.2 Finding Inspection & Telemetry Flow (`GET /api/scans/{id}/findings`)
1. `VulnerabilityFindings.jsx` queries all findings for the active scan.
2. Findings render with real severity pills (`Critical`, `High`, `Medium`, `Low`) and status badges (`Open`, `Resolved`).
3. Expanding a finding unpacks technical HTTP evidence:
   - Principal role (`evidence.test_user`)
   - Resource targeted (`evidence.requested_resource`)
   - Observed HTTP code vs Expected secure HTTP code
   - Redacted request and response payload snippets.

### 3.3 AI Explanation & Caching Flow (`POST /api/findings/{id}/explain`)
1. `AiExplanationPanel.jsx` checks if `finding.ai_explanation` already exists:
   - If present: renders cached explanation immediately with the badge `"Cached in SQLite"`.
   - If absent: renders **"Explain with Nemotron AI"** action button.
2. On click: triggers animated loading skeleton and dispatches `POST /api/findings/{id}/explain`.
3. Backend calls `AIService`:
   - If online and key valid: invokes NVIDIA Nemotron-3.5-lightning (3072 token budget), validates JSON against `AIExplanationOutput`, and persists to SQLite.
   - If offline or key absent: invokes deterministic rule-based engine, persists to SQLite.
4. Frontend renders three structured tabs: *Vulnerability Breakdown*, *Attack Scenarios & Impact*, and *Step-by-Step Remediation*.
5. Badge displays `NVIDIA Nemotron (Live AI)` or `Deterministic Rule Engine`.
6. Clicking **"Regenerate AI Analysis"** passes `force_refresh=true` to regenerate analysis while keeping current explanation visible.

### 3.4 Retest & Verification Flow (`POST /api/scans/{id}/retest`)
1. In `RetestingVerification.jsx`, user selects an open finding (e.g. BOLA on `/api/patients/{id}`) and clicks **"Execute Targeted Verification Probe"**.
2. UI sets `isProbing=true`, clears previous results, and streams probe dispatch logs to the terminal console.
3. Backend invokes `RetestService.retest_scan(scan_id, specific_finding_id)`:
   - Member 1 engine connects directly to the pinned destination IP.
   - Re-authenticates test principal `patient_a` and probes `GET /api/patients/102`.
   - Evaluates response code and payload.
   - Updates `Finding.status` in database.
   - Appends an audit entry into `RetestHistory`.
4. Frontend receives `RetestResponse`, checks `results[0].verified` and `results[0].new_status`:
   - If `Resolved` (HTTP 403 Forbidden observed) $\rightarrow$ green certified banner.
   - If `Still Vulnerable` (HTTP 200 observed) $\rightarrow$ red alert banner.
5. Immediately calls `apiClient.getFindingHistory(finding_id)` to update the chronological audit history table.

### 3.5 Security Report Flow (`GET /api/scans/{id}/report`)
1. `Reports.jsx` requests report data for the selected scan.
2. Backend aggregates scan summary, category distributions, severity breakdown, and finding list.
3. Frontend renders real OWASP API Top 10 compliance metrics, calculated security health score ($10-100$), and provides working JSON file export.

---

## 4. Integration Verification Summary

All 12 endpoints communicate seamlessly with real backend data, proper error handling, response validation, and zero reliance on mock simulations.
