# API SENTINEL — USER & AUDITOR GUIDE

**Product:** API Sentinel  
**Version:** v1.1.0  
**Tagline:** *Find it. Understand it. Fix it. Verify it.*  
**Primary Users:** Student Developers, AppSec Engineers, DevSecOps Auditors, Startup CTOs

---

## 1. PRODUCT NAVIGATION & DASHBOARD INTERFACE

The API Sentinel React dashboard features 11 primary views accessed via the left sidebar:

| Sidebar Navigation Item | Purpose | Key User Actions |
| :--- | :--- | :--- |
| **Security Overview** | Executive summary & real-time telemetry | Monitor health score, recent scans, OWASP breakdown |
| **API Onboarding** | Register targets & import OpenAPI specs | Upload/paste specs, discover endpoints, set dual test credentials |
| **New Security Scan** | Configure and initiate active tests | Select target, choose test categories, confirm authorization |
| **Scan History** | Chronological registry of all scan sessions | Inspect past scan execution metrics, durations, and statuses |
| **Vulnerability Findings** | Detailed catalog of detected weaknesses | Expand technical evidence, view reproducible curl, read AI fixes |
| **AI Security Analysis** | LLM-driven root-cause explanations | Deep dive into architectural flaws with code fixes |
| **Retesting & Verification**| Dual-probe automated patch verification | Retest fixed findings, verify owner access & attacker rejection |
| **Reports** | Exportable executive & compliance audits | Download sanitized JSON and Markdown security reports |
| **API Key Intelligence** | Synthetic dataset token benchmark | Test individual API keys, batch test, run 10k benchmark |
| **Notifications** | Real-time SSE alert stream | Review system alerts, critical vulnerability popups |
| **Settings** | Target configuration & environment info | View server configuration and system status |

---

## 2. THE 4-PILLAR WORKFLOW: STEP-BY-STEP

### Pillar 1: FIND IT (Discovery & Active Scanning)
1. Go to **API Onboarding**.
2. Enter your API name (e.g., `Billing Service`) and base URL (e.g., `https://api.myapp.com`).
3. Paste or upload your OpenAPI/Swagger YAML or JSON specification and click **Parse Specification & Preview**.
4. Sentinel maps all endpoints and parameters (e.g., `/users/{user_id}/invoices`).
5. Configure two test accounts under **Authentication Profiles**:
   - **User A (Owner):** Token for legitimate resource owner (e.g., User ID 101).
   - **User B (Attacker):** Token for an unauthorized foreign user (e.g., User ID 102).
6. Navigate to **New Security Scan**, confirm legal scanning authorization, select categories (`BOLA`, `AUTH`, `HEADERS`), and click **Launch Security Scan**.

### Pillar 2: UNDERSTAND IT (Explainable Evidence & AI Root Cause)
1. Navigate to **Vulnerability Findings**.
2. Click on any finding (e.g., `Broken Object Level Authorization (BOLA)`).
3. Open the **Technical Evidence Drawer**:
   - Inspect the exact HTTP status (`200 OK` vs expected `403 Forbidden`).
   - Observe the foreign data exposed in the sanitized response snippet.
   - Click **Copy Reproduction Curl** to reproduce the vulnerability from your terminal.
4. Read the **AI Root-Cause Explanation** to understand the exact code flaw.

### Pillar 3: FIX IT (Developer Remediation Steps)
1. Review the step-by-step remediation advice provided in the finding drawer.
2. Example BOLA fix:
   ```python
   # INSECURE: Relies on user-provided path parameter alone
   # record = db.query(Invoice).filter(Invoice.id == invoice_id).first()

   # SECURE: Validates that authenticated user owns the resource
   record = db.query(Invoice).filter(
       Invoice.id == invoice_id,
       Invoice.owner_user_id == current_authenticated_user.id
   ).first()
   if not record:
       raise HTTPException(status_code=403, detail="Access denied")
   ```
3. Deploy the patch to your application server.

### Pillar 4: VERIFY IT (Dual-Probe Retesting)
1. Navigate to **Retesting & Verification**.
2. Click **Run Retest Probe** on the patched finding.
3. Sentinel executes two automated checks:
   - **Probe 1 (Owner Access):** User A requests resource -> Verifies **HTTP 200 OK** (Legitimate user access preserved).
   - **Probe 2 (Attacker Access):** User B requests resource -> Verifies **HTTP 403 Forbidden** (Attacker blocked).
4. Finding status automatically promotes from `Open` to **`Resolved`**.
5. An immutable audit record is permanently logged in the retest history.

---

## 3. AUDITING & COMPLIANCE REPORTING

1. Navigate to **Reports**.
2. Select your scan from the session dropdown.
3. Review the OWASP API Top 10 distribution chart and overall security health score.
4. Click **Export Audit JSON** to export machine-readable data for your CI/CD or SIEM pipeline.
5. Click **Export Audit Markdown** to generate a clean, shareable document for team pull requests or compliance reviews.
