# API SENTINEL – COMPLETE PLATFORM & INTEGRATION GUIDE

> **Tagline:** *Find it. Understand it. Fix it. Verify it.*  
> **Release Version:** `v1.0.0` (Production Stable)  
> **Target Audience:** Student Developers and Small Engineering Teams

---

## 1. Quick Launch Scripts (Windows)

API Sentinel includes automated launch scripts that check prerequisites, verify port availability, and manage service lifecycles cleanly:

```powershell
# 1. Start Development Environment (Vite 5173 + FastAPI 8000 + Demo API 8001)
.\start-development.ps1

# 2. Start Production Environment (Compiles React frontend & mounts on FastAPI 8000 + Demo API 8001)
.\start-production.ps1

# 3. Clean Shutdown (Safely terminates all API Sentinel processes)
.\stop-api-sentinel.ps1
```

### Access URLs
- **React Dashboard (Vite Dev):** `http://127.0.0.1:5173/`
- **FastAPI Production Direct Mount:** `http://127.0.0.1:8000/` *(serves production dashboard at `/`)*
- **API Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
- **Healthcare Demo API:** `http://127.0.0.1:8001/health`

---

## 2. Project Overview

**API Sentinel** is an explainable API security testing and remediation platform designed specifically for student developers and small business engineering teams. It empowers developers to:
1. **Find** critical API security weaknesses (BOLA/IDOR, Broken Authentication, Missing Security Headers, API Misconfigurations).
2. **Understand** vulnerabilities through concrete technical evidence (observed HTTP telemetry vs. expected security behavior) and AI-assisted explanations powered by **NVIDIA Nemotron**.
3. **Fix** vulnerabilities using actionable code-level remediation patterns.
4. **Verify** fixes via targeted retesting to confirm that vulnerabilities are genuinely mitigated before deploying to production.

---

## 2. Technology Stack

- **Framework:** FastAPI (0.118+) & Uvicorn ASGI
- **Data Validation & Typing:** Pydantic v2 & Pydantic-Settings
- **ORM & Database:** SQLAlchemy 2.0 with persistent SQLite storage
- **AI Integration:** NVIDIA Nemotron LLM (OpenAI-compatible client with intelligent rule-based fallback)
- **HTTP Client & Security:** HTTPX
- **Testing:** Pytest & Pytest-Asyncio
- **Containerization:** Docker & Docker Compose
- **Configuration:** Python-dotenv & environment-driven settings

---

## 3. Backend Architecture & Workflow

```
       ┌───────────────────────────────┐
       │   Streamlit Frontend (M2)     │
       └──────────────┬────────────────┘
                      │ JSON / REST
                      ▼
       ┌───────────────────────────────┐
       │     FastAPI Backend (M3)      │
       │  (Routes, Authz, Validation)  │
       └──────┬───────────────┬────────┘
              │               │
       ┌──────▼──────┐ ┌──────▼────────┐ ┌────────────────────────┐
       │   SQLite    │ │ NVIDIA AI     │ │ Security Engine (M1)   │
       │ Persistence │ │ (Nemotron-3)  │ │ (BOLA, Auth, Headers)  │
       └─────────────┘ └───────────────┘ └────────────────────────┘
```

### Main Workflow
1. User enters an API URL and confirms testing authorization in the Streamlit frontend.
2. Frontend sends scan configuration to `POST /api/scans`.
3. Backend validates safety rules (SSRF mitigation, private IP policy).
4. Backend invokes Member 1's Security Testing Engine.
5. Structured findings and technical evidence are saved to SQLite.
6. User inspects findings and can click **"Explain with Nemotron"** (`POST /api/findings/{id}/explain`).
7. AI generates plain-English explanations, threat impact, and remediation steps. Explanations are cached in SQLite.
8. Developer applies fixes to their API and triggers **"Retest"** (`POST /api/scans/{id}/retest`).
9. Security engine re-tests the endpoint, comparing against the original baseline.
10. Updated verification status (`Resolved` vs. `Still Vulnerable`) and audit history are recorded.
11. Complete security report can be fetched via `GET /api/scans/{id}/report`.

---

## 4. Directory Structure

```
api-sentinel/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entrypoint & middleware
│   │   ├── config.py                   # Centralized Pydantic settings & env management
│   │   ├── database.py                 # SQLAlchemy engine, session maker, get_db
│   │   ├── models.py                   # Database models (Scan, Finding, Evidence, etc.)
│   │   ├── schemas.py                  # Pydantic schemas for requests/responses
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── scans.py                # POST /scans, GET /scans, GET /scans/{id}
│   │   │   ├── findings.py             # GET /findings/{id}, POST /findings/{id}/explain
│   │   │   ├── retesting.py            # POST /scans/{id}/retest
│   │   │   └── reports.py              # GET /scans/{id}/report
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scan_service.py         # Scan coordination & telemetry persistence
│   │   │   ├── ai_service.py           # Nemotron integration & rule fallback
│   │   │   ├── retest_service.py       # Verification & retesting comparison engine
│   │   │   └── report_service.py       # Metric aggregation & report synthesis
│   │   │
│   │   └── security_engine/
│   │       ├── __init__.py
│   │       └── integration.py          # Member 1 adapter interface & mock harness
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Fixtures & DB isolation
│   │   └── test_endpoints.py           # 9 unit & integration tests
│   │
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 5. Setup & Installation

### Prerequisites
- Python 3.11+
- Git

### 1. Configure Environment
Navigate to `backend/` and copy `.env.example` to `.env`:
```powershell
cd backend
Copy-Item .env.example .env
```

Edit `.env` to configure your settings:
```ini
ENVIRONMENT=development
DEBUG=True
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
DATABASE_URL=sqlite:///./api_sentinel.db
ALLOW_LOCAL_LAB_SCANNING=True

