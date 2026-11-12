# API SENTINEL — FRONTEND MASTER FORENSIC AUDIT REPORT
**Document Reference:** `docs/frontend/FRONTEND_MASTER_FORENSIC_AUDIT.md`  
**Classification:** Enterprise Cyber-Defense Audit & Technical Assessment  
**Audited Target:** `C:\PROJECTS\api-sentinel\frontend`  
**Branch:** `feature/api-key-dataset`  
**Runtime Engine:** React 18.3.1 + Vite 5.2.11 + FastAPI 1.0.0 + NVIDIA Nemotron 3.5  
**Auditor:** Principal Frontend Architect & Application Security Auditor  
**Date of Audit:** November 12, 2026  

---

## EXECUTIVE SUMMARY

A forensic examination of the API Sentinel frontend codebase (`frontend/src/`) was conducted across 15 major end-to-end workflows, 14 view workspaces, 16 UI components, centralized context providers, SSE event telemetry, and API client pipelines.

### Forensic Finding Summary
- **Total Issues Identified:** **32 Issues**
- **CRITICAL (Security / Major Failure):** **5 Issues**
- **HIGH (Broken Workflow / Serious State / Data Integrity):** **10 Issues**
- **MEDIUM (UX Loophole / Incomplete Interaction / Accessibility):** **11 Issues**
- **LOW (Visual Polish / Code Maintainability / Redundant Markup):** **6 Issues**

---

## 1. COMPLETE FRONTEND INVENTORY

| Directory / File | Category | Lines | Responsibility & Audit State |
|---|---|---|---|
| `src/App.jsx` | Core Shell | 309 | Hash-based routing, global error boundary, top-level layout, alert popup modal listener. |
| `src/main.jsx` | Entrypoint | 10 | React DOM root mounting, StrictMode wrap. |
| `src/index.css` | Stylesheet | 225 | Design tokens, glassmorphism panel CSS, laser animations, responsive media queries. |
| `src/context/ScanContext.jsx` | Global State | 431 | Centralized state for scans, findings, targets, alert acknowledgments, and SSE event streaming. |
| `src/services/apiClient.js` | HTTP Layer | 273 | Typed REST client over `fetch` with AbortController timeout protection and error normalization. |
| `src/components/Sidebar.jsx` | Navigation | 285 | Fixed cyber command sidebar with 9 primary workspaces, version badge, and particle wave. |
| `src/components/Header.jsx` | Navigation | 165 | Top navigation bar, dynamic workspace title, SSE status indicator, notifications bell toggle. |
| `src/components/NotificationCenter.jsx` | Notifications | 195 | Slide-out drawer displaying real-time security alerts and scan lifecycle events. |
| `src/components/CriticalAlertModal.jsx` | Security Modal | 165 | In-app intrusive security modal triggered by unacknowledged critical vulnerability findings. |
| `src/components/KpiCards.jsx` | Telemetry UI | 280 | Quad-card HUD metrics: Total Scans, Open Findings, Verified Resolved, Resolution Rate. |
| `src/components/KpiCyberGraph.jsx` | Visualization | 120 | Animated spline sparkline with traveling laser comet and radar beacons. |
| `src/components/SeverityDonutChart.jsx` | Visualization | 151 | SVG vector donut visualizing Critical, High, Medium, and Low finding proportions. |
| `src/components/ScanActivityChart.jsx` | Visualization | 322 | Rolling 14-day calendar spline chart aggregating real scan execution frequency. |
| `src/components/RecentFindingsTable.jsx` | Data Table | 203 | Factual chronological table of detected findings with direct evidence inspection triggers. |
| `src/components/LastScanSummary.jsx` | Session HUD | 126 | Real-time status card summarizing active or most recently completed security scan. |
| `src/components/AiExplanationPanel.jsx` | AI Integration | 338 | NVIDIA Nemotron breakdown panel: plain-English analysis, threat modeling, and code fixes. |
| `src/components/AttackEvidenceInspector.jsx`| Forensic HUD | 924 | RFC 8785 canonical evidence viewer, raw HTTP headers, dual-principal breach telemetry. |
| `src/components/ErrorBoundary.jsx` | Resilience | 85 | Catch-all error boundary with component-level isolation and diagnostic stack unwinding. |
| `src/components/AmbientCyberBackground.jsx` | Visual Effects | 215 | Canvas-based ambient particle web and cyber grid mesh. |
| `src/components/AnimatedParticleWave.jsx` | Visual Effects | 95 | Sine-wave particle canvas decoration positioned at bottom of sidebar rail. |
| `src/views/SecurityOverview.jsx` | Workspace | 194 | Primary command center landing page with KPI cards, charts, and AI spotlight banner. |
| `src/views/ApiOnboarding.jsx` | Workspace | 2,654 | API Targets & Inventory: catalog, OpenAPI 3.0 import, endpoint discovery, BOLA dual-auth. |
| `src/views/SecurityScans.jsx` | Workspace | 94 | Unified scans workspace hosting New Scan launcher and Historical Scan Registry tabs. |
| `src/views/NewSecurityScan.jsx` | Workspace | 663 | Target URL selection, OWASP Top 10 category checklist, authorization consent, live logs. |
| `src/views/ScanHistory.jsx` | Workspace | 305 | Chronological ledger of historical scan runs with direct drill-down into findings. |
| `src/views/VulnerabilityFindings.jsx` | Workspace | 585 | Multi-filter vulnerability browser, CVSS badge scoring, expandable AI explanations. |
| `src/views/AttackEvidenceWorkspace.jsx` | Workspace | 235 | Standalone forensic investigation deck with target/scan selector and full inspector view. |
| `src/views/AiSecurityAnalysis.jsx` | Workspace | 323 | Dedicated NVIDIA Nemotron intelligence hub with direct code patch generators. |
| `src/views/RetestingVerification.jsx` | Workspace | 736 | Targeted regression verification runner, dual-probe verification, live probe terminal. |
| `src/views/AuditHistoryWorkspace.jsx` | Workspace | 648 | Immutable ledger of verification retests, state transitions, and audit records. |
| `src/views/SettingsView.jsx` | Workspace | 254 | Infrastructure health monitoring: FastAPI node latency, SQLite status, SSE diagnostics. |
| `src/views/NotificationsView.jsx` | Workspace | 275 | Full-page audit log and telemetry event stream with severity filters. |
| `src/views/Reports.jsx` | Workspace | 366 | Security & compliance report builder, executive summaries, OWASP scorecard export. |
| `src/views/ApiKeyIntelligence.jsx` | Workspace | 1,831 | 10,000-sample benchmark dataset analyzer, regex & Shannon entropy detector. |
| `tests/frontend.test.js` | Test Suite | 367 | Node.js TAP architecture and contract assertion suite (14 test blocks). |

