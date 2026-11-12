# API SENTINEL — ATTACK DEMONSTRATION & EVIDENCE INSPECTOR GUIDE
**Platform:** API Sentinel  
**Tagline:** *Find it. Understand it. Fix it. Verify it.*  
**Status:** Certified & Active  
**Version:** v1.1.0-sec-inspector

---

## 1. EXECUTIVE SUMMARY & ARCHITECTURE

The **Attack Demonstration & Evidence Inspector** is an explainable forensic security analysis interface integrated into API Sentinel. It bridges the gap between abstract vulnerability metrics and actionable developer remediation by exposing full, unvarnished HTTP request/response telemetry, an end-to-end attack timeline, and a cryptographically verifiable evidence package.

```
+---------------------------------------------------------------------------------------------------+
|                                  ATTACK & EVIDENCE INSPECTOR PIPELINE                             |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ 1. PROBE EXECUTION ]             [ 2. TELEMETRY CAPTURE ]           [ 3. VERIFIABLE EXPORT ]   |
|  Target: /api/patients/102           Real duration (ms)                 Canonical JSON format     |
|  Bearer: sent..._101                 Masked sensitive tokens            SHA-256 Cryptographic     |
|  Client: PinnedHTTPTransport         Highlighted victim payload         Digest generated on wire  |
|                                                                                                   |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
                     +--------------------------------------------------------+
                     |             5 FORENSIC EXPLORATION PANELS              |
                     |  1. Attack Overview & Visual Flow Diagram              |
                     |  2. Raw HTTP Request (Headers + Copyable cURL)         |
                     |  3. Raw HTTP Response (Body + Exposed PHI Attributes)  |
                     |  4. 9-Step Chronological Attack Timeline               |
                     |  5. SHA-256 Digest & One-Click Evidence JSON Export    |
                     +--------------------------------------------------------+
                                                  |
                                                  v
                     +--------------------------------------------------------+
                     |           DUAL-PROBE RETEST VERIFICATION MATRIX        |
                     |  Owner Access:    Alice -> Alice (200 OK Preserved)    |
                     |  Attacker Probe:  Alice -> Bob   (403 Forbidden Fixed) |
                     +--------------------------------------------------------+
```

---

## 2. THE FIVE FORENSIC EXPLORATION PANELS

### Tab 1: Attack Overview & Visual Flow Diagram
- **Vulnerability Metadata:** Displays OWASP Top 10 API category (e.g. `API1:2023 - Broken Object Level Authorization`), severity pill, affected endpoint, and targeted record identifier.
- **BOLA Visual Attack Flow:** An interactive node diagram illustrating the attack chain:
  1. `Alice (Attacker)` Authenticated as user `patient_a`.
  2. `GET /api/patients/102` Target patient `Bob` identifier injected into URL parameter.
  3. `Authorization Boundary`: Evaluates if access control validates `user_id == record.owner_id`.
  4. `Outcome`: Visual indicator displaying data leakage (Vulnerable) vs `403 Forbidden` (Remediated).
