# API SENTINEL — LOCAL SETUP & DEPLOYMENT GUIDE
**Execution Instructions for Local Subsystems and Docker Environments**

- **Date:** November 12, 2026
- **Repository:** `C:\PROJECTS\api-sentinel`
- **Protected Baseline Git Commit:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93`
- **Target Systems:** Windows, Linux, macOS, Docker

---

## 1. System Architecture Overview

API Sentinel comprises four primary local network services:

| Subsystem | Port | Technology | Primary Role |
| :--- | :--- | :--- | :--- |
| **Healthcare Demo API** | `8001` | FastAPI / Uvicorn | Controlled local vulnerable API target |
| **FastAPI Backend** | `8000` | FastAPI / Uvicorn / SQLAlchemy | Core DAST scanning, vault & persistence |
| **React Frontend** | `5173` | React 18 / Vite 5 | Primary 9-section cybersecurity dashboard |
| **Streamlit Dashboard** | `8501` | Streamlit 1.39 | Secondary dataset exploration & reports |

---

## 2. Prerequisites

- **Python**: 3.11, 3.12, or 3.13
- **Node.js**: v18 or v20+ with npm
- **Docker** *(Optional)*: Docker Engine 24+ & Docker Compose v2

---

## 3. Local Native Startup (Step-by-Step)

### Step 1: Environment Configuration
Copy `.env.example` to `.env` in `backend/`:
```bash
# In backend/.env:
DATABASE_URL=sqlite:///./sentinel.db
SECRET_KEY=change-me-to-a-secure-random-32-byte-string
FERNET_KEY=YOUR_BASE64_32_BYTE_FERNET_KEY=
NVIDIA_API_KEY=optional_nemotron_key
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501
```

### Step 2: Install Dependencies
```bash
# Python backend & demo API
cd C:\PROJECTS\api-sentinel
pip install -r backend/requirements.txt

# React frontend
cd C:\PROJECTS\api-sentinel\frontend
npm install
```

### Step 3: Launch Services in Separate Terminals

#### Terminal 1 — Healthcare Demo API (Port 8001)
```powershell
Set-Location 'C:\PROJECTS\api-sentinel'
python -m uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```

#### Terminal 2 — FastAPI Backend (Port 8000)
```powershell
Set-Location 'C:\PROJECTS\api-sentinel\backend'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

#### Terminal 3 — React Frontend (Port 5173)
```powershell
Set-Location 'C:\PROJECTS\api-sentinel\frontend'
npm run dev -- --host 127.0.0.1 --port 5173
```

#### Terminal 4 — Streamlit Dashboard (Port 8501)
```powershell
Set-Location 'C:\PROJECTS\api-sentinel'
python -m streamlit run dashboard/app.py --server.port 8501 --server.headless true
```

---

## 4. Docker Deployment

API Sentinel includes a containerized deployment configuration:

```bash
cd C:\PROJECTS\api-sentinel
docker compose up --build -d
```

### Services Defined in `docker-compose.yml`:
1. `backend`: FastAPI API engine exposing port `8000`.
2. `frontend`: Nginx serving the compiled Vite production bundle on port `80` (mapped to `5173`).
3. `demo-api`: Synthetic healthcare target on port `8001`.
4. `dashboard`: Streamlit interactive explorer on port `8501`.

---

## 5. Health Verification Commands

```powershell
# Check Backend Health
curl -s http://127.0.0.1:8000/health

# Check Demo API Health
curl -s http://127.0.0.1:8001/health

# Check Frontend Availability
curl -s http://127.0.0.1:5173

# Check Streamlit Health
curl -s http://127.0.0.1:8501/_stcore/health
```

---

## 6. Production Frontend Build
To test the production build bundle:
```bash
cd C:\PROJECTS\api-sentinel\frontend
npm run build
```
The output is generated into `frontend/dist/` with optimized chunking and no source code leakage.