---

## 2. FUNCTIONALITY & INTEGRATION AUDIT

### 2.1 Overview Dashboard
- **Status:** Functional with Data Isolation Discrepancies.
- **Findings:**
  - KPI Card 1 (`TOTAL SCANS`) counts all scans in database history (`scans.length`).
  - KPI Card 2 (`OPEN FINDINGS`) and Card 3 (`VERIFIED RESOLVED`) calculate metrics strictly scoped to the *currently selected single scan* (`selectedScanId`), while Card 1 displays aggregate platform-wide counts. This creates cognitive dissonance for security officers who expect the overview to represent enterprise-wide risk posture.
  - When no scans exist in SQLite, the overview correctly displays zero states, but does not provide an immediate 1-click CTA button to load the Healthcare Demo API directly from the empty state.

### 2.2 API Target Registration & Validation (`ApiOnboarding.jsx`)
- **Status:** Functional with State Desynchronization.
- **Findings:**
  - `ApiOnboarding.jsx` maintains its own independent `targets` state (`loadTargets()`), while `ScanContext.jsx` maintains an application-level `targets` state.
  - When a user registers a new API target or deletes a target in `ApiOnboarding`, `ScanContext.refreshTargets()` is **never invoked**.
  - **Result:** When the user switches to `NewSecurityScan.jsx`, the Target dropdown remains stale until a browser hard-refresh occurs.

