# API Sentinel — Deployment & Operations Guide

## 1. System Architecture Overview

API Sentinel is structured into three interconnected tiers:
1. **Target Layer:** Controlled API targets (such as the included synthetic Healthcare Demo API on port `8001`).
2. **Core Security Engine & Backend:** FastAPI ASGI server (port `8000`) managing scan orchestration, Member 1 vulnerability detection, SSRF protection, SQLite WAL persistence, and NVIDIA Nemotron AI integration.
3. **User Interface Deck:** React 18 single-page application with 9 cybersecurity views, Server-Sent Events (SSE) telemetry, and in-app alert modals.

---

## 2. Windows Automated Deployment (Recommended)

Three production-tested PowerShell launch scripts are provided in the repository root:

### Option A: Development Mode (Vite Dev Server + Hot Reloading)
```powershell
Set-Location 'C:\PROJECTS\api-sentinel'
.\start-development.ps1
```
* **Ports Used:**
  * Port `5173`: React Vite Development Dashboard (`http://127.0.0.1:5173/`)
  * Port `8000`: FastAPI Core Backend & Swagger Docs (`http://127.0.0.1:8000/docs`)
  * Port `8001`: Healthcare Demo API (`http://127.0.0.1:8001/health`)
* **Behavior:** Checks Python and Node prerequisites, verifies port availability, starts all 3 services, and tracks PIDs in `.sentinel_pids.json`.

### Option B: Production Mode (Compiled Single-Origin Deployment)
```powershell
Set-Location 'C:\PROJECTS\api-sentinel'
.\start-production.ps1
```
* **Ports Used:**
  * Port `8000`: FastAPI Production Server serving the compiled React frontend directly at root (`http://127.0.0.1:8000/`)
  * Port `8001`: Healthcare Demo API (`http://127.0.0.1:8001/health`)
* **Behavior:** Executes `npm run build` in `frontend/`, syncs assets to `backend/frontend/dist/`, and launches the core server without needing any separate frontend web server process.

### Option C: Clean Shutdown
```powershell
Set-Location 'C:\PROJECTS\api-sentinel'
.\stop-api-sentinel.ps1
```
* **Behavior:** Reads tracked PIDs and gracefully terminates only API Sentinel processes. Re-checks ports `8000`, `8001`, and `5173` to ensure zero lingering background processes remain, while never touching unrelated user processes.

---

## 3. Containerized Docker Deployment

### Prerequisites
- Docker Desktop 24+ with Docker Compose v2+

### Launch via Docker Compose
```bash
cd C:\PROJECTS\api-sentinel
docker compose up -d --build
```

### Inspect Running Containers
```bash
docker compose ps
```
Expected output:
```text
NAME                     IMAGE                  COMMAND                  SERVICE      STATUS      PORTS
api_sentinel_backend     api-sentinel-backend   "uvicorn app.main:ap…"   backend      Up          0.0.0.0:8000->8000/tcp
api_sentinel_demo_api    api-sentinel-backend   "uvicorn demo_api.ma…"   demo-api     Up          0.0.0.0:8001->8001/tcp
```

### Verify Container Health
```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health
```

### Data Persistence in Docker
All scan history, vulnerability findings, and cached AI explanations are persisted inside the named volume `sentinel_data` (`/app/data/api_sentinel.db`). Rebuilding or recreating containers preserves all historical audit data.

---

## 4. Environment Variables Reference

| Variable | Default Value | Production Recommendation | Description |
|---|---|---|---|
| `ENVIRONMENT` | `development` | `production` | Set to `production` to disable debug tracebacks |
| `DEBUG` | `True` | `False` | Disables verbose debug logging |
| `PORT` | `8000` | `8000` | Port for FastAPI core server |
| `HOST` | `0.0.0.0` | `0.0.0.0` | Bind address |
| `DATABASE_URL` | `sqlite:///./api_sentinel.db` | `sqlite:////app/data/api_sentinel.db` | SQLite connection string with WAL mode |
| `ALLOW_LOCAL_LAB_SCANNING` | `False` | `False` | Must remain `False` in production to prevent SSRF against internal subnets |
| `NVIDIA_API_KEY` | *(empty string)* | User API Key | NVIDIA Nemotron API authentication token |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | `https://integrate.api.nvidia.com/v1` | OpenAI-compatible endpoint |
| `NVIDIA_MODEL` | `nvidia/nemotron-3.5-lightning-30b-a3b` | `nvidia/nemotron-3.5-lightning-30b-a3b` | Model identifier |
| `AI_TIMEOUT_SECONDS` | `30` | `30` | Timeout before failover to offline rule engine |