- **Security Observations:** Highlights specific boundary failures (e.g., *Cross-tenant boundary breach: Alice successfully accessed Bob's confidential medical records*).

### Tab 2: Raw HTTP Request
- **Method & Destination:** Full resolved destination URL (`http://127.0.0.1:8001/api/patients/102`).
- **Sanitized Headers:** Formatted table of sent headers with masked secrets (e.g. `Authorization: Bearer sent..._101`).
- **Live Network Capture Badge:** Verifies that this probe was dispatched over real network sockets via `PinnedHTTPTransport` with zero simulation.
- **Copyable cURL Command:** One-click copyable cURL string for independent reproduction in terminal or external penetration testing tools:
  ```bash
  curl -X GET "http://127.0.0.1:8001/api/patients/102" \
    -H "Authorization: Bearer sent..._101" \
    -H "Accept: application/json"
  ```

### Tab 3: Raw HTTP Response
- **Response Metrics:** Status code badge (`HTTP 200 OK` in vulnerable mode, `HTTP 403 Forbidden` in remediated mode) and real roundtrip latency in milliseconds (`duration_ms`).
- **Response Headers:** Content-Type, Content-Length, and Server headers.
- **Formatted Response Body:** Clean JSON syntax view with highlighted sensitive victim fields.
- **Exposed PHI Attributes:** High-visibility badges identifying specific leaked fields (e.g. `diagnosis`, `prescriptions`, `patient_name`, `dob`).

### Tab 4: 9-Step Chronological Attack Timeline
A step-by-step audit record illustrating how the security engine identified the vulnerability:
1. `Target Registration`: Endpoint discovery via OpenAPI specification.
2. `Credential Retrieval`: Test credentials loaded from isolated AES-256 Credential Vault.
3. `Socket Binding & IP Pinning`: SSRF prevention transport pinned to validated IP.
4. `Baseline Owner Request`: Alice fetches own record (`/api/patients/101`) -> returns `200 OK`.
5. `Cross-Tenant Parameter Injection`: Endpoint mutated to target Bob (`/api/patients/102`).
6. `Exploit Dispatch`: Authenticated GET probe transmitted.
7. `Response Telemetry Interception`: Captured `HTTP 200 OK` in 14.2 ms.
8. `Payload Content Inspection`: Verified response body contains `patient_b` private PHI.
9. `Finding Commitment`: Finding persisted with immutable cryptographic snapshot.

### Tab 5: Evidence Integrity & SHA-256 Export
- **Cryptographic Digest:** Canonical SHA-256 hash calculated over the sorted, normalized JSON payload:
  $$\text{Digest} = \text{SHA256}(\text{CanonicalJSON}(\text{Evidence}))$$
- **Export Endpoint:** Backend route `GET /api/findings/{finding_id}/export-evidence`.
- **One-Click Download:** Exports `api-sentinel-evidence-<finding_id>.json` directly to the investigator's workstation.

---

## 3. DUAL-PROBE VERIFICATION WORKFLOW

API Sentinel rejects "blind" status flips. When verifying whether a vulnerability has truly been remediated, the platform executes a **Dual-Probe Matrix**:

| Probe Dimension | Legitimate Owner Probe | Cross-Tenant Attacker Probe | Verdict Requirement |
| :--- | :--- | :--- | :--- |
| **Request Vector** | `Alice` accessing `Alice's` record (`101`) | `Alice` accessing `Bob's` record (`102`) | Segregated Authorization |
| **Vulnerable Mode** | `HTTP 200 OK` | `HTTP 200 OK` *(Vulnerability Confirmed)* | **OPEN / FAIL** |
| **Remediated Mode** | `HTTP 200 OK` | `HTTP 403 Forbidden` *(Access Denied)* | **RESOLVED / PASS** |
| **Security Delta** | Legitimate operation is preserved | Foreign object access strictly blocked | **ZERO FALSE POSITIVES** |

---

## 4. REST API SPECIFICATION FOR EVIDENCE

### `GET /api/findings/{finding_id}/export-evidence`
- **Method:** `GET`
- **Access:** Authenticated / Admin
- **Description:** Returns the complete self-contained evidence bundle for external reporting or auditing.

#### Response Structure:
```json
{
  "export_version": "1.1.0",
  "generated_at": "2026-11-11T18:00:00Z",
  "sha256_digest": "4a7b2e9c1f8d3a5e...",
  "finding": {
    "id": "e391490d-27b2-4dcf-8bb5-9fcfa1c68285",
    "scan_id": "8f3b4c1a-...",
    "vulnerability": "Broken Object Level Authorization (BOLA)",
    "severity": "Critical",
    "endpoint": "/api/patients/{patient_id}",
    "status": "Open",
    "description": "...",
    "recommendation": "..."
  },
  "evidence": {
    "test_user": "patient_a",
    "requested_resource": "/api/patients/102",
    "observed_status": 200,
    "expected_status": 403,
    "duration_ms": 14.5,
    "curl_command": "curl -X GET \"http://127.0.0.1:8001/api/patients/102\" ...",
    "request_details": {
      "method": "GET",
      "url": "http://127.0.0.1:8001/api/patients/102",
      "headers": {
        "Host": "127.0.0.1:8001",
        "Authorization": "Bearer sent..._101"
      }
    },
    "response_details": {
      "status_code": 200,
      "headers": {
        "content-type": "application/json"
      },
      "body": {
        "id": 102,
        "name": "Bob Smith",
        "diagnosis": "Arrhythmia"
      }
    },
    "timeline": [ ... ]
  }
}
```

---

## 5. SECURITY & COMPLIANCE ASSURANCE

1. **Secret Masking:** Authorization tokens and credentials are masked before disk commitment and UI rendering (`sent..._101`).
2. **SSRF Guard:** Probes only traverse through `PinnedHTTPTransport` preventing DNS rebinding or private cloud metadata egress.
3. **Immutability:** Each probe verification write creates an append-only row in the `retest_history` table.
4. **Remediation Disclaimer:** All AI-generated remediations contain the explicit disclaimer:
   > *"Suggested remediation — not automatically applied or verified."*