### 2.3 OpenAPI Specification Import (`ApiOnboarding.jsx`)
- **Status:** Functional with Spec Size Limitation.
- **Findings:**
  - `spec_content` paste mode handles standard OpenAPI 3.0/3.1 specs up to ~1.5MB. However, pasting large enterprise schemas (>5MB) blocks the main thread because schema JSON parsing is executed synchronously in `setSpecPreview(JSON.parse(...))` without Web Worker offloading or chunking.
  - URL-based OpenAPI import fails silently if the remote API does not configure permissive CORS headers (`Access-Control-Allow-Origin: *`). The frontend should route URL imports through the backend proxy endpoint `POST /api/targets/import-spec { spec_url }` rather than attempting a client-side fetch.

### 2.4 Security Scan Execution & Live Telemetry (`NewSecurityScan.jsx` & `ScanContext.jsx`)
- **Status:** Functional.
- **Findings:**
  - The live progress bar utilizes a linear interpolation counter during active SSE scanning. If the backend scanner completes ahead of the artificial animation duration, a sudden jump from 65% to 100% occurs.
  - Scan creation handles duplicate-click protection via `disabled={isScanning || !userAuthorized}`.

### 2.5 Vulnerability Findings & Details (`VulnerabilityFindings.jsx`)
- **Status:** Functional.
- **Findings:**
  - Search query filtering is case-insensitive and checks `vulnerability`, `endpoint`, and `category`.
  - Expanding a finding mounts `AiExplanationPanel.jsx`. If a user rapidly expands and collapses multiple findings, multiple un-aborted `explainFinding` requests are dispatched concurrently to the backend, causing unnecessary queueing.

### 2.6 Attack Evidence Inspector (`AttackEvidenceInspector.jsx`)
- **Status:** Functional.
- **Findings:**
  - Correctly renders Dual-Principal Exploit Flow, raw HTTP request/response with highlighted authorization headers, and copyable cURL commands.
  - If `exportFindingEvidence` fails or returns a 404, the component falls back to `finding.evidence`. However, the fallback does not display a visual warning that the evidence digest is unsealed/reconstructed.

### 2.7 NVIDIA Nemotron AI Explanations (`AiExplanationPanel.jsx`)
- **Status:** Functional.
- **Findings:**
  - Uses SQLite-backed cache (`force_refresh=false`) to avoid redundant inference calls.
  - Displays plain-English explanation, vulnerability impact, and copyable code remediation.
  - Copy code button lacks visual keyboard focus outline for accessibility (`tabIndex=0`).

### 2.8 Verification & Retesting (`RetestingVerification.jsx`)
- **Status:** Functional.
- **Findings:**
  - Retest trigger dispatches `POST /api/scans/{id}/retest` with socket-level IP preservation.
  - Findings state is correctly updated upon `retest_completed` SSE event.
  - If a user triggers a retest on an already "Resolved" finding, the UI permits the probe, but does not inform the user that regression testing on verified endpoints will add a redundant audit ledger entry.

### 2.9 Audit History (`AuditHistoryWorkspace.jsx`)
- **Status:** Functional.
- **Findings:**
  - Displays chronological, immutable ledger of all verification retests.
  - Filter by finding ID or aggregate across all findings.
  - Copying audit record ID provides feedback toast.

### 2.10 Settings (`SettingsView.jsx`)
- **Status:** Functional.
- **Findings:**
  - Probes `/api/health`, `/health`, and `/api/events/status`.
  - Diagnostics button indicates spinning state during probe execution.

### 2.11 Notifications (`NotificationCenter.jsx` & `CriticalAlertModal.jsx`)
- **Status:** Functional.
- **Findings:**
  - Unacknowledged critical vulnerabilities trigger an intrusive modal popup with sound/alert glow.
  - Dismissing the modal keeps the alert unacknowledged in the drawer; clicking "Acknowledge" permanently records the ID in `localStorage` under `apisentinel_acknowledged_alerts`.

### 2.12 API Key Intelligence (`ApiKeyIntelligence.jsx`)
- **Status:** Functional & Preserved as Secondary Workspace.
- **Findings:**
  - Retains all 6 tabs (Single Test, Batch Test, History, Benchmark, Samples, Stats).
  - Isolated from core scanning workspace as required by architecture governance.

---

