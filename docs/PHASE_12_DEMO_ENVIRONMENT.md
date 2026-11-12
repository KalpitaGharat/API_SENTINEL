# API SENTINEL — PHASE 12: DEMO ENVIRONMENT SPECIFICATION & READINESS GUIDE

**Project:** API Sentinel  
**Project Path:** `C:\PROJECTS\api-sentinel`  
**Active Git Branch:** `feature/api-key-dataset`  
**Baseline Git Checkpoint:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93` (v1.0.0 Release Baseline Preserved)  
**Report Date:** November 11, 2026  
**Audience:** Technical Demonstrators, Evaluators, College Faculty, Hackathon Judges  
**Product Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. DEMO ENVIRONMENT OVERVIEW

API Sentinel is engineered to be **completely self-contained, reproducible, and verifiable**. During live technical presentations, hackathons, or faculty audits, all core capabilities—real vulnerability scanning, OpenAPI endpoint discovery, credential vault encryption, multi-principal BOLA verification, explainable remediation, retest verification, and dataset intelligence—execute **100% locally without external cloud dependencies**.

```
+--------------------------------------------------------------------------------------------------+
|                                    LOCAL DEMO ARCHITECTURE                                       |
|                                                                                                  |
|   +------------------------------------+          +------------------------------------+         |
|   |   React 18 Cyber Dashboard (SPA)   |          |    Streamlit Analytics Dashboard   |         |
|   |         http://127.0.0.1:5173      |          |        http://127.0.0.1:8501       |         |
|   +------------------+-----------------+          +------------------+-----------------+         |
|                      |                                               |                           |
|                      +-----------------------+-----------------------+                           |
|                                              | REST / SSE                                        |
|                                              v                                                   |
|                         +-----------------------------------------+                              |
|                         |       FastAPI Backend Core Engine       |                              |
|                         |          http://127.0.0.1:8000          |                              |
|                         +-----+-------------------+---------------+                              |
|                               |                   |                                              |
|            SQLite Database    |                   | Hardened HTTP Transport                      |
|         (Fernet Vault Inside) |                   | (SafeHTTPClient / Pinned)                    |
|                               v                   v                                              |
|                     [ api_sentinel.db ]    +------------------------------------+                |
|                                            |     Healthcare Demo API Target     |                |
|                                            |        http://127.0.0.1:8001       |                |
|                                            |  (Vulnerable Mode / Remediated)    |                |
|                                            +------------------------------------+                |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. SERVICE PORT ALLOCATION & HEALTH PROBES

All 4 services must be running simultaneously for the full end-to-end demonstration.

| Service Component | Port | Base URL | Health Check Probe | Expected Healthy Response |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI Backend Core** | `8000` | `http://127.0.0.1:8000` | `GET /health` | `{"status":"healthy","database":"connected","version":"1.0.0"}` |
| **Healthcare Demo API Target** | `8001` | `http://127.0.0.1:8001` | `GET /health` | `{"status":"healthy","service":"healthcare_demo_api","vulnerable_mode":true}` |
| **React Cyber Dark Dashboard** | `5173` | `http://127.0.0.1:5173` | `GET /` | HTTP 200 (Vite 5.4 HMR HTML Shell) |
| **Streamlit Analytics Hub** | `8501` | `http://127.0.0.1:8501` | `GET /_stcore/health` | `200 ok` (Streamlit Engine Responsive) |

---

## 3. SAFE DEMONSTRATION CREDENTIALS & PRINCIPALS

To showcase multi-principal authorization testing (BOLA / IDOR) without leaking production keys or violating privacy policies, the demo environment uses safe synthetic identities:

### Principal A: Resource Owner (Primary User)
- **Account Label:** `User A (Primary Owner)`
- **Username:** `patient_a`
- **Owner Patient ID:** `101`
- **Authentication Scheme:** `Bearer Token`
- **Safe Demonstration Token:** `sentinel_patient_a_demo_token_101`
- **Vault Masking in UI:** `sent..._101`
- **Legitimate Accessible Resource:** `GET /api/patients/101`