# NVIDIA Nemotron LLM Configuration
NVIDIA_API_KEY=your_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
AI_TIMEOUT_SECONDS=30
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the FastAPI Server
```powershell
uvicorn app.main:app --app-dir . --host 0.0.0.0 --port 8000 --reload
```
The server will start at `http://localhost:8000`.  
Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

---

## 6. REST API Endpoints Specification

### System Health
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Basic operational health check |
| `GET` | `/api/health` | Comprehensive API & database connectivity check |

### Scan Management
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scans` | Start new scan with target validation and safety verification |
| `GET` | `/api/scans` | List scan history (supports `skip`, `limit`, `status` query params) |
| `GET` | `/api/scans/{scan_id}` | Retrieve individual scan metadata |
| `GET` | `/api/scans/{scan_id}/findings` | Retrieve all findings and evidence for a scan |

#### Example: Start Scan Request (`POST /api/scans`)
```json
{
  "target_url": "https://api.student-lab.local",
  "user_authorized": true,
  "categories": ["BOLA", "AUTH", "HEADERS", "CONFIG"],
  "auth_token": "optional_bearer_token"
}
```
*Note: `user_authorized` must be `true`. If `false`, the request is rejected with HTTP 422.*

### Finding Details & Explainability
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/findings/{finding_id}` | Retrieve finding details with evidence |
| `POST` | `/api/findings/{finding_id}/explain` | Request NVIDIA Nemotron explanation (cached in SQLite) |

#### Example: Explain Finding Response (`POST /api/findings/{id}/explain`)
```json
{
  "id": "exp-9921-abc",
  "finding_id": "fnd-1234-xyz",
  "explanation": "Broken Object Level Authorization (BOLA/IDOR) occurs on GET /api/patients/{id}...",
  "impact": "High risk of massive data breaches and student privacy violations...",
  "remediation": "1. Extract user_id from token claims.\n2. Query using compound filters: SELECT * FROM records WHERE id = :id AND owner_id = :uid",
  "model_name": "nvidia/nemotron-3.5-lightning-30b-a3b",
  "created_at": "2026-11-07T12:00:00Z",
  "is_ai_generated": true
}
```

### Retesting & Verification
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scans/{scan_id}/retest` | Re-test findings to verify remediation |

#### Request (`POST /api/scans/{id}/retest`):
```json
{
  "finding_id": "fnd-1234-xyz"
}
```
*(Leave empty to re-test all open findings in the scan).*

### Security Reports
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/scans/{scan_id}/report` | Retrieve aggregated report with metrics and history |

---

## 7. Running Tests

Run the test suite using pytest:
```powershell
cd backend
pytest -v
```

All 9 core tests verify:
- Backend health endpoints (`/health`, `/api/health`).
- Authorization confirmation enforcement (fails when `user_authorized=False`).
- URL scheme validation (rejects invalid schemes like `ftp://`).
- SSRF prevention (strictly blocks AWS/GCP cloud metadata IP `169.254.169.254`).
- Full scan creation, evidence storage, and credential sanitization.
- Scan history pagination and status filtering.
- AI explanation generation, fallback handler, and SQLite caching.
- Retesting verification workflow (`Still Vulnerable` vs. `Resolved`).
- Full security report aggregation and severity metric calculations.

---

## 8. Docker Deployment

### Run with Docker Compose
```bash
docker-compose up --build -d
```
The backend will be running on port `8000` with persistent SQLite volume mounted.

---

## 9. Security Engine Integration (For Member 1)

Member 1's engine integrates directly via `app.security_engine.integration`:
- An abstract base class `BaseSecurityEngineAdapter` defines the expected contract:
  - `run_scan(target_url, config) -> List[FindingCreate]`
  - `retest_finding(target_url, finding_data, config) -> Dict[str, Any]`
- When Member 1 provides `member1_engine.py`, the factory function `get_security_engine()` automatically binds it.
- Until then, the isolated `MockSecurityEngineAdapter` provides realistic simulated findings for frontend and backend integration.

---

## 10. AI Safety & Responsible Disclosure Rules

1. **Authorization is Mandatory:** API Sentinel must only be used on APIs the user owns or has explicit written authorization to test.
2. **SSRF Guard:** Cloud metadata IP ranges (`169.254.169.254`) and unauthorized internal network sweeps are blocked by default.
3. **No Secret Storage:** Passwords, private tokens, and API keys are redacted prior to SQLite persistence.
4. **AI Separation of Concerns:**
   - The Security Engine **alone** decides whether a vulnerability is present or resolved.
   - NVIDIA Nemotron **only explains** verified findings and provides remediation advice.
   - AI outputs are explicitly labeled (`is_ai_generated: true`) and never overwrite raw scan telemetry.
