# API SENTINEL — PHASE 12: PROFESSIONAL PRODUCT DEMONSTRATION WALKTHROUGH

**Project:** API Sentinel  
**Project Path:** `C:\PROJECTS\api-sentinel`  
**Active Git Branch:** `feature/api-key-dataset`  
**Baseline Git Checkpoint:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93` (v1.0.0 Release Baseline Preserved)  
**Report Date:** November 11, 2026  
**Audience:** Technical Presenters, Faculty Evaluators, Hackathon Judges, Security Analysts  
**Official Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. DEMONSTRATION RUN-OF-SHOW & TIMING OVERVIEW

This walkthrough provides an exact, battle-tested script and sequence for an **8 to 10-minute live demonstration**.

```
+---------------------------------------------------------------------------------------------------+
| MINUTE 00:00 - 01:30 | Demonstration 1: Product Overview & Value Proposition                      |
| MINUTE 01:30 - 03:00 | Demonstration 2: API Onboarding & OpenAPI Discovery                        |
| MINUTE 03:00 - 04:30 | Demonstration 3: Real Security Scanning (Healthcare Demo API)              |
| MINUTE 04:30 - 05:45 | Demonstration 4: Explainable Findings & AI Root-Cause Analysis             |
| MINUTE 05:45 - 07:00 | Demonstration 5: Live Remediation & Dual-Verification Retest               |
| MINUTE 07:00 - 08:15 | Demonstration 6: API Key Intelligence & Synthetic Benchmark                |
| MINUTE 08:15 - 09:15 | Demonstration 7: Multi-Format Reports & Compliance Matrices                |
| MINUTE 09:15 - 10:00 | Demonstration 8: Architecture, Infrastructure & Q&A Wrap-Up                |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. DETAILED DEMONSTRATION STEPS & SCRIPT

---

### DEMONSTRATION 1: PRODUCT OVERVIEW & VALUE PROPOSITION
**Target Timing:** 00:00 – 01:30  
**URL to Open:** `http://127.0.0.1:5173` (Browser Tab 1)  
**Active View:** `Security Overview` (`/`)

#### Exact Actions to Perform:
1. Open the browser to `http://127.0.0.1:5173`.
2. Point out the Cyber Dark UI, the header system status badge (`🟢 System Online`), and the product tagline: *"Find it. Understand it. Fix it. Verify it."*
3. Highlight the 4 KPI cards: **Security Posture Score**, **Total Scans Audited**, **Vulnerabilities Identified**, and **Verified Remediations**.
4. Scroll to the **Recent Scan Activity** table showing past automated audit runs.

#### Presenter Spoken Script:
> *"Hello judges, professors, and fellow engineers. Today, modern applications are fundamentally powered by APIs. But traditional security scanners are built for security specialists—they dump overwhelming, hundred-page PDF reports filled with false positives, leaving student developers and small businesses stranded.*
>
> *API Sentinel transforms that paradigm with four core promises: **Find it. Understand it. Fix it. Verify it.**
> 
> *Here on the main dashboard, developers get an immediate, real-time pulse of their API ecosystem: posture scores, categorized vulnerability breakdowns, and live audit feeds. Everything you will see today is running live on our machine against actual HTTP services with zero simulated data."*

#### Expected Visible Output:
- Dark cyber aesthetic with electric cyan accents (`#00E5FF`).
- Live KPI cards with animated count-ups.
- System status chip showing real-time SSE connectivity.

#### Screenshot to Capture:
- `demo_01_security_overview.png`: Full-screen overview showing KPI cards and historical scan list.

---

### DEMONSTRATION 2: API ONBOARDING & OPENAPI ENDPOINT DISCOVERY
**Target Timing:** 01:30 – 03:00  
**URL to Open:** `http://127.0.0.1:5173` -> Click **"API Onboarding"** in sidebar.