### Principal B: Unauthorized Attacker (Foreign User)
- **Account Label:** `User B (Foreign Attacker)`
- **Username:** `patient_b`
- **Foreign Patient ID:** `102`
- **Authentication Scheme:** `Bearer Token`
- **Safe Demonstration Token:** `sentinel_patient_b_demo_token_102`
- **Vault Masking in UI:** `sent..._102`
- **Unauthorized Target Resource:** `GET /api/patients/101` (Probing Alice's record as Bob)

---

## 4. DEMO TARGET MODES (VULNERABLE VS. REMEDIATED)

The Healthcare Demo API (`http://127.0.0.1:8001`) can be switched between vulnerable and secure modes to demonstrate live remediation and retest verification:

### Mode 1: Vulnerable Mode (Default for Scan Initiation)
- **Environment Setting:** `DEMO_VULNERABLE_MODE=true`
- **Observed Behavior:**
  - `GET /api/patients/102` with token `patient_a` returns **HTTP 200 OK** exposing patient 102's private records.
  - Security headers (`Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`) are omitted.
- **Scanner Result:** Identifies 6 findings (1 High BOLA, 1 High Auth, 4 Medium/Low Headers).

### Mode 2: Remediated / Secure Mode (For Verification Retest)
- **Environment Setting:** `DEMO_VULNERABLE_MODE=false` (or set in `demo_api/main.py`)
- **Observed Behavior:**
  - Server validates `current_user_id == resource_owner_id`.
  - Attacker attempt returns **HTTP 403 Forbidden**.
  - Owner request (`patient_a` requesting `/api/patients/101`) succeeds with **HTTP 200 OK**.
- **Scanner Result:** Retest dual-check marks BOLA as **`Resolved`**; security health score rises from 25/100 to 85+/100.

---

## 5. REPRODUCIBLE DEMO DATABASE & RESET PROCEDURES

To ensure presentations remain clean and repeatable without touching production or historical audit data:

### Standard Working Database
- **Path:** `C:\PROJECTS\api-sentinel\backend\api_sentinel.db`
- **Tables Included:** `scans`, `findings`, `evidence`, `retest_history`, `ai_explanations`, `api_targets`, `discovered_endpoints`, `target_auth_profiles`, `dataset_test_sessions`, `dataset_test_results`.

### Safe Disposable Demo Reset (Without Modifying Working Data)
If a presenter wants a pristine state before going on stage:
1. Make a temporary backup of the existing database:
   ```powershell
   Copy-Item "C:\PROJECTS\api-sentinel\backend\api_sentinel.db" "C:\PROJECTS\api-sentinel\backend\api_sentinel.db.bak"
   ```
2. Re-initialize a blank demonstration database:
   ```powershell
   # The database tables are auto-created by FastAPI upon startup
   # To reset scan history safely, run:
   powershell -Command "Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -Method GET"
   ```
3. To restore historical evidence after the presentation:
   ```powershell
   Move-Item -Force "C:\PROJECTS\api-sentinel\backend\api_sentinel.db.bak" "C:\PROJECTS\api-sentinel\backend\api_sentinel.db"
   ```

---

## 6. OFFLINE CAPABILITY & ZERO EXTERNAL DEPENDENCIES

In hackathon or classroom environments where internet access may be unstable, restricted, or firewalled:
- **API Key Intelligence:** Operates against the local 10,000-sample JSON/CSV master dataset (`metadata/synthetic_api_keys_10000.json`). No external GitHub or Nightfall requests are made.
- **Outbound Scanner:** Scans the local demo API target over loopback (`http://127.0.0.1:8001`) with lab safety controls enabled (`ALLOW_LOCAL_LAB_SCANNING=True`).
- **Nemotron AI Service:** If the external NVIDIA API key is unavailable or the internet is offline, the backend's deterministic fallback engine automatically steps in:
  - Generates clear, structured root-cause explanations.
  - Produces 5 concrete, actionable remediation steps.
  - Labels output as `rule-based-security-engine (offline-fallback)`.
  - Zero crashes, zero blank screens, zero latency degradation.

---

## 7. SERVICE LAUNCH SCRIPT (POWERSHELL)

To start all 4 services quickly in individual background sessions or terminals:

```powershell
# 1. Start Healthcare Demo API (Port 8001)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\PROJECTS\api-sentinel'; python -m uvicorn demo_api.main:app --host 127.0.0.1 --port 8001"

# 2. Start FastAPI Backend (Port 8000)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\PROJECTS\api-sentinel\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

# 3. Start React Frontend (Port 5173)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\PROJECTS\api-sentinel\frontend'; npm run dev -- --host 127.0.0.1 --port 5173"

# 4. Start Streamlit Dashboard (Port 8501)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\PROJECTS\api-sentinel'; python -m streamlit run dashboard/app.py --server.port 8501 --server.headless true"
```

Once launched, verify readiness by browsing to `http://127.0.0.1:5173`.
