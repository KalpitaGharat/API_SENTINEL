# API Sentinel – Member 1 Security Testing Engine

## 1. Engine Architecture & Overview

The **Member 1 Real Security Testing Engine** (`backend/app/security_engine/member1_engine.py`) provides evidence-based, reproducible, non-destructive vulnerability detection for the API Sentinel platform.

It directly implements the `BaseSecurityEngineAdapter` contract established by Member 3, identifying itself as:
- **`engine_name`**: `"api_sentinel_real_detection_engine"`
- **`is_simulated`**: `False`

The backend dynamically detects and loads this engine automatically upon startup without requiring manual code changes or configuration flags.

```
                           +----------------------------+
                           |     FastAPI Backend        |
                           |   (Scan & Retest Serv.)    |
                           +--------------+-------------+
                                          |
                        BaseSecurityEngineAdapter Contract
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               Member 1 Real Detection Engine (member1_engine.py)                  |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |  BOLA/IDOR Probe   |   |   Auth Probes (401)   |   | Header & Config Audits |  |
|  | (Dual-Principal)   |   | (Invalid Token Sigs)  |   | (HSTS, CSP, nosniff)   |  |
|  +---------+----------+   +-----------+-----------+   +-----------+------------+  |
|            |                          |                           |               |
|            +--------------------------+---------------------------+               |
|                                       |                                           |
|                                       v                                           |
|                     +----------------------------------+                          |
|                     |   Safe HTTP Client Integration   |                          |
|                     | (SSRF Guard, Redaction, Timeout) |                          |
|                     +-----------------+----------------+                          |
+---------------------------------------|-------------------------------------------+
                                        |
                   Live Network or In-Process Transport
                                        |
                                        v
                 +---------------------------------------------+
                 |            Target API / Demo API            |
                 |      (e.g., Healthcare Demo API 8001)       |
                 +---------------------------------------------+
```

---

## 2. Vulnerability Categories & Detection Logic

### A. Broken Object Level Authorization (BOLA / IDOR) – Highest Priority MVP
- **Category:** `BOLA`
- **Methodology (Dual-Principal Testing):**
  1. Resolves credentials for two synthetic accounts: **Principal A** (`patient_a`, ID 101) and **Principal B** (`patient_b`, ID 102).
  2. If tokens are not provided upfront, auto-authenticates against `/api/auth/login`.
  3. **Baseline Check:** Principal A queries their own record (`GET /api/patients/101`). If access is denied, testing halts to avoid inconclusive false positives.
  4. **Cross-Tenant Probe:** Principal A requests Principal B's record (`GET /api/patients/102`).
  5. **False-Positive Filter (`_verify_foreign_data_exposure`):** Confirms the HTTP 200 response contains foreign identifier keys (`patient_b`, ID 102, clinical fields) rather than a generic or masked success message.
  6. **Evidence Generation:** Records observed status (200), expected status (403), request details (with tokens redacted), and body preview.

### B. Authentication Weaknesses
- **Category:** `AUTH`
- **Methodology:**
  1. **Unauthenticated Access:** Queries sensitive routes (`/api/patients/me`, `/api/admin/metrics`) without credentials. If HTTP 200 is returned, flags a **Critical** finding.
  2. **Token Signature Bypass:** Queries protected endpoints with invalid/forged bearer tokens (`Bearer sentinel_invalid_test_token_9999`). If HTTP 200 is returned, flags a **High** finding for broken signature validation.

### C. Missing HTTP Security Headers
- **Category:** `HEADERS`
- **Checks Performed:**
  - `Strict-Transport-Security` (HSTS): Prevents MITM attacks and forces HTTPS.
  - `X-Content-Type-Options`: Enforces `nosniff` against MIME confusion.
  - `X-Frame-Options`: Enforces `DENY` against clickjacking.
  - `Content-Security-Policy` (CSP): Defense-in-depth against client-side injection.

### D. API Configuration & Information Disclosure
- **Category:** `CONFIG`
- **Checks Performed:**
  - Audits default debug endpoints, framework telemetry, and administrative metric exposures.

---

## 3. Retesting & Verification Logic

Retesting verifies whether a developer's fix was effective:
- **`Resolved`** (`verified: True`):
  - BOLA probe receives HTTP 403 Forbidden or 404 Not Found.
  - Unauthenticated / forged token probes receive HTTP 401 Unauthorized.
  - Required security headers are now present in response headers.
- **`Still Vulnerable`** (`verified: False`):
  - BOLA probe still successfully extracts Principal B's record with HTTP 200.
- **`Retest Failed`** (`verified: False`):
  - The target host is unreachable, DNS resolution fails, or an unexpected HTTP status code requires manual operator review.

---

## 4. Intentionally Vulnerable Healthcare Demo API

Located at `demo_api/`:
- **Port:** `8001`
- **Synthetic Test Accounts:**
  - `patient_a` / `demo_password_a` (Owns record ID 101)
  - `patient_b` / `demo_password_b` (Owns record ID 102)
- **Vulnerable Behavior (`DEMO_VULNERABLE_MODE=True`):**
  - `GET /api/patients/102` with Token A returns Patient B's diagnosis and prescription without authorization check.
- **Remediated Behavior (`DEMO_VULNERABLE_MODE=False`):**
  - Server enforces `record["owner_id"] == current_user["id"]`, returning HTTP 403 Forbidden on cross-user access.
- **Toggle Endpoint:**
  - `POST /api/demo/mode` with `{"vulnerable": false, "enable_security_headers": true}`.

---

## 5. Execution Instructions

### A. Run Demo API
```powershell
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001 --reload
```

### B. Run API Sentinel Backend
```powershell
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### C. Execute Test Suite
```powershell
cd backend
pytest -c pytest.ini -v
```

All 25 tests pass across unit, integration readiness, and Member 1 engine suites in under 3 seconds.
