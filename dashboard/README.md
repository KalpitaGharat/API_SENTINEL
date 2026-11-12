# API SENTINEL — Premium Dark Cybersecurity Dashboard
**Enterprise API Security Testing & Remediation Platform**

A commercial-grade, responsive cybersecurity SaaS dashboard built with **Python**, **Streamlit**, and **Plotly**.

---

## 🛡️ Design System & Color Palette

- **Midnight Navy Background:** `#061426`
- **Deep Navy Sidebar:** `#07182B`
- **Card Background:** `#0B1D32`
- **Cyan Primary Accent:** `#00D4E8`
- **Electric Blue:** `#168BFF`
- **Border Outline:** `#153B58`
- **White Headings:** `#F4F8FF`
- **Muted Text:** `#91A6BD`

---

## 🚀 Key Features

1. **Fixed Enterprise Sidebar**
   - API Sentinel Shield logo & subtitle: *API Security Testing & Remediation*
   - Interactive Navigation with cyan active indicator and gradient glow
   - Slogan: *Find it. Understand it. Fix it. Verify it.*
   - Subtle animated cyan particle-wave SVG decoration with CSS keyframes

2. **Top Header & User Profile**
   - Title & live posture subtitle
   - Unread alert notification pill
   - SecOps Core Team enterprise admin dropdown

3. **4 High-Impact KPI Cards**
   - **Total Scans:** 24 (+26%)
   - **Total Vulnerabilities:** 37 (-18%)
   - **Fixed / Verified:** 28 (+40%)
   - **Security Health:** 76% (+12 points)

4. **Analytics Section (Side-by-Side Cards)**
   - **Severity Distribution:** Plotly Donut Chart displaying **37 Findings** in the center (Critical: 6, High: 10, Medium: 14, Low: 7)
   - **Scan Activity (14 Days):** Interactive Plotly area/line chart with smooth cyan splines and custom dark tooltips

5. **Recent Vulnerability Findings & Last Scan Summary**
   - Formatted security findings table with severity & status badges:
     - Broken Object Level Authorization (BOLA) on `GET /api/users/{id}`
     - Missing Security Headers on `/ (global)`
     - Weak Authentication Configuration on `POST /api/login`
     - Insecure API Configuration on `GET /api/config`
     - Missing Rate Limiting on `POST /api/register`
   - Last scan card with metadata and prominent **Run New Security Scan** CTA

6. **Full Multi-View Architecture**
   - **Security Overview:** Primary executive dashboard
   - **New Security Scan:** Interactive scanner with real-time log terminal and simulated probing
   - **Vulnerability Findings:** Complete list of all 37 findings with CVSS scores, OWASP mapping, and remediation code snippets (FastAPI/Python)
   - **Retesting & Verification:** Live exploit regression runner for verified status promotion
   - **Scan History:** Audit trail of all 24 historical scans
   - **Reports & Compliance:** OWASP API Top 10 breakdown, regulatory scorecards, JSON and CSV exports

7. **Backend Ready Architecture**
   - Isolated HTTPX client (`services/api_client.py`) pre-configured to attach to a FastAPI backend.

---

## 🏃 Quick Start

Run the dashboard with Streamlit:

```bash
cd "C:\Users\AaYushman Parab\.gemini\antigravity\scratch\api-sentinel-dashboard"
streamlit run app.py
```
Or using the Python binary:
```bash
& "C:\Users\AaYushman Parab\AppData\Local\Programs\Python\Python313\python.exe" -m streamlit run app.py
```
