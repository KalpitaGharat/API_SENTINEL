# API SENTINEL — INSTALLATION & SETUP GUIDE

**Product:** API Sentinel  
**Version:** v1.1.0 (Release Candidate)  
**Tagline:** *Find it. Understand it. Fix it. Verify it.*  
**Target Environments:** Windows 10/11 x64, macOS (Apple Silicon / Intel), Ubuntu Linux 22.04+ LTS

---

## 1. PREREQUISITES & SYSTEM REQUIREMENTS

Before installing API Sentinel, ensure your system meets the following software prerequisites:

| Component | Minimum Version | Recommended Version | Verification Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | 3.11 or 3.13 | `python --version` |
| **Node.js** | 18.0+ | 20.x LTS | `node --version` |
| **npm** | 9.0+ | 10.x | `npm --version` |
| **Git** | 2.30+ | Latest | `git --version` |
| **Docker** (Optional) | 24.0+ | 26.x+ with Compose v2 | `docker --version` |

---

## 2. REPOSITORY & PACKAGE EXTRACTION

### Option A: From Git Repository
```bash
git clone https://github.com/your-org/api-sentinel.git
cd api-sentinel
git checkout feature/api-key-dataset
```

### Option B: From Release Candidate Archive (`API_Sentinel_v1.1.0_Release_Candidate.zip`)
```bash
unzip API_Sentinel_v1.1.0_Release_Candidate.zip -d api-sentinel
cd api-sentinel
```

---

## 3. BACKEND SETUP & CONFIGURATION

### Step 1: Create Virtual Environment
```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Generate a secure 32-byte Fernet key for the credential vault:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Edit `.env` and set:
```ini
ENVIRONMENT=development
DEBUG=True
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000
DATABASE_URL=sqlite:///./api_sentinel.db
ALLOW_LOCAL_LAB_SCANNING=True
TARGET_CREDENTIAL_ENCRYPTION_KEY=<PASTE_GENERATED_KEY_HERE>
NVIDIA_API_KEY=
```

---

## 4. FRONTEND SETUP & BUILD

```bash
cd ../frontend
npm install
npm run build
```
The compiled, production-ready static assets are written to `frontend/dist/`.

---

## 5. STARTING THE FULL PLATFORM

### Quick Start (Windows PowerShell)
From the project root:
```powershell
.\start-development.ps1
```
This automatically starts:
1. Healthcare Demo API (`http://127.0.0.1:8001`)
2. FastAPI Backend Engine (`http://127.0.0.1:8000`)
3. React Cyber Dark Dashboard (`http://127.0.0.1:5173`)
4. Streamlit Analytics Hub (`http://127.0.0.1:8501`)

### Manual Startup (Cross-Platform)

**Terminal 1 — Healthcare Demo API (Local Lab Target):**
```bash
python -m uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```

**Terminal 2 — FastAPI Core Engine:**
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 3 — React Dashboard:**
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 6. VERIFYING INSTALLATION

Run the automated verification suite to validate everything:

```bash
# 1. Backend test suite (125 tests)
cd backend
python -m pytest -c pytest.ini -q

# 2. Frontend test suite (10 tests)
cd ../frontend
npm test

# 3. Live end-to-end regression
cd ..
python backend/tests/run_live_regression.py
```
Open your browser to `http://127.0.0.1:5173` to access API Sentinel.
