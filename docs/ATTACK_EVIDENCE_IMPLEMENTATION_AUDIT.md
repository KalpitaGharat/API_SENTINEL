# API SENTINEL — ATTACK & EVIDENCE IMPLEMENTATION AUDIT
## Real Architecture Inspection & Gap Analysis

**Project:** API Sentinel  
**Project Path:** `C:\PROJECTS\api-sentinel`  
**Active Git Branch:** `feature/api-key-dataset`  
**Baseline Git Checkpoint:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93` (v1.0.0 Release Baseline Preserved)  
**Audit Date:** November 11, 2026  
**Auditor:** Senior Application Security Engineer & System Architect  
**Product Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. EXECUTIVE AUDIT SUMMARY

An independent code-level inspection of the complete end-to-end workflow was performed:
```
Target Registration -> OpenAPI Import -> Auth Profiles -> Scan Execution -> Finding Creation -> Evidence Retrieval -> AI Explanation -> Retest -> Finding Status Update -> Report Generation
```

The objective is to establish ground truth regarding what is genuinely implemented, what is partial, what is simulated, and what must be enhanced to deliver the **Attack Demonstration & Evidence Inspector**.

---

## 2. DETAILED IMPLEMENTATION VERIFICATION BY STAGE

### A. Scanner Execution (`backend/app/security_engine/member1_engine.py` & `scan_service.py`)
- **Real Network Probes:** **Verified**. The scanner dispatches real HTTP requests over `httpx.Client` wrapped by `PinnedHTTPTransport` (which enforces SSRF defenses, IP pinning, and scheme restrictions).
- **Authentication Profiles:** **Verified**. When scans are initiated via `POST /api/targets/{id}/scan`, `TargetAuthProfile` records are decrypted via the Fernet vault and mapped to `test_accounts["patient_a"]` and `test_accounts["patient_b"]`.
- **Multi-Principal Comparison:** **Verified**. In `_check_bola()`, the engine probes Principal A's own record (`/api/patients/101`) to establish a legitimate baseline, then probes Principal B's record (`/api/patients/102`) using Principal A's bearer credentials.
- **Content-Aware Verification:** **Verified**. Uses `_verify_foreign_data_exposure()` to inspect the JSON response body for target identifiers (`patient_id`, `owner_username`, `diagnosis`). A vulnerability is flagged only when unauthorized foreign data is genuinely exposed.
- **Evidence Telemetry Captured:** **Partial**. Currently, `request_details` stores `method`, `url`, `test_principal`, `authorization: "[REDACTED_TOKEN]"`, and `target_object_id`. `response_details` stores `status_code`, `foreign_record_accessed`, `target_owner_id`, and `data_snippet`. However, complete masked request headers, response headers, response duration (`duration_ms`), full sanitized response body, and attack timeline milestones are not comprehensively formatted for direct inspector display.

### B. Findings & Evidence Persistence (`backend/app/models.py` & `routes/findings.py`)
- **Stable Identifiers:** **Verified**. Both `Finding` and `Evidence` tables utilize UUID4 primary keys with cascade relationships.
- **Sanitization:** **Verified**. Credentials and tokens are redacted (`[REDACTED_TOKEN]` or masked `sent..._101`).
- **Evidence Retrieval:** **Verified**. `GET /api/findings/{id}` eager-loads `evidence` and `ai_explanation`.
- **Evidence Export & Hashing:** **Missing**. No dedicated endpoint exists to export sanitized evidence with an immutable SHA-256 integrity digest for external audits or SIEM ingestion.

### C. Retesting & Verification Workflow (`backend/app/services/retest_service.py` & `member1_engine.py`)
- **Real HTTP Probes:** **Verified**. `_retest_bola()` dispatches real requests to the target.
- **Dual-Probe Logic:** **Verified**.
  - Probe 1 (Owner Access): Checks `/api/patients/101` with Alice's token -> requires `HTTP 200 OK`. If broken, returns `Needs Review` (preventing false resolution).
  - Probe 2 (Attacker Access): Checks `/api/patients/102` with Alice's token -> requires `HTTP 403/404`. If access is rejected, status transitions to `Resolved`.
- **Detailed Retest Telemetry:** **Partial**. While `observed_result` logs a human-readable summary, it lacks structured dual-probe telemetry comparing owner status vs. attacker status side-by-side for before/after comparison tables in the UI.

### D. AI Explanation & Fallback (`backend/app/services/ai_service.py`)
- **Finding Grounding:** **Verified**. The finding's description, endpoint, category, and recommendation are passed to the AI prompt.
- **Offline Deterministic Fallback:** **Verified**. When `NVIDIA_API_KEY` is omitted or times out (30s bound), the engine automatically falls back to `_generate_rule_based_fallback()`, returning 5 actionable remediation steps.
- **Evidence Enrichment:** **Partial**. The AI service prompt does not currently incorporate the rich request/response evidence snippet into its prompt context.

### E. Frontend Inspector UX (`frontend/src/views/VulnerabilityFindings.jsx`)
- **Current Findings UI:** Displays finding cards, severity chips, expandable description, high-level recommendation, and raw JSON dump of `request_details`.
- **Dedicated Attack & Evidence Inspector Modal/Drawer:** **Missing**. There is no visual attacker vs. resource owner diagram, no raw HTTP request/response inspector with tabs, no copyable sanitized cURL command, no attack timeline, and no SHA-256 signed evidence export.

---

## 3. AUDIT MATRIX & REQUIRED ENHANCEMENTS

| Feature | Current Implementation | Verified Status | Required Action |
| :--- | :--- | :--- | :--- |
| **Active Security Scanning** | `member1_engine.py` executes real HTTP requests with IP-pinned transport and BOLA content matching. | **Verified** | Enhance `_check_bola()` to capture complete request headers, response headers, response duration, and structured timeline events. |
| **Request Evidence** | Stores method, URL, and redacted authorization token. | **Partial** | Include full sanitized headers, query params, body, copyable masked cURL, and indication of reconstructed vs. captured request. |
| **Response Evidence** | Stores status code, foreign data boolean, and data snippet. | **Partial** | Store complete response headers, duration in ms, sanitized response body, security observations, and exposed fields. |
| **Attack Demonstration UI** | Simple JSON code snippet in finding drawer. | **Partial** | Build a dedicated, cyber-dark **Attack & Evidence Inspector** modal with tabs for Attack Overview (visual diagram), Request, Response, Timeline, and Integrity. |
| **Retesting Workflow** | `retest_service.py` executes real dual-check probes and updates status to `Resolved`. | **Verified** | Structure retest `observed_result` to explicitly output owner probe vs. attacker probe metrics for side-by-side UI comparison. |
| **Evidence Export** | Only full scan reports exportable in JSON/Markdown. | **Missing** | Add `GET /api/findings/{id}/export-evidence` generating a self-contained JSON payload with an immutable SHA-256 digest. |
| **AI Root Cause Grounding**| Prompt receives finding title, endpoint, and category. | **Verified** | Pass captured request and response evidence into `ai_service.py` to enrich explanation context. |

---

## 4. IMPLEMENTATION ROADMAP

1. **Backend Telemetry & Schema Enhancement:**
   - Update `member1_engine.py` to capture rich request headers, response headers, duration, and attack timeline milestones.
   - Add `GET /api/findings/{id}/export-evidence` in `backend/app/routes/findings.py` with canonical SHA-256 checksum generation.
   - Enhance `retest_service.py` and `_retest_bola` to include structured dual-probe before/after comparisons.
2. **Frontend Attack & Evidence Inspector Component:**
   - Build a polished, accessible, responsive `AttackEvidenceInspector` modal/drawer in `frontend/src/components/AttackEvidenceInspector.jsx`.
   - Integrate "Inspect Attack & Evidence" trigger button into `VulnerabilityFindings.jsx`.
   - Provide 5 specialized tabs: **Attack Overview** (with visual flow), **Raw HTTP Request** (with safe cURL copy), **Raw HTTP Response** (with field highlighting), **Attack Timeline**, and **Evidence Integrity & Export** (with one-click JSON download and SHA-256 verification).
3. **Connect to Existing Healthcare Demo API:**
   - Validate live execution in vulnerable mode (`DEMO_VULNERABLE_MODE=true`) and secure mode (`DEMO_VULNERABLE_MODE=false`).
4. **Validation & Regression:**
   - Add automated backend and frontend tests.
   - Verify 125 backend tests and 10 frontend tests continue passing with 100% success.
