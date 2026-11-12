# API Sentinel — Final Launch & Operational Guide

## Welcome to API Sentinel

**Tagline:** Find it. Understand it. Fix it. Verify it.

---

## 1. Quick Access in Your Browser

Both of the following URLs are currently live, serving the latest **v1.2.0-phase5-prod** build:

- **React Vite Development Server:**
  👉 **`http://127.0.0.1:5173/`**
- **FastAPI Production Mount (Direct):**
  👉 **`http://127.0.0.1:8000/`**

> **IMPORTANT CACHE CLEARING STEP:**
> If you previously had the page open, press **`Ctrl + Shift + R`** (or **`Ctrl + F5`**) in your browser to reload the latest bundle.
> You will immediately see the persistent **`v1.2.0-phase5-prod`** badge at the bottom-left of the sidebar.

---

## 2. Where to Find NVIDIA Nemotron AI on the Dashboard

You now have **three distinct, unmissable ways** to interact with NVIDIA Nemotron AI:

### Way 1: The Dedicated "AI Security Analysis" Tab
1. Click **`AI Security Analysis`** (with the purple **`+ AI`** badge) in the left sidebar.
2. Select any vulnerability from the **Detected Findings** list on the left.
3. On the right, click **`✨ Explain with Nemotron AI`** (or **`🔄 Regenerate AI Analysis`**).
4. Browse the three structured tabs:
   - **Vulnerability Breakdown**: Root cause explanation and OWASP classification.
   - **Attack Scenarios & Impact**: Real-world exploit simulation and HIPAA/GDPR compliance risks.
   - **Step-by-Step Remediation**: Exact code diffs and verification tests.

### Way 2: Inside "Vulnerability Findings"
1. Click **`Vulnerability Findings`** in the sidebar.
2. The first vulnerability automatically expands upon loading.
3. Scroll down inside any finding card to the purple **`AI-POWERED SECURITY ANALYSIS`** section.
4. Click **`✨ Explain with Nemotron AI`**.

### Way 3: From the "Overview" Dashboard
1. The top of the Overview dashboard features a large purple banner:
   **`NVIDIA Nemotron AI Security Intelligence [ACTIVE & INTEGRATED]`**
2. Click the purple button **`Explore AI Findings ->`** to jump directly to the AI Hub.
3. In the "Recent Vulnerability Findings" table, click **`✨ AI Explain`** in any row.

---

## 3. Running Services Reference

All three services are configured to run locally:

| Component | Port | Health Check URL | Launch Command |
|---|---|---|---|
| **Healthcare Demo API** | `8001` | `http://127.0.0.1:8001/health` | `python -m uvicorn demo_api.main:app --host 127.0.0.1 --port 8001` |
| **FastAPI Backend Core** | `8000` | `http://127.0.0.1:8000/api/health` | `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |
| **React Vite Dashboard** | `5173` | `http://127.0.0.1:5173/` | `npm run dev -- --host 127.0.0.1 --port 5173` |

---

## 4. Key Verification Features

- **Live Server-Sent Events (SSE)**: Green `● LIVE STREAM` badge in the header shows real-time synchronization with zero page reloads.
- **Critical Alert Modal**: If a Critical vulnerability (like BOLA or SQL Injection) is detected, an in-app cyber modal appears automatically with "Inspect Finding" and "Acknowledge" actions.
- **Verification Retest**: Use the **`Verification & Retesting`** tab to trigger targeted regression probes against repaired endpoints to mathematically prove vulnerabilities are resolved.
