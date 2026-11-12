# API Sentinel — Hackathon Demonstration & Execution Runbook

**Tagline:** Find it. Understand it. Fix it. Verify it.  
**Platform Version:** 1.0.0 Production Ready  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Distribution ZIP:** `C:\PROJECTS\API_Sentinel_Complete_Platform.zip`  
**Target Audience:** Hackathon Judges, Student Developers, Small Business Engineers

---

## 1. Quick Start / Demo Overview

This runbook guides presenters through a 5-minute live hackathon presentation demonstrating the complete explainable API security lifecycle using API Sentinel and the Healthcare Demo API.

### Service Ports Summary

| Service | Port | Technology | URL |
|---|:---:|---|---|
| **API Sentinel Backend** | `8000` | FastAPI / Python 3.13 / SQLite WAL | `http://127.0.0.1:8000/docs` |
| **Healthcare Demo API** | `8001` | FastAPI / In-Memory Mock Target | `http://127.0.0.1:8001/health` |
| **Primary Streamlit UI** | `8501` | Streamlit Cyber Dashboard | `http://127.0.0.1:8501` |
| **Standalone React UI** | `5173` | React 18 / Vite / Tailwind CSS | `http://127.0.0.1:5173` |

---

## 2. Startup Sequence (3 Terminal Windows)

Open 3 PowerShell terminal windows.

### Terminal 1: Launch API Sentinel Backend
```powershell
Set-Location "C:\PROJECTS\api-sentinel\backend"
$env:PYTHONPATH = "C:\PROJECTS\api-sentinel;C:\PROJECTS\api-sentinel\backend"
& "C:\Users\AaYushman Parab\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Verification:* Navigate to `http://127.0.0.1:8000/health` $\rightarrow$ `{"status": "healthy", ...}`

---

### Terminal 2: Launch Healthcare Demo Target API
```powershell
Set-Location "C:\PROJECTS\api-sentinel"
$env:PYTHONPATH = "C:\PROJECTS\api-sentinel"
& "C:\Users\AaYushman Parab\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn demo_api.main:app --host 127.0.0.1 --port 8001 --reload
```
*Verification:* Navigate to `http://127.0.0.1:8001/health` $\rightarrow$ `{"status": "healthy", "vulnerable_mode": true, ...}`

---

### Terminal 3: Launch Streamlit Cybersecurity Dashboard
```powershell
Set-Location "C:\PROJECTS\api-sentinel"
& "C:\Users\AaYushman Parab\AppData\Local\Programs\Python\Python313\python.exe" -m streamlit run dashboard/streamlit_app.py --server.port 8501
```
*Verification:* Browser opens automatically at `http://127.0.0.1:8501`.

*(Optional) Standalone React Dashboard:*
```powershell
Set-Location "C:\PROJECTS\api-sentinel-dashboard"
npm run dev
```

---

## 3. Step-by-Step Live Demonstration Script

### Step 1: Introduce the Problem & Dashboard Overview (1 Minute)
1. Show the **API Sentinel Dashboard** in browser (`http://127.0.0.1:8501`).
2. Highlight the 4-phase philosophy: **Find it. Understand it. Fix it. Verify it.**
3. Explain that traditional DAST tools produce noisy, unexplainable reports with no verification. API Sentinel provides actionable AI remediation and mathematically verifies whether code fixes resolved the vulnerability.

---

### Step 2: "Find It" — Launch Live Scan on Vulnerable Target (1 Minute)
1. In the sidebar, navigate to **"🚀 New Scan"**.
2. Target URL is pre-filled: `http://127.0.0.1:8001`
3. Profile selected: **"OWASP API Top 10 Deep Audit"**
4. Checkbox selected: **"I authorize security testing on this target API"**
5. Click **"🚀 Launch Automated Security Scan"**.
6. Scan completes in < 2 seconds. Total findings: **6 vulnerabilities**.
7. Click the link or sidebar to open **"🔍 Scan Findings"**.

---

### Step 3: Inspect Real Telemetry & HTTP Evidence (1 Minute)
1. Select the **Broken Object Level Authorization (BOLA)** finding:
   - Severity: `High`
   - Endpoint: `GET /api/patients/{patient_id}`
2. Expand the **"🔬 Technical HTTP Evidence & Telemetry"** accordion:
   - Point out **Observed Status**: `HTTP 200 OK` (Expected: `HTTP 403 Forbidden`).
   - Point out **Test Principal**: `patient_a (ID 101)`.
   - Point out **Target Resource**: `patient_b (ID 102)`.
   - Show that patient_a was able to inspect patient_b's medical records and prescriptions.
   - Point out that all bearer tokens and authorization headers are safely redacted (`[REDACTED_TOKEN]`).

---

### Step 4: "Understand It" — AI Explanation with NVIDIA Nemotron (1 Minute)
1. Under the finding, locate the AI section and click **"✨ Explain with Nemotron AI"**.
2. If online with NVIDIA API key configured, Nemotron-3.5-lightning generates a structured analysis in seconds.
3. If offline, the deterministic rule engine provides the exact analysis instantly.
4. Show the three distinct sections:
   - **Plain English Breakdown:** Explains how missing ownership checks let user A view user B's records.
   - **Attack Scenarios & Business Impact:** Explains data breach risk, HIPAA/regulatory fines, and account takeover.
   - **Step-by-Step Remediation:** Provides exact code-level guidance (e.g. verifying `current_user.id == record.owner_id` before returning data).
5. Point out that this explanation is now permanently cached in SQLite for offline team review.

---

### Step 5: "Fix It" & "Verify It" — Remediation & Retesting (1 Minute)
1. Switch to the target API terminal or issue a curl command to toggle the Healthcare Demo API into **Secure Mode**:
   ```powershell
   curl.exe -X POST http://127.0.0.1:8001/api/demo/mode -H "Content-Type: application/json" -d "{\"vulnerable_mode\": false, \"enable_security_headers\": true}"
   ```
   *(Response: `{"vulnerable_mode": false, "enable_security_headers": true, "message": "Demo API mode updated successfully"}`)*
2. In the dashboard sidebar, navigate to **"🔬 Retesting & Verification"**.
3. Select the scan and click **"🔬 Execute Retest Probe"**.
4. The testing engine re-probes `GET /api/patients/102` using `patient_a`'s credentials.
5. The probe receives **HTTP 403 Forbidden**.
6. Watch the status transition dynamically:
   - **Previous Status:** `Open`
   - **New Status:** `Resolved`
   - **Verified:** `True`
7. Scroll down to the **Retest Audit History** table:
   - Show the append-only chronological audit log preserving the exact timestamp, state transition, and probe response.

---

### Step 6: Generate Executive Audit Report (30 Seconds)
1. Navigate to **"📊 Reports & Compliance"**.
2. Show the real-time posture chart:
   - Health score increased.
   - Finding promoted to **Resolved**.
   - OWASP API Category distribution breakdown.
3. Summarize:
   > *"API Sentinel found the BOLA vulnerability, explained the impact with Nemotron AI, guided the developer to the fix, and proved the vulnerability was remediated with an immutable audit trail."*

---

## 4. Alternative: Docker Deployment Runbook

For a containerized demonstration:

```powershell
Set-Location "C:\PROJECTS\api-sentinel"
docker-compose up --build -d
```

- Backend: `http://localhost:8000`
- Demo API: `http://localhost:8001`
- Persistent SQLite Volume: `sentinel_data` (mapped to `/app/data/api_sentinel.db`)
- Health checks: Configured with 30s intervals and 5s timeouts.

To stop:
```powershell
docker-compose down
```
