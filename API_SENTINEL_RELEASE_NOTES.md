# API Sentinel — Release Notes (v1.0.0 Production Release)

**Release Version:** `v1.0.0`  
**Release Date:** 2026-11-11  
**Tagline:** Find it. Understand it. Fix it. Verify it.

---

## 1. Release Highlights

API Sentinel is an explainable API security testing, intelligence, and remediation platform designed for student developers and small businesses. Version 1.0.0 marks the completion of all stabilization, security hardening, live update telemetry, and dual-engine AI explainability workflows.

---

## 2. What's Included in v1.0.0

### Core Security Detection Engine
- **Member 1 Real Security Engine Integration**: Performs live detection of Broken Object Level Authorization (BOLA/IDOR), authentication bypass vectors, missing security headers, and API misconfigurations.
- **Controlled Healthcare Demo API**: Intentionally vulnerable synthetic patient API (`port 8001`) with dynamic vulnerable/secure mode switching for live testing demonstrations.

### AI-Powered Explainability
- **NVIDIA Nemotron Dual Engine**: Remote inference via `nvidia/nemotron-3.5-lightning-30b-a3b` backed by an instant offline deterministic rule fallback engine.
- **Tri-Fold Analysis Structure**: Every vulnerability produces:
  1. Plain-English Vulnerability Breakdown.
  2. Realistic Attack Scenarios & Regulatory Impact (HIPAA/GDPR).
  3. Step-by-Step Remediation code diffs and verification tests.
- **Instant SQLite Caching**: All generated explanations are stored in SQLite and load in <10ms on repeat visits.

### Live Telemetry & Real-Time Sync
- **Server-Sent Events (SSE)**: Native `/api/events` pub/sub stream eliminates manual browser refreshing.
- **In-App Critical Alert Modal**: High-severity vulnerabilities trigger an immediate in-app warning modal with persistent acknowledgment.
- **Notification Drawer**: Centralized notification center with severity filtering.

### Verification & Targeted Retesting
- **Automated Regression Probes**: Re-executes targeted HTTP requests against repaired endpoints.
- **State Transition Engine**: Automatically transitions findings from `Still Vulnerable` to `Resolved` once fixes are mathematically proven.
- **Append-Only Retest Audit Trail**: Full historical verification timeline stored in SQLite.

### Production-Ready Dashboard
- **9 Fully Implemented Navigation Views**:
  1. 🛡️ Security Overview
  2. 🚀 New Security Scan
  3. 📋 Scan History
  4. ⚠️ Vulnerability Findings
  5. 🤖 AI Security Analysis *(Dedicated Hub)*
  6. 🧪 Verification & Retesting
  7. 🔔 Notifications
  8. 📄 Security Reports
  9. ⚙️ System Settings & Diagnostics
- **Persistent Version Badge**: `API Sentinel | v1.2.0-phase5-prod` rendered on sidebar footer.
- **Dual-Serving Architecture**: Served directly via Vite (`port 5173`) or statically mounted by FastAPI (`port 8000`).

---

## 3. Compatibility & Requirements

- **Backend:** Python 3.11 – 3.13
- **Frontend:** Node.js 18+, React 18, Vite 5, Tailwind CSS
- **Database:** SQLite 3.35+ with WAL mode enabled
- **Docker:** Docker 24+, Docker Compose v2+
