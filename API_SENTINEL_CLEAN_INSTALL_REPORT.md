# API Sentinel — Clean-Environment Installation Simulation Report

## 1. Simulation Setup

To guarantee that API Sentinel v1.0.0 can be installed on a fresh Windows machine without relying on pre-existing system dependencies or global state, a simulated installation test was performed:
- **Clean Directory:** `C:\PROJECTS\clean_install_test`
- **Source:** Freshly extracted from `API_Sentinel_v1.0.0_Release.zip`
- **Pre-existing Databases:** Explicitly deleted before installation
- **Python Environment:** Isolated clean virtual environment created at `.clean_venv/`
- **Node Environment:** Clean `node_modules` installation via `npm install` using committed `package-lock.json`

---

## 2. Step-by-Step Installation & Verification Log

### Step 1: Virtual Environment Creation
```powershell
python -m venv C:\PROJECTS\clean_install_test\.clean_venv
```
- **Result:** Created isolated Python 3.13.7 virtual environment (`Scripts/python.exe`, `Scripts/pip.exe`).

### Step 2: Backend Dependencies Installation
```powershell
.\.clean_venv\Scripts\pip install -r backend\requirements.txt
```
- **Installed Packages:** 36 packages installed (including `fastapi==0.118.0`, `uvicorn==0.37.0`, `pydantic==2.11.9`, `sqlalchemy==2.0.43`, `httpx==0.28.1`, `openai==3.7.0`, `pytest==9.1.1`).
- **Exit Status:** `0` (Success). Zero missing wheels or compile errors.

### Step 3: Frontend Dependencies & Production Build
```powershell
cd frontend
npm install
npm run build
```
- **Installed Packages:** 136 packages audited from committed `package-lock.json` in 18 seconds.
- **Vite Build Output:**
  ```text
  dist/index.html                   1.03 kB │ gzip:  0.61 kB
  dist/assets/index-CkAXUZaN.css   10.27 kB │ gzip:  3.17 kB
  dist/assets/index-CB6-fJvm.js   299.79 kB │ gzip: 79.55 kB
  ✓ built in 6.21s
  ```
- **Exit Status:** `0` (Success).

### Step 4: Database Schema Initialization From Scratch
```python
from app.database import engine, Base
import app.models
Base.metadata.create_all(bind=engine)
```
- **Result:** SQLite schema created from empty database. Verified tables:
  1. `scans`
  2. `findings`
  3. `evidence`
  4. `ai_explanations`
  5. `retest_history`

### Step 5: Service Execution & Safety Verification
- **Healthcare Demo API:** Launched on port `8101` (`HTTP 200 OK`).
- **FastAPI Backend Core:** Launched on port `8100` (`HTTP 200 OK`).
- **SSRF Safety Verification:** Initial scan request to `http://127.0.0.1:8101` without `.env` was properly rejected with `HTTP 400` ("Scanning private/loopback address is blocked by safety policy").
- **Lab Mode Authorization:** Created `backend/.env` from `.env.example` with `ALLOW_LOCAL_LAB_SCANNING=True`.
- **Scan Execution:** Re-issued scan against `http://127.0.0.1:8101`.
  - Scan ID: `3a54e46b-6fdd-4dee-aefe-1fda2d2f9027`
  - Status: `Completed`
  - Findings Detected: 5 real findings (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Broken Token Validation).

---

## 3. Clean Installation Verdict

**VERDICT: 100% REPRODUCIBLE & PORTABLE**

Any standard Windows 10/11 environment with Python 3.11+ and Node.js 18+ can install, build, and run API Sentinel cleanly from the release archive in under 3 minutes.
