# API SENTINEL — LIVE DEMONSTRATION & EVALUATION SCRIPT
**Step-by-Step Presentation Guide for Academic & Technical Review**

- **Project:** API Sentinel
- **Tagline:** *Find it. Understand it. Fix it. Verify it.*
- **Target Audience:** College Evaluation Panel, Security Auditors, Small Business Developers
- **Total Demo Duration:** 10–12 Minutes

---

## 1. Presentation Outline & Timing

| Segment | Topic | Duration | Key Visual / Screen |
| :---: | :--- | :---: | :--- |
| **01** | **Introduction & Problem Statement** | 1.5 min | Slide / Architecture Diagram |
| **02** | **Target Onboarding & Discovered Endpoints** | 2.0 min | `#targets` Workspace |
| **03** | **Security Scan Launch & SSE Telemetry** | 1.5 min | `#scans` Live Terminal |
| **04** | **Vulnerability Findings & Prioritization** | 1.5 min | `#findings` View |
| **05** | **Attack Evidence Inspector & SHA-256 Digest** | 2.0 min | `#evidence` Workspace |
| **06** | **AI Explanation & Code Remediation** | 1.5 min | `#ai_analysis` Panel |
| **07** | **Dual-Probe Retest & Audit History** | 1.5 min | `#retesting` & `#audit` |
| **08** | **API Key Intelligence & Benchmark** | 1.0 min | `#api_key_intel` |

---

## 2. Step-by-Step Demonstration Walkthrough

### Part 1: Problem Statement & Core Philosophy (1.5 min)
- **Speaker**: *"Modern web APIs account for over 80% of internet traffic, but small businesses and student developers lack explainable tools to test against sophisticated authorization flaws like BOLA/IDOR. Traditional scanners simply output alerts without proving the vulnerability or verifying the fix. API Sentinel solves this with a 4-step guarantee: Find it. Understand it. Fix it. Verify it."*

### Part 2: Target Onboarding & Discovered Endpoints (2.0 min)
- **Action**: Open browser at `http://127.0.0.1:5173/#targets`.
- **Display**:
  1. Show configured **Healthcare Demo API** (`http://127.0.0.1:8001`).
  2. Click **Validate**: Show real-time connectivity latency (`20ms`, `HTTP 200 OK`).
  3. Click **Endpoints**: Show 6 operations parsed from OpenAPI specification, highlighting sensitive paths (`/api/patients/{patient_id}`).
  4. Click **Auth**: Show dual-principal configuration (User A Alice vs User B Bob), emphasizing that credentials are encrypted in our AES-128 Fernet vault and masked as `sent..._101`.

### Part 3: Scan Launch & Live Telemetry (1.5 min)
- **Action**: Click **Scan** button on the target card.
- **Display**:
  1. Observe seamless transition to `#scans` with Healthcare Demo API preselected.
  2. Point out the **Target Security Telemetry Card** displaying 6 operations and 2 auth profiles.
  3. Click **Launch Security Scan**.
  4. Point out the live **Cybersecurity Audit Terminal**: Server-Sent Events (SSE) streaming real-time status transitions (`[INIT]`, `[TARGET]`, `[PROBING]`, `[COMPLETE]`).

### Part 4: Vulnerability Findings (1.5 min)
- **Action**: Click **Navigate to Findings** (`#findings`).
- **Display**:
  1. Highlight the detected findings list:
     - `High`: Broken Object Level Authorization (BOLA) at `/api/patients/{patient_id}`
     - `High`: Broken Token Signature Validation at `/api/admin/metrics`
     - `Medium`: Missing HSTS header
     - `Low`: Missing CSP and Framing headers.
  2. Explain that detection is 100% deterministic — no generative hallucinations.

### Part 5: Attack Demonstration & Evidence Inspector (2.0 min)
- **Action**: Click **Inspect Attack & Evidence** on the BOLA finding.
- **Display**:
  1. **Attack Overview**: Show foreign principal (Alice) successfully fetching Bob's medical records.
  2. **Raw HTTP Request / Response**: Show real copyable cURL, request headers, and returned JSON payload.
  3. **Evidence Integrity & SHA-256 Digest**:
     - Point out the cryptographic digest: `38082171988995c6...`.
     - Click **Export Forensic Evidence JSON**.
     - Explain that canonicalized payload verification guarantees evidence is untampered.

### Part 6: NVIDIA Nemotron AI Explanation (1.5 min)
- **Action**: Click **Request AI Explanation** (`#ai_analysis`).
- **Display**:
  1. Show Nemotron 30B / deterministic fallback explanation.
  2. Highlight the 3 key sections:
     - **Vulnerability Breakdown**: Why BOLA happened.
     - **Attack Scenario**: How an attacker exploits client-supplied patient IDs.
     - **Exact Code Remediation**: Show the recommended Python / FastAPI fix verifying token claims.

### Part 7: Dual-Probe Retest & Audit History (1.5 min)
- **Action**: Navigate to `#retesting`.
- **Display**:
  1. Click **Trigger Verification Retest** while vulnerable: System reports **Still Vulnerable** (foreign data still exposed).
  2. Toggle Demo API to Secure Mode (via script or demo toggle).
  3. Click **Trigger Verification Retest** again:
     - **Owner Baseline Probe**: Alice accessing Alice's record $\rightarrow$ **HTTP 200 OK (Preserved)**.
     - **Attacker Probe**: Alice accessing Bob's record $\rightarrow$ **HTTP 403 Forbidden (Blocked)**.
     - **Verdict**: **VERIFIED RESOLVED**.
  4. Click **View in Audit Ledger** (`#audit`): Show immutable append-only history log proving the fix.

### Part 8: API Key Intelligence & Benchmark (1.0 min)
- **Action**: Navigate to `#api_key_intel`.
- **Display**:
  1. Showcase the 10,000-sample Master Dataset across 10 cloud providers.
  2. Show live Shannon entropy calculation ($H \ge 3.2\text{ bits}$).
  3. Highlight verified benchmark metrics: **99.50% Accuracy, 100.00% Precision, 0 False Positives**.

---

## 3. Anticipated Panel Questions & Verified Answers

1. **Q: Does your scanner use AI to decide whether an API is vulnerable?**
   - **A**: *No. AI never determines vulnerability status. All vulnerability detections and dual-probe retest decisions are 100% deterministic, based on strict HTTP response code and payload assertions. AI is used solely for explainability and remediation advice.*
2. **Q: How do you prevent BOLA false positives from generic HTTP 200 responses?**
   - **A**: *Our engine employs a dual-principal discrimination matrix. It requires proof of foreign/victim data exposure in the response payload. If the server returns a generic 200 with no sensitive data, BOLA is not flagged.*
3. **Q: How does the system defend against SSRF if a user scans internal services?**
   - **A**: *The transport layer performs pinned socket pre-flight checks, blocking cloud metadata (169.254.169.254 in IPv4, IPv6, hex, and dword), link-local, multicast, and RFC 1918 private subnets.*

---

## 4. Conclusion
The demonstration provides a concrete, hands-on proof of API Sentinel's capabilities, demonstrating true end-to-end integration and forensic verification.