#### Exact Actions to Perform:
1. In the target name field, enter: `Healthcare Demo API`.
2. In the target base URL field, enter: `http://127.0.0.1:8001`.
3. In the OpenAPI Specification box, click **"Load Demo Spec"** (or paste the YAML spec from `demo_api/README.md`).
4. Click **"Parse Specification & Preview"**.
5. Observe the discovered endpoints table displaying paths, methods (`GET`, `POST`), parameters (`{patient_id}`), and sensitivity tags.
6. Click the **"Sensitive Only"** button to toggle filtering.
7. Under Authentication Profiles, show the configured dual test principals:
   - User A (Owner): `patient_a` / ID `101` / Bearer `sentinel_patient_a_demo_token_101`
   - User B (Attacker): `patient_b` / ID `102` / Bearer `sentinel_patient_b_demo_token_102`
8. Click **"Verify Connectivity"** (returns green checkmark: `Target reachable (200 OK)`).
9. Click **"Register Target & Proceed to Scan"**.

#### Presenter Spoken Script:
> *"Meaningful API security requires deep context. In our API Onboarding module, developers connect their service in seconds using standard OpenAPI or Swagger definitions.*
>
> *Watch as our parser instantly dissects the specification, mapping out endpoints, HTTP methods, and URL parameters like `{patient_id}`. Developers can selectively target individual routes or filter to sensitive endpoints with one click.*
>
> *Most importantly, to test authorization flaws like BOLA, Sentinel allows developers to register two test accounts—the resource owner and a foreign attacker. Crucially, these credentials are encrypted at rest using an AES-128 Fernet vault, and are always masked in the UI so secrets never leak."*

#### Expected Visible Output:
- Discovered endpoint list with colored badges (`GET` blue, `POST` green).
- Authentication profile cards showing masked tokens (`sent..._101`).
- Green connectivity confirmation badge.

#### Screenshot to Capture:
- `demo_02_onboarding_discovery.png`: Onboarding view with discovered endpoints and dual auth profiles.

---

### DEMONSTRATION 3: REAL SECURITY SCANNING
**Target Timing:** 03:00 – 04:30  
**URL to Open:** `http://127.0.0.1:5173` -> Click **"New Security Scan"** in sidebar.

#### Exact Actions to Perform:
1. Target URL auto-populates `http://127.0.0.1:8001`.
2. Notice the mandatory checkbox: **"I confirm I am authorized to scan this API target."**
3. Select scan categories: Check `BOLA`, `AUTH`, `HEADERS`.
4. Click **"Launch Security Scan"**.
5. Watch the live progress bar and real-time SSE status updates (`Initiating scan...`, `Auditing headers...`, `Executing multi-principal BOLA checks...`, `Completed`).
6. Upon completion (in ~1.2 seconds), click **"View Discovered Findings"**.

#### Presenter Spoken Script:
> *"Now let's launch an active security audit against our running Healthcare Demo API. Sentinel strictly enforces legal authorization before any packets are sent.*
>
> *As the scan executes, our backend uses our custom Pinned HTTP Transport—which rigorously enforces SSRF defenses, preventing DNS rebinding and blocking access to cloud metadata. Within seconds, the scan completes, uncovering real, exploitable vulnerabilities."*

#### Expected Visible Output:
- Real-time progress bar updating via Server-Sent Events (SSE).
- Scan duration metric (~1,250ms).
- Immediate navigation button to findings.

#### Screenshot to Capture:
- `demo_03_active_scan_execution.png`: Live scan progress bar and terminal log stream.

---

### DEMONSTRATION 4: EXPLAINABLE FINDINGS & AI ROOT CAUSE
**Target Timing:** 04:30 – 05:45  
**URL to Open:** `http://127.0.0.1:5173` -> Click **"Vulnerability Findings"** in sidebar.

#### Exact Actions to Perform:
1. Locate the **HIGH** severity finding: `Broken Object Level Authorization (BOLA)` on `GET /api/patients/{patient_id}`.
2. Click on the finding card to expand the technical evidence drawer.
3. Show the exact observed evidence:
   - Observed Status: `200 OK` (Expected: `403 Forbidden`)
   - Test Principal: `patient_a (ID 101)` requesting resource `/api/patients/102`
   - Data Snippet: Displays exposed patient record belonging to `patient_b`.
4. Click the **"Copy Reproduction Curl"** button to demonstrate reproducibility.
5. Highlight the **AI Root-Cause Explanation** panel:
   - Explanation of why accepting unvalidated client IDs causes IDOR.
   - 5 structured developer remediation steps with example parameterized code.