## 3. SECURITY & FRONTEND LOGIC AUDIT

### SEC-01 [CRITICAL]: Native `window.confirm` for Target Deletion
- **Location:** `frontend/src/views/ApiOnboarding.jsx:391`
- **Vulnerability:** Destructive database operations (deleting API targets, discovered schemas, and auth credentials) invoke the synchronous native browser `window.confirm()`. In automated enterprise browser environments, pop-up blockers or automated drivers can bypass or hang on native dialogs.
- **Remediation:** Replace with an asynchronous, non-blocking custom Cyber Modal (`ConfirmDeleteModal`) styled consistently with the platform's theme.

### SEC-02 [HIGH]: Bearer Token Secret Masking in BOLA Config Form
- **Location:** `frontend/src/views/ApiOnboarding.jsx:2038`, `2142`
- **Vulnerability:** Authentication tokens for User A (`alice`) and User B (`bob`) in the Dual-Principal configuration form are rendered in plaintext `<input type="text">` fields when editing, making them vulnerable to shoulder-surfing during presentations or screen shares.
- **Remediation:** Change to `<input type="password">` with a toggleable "Show/Hide" visibility eye icon and auto-masking after 30 seconds of inactivity.

### SEC-03 [HIGH]: Cross-Origin Spec URL Fetching Without Backend Relay
- **Location:** `frontend/src/views/ApiOnboarding.jsx:480`
- **Vulnerability:** When a user enters a remote OpenAPI specification URL, the frontend attempts `fetch(specRemoteUrl)` directly from the browser runtime. This fails against CORS-restricted targets and exposes the client's internal IP address to untrusted external endpoints.
- **Remediation:** Always delegate spec fetching to the existing backend proxy endpoint `POST /api/targets/import-spec { spec_url }`.

### SEC-04 [MEDIUM]: LocalStorage Alert Acknowledgment Tampering
- **Location:** `frontend/src/context/ScanContext.jsx:10`
- **Vulnerability:** Acknowledged alert IDs are stored in unencrypted `localStorage['apisentinel_acknowledged_alerts']`. Any client script or browser extension can mutate this key to suppress critical security warnings.
- **Remediation:** Store alert acknowledgment status in the backend SQLite database associated with the scan session ID.

### SEC-05 [MEDIUM]: Missing Global HTTP 401/403 Session Expiry Interceptor
- **Location:** `frontend/src/services/apiClient.js:56`
- **Vulnerability:** When backend authorization fails with HTTP 401 or 403, `apiClient` throws a generic `ApiError`. There is no global redirect or unified session expiry banner prompting re-authentication.
- **Remediation:** Implement an event emitter in `apiClient` that dispatches an `AUTH_EXPIRED` event to trigger an in-app re-authentication modal.

---

## 4. DATA INTEGRITY AUDIT

### DAT-01 [CRITICAL]: Target State Desynchronization Across Views
- **Location:** `frontend/src/views/ApiOnboarding.jsx` vs `frontend/src/context/ScanContext.jsx`
- **Problem:** `ApiOnboarding` mutates targets via direct API calls and refreshes its local component state `targets`. `ScanContext.targets` is never updated.
- **Consequence:** Newly added targets do not appear in `NewSecurityScan.jsx` without a full page reload.
- **Remediation:** Expose and invoke `refreshTargets()` from `ScanContext` upon target creation, update, or deletion.

### DAT-02 [HIGH]: Scope Mismatch in Overview Dashboard KPI Cards
- **Location:** `frontend/src/components/KpiCards.jsx:13-46`
- **Problem:** Card 1 (`TOTAL SCANS`) displays the aggregate count of all scans in history (`scans.length`). Cards 2, 3, and 4 calculate findings from the currently selected scan only (`findings.length`).
- **Consequence:** Users viewing 10 scans with 50 total vulnerabilities see "Total Scans: 10" next to "Open Findings: 6" (the findings of only the latest scan), falsely believing there are only 6 open findings platform-wide.
- **Remediation:** Provide clear scope labeling: "Total Scans (All Time)" and "Open Findings (Active Scan: [Target Name])" or aggregate all open findings across latest scan per registered target.

