# API Sentinel — Security Verification & Vulnerability Audit Report

**Date:** November 11, 2026  
**Auditor:** Senior Application Security Engineer & DevSecOps Specialist  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Target Assessed:** API Sentinel Platform + Healthcare Demo API Target  
**Scope:** SSRF Hardening, TOCTOU / DNS Rebinding Prevention, BOLA Detection, Credential Protection, and Verification Lifecycle

---

## 1. Executive Summary

This security audit report provides technical verification of the security controls engineered into the API Sentinel platform. As an active security scanning platform, API Sentinel must not only discover vulnerabilities in target APIs, but must also ensure that its own testing engine cannot be coerced into launching Server-Side Request Forgery (SSRF), leaking credentials to untrusted hosts, or falling victim to Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks.

All security mechanisms detailed in this report have been verified through automated regression tests and socket-level connection tracing.

---

## 2. Threat Model & Implemented Defense Controls

### 2.1 SSRF & Network Boundary Protection
- **Vulnerability Addressed:** Attacker initiates an API scan pointing to private network resources (RFC 1918), AWS/GCP cloud metadata services (`169.254.169.254`), container control sockets, or internal microservices.
- **Implementation:** [backend/app/security_engine/integration.py](file:///C:/PROJECTS/api-sentinel/backend/app/security_engine/integration.py)
  - `_parse_ip_literal`: Resolves and parses standard dotted-decimal, decimal integer (e.g. `2130706433`), hexadecimal (e.g. `0x7f000001`), and IPv6 literals.
  - `_check_ip_safety`:
    1. **Unspecified Addresses (`0.0.0.0`, `::`):** Strictly blocked under all circumstances, even in educational lab mode (`allow_lab=True`).
    2. **Cloud Metadata Endpoints:** `169.254.169.254` (IPv4) and `fd00:ec2::254` (IPv6) are unconditionally rejected.
    3. **Link-Local & Multicast:** `169.254.0.0/16`, `fe80::/10`, `224.0.0.0/4`, and `ff00::/8` are unconditionally rejected.
    4. **Private & Loopback (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`):** Blocked by default in production. Only permitted when `ALLOW_LOCAL_LAB_SCANNING=True` is explicitly set in configuration for authorized local testing.

### 2.2 TOCTOU & DNS Rebinding Hardening (Socket-Level IP Pinning)
- **Vulnerability Addressed:** An adversary registers a domain with a low TTL (e.g. 1 second). During the pre-flight safety check, the domain resolves to a safe public IP. When the HTTP client connects moments later, the DNS record has rebound to `127.0.0.1` or `169.254.169.254`.
- **Implementation:** [backend/app/security_engine/integration.py](file:///C:/PROJECTS/api-sentinel/backend/app/security_engine/integration.py)
  - `PinnedSyncBackend` extends `httpcore.SyncBackend`.
  - Override of `connect_tcp`:
    ```python
    target_ip = self.pinned_map[clean_host]
    return super().connect_tcp(
        target_ip, # Connect directly to the validated IP address
        port,
        timeout=timeout,
        local_address=local_address,
        socket_options=socket_options,
    )
    ```
  - **TLS SNI & Host Header Preservation:** The original target domain name is preserved for the HTTP `Host` header and TLS Server Name Indication (SNI), ensuring standard TLS certificate validation succeeds.
  - **Zero-Keepalive Pooling:** `PinnedHTTPTransport` sets `max_keepalive_connections=0` and `keepalive_expiry=0.0`. Sockets are closed after use and never pooled or reused across differing validated destinations.

### 2.3 HTTP Redirect Hardening
- **Vulnerability Addressed:** Open redirect vulnerabilities on target servers redirecting probes to unauthorized private destinations, protocol downgrades, or infinite redirect loops.
- **Implementation:** [backend/app/security_engine/integration.py](file:///C:/PROJECTS/api-sentinel/backend/app/security_engine/integration.py)
  - `execute_safe_request` enforces:
    1. Maximum 5 redirect hops; exceeding 5 raises `TargetSafetyError`.
    2. Redirect loop detection: Tracks visited URLs in a set; circular redirects raise `TargetSafetyError`.
    3. Protocol downgrade rejection: Redirects from `https://` to `http://` are rejected.
    4. Per-hop DNS & IP validation: Every redirect destination URL is evaluated against `validate_target_safety`.
    5. Cross-origin credential stripping: If the redirect host, port, or scheme differs from the original, `Authorization`, `Cookie`, and `X-API-Key` headers are stripped prior to making the next request.
    6. `follow_redirects=False`: HTTPX automatic redirect following is strictly disabled.

### 2.4 Synthetic Demo Credential Protection
- **Vulnerability Addressed:** Built-in demo accounts leaking credentials to external or unauthorized private endpoints during scanning.
- **Implementation:** [backend/app/security_engine/member1_engine.py](file:///C:/PROJECTS/api-sentinel/backend/app/security_engine/member1_engine.py)
  - `is_authorized_demo_target` requires all of:
    1. `allow_lab=True`.
    2. Target hostname is explicitly `127.0.0.1`, `localhost`, `::1`, or `testserver`.
    3. Target destination resolves strictly to a loopback address.
    4. Target port matches the configured demo API port (`8001` or standard test port).
  - External or unauthorized private targets receive NO synthetic credentials; real credentials must be explicitly provided in scan configuration.

### 2.5 Credential Redaction in Persistence and Logging
- **Vulnerability Addressed:** Plaintext passwords, tokens, or API keys stored in SQLite scan records or emitted in application logs.
- **Implementation:** [backend/app/services/scan_service.py](file:///C:/PROJECTS/api-sentinel/backend/app/services/scan_service.py) & [backend/app/services/ai_service.py](file:///C:/PROJECTS/api-sentinel/backend/app/services/ai_service.py)
  - `redact_sensitive_credentials` recursively redacts keys matching authorization, bearer, token, secret, password, api_key, credential, or cookie with `[REDACTED_FOR_SECURITY]`.
  - Telemetry stored in `evidence` and `scans.scan_configuration` stores only sanitized representations.
  - AI error handlers sanitize API keys (`nvapi-*`) and bearer tokens before emitting logs.

---

## 3. Vulnerability Detection Verification (BOLA / IDOR)

### 3.1 Detection Methodology
The testing engine audits endpoints with object identifiers (e.g. `GET /api/patients/{patient_id}`) using a dual-principal matrix:

```
[Principal A: patient_a (ID 101)] ────────► Authenticates ────────► Token A
[Principal B: patient_b (ID 102)] ────────► Authenticates ────────► Token B

Probe: Token A ──(GET /api/patients/102)──► Target API
```

### 3.2 Detection Verdict Logic
To prevent false positives from generic 200 OK responses (e.g. login landing pages or generic error bodies), the engine executes `_verify_foreign_data_exposure`:
- Verifies HTTP status is `200 OK`.
- Verifies response JSON body contains `patient_id == 102` or `owner_username == "patient_b"`.
- Captures clinical data exposure indicator (`diagnosis` or `prescription` presence).

### 3.3 Verification Retesting Logic
When the target application is remediated (e.g. transitioning the demo API to Secure Mode):
1. Target endpoint returns `HTTP 403 Forbidden` when Principal A queries Principal B's record.
2. The retest engine evaluates the response:
   - Observed status: `403`.
   - Access denied detail confirmed.
3. Status is updated in the database: `Open` $\rightarrow$ `Resolved`.
4. An immutable audit record is committed to `RetestHistory`:
   - `previous_status: "Open"`
   - `new_status: "Resolved"`
   - `verified: True`
   - `retested_at: <UTC Timestamp>`

---

## 4. Test Evidence & Automated Security Regression Matrix

The security test suite [backend/tests/test_ssrf_security.py](file:///C:/PROJECTS/api-sentinel/backend/tests/test_ssrf_security.py) and [backend/tests/test_member1_engine.py](file:///C:/PROJECTS/api-sentinel/backend/tests/test_member1_engine.py) verified the following test cases:

| Test Case | Target / Scenario | Expected Security Behavior | Status |
|---|---|---|:---:|
| `test_unspecified_address_rejected_even_in_lab_mode` | `http://0.0.0.0:8000` | Rejected with `TargetSafetyError` | **PASSED** |
| `test_decimal_and_hex_ip_representations` | `http://2130706433:8000`, `http://0x7f000001:8000` | Normalized to `127.0.0.1` and controlled | **PASSED** |
| `test_cloud_metadata_endpoints_strictly_blocked` | `http://169.254.169.254/latest/meta-data` | Unconditionally blocked | **PASSED** |
| `test_link_local_multicast_and_reserved_blocked` | `http://[fe80::1]`, `http://224.0.0.1` | Unconditionally blocked | **PASSED** |
| `test_private_ips_blocked_by_default_allowed_in_lab` | `http://192.168.1.1` | Blocked if `allow_lab=False`, allowed if `True` | **PASSED** |
| `test_pinned_backend_connects_to_exact_validated_ip` | Direct socket inspection | Verified TCP connects to pinned IP | **PASSED** |
| `test_dns_rebinding_simulation_prevented` | Host rebinding simulation | Connection refuses altered DNS IP | **PASSED** |
| `test_tls_sni_and_host_header_preserved` | HTTPS probe | Host header and SNI match target domain | **PASSED** |
| `test_redirect_https_to_http_downgrade_rejected` | `https://` $\rightarrow$ `http://` | Downgrade rejected | **PASSED** |
| `test_redirect_to_cloud_metadata_rejected` | Redirect hop to `169.254.169.254` | Hop rejected with `TargetSafetyError` | **PASSED** |
| `test_redirect_to_private_network_rejected` | Redirect hop to `10.0.0.1` | Hop rejected with `TargetSafetyError` | **PASSED** |
| `test_redirect_loop_detected` | Circular redirects (A $\rightarrow$ B $\rightarrow$ A) | Loop detected and halted | **PASSED** |
| `test_max_redirect_hops_enforced` | 6 redirect hops | Halted at hop 5 | **PASSED** |
| `test_cross_origin_redirect_strips_sensitive_headers` | `http://origin.com` $\rightarrow$ `http://other.com` | Auth & Cookie headers stripped | **PASSED** |
| `test_authorized_demo_target_guard` | `http://127.0.0.1:8001` vs `http://127.0.0.1:9000` | Non-demo ports refuse synthetic creds | **PASSED** |
| `test_synthetic_credentials_refused_on_external_targets` | `https://api.github.com` | Synthetic credentials refused | **PASSED** |
| `test_bola_detection_on_vulnerable_demo_api` | Vulnerable Demo API | BOLA detected with HTTP evidence | **PASSED** |
| `test_bola_prevention_on_secure_mode` | Remediated Demo API | HTTP 403 confirmed; no false positive | **PASSED** |
| `test_retesting_lifecycle_vulnerable_then_resolved` | Full remediation lifecycle | Open $\rightarrow$ Resolved with history record | **PASSED** |

---

## 5. Security Posture Conclusion

The API Sentinel platform demonstrates enterprise-grade defensive architecture. It successfully identifies critical API security flaws (OWASP API1: BOLA, missing authentication, missing security headers) while maintaining strict socket-level containment to ensure safety against SSRF and DNS rebinding attacks.