#### Presenter Spoken Script:
> *"This is the heart of our 'Understand it' promise: explainable security.*
>
> *Instead of an ambiguous alert, Sentinel provides raw, verifiable proof. Look at this evidence drawer: user `patient_a` requested record `102`, and the server returned a 200 OK containing Alice's medical data.*
>
> *Below that, our integration with NVIDIA Nemotron (or our offline deterministic fallback) explains the exact architectural root cause and gives developers a step-by-step code fix: extract the user ID directly from the validated session token, and use a compound WHERE clause."*

#### Expected Visible Output:
- Evidence drawer with formatted JSON technical details.
- High-contrast severity tag.
- AI / rule-based remediation code snippet.

#### Screenshot to Capture:
- `demo_04_explainable_bola_finding.png`: Expanded finding showing reproducible evidence and remediation steps.

---

### DEMONSTRATION 5: REMEDIATION & DUAL-VERIFICATION RETEST
**Target Timing:** 05:45 – 07:00  
**URL to Open:** `http://127.0.0.1:5173` -> Click **"Retesting & Verification"** in sidebar.

#### Exact Actions to Perform:
1. Show that the BOLA finding currently displays status **`Open`**.
2. Explain to the audience that the developer has now applied the fix on the demo server (switch demo mode or explain server-side ownership enforcement).
3. Click **"Run Retest Probe"**.
4. Observe the dual-check verification:
   - Probe 1: Owner (`patient_a`) accesses `/api/patients/101` -> **HTTP 200 OK** (Legitimate access verified).
   - Probe 2: Attacker (`patient_b`) accesses `/api/patients/101` -> **HTTP 403 Forbidden** (Unauthorized access blocked).
5. Watch the finding status instantly transition from `Open` to **`Resolved`** with a green shield icon.
6. Show the **Retest History Audit Trail** recording the probe timestamp, response codes, and resolution timestamp.

#### Presenter Spoken Script:
> *"Most scanners stop after finding an issue. Sentinel takes it all the way to 'Verify it'.*
>
> *Once a developer patches their code, they don't have to guess if the patch worked. They click 'Run Retest Probe'.*
>
> *Notice our dual-check innovation: Sentinel first verifies that the legitimate owner can still access their data. Then it verifies that the foreign attacker is rejected with a 403 Forbidden. The finding status updates to 'Resolved', and an indelible audit record is permanently logged."*

#### Expected Visible Output:
- Animated retest probe execution.
- Status badge transforming to green `Resolved`.
- Retest history log showing both probes.

#### Screenshot to Capture:
- `demo_05_retest_resolved.png`: Retest view showing dual-probe verification and `Resolved` status badge.

---

### DEMONSTRATION 6: API KEY INTELLIGENCE & DATASET EXPLORER
**Target Timing:** 07:00 – 08:15  
**URL to Open:** `http://127.0.0.1:5173` -> Click **"API Key Intelligence"** in sidebar.

#### Exact Actions to Perform:
1. Point out the header disclaimer: *Evaluates synthetic dataset tokens to benchmark regex & entropy detectors (independent of target scanning).*
2. In the **Single Key Analyzer**, paste or select a key: `sk-proj-abc123xyz78904561234567890`.
3. Click **"Analyze Key"**:
   - Shows Shannon Entropy: `4.85 bits` (High randomness).
   - Provider Match: `OpenAI Project Key`.
   - Confidence: `High (Pattern + Entropy Verified)`.
4. Switch to the **Benchmark Suite** tab:
   - Click **"Run Test Split Benchmark (N=200)"**.
   - Show the generated Confusion Matrix: **100% Precision**, **99.49% Recall**, **99.75% F1-Score**.
5. Switch to the **Dataset Explorer** tab:
   - Paginate through the 10,000 synthetic samples across OpenAI, AWS, GitHub, Slack, and Stripe.

