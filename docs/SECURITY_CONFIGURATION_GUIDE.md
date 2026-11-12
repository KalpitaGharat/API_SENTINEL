# API SENTINEL — SECURITY CONFIGURATION & HARDENING GUIDE

**Product:** API Sentinel  
**Classification:** Application Security Architecture & Defense Guide  
**Version:** v1.1.0  
**Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. DEFENSE-IN-DEPTH ARCHITECTURE OVERVIEW

API Sentinel handles sensitive tasks—making outbound network requests, ingesting third-party specifications, and storing test credentials. Layered security defenses ensure the platform itself cannot be exploited or abused as an attack vector.

```
+-------------------------------------------------------------------------------------------------+
|                                 DEFENSE-IN-DEPTH LAYERS                                         |
|                                                                                                 |
|   LAYER 1: Ingestion Gate        - YAML Safe Loader, 5MB Size Ceiling, Ref Quarantine          |
|   LAYER 2: Credential Vault      - AES-128-CBC + HMAC-SHA256 (Fernet) Encryption at Rest       |
|   LAYER 3: Network Transport     - DNS Pre-resolution, IP Pinning, SSRF Blocklist (19 Vectors)   |
|   LAYER 4: Application Boundary  - Parameterized ORM Queries, Strict CORS Whitelist, Traversal |
+-------------------------------------------------------------------------------------------------+
```

---

## 2. HARDENED OUTBOUND TRANSPORT (SSRF DEFENSE)

Outbound scanning requests are mediated through `backend/app/security_engine/integration.py` using `SafeHTTPClient` and `PinnedHTTPTransport`.

### Blocked Target Destinations:
- **Cloud Metadata Services:**
  - AWS / Azure / DigitalOcean: `169.254.169.254` (IPv4) & `fd00:ec2::254` (IPv6)
  - Google Cloud: `metadata.google.internal`
- **Private RFC1918 Subnets (in production mode):**
  - `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- **Reserved & Special Purpose Addresses:**
  - Loopback (`127.0.0.0/8`, `::1`)
  - Link-Local (`169.254.0.0/16`, `fe80::/10`)
  - Multicast (`224.0.0.0/4`, `ff00::/8`)
  - Unspecified (`0.0.0.0`)
- **Dangerous URL Schemes:**
  - Only `http://` and `https://` are accepted. Schemes such as `file://`, `gopher://`, `ftp://`, or `dict://` are rejected immediately.
- **DNS Pinning Protection:**
  - Outbound requests resolve DNS addresses upfront and bind directly to the validated IP address, preventing Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks.

---

## 3. CREDENTIAL VAULT STORAGE & MASKING

Authentication tokens registered during target onboarding are managed by `backend/app/services/credential_vault.py`.

### Encryption Specification:
- **Cipher:** AES-128 in Cipher Block Chaining (CBC) mode.
- **Authentication & Integrity:** HMAC using SHA-256 with constant-time comparison.
- **Padding:** PKCS7 padding.
- **Key Requirement:** A 32-byte URL-safe base64 string configured via `TARGET_CREDENTIAL_ENCRYPTION_KEY`.
- **Zero Plaintext Storage:** Stored records in the `target_auth_profiles` table contain only encrypted ciphertexts (starting with `gAAAAA...`).
- **UI Masking:** Frontend responses display masked representations showing only the first 4 and last 3-4 characters (e.g., `sent..._101`), preventing credential leakage over shoulder-surfing or browser screenshots.

---

## 4. OPENAPI SPECIFICATION PARSER GUARDRAILS

To prevent Denial of Service (DoS) and Remote Entity Injection:
- **Payload Ceiling:** Ingestion rejects payloads exceeding **5,242,880 bytes (5 MB)**.
- **Safe Parsing:** Uses `yaml.safe_load` exclusively to prevent arbitrary Python object deserialization.
- **External `$ref` Quarantine:** Any remote schema references (e.g. `"$ref": "http://evil.com/schema.json"`) are intercepted, quarantined, and forbidden from executing outbound network fetches.

---

## 5. ENVIRONMENT VARIABLE AUDIT & CLASSIFICATION

| Variable Name | Classification | Requirement | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Public Config | Optional | `development` | Deployment environment (`development`, `staging`, `production`). |
| `DEBUG` | Public Config | Required | `False` (Prod) | Enables debug stack traces in dev; must be `False` in prod. |
| `PORT` | Public Config | Optional | `8000` | Port for FastAPI server. |
| `HOST` | Public Config | Optional | `0.0.0.0` | Bind IP for FastAPI server. |
| `CORS_ORIGINS` | Security Config | **Required** | Specific domains | Whitelist of allowed frontend origins. Never use `*`. |
| `DATABASE_URL` | Infrastructure | **Required** | `sqlite:///...` | SQLAlchemy connection string. |
| `ALLOW_LOCAL_LAB_SCANNING` | Security Control | **Critical** | `False` (Prod) | Allows scanning 127.0.0.1 in lab demo; must be `False` in production. |
| `TARGET_CREDENTIAL_ENCRYPTION_KEY` | **Secret** | **Critical** | None | 32-byte Base64 key for Fernet credential vault. |
| `NVIDIA_API_KEY` | **Secret** | Optional | None | API key for NVIDIA Nemotron LLM explanations. |
| `NVIDIA_BASE_URL` | Public Config | Optional | NVIDIA URL | Base endpoint for NVIDIA NIM completions. |
| `NVIDIA_MODEL` | Public Config | Optional | Nemotron 30b | Model identifier. |
| `AI_TIMEOUT_SECONDS` | Operational | Optional | `30` | Request timeout for outbound LLM calls. |