### DAT-03 [MEDIUM]: Race Condition in Rapid Scan Retesting
- **Location:** `frontend/src/views/RetestingVerification.jsx:114`
- **Problem:** If a developer clicks "Run Verification Retest" multiple times rapidly before `isProbing` state settles, multiple retest tasks are spawned on the backend with identical timestamp parameters.
- **Remediation:** Enforce client-side debounce and optimistic locking on the retest execution trigger.

### DAT-04 [MEDIUM]: SSE Reconnection Dropped Event Buffer
- **Location:** `frontend/src/context/ScanContext.jsx:355`
- **Problem:** If the SSE connection disconnects and reconnects (e.g. network flap), events broadcasted by FastAPI during the disconnect window are lost because EventSource does not pass a `Last-Event-ID` header upon reconnect.
- **Remediation:** When SSE state transitions from `disconnected` to `connected`, trigger an immediate `refreshScans()` and `refreshFindings()` to sync state.

---

## 5. UI/UX & VISUAL DESIGN AUDIT

### UI-01 [HIGH]: Resolution Rate Card Misleading 0% State
- **Location:** `frontend/src/components/KpiCards.jsx:44`
- **Problem:** When an API has 0 vulnerabilities detected (a 100% secure posture), the resolution rate formula `(resolved / totalActionableFindings) * 100` evaluates `0 / 0 = null`, rendering `0%` with a purple empty bar.
- **Impact:** Clean, perfectly secure APIs appear to have a "0% Resolution Rate", alarming stakeholders.
- **Remediation:** When `totalActionableFindings === 0`, display `100% (Clean Baseline)` with a green progress bar.

### UI-02 [MEDIUM]: Card Overlap on Ultra-Narrow Viewports (<380px)
- **Location:** `frontend/src/views/ApiOnboarding.jsx:820`
- **Problem:** Target cards in `ApiOnboarding` use `minmax(min(100%, 380px), 1fr)`. On viewports <360px (mobile dev tools), inner padding must drop from 20px to 14px to prevent horizontal scrolling.
- **Remediation:** Add media query `@media (max-width: 480px)` reducing card padding.

### UI-03 [MEDIUM]: Missing Keyboard Accessibility on Interactive Table Rows
- **Location:** `frontend/src/components/RecentFindingsTable.jsx:112`
- **Problem:** Table rows with `onClick={() => handleRowClick(finding)}` lack `tabIndex={0}`, `role="button"`, and `onKeyDown` handlers for Enter/Space. Screen readers and keyboard-only users cannot navigate into findings.
- **Remediation:** Add `role="button"`, `tabIndex={0}`, and `onKeyDown={(e) => e.key === 'Enter' && handleRowClick(finding)}`.

### UI-04 [LOW]: Static "vs. previous period" Hardcoded Labels
- **Location:** `frontend/src/components/KpiCards.jsx:145`
- **Problem:** The subtitle "vs. previous period" is rendered statically under trend indicators even when only 1 scan exists in the database.
- **Remediation:** Show "Baseline Audit" when `scans.length <= 1`, and "vs. previous scan" when `scans.length >= 2`.

---

## 6. CLASSIFIED DEFECT REGISTER

