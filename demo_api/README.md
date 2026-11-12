# INTENTIONALLY VULNERABLE HEALTHCARE DEMO API

> **Purpose:** Local testbed for API Sentinel vulnerability scanning and remediation verification.  
> **Safety:** Uses **100% synthetic mock patient data**. Never store or process real PII or medical data.

---

## 1. Quick Start

Run the Demo API with Uvicorn on port 8001:

```powershell
# Start in Vulnerable Mode (BOLA enabled by default)
$env:DEMO_VULNERABLE_MODE="true"
uvicorn demo_api.main:app --port 8001 --reload
```

To start in Secure / Remediated Mode:
```powershell
$env:DEMO_VULNERABLE_MODE="false"
uvicorn demo_api.main:app --port 8001 --reload
```

Swagger UI documentation: `http://localhost:8001/docs`  
Health check: `http://localhost:8001/health`

---

## 2. Test Accounts & Ownership Matrix

| Account | User ID | Username | Password | Owns Record ID |
|---|---|---|---|---|
| **Patient A** | 101 | `patient_a` | `demo_password_a` | 101 |
| **Patient B** | 102 | `patient_b` | `demo_password_b` | 102 |

---

## 3. Vulnerability Behaviors

### BOLA / IDOR on `GET /api/patients/{patient_id}`:
- **Vulnerable Mode (`DEMO_VULNERABLE_MODE=true`):**  
  Patient A logs in, receives token, and requests `GET /api/patients/102`.  
  The API returns Patient B's diagnosis and prescription with **HTTP 200 OK**.
- **Secure Mode (`DEMO_VULNERABLE_MODE=false`):**  
  Patient A requests `GET /api/patients/102`.  
  The server verifies ownership and returns **HTTP 403 Forbidden**.

### Runtime Mode Toggle:
You can also toggle the demo mode dynamically via HTTP without restarting:
```bash
curl -X POST http://localhost:8001/api/demo/mode \
  -H "Content-Type: application/json" \
  -d '{"vulnerable": false, "enable_security_headers": true}'
```
