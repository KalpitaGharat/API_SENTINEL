# API Sentinel — Phase 6 Security & SSRF Hardening Report

## Executive Summary

API Sentinel performs automated vulnerability testing against user-specified API targets. Because this involves issuing outbound network requests on behalf of users, strict defenses against Server-Side Request Forgery (SSRF), DNS rebinding, internal network reconnaissance, and credential leakage are paramount.

This security evaluation confirms that all 18 security controls pass automated regression tests with zero exceptions.

---

## 1. Network & SSRF Defenses (`ssrf_guard.py` & `http_client.py`)

| Threat Vector | Defense Mechanism | Automated Test | Status |
|---|---|---|---|
| **DNS Rebinding Attacks** | Pre-resolves target hostname and pins the exact IP address for the HTTP connection. Re-resolution is blocked during request lifecycle. | `test_dns_rebinding_simulation_prevented` | **VERIFIED BLOCKED** |
| **Cloud Metadata Theft** | Strictly blocks requests targeting link-local metadata addresses (`169.254.169.254`, `fd00:ec2::254`, `metadata.google.internal`). | `test_cloud_metadata_endpoints_strictly_blocked` | **VERIFIED BLOCKED** |
| **Alternate IP Encodings** | Validates decimal (`2130706433`), hex (`0x7f000001`), octal, and mapped IPv6 formats before resolution. | `test_decimal_and_hex_ip_representations` | **VERIFIED BLOCKED** |
| **Internal Subnet Probing** | RFC 1918 private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`) are blocked by default. Only enabled when `ALLOW_LOCAL_LAB_SCANNING=True` is explicitly configured for educational demos. | `test_private_ips_blocked_by_default_allowed_in_lab` | **VERIFIED ENFORCED** |
| **Unspecified Address (0.0.0.0)** | Explicitly blocked even in educational lab mode to prevent host bind exploits. | `test_unspecified_address_rejected_even_in_lab_mode` | **VERIFIED BLOCKED** |
| **HTTPS-to-HTTP Downgrade** | Rejects redirects from secure `https://` endpoints to insecure `http://` targets. | `test_redirect_https_to_http_downgrade_rejected` | **VERIFIED BLOCKED** |
| **Redirect Loops & Max Hops** | Restricts redirection chains to a maximum of 3 hops and terminates circular redirect paths. | `test_redirect_loop_detected`, `test_max_redirect_hops_enforced` | **VERIFIED ENFORCED** |
| **Cross-Origin Credential Leak** | Strips `Authorization`, `Cookie`, and custom token headers if an authorized endpoint redirects across origins. | `test_cross_origin_redirect_strips_sensitive_headers` | **VERIFIED STRIPPED** |
| **Synthetic Token Guard** | Refuses to transmit synthetic healthcare demo credentials to unapproved external targets. | `test_synthetic_credentials_refused_on_external_targets` | **VERIFIED ENFORCED** |

---

## 2. Data Protection & Secret Hygiene

1. **Credential Redaction in SQLite**:
   All user-supplied tokens, passwords, and authorization headers submitted via `ScanCreateRequest` are recursively sanitized and stored as `[REDACTED_FOR_SECURITY]` in `api_sentinel.db`. Non-sensitive configuration headers (`Content-Type`, `Accept`) are preserved intact.
2. **Zero Client Secrets**:
   NVIDIA Nemotron API keys reside exclusively in the FastAPI server environment (`.env`). No API keys or tokens are included in the React frontend bundle (`frontend/dist`).
3. **Database Injection Resistance**:
   All database operations utilize SQLAlchemy 2.0 parameterized queries and ORM objects. Raw string concatenation is prohibited across all services.
4. **Sanitized Error Messaging**:
   Internal exception tracebacks are logged on the server and replaced with structured, sanitized HTTP error envelopes (`HTTP 400`, `HTTP 404`, `HTTP 422`, `HTTP 500`) to prevent internal path and library disclosure.