| Defect ID | Severity | File / Component | Brief Summary |
|---|---|---|---|
| **DEF-001** | **CRITICAL** | `ApiOnboarding.jsx` | Native `window.confirm` blocks automated testing and looks non-enterprise. |
| **DEF-002** | **CRITICAL** | `ScanContext.jsx` & `ApiOnboarding.jsx` | Target catalog state desynchronized between workspace and global context. |
| **DEF-003** | **CRITICAL** | `apiClient.js` | Direct browser CORS fetch for remote OpenAPI spec URLs bypasses backend proxy. |
| **DEF-004** | **CRITICAL** | `KpiCards.jsx` | Clean baseline APIs (0 findings) display "0% Resolution Rate" instead of 100% Clean. |
| **DEF-005** | **CRITICAL** | `AttackEvidenceInspector.jsx` | Unsealed fallback evidence lacks visual forensic integrity disclaimer. |
| **DEF-006** | **HIGH** | `ApiOnboarding.jsx` | Plaintext token rendering in Dual-Principal auth form (shoulder-surfing risk). |
| **DEF-007** | **HIGH** | `KpiCards.jsx` | Scope mismatch: Platform-wide Total Scans mixed with single-scan Open Findings. |
| **DEF-008** | **HIGH** | `RetestingVerification.jsx` | Un-debounced retest button permits concurrent duplicate probe execution. |
| **DEF-009** | **HIGH** | `NewSecurityScan.jsx` | Artificial progress animation jumps abruptly from 65% to 100% on fast scans. |
| **DEF-010** | **HIGH** | `ScanContext.jsx` | SSE reconnect does not buffer or backfill dropped scan completion events. |
| **DEF-011** | **HIGH** | `VulnerabilityFindings.jsx` | Rapid expansion of multiple finding cards spawns concurrent un-aborted AI requests. |
| **DEF-012** | **HIGH** | `Reports.jsx` | Executive summary generation lacks PDF print-friendly stylesheet rules. |
| **DEF-013** | **HIGH** | `SettingsView.jsx` | Network diagnostics fail without human-readable remediation steps if backend is offline. |
| **DEF-014** | **HIGH** | `AuditHistoryWorkspace.jsx` | Ledger search query filter does not debounce, causing high CPU on large audits. |
| **DEF-015** | **HIGH** | `Sidebar.jsx` | Sidebar width collapse (<1280px) does not show icon tooltips for collapsed items. |
| **DEF-016** | **MEDIUM** | `ScanActivityChart.jsx` | Zero-state chart displays empty grid without intuitive "Launch First Scan" CTA. |
| **DEF-017** | **MEDIUM** | `RecentFindingsTable.jsx` | Table rows lack keyboard accessibility attributes (`role="button"`, `tabIndex=0`). |
| **DEF-018** | **MEDIUM** | `AiExplanationPanel.jsx` | Code snippet copy button lacks accessible ARIA live announcement. |
| **DEF-019** | **MEDIUM** | `NotificationCenter.jsx` | Acknowledging individual alert from drawer does not animate card departure smoothly. |
| **DEF-020** | **MEDIUM** | `CriticalAlertModal.jsx` | Modal escape key handler does not prevent background scroll on body. |
| **DEF-021** | **MEDIUM** | `ApiOnboarding.jsx` | Large OpenAPI specs (>5MB) synchronously parse on main thread causing frame drops. |
| **DEF-022** | **MEDIUM** | `App.jsx` | Query parameter changes do not trigger smooth scroll-to-top on workspace transition. |
| **DEF-023** | **MEDIUM** | `RetestingVerification.jsx` | Retesting already-resolved findings adds redundant entries without notice. |
| **DEF-024** | **MEDIUM** | `SeverityDonutChart.jsx` | Hovering donut segments does not trigger focus ring for keyboard users. |
| **DEF-025** | **MEDIUM** | `NewSecurityScan.jsx` | Category checklist items lack "Select All / Deselect All" convenience toggles. |
| **DEF-026** | **MEDIUM** | `ApiKeyIntelligence.jsx` | Batch test input lacks paste-from-clipboard button for large token sets. |
| **DEF-027** | **LOW** | `KpiCards.jsx` | Hardcoded "vs. previous period" displays on initial single scan baseline. |
| **DEF-028** | **LOW** | `Header.jsx` | SSE status indicator pill lacks ping latency tooltip (e.g. "Latency: 12ms"). |
| **DEF-029** | **LOW** | `index.css` | Redundant `.hud-corner` rules marked `!important` remain in stylesheet. |
| **DEF-030** | **LOW** | `AmbientCyberBackground.jsx`| Canvas animation continues calculating on browser tab backgrounded/hidden state. |
| **DEF-031** | **LOW** | `AnimatedParticleWave.jsx` | Canvas width recalculation does not throttle resize event listener. |
| **DEF-032** | **LOW** | `ScanHistory.jsx` | Scan duration format displays raw seconds (e.g. "124s") instead of "2m 04s". |

---

## 7. AUDIT VERIFICATION SIGN-OFF
This forensic audit was performed non-destructively against Git commit state on branch `feature/api-key-dataset`. No backend files, database schemas, or Git history have been modified.