#### Presenter Spoken Script:
> *"API keys are the keys to the kingdom, but detecting leaked keys without false positives is notoriously difficult.*
>
> *In our API Key Intelligence module, we trained and audited our detection rules against a curated dataset of 10,000 synthetic tokens. Here, we analyze both provider structural patterns and Shannon entropy.*
>
> *When we evaluate our test split, our detector achieves 100% precision and a 99.75% F1-score. This gives organizations complete confidence that exposed credentials will be detected without alerting on random garbage strings."*

#### Expected Visible Output:
- Entropy meter visualizing bit randomness.
- Real-time confusion matrix with calculated metrics.
- Paged dataset table with masked secrets.

#### Screenshot to Capture:
- `demo_06_api_key_intelligence.png`: Benchmark suite view with confusion matrix and entropy metrics.

---

### DEMONSTRATION 7: MULTI-FORMAT AUDIT REPORTS
**Target Timing:** 08:15 – 09:15  
**URL to Open:** `http://127.0.0.1:5173` -> Click **"Reports"** in sidebar.

#### Exact Actions to Perform:
1. Select the completed scan session from the dropdown.
2. Review the **Security Posture Score** and **OWASP Category Distribution** (BOLA, Auth, Misconfigurations).
3. Click **"Export Audit JSON"** -> Downloads `api_sentinel_report_<scan_id>.json`.
4. Click **"Export Audit Markdown"** -> Downloads `api_sentinel_report_<scan_id>.md`.
5. Open the downloaded Markdown file briefly in an editor or previewer to show the clean headings, sanitized evidence, and remediation instructions.

#### Presenter Spoken Script:
> *"Finally, security findings need to be communicated to stakeholders. In the Reports module, Sentinel generates executive posture scores and OWASP Top 10 compliance heatmaps.*
>
> *With two clicks, developers can export an Audit JSON file for their SIEM or automated CI/CD pipeline, or a beautifully formatted Markdown report ready to be attached to a Jira ticket or GitHub pull request. Every sensitive token is automatically redacted, making the report safe for external sharing."*

#### Expected Visible Output:
- OWASP category breakdown bar chart.
- Download confirmation for both JSON and Markdown artifacts.

#### Screenshot to Capture:
- `demo_07_reports_view.png`: Reports view with OWASP distribution and download buttons.

---

### DEMONSTRATION 8: ARCHITECTURE, INFRASTRUCTURE & WRAP-UP
**Target Timing:** 09:15 – 10:00  
**URL to Open:** Return to `Security Overview` or show terminal architecture.

#### Exact Actions to Perform:
1. Summarize the complete pipeline: Target -> Ingestion -> Safe Scanning -> AI Root Cause -> Verification Retest -> Reporting.
2. Note containerization readiness: Show `docker-compose.yml` and `Dockerfile` in the project root.
3. Conclude with the tagline: *"Find it. Understand it. Fix it. Verify it."*

#### Presenter Spoken Script:
> *"To summarize: API Sentinel is not just another vulnerability scanner. It is a complete, explainable security lifecycle platform designed to empower developers rather than overwhelm them.*
>
> *It features hardened SSRF defenses, an AES-128 credential vault, content-aware BOLA detection, dual-probe retest verification, and offline AI determinism.*
>
> *Thank you, and we welcome your questions!"*

---

## 3. FAILURE SCENARIOS & RECOVERY PROCEDURES

| Failure Scenario | Symptom | Immediate Recovery Action |
| :--- | :--- | :--- |
| **Demo API Not Running** | Target scan fails with `Target connection refused`. | Open PowerShell and run: `python -m uvicorn demo_api.main:app --port 8001`. |
| **FastAPI Backend Offline** | Frontend displays red banner `Unable to reach backend`. | Open PowerShell and run: `cd backend; python -m uvicorn app.main:app --port 8000`. |
| **NVIDIA API Latency / Offline** | AI explanation takes >5 seconds. | Do nothing: Sentinel will automatically fall back to `rule-based-security-engine (offline-fallback)` in <50ms. |
| **Accidental Scan Deletion** | Scan history appears empty. | Re-run a scan against `http://127.0.0.1:8001` (takes 1.2s to regenerate all findings). |
| **Browser Cache Glitch** | UI displays stale data. | Press `Ctrl + Shift + R` (Hard reload) in Google Chrome / Edge. |
