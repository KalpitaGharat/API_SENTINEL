# API SENTINEL — DEPLOYMENT & INFRASTRUCTURE GUIDE

**Product:** API Sentinel  
**Version:** v1.1.0  
**Target Architecture:** Docker / Docker Compose / Containerized Microservices / Reverse Proxy  
**Official Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. PRODUCTION DEPLOYMENT TOPOLOGY

In a production environment, API Sentinel should be deployed behind a TLS-terminating reverse proxy (such as Nginx, Caddy, or Cloudflare).

```
+-----------------------------------------------------------------------------------------------+
|                                    PRODUCTION INGRESS                                         |
|                                                                                               |
|                                  [ Internet / Clients ]                                       |
|                                            |                                                  |
|                                   HTTPS :443 (TLS 1.3)                                        |
|                                            v                                                  |
|                            +-------------------------------+                                  |
|                            |    Reverse Proxy / Ingress    |                                  |
|                            |   (Nginx / Caddy / Traefik)   |                                  |
|                            +---------------+---------------+                                  |
|                                            |                                                  |
+--------------------------------------------|--------------------------------------------------+
                                             |
                   +-------------------------+-------------------------+
                   | Proxy /api to :8000                               | Static Web Files :80
                   v                                                   v
+-------------------------------------+             +-------------------------------------+
|      api_sentinel_backend           |             |       React Frontend (SPA)          |
|   - FastAPI ASGI Application        |             |   - Nginx hosting frontend/dist     |
|   - Non-Root User (UID 1000)        |             |   - Cyber Dark Dashboard            |
|   - AES-128 Fernet Credential Vault |             +-------------------------------------+
|   - Pinned HTTP Transport (SSRF)    |
|   - Persistent SQLite Volume        |
+------------------+------------------+
                   |
                   v
       [ /app/data/api_sentinel.db ]
```

---

## 2. DOCKER COMPOSE DEPLOYMENT

The repository includes a ready-to-run `docker-compose.yml` file defining containerized microservices:

### Step 1: Prepare Environment File
Create a production `.env` in the project root:
```ini
ENVIRONMENT=production
DEBUG=False
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=https://sentinel.yourdomain.com
DATABASE_URL=sqlite:////app/data/api_sentinel.db
ALLOW_LOCAL_LAB_SCANNING=False
TARGET_CREDENTIAL_ENCRYPTION_KEY=<SECURE_32_BYTE_BASE64_KEY>
NVIDIA_API_KEY=<OPTIONAL_NVIDIA_KEY>
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
```

### Step 2: Build & Start Containers
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
docker compose logs backend
```

---

## 3. SECURITY CONFIGURATION CHECKLIST FOR PRODUCTION

Before exposing API Sentinel to external networks, ensure these critical settings are applied:

1. **`ALLOW_LOCAL_LAB_SCANNING=False` (MANDATORY):**
   Strictly enforces SSRF blocking against all private RFC1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback addresses, link-local, and cloud metadata (`169.254.169.254`).
2. **`DEBUG=False` (MANDATORY):**
   Disables verbose tracebacks in HTTP 500 error responses, preventing server stack trace disclosures.
3. **`CORS_ORIGINS` Whitelist (MANDATORY):**
   Set explicitly to the exact domain names of your authorized frontend. Never use wildcard `*`.
4. **`TARGET_CREDENTIAL_ENCRYPTION_KEY` (MANDATORY):**
   Must be set to a cryptographically secure 32-byte URL-safe base64 key generated outside version control.
5. **Non-Root Execution:**
   The `Dockerfile` creates and runs as unprivileged user `sentinel` (UID 1000), following the principle of least privilege.

---

## 4. DATABASE BACKUP & RESTORATION

API Sentinel persists scan sessions, findings, authorization profiles, and retest logs in SQLite with WAL mode enabled.

### Live Backup Command (Zero-Downtime)
```bash
# Using SQLite backup API or CLI safe copy:
sqlite3 /app/data/api_sentinel.db ".backup '/app/data/backups/api_sentinel_backup_$(date +%Y%m%d_%H%M%S).db'"
```

### Restoration
1. Stop the backend service: `docker compose stop backend`
2. Replace `/app/data/api_sentinel.db` with the backup file.
3. Start the service: `docker compose start backend`
