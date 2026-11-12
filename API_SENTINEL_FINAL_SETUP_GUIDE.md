# API Sentinel — Final Setup & Operational Launch Guide

## Quick Start (Run Locally)

### Prerequisites
- Python 3.11 – 3.13 installed
- Node.js 18+ and npm installed
- Google Chrome (or modern Chromium browser)

---

## 1. Environment Configuration

Copy the example environment file:
```bash
cd C:\PROJECTS\api-sentinel\backend
copy .env.example .env
```

Ensure `.env` contains the required settings:
```ini
ENVIRONMENT=development
DEBUG=True
PORT=8000
HOST=0.0.0.0
DATABASE_URL=sqlite:///./api_sentinel.db
ALLOW_LOCAL_LAB_SCANNING=True

# NVIDIA Nemotron AI
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
AI_TIMEOUT_SECONDS=30
```

---

## 2. Launching All Services (3 Terminals)

### Terminal 1: Launch the Healthcare Demo API (Port 8001)
```powershell
cd C:\PROJECTS\api-sentinel
python -m uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```
*Health Check:* `http://127.0.0.1:8001/health`

### Terminal 2: Launch the FastAPI Backend (Port 8000)
```powershell
cd C:\PROJECTS\api-sentinel\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*Health Check:* `http://127.0.0.1:8000/api/health`

### Terminal 3: Launch the React Dashboard (Port 5173)
```powershell
cd C:\PROJECTS\api-sentinel\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
*Browser URL:* `http://127.0.0.1:5173/`

*(Alternatively, access `http://127.0.0.1:8000/` directly — the FastAPI backend serves the compiled production build!)*

---

## 3. Complete Demonstration Workflow

Follow this 5-step workflow to demonstrate the full capabilities of API Sentinel:

```
Step 1: AUDIT           Step 2: EXPLAIN          Step 3: ALERT           Step 4: REMEDIATE       Step 5: VERIFY
Launch Scan on   ───►  Analyze Findings   ───►  Review In-App    ───►  Switch Demo API  ───►  Run Verification
Port 8001              with Nemotron AI         Critical Modal         to Secure Mode         Targeted Retest
```

1. **Launch a Security Scan:**
   - In the dashboard, click **`New Security Scan`**.
   - Target URL is pre-filled: `http://127.0.0.1:8001`.
   - Click **`Launch Security Audit`**. Watch real-time scan progress update live via SSE without page refreshing.
2. **Explore AI Explainability:**
   - Click **`AI Security Analysis`** in the sidebar.
   - Select the detected **Broken Object Level Authorization (BOLA)** finding.
   - Click **`✨ Explain with Nemotron AI`** to view the 3 analysis tabs (Breakdown, Threat Scenarios, Remediation Code).
3. **Inspect Critical Alerts:**
   - Open the **`Notifications`** tab or click the header bell icon to review real-time security alerts and acknowledge them.
4. **Demonstrate Remediation & Retesting:**
   - Switch the demo API to Secure Mode (via PowerShell):
     ```powershell
     Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/demo/mode' -Method POST -Body '{"vulnerable":false,"enable_security_headers":true}' -ContentType 'application/json'
     ```
   - In the dashboard, navigate to **`Verification & Retesting`**.
   - Click **`Run Targeted Retest`**.
   - Watch the status dynamically change from `Still Vulnerable` to `Resolved`!
5. **Generate Compliance Report:**
   - Click **`Security Reports`** to inspect the executive summary and compliance scorecards.

---

## 4. Docker Deployment (Optional)

To launch the complete platform inside containers:
```bash
cd C:\PROJECTS\api-sentinel
docker compose up -d --build
```
- Core Backend & Frontend: `http://localhost:8000/`
- Healthcare Demo API: `http://localhost:8001/`
- Persistent Volume: `sentinel_data`
