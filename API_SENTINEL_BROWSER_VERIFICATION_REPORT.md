# API Sentinel — Browser Verification & Visual Evidence Report

## 1. Visual Verification Overview

Headless Google Chrome automated verification was conducted on port `5173` (Vite Dev Server) and port `8000` (FastAPI Static Serve).

Three high-resolution screen captures were recorded and saved directly in the project workspace:

1. **`dashboard_overview_live.png`**: Security Overview dashboard showing live telemetry, health scores, OWASP distribution, and the prominent NVIDIA Nemotron banner.
2. **`dashboard_findings_live.png`**: Vulnerability Findings view showing auto-expanded finding cards, HTTP request evidence, and the prominent purple `AI-POWERED SECURITY ANALYSIS` card with the `✨ Explain with Nemotron AI` button.
3. **`dashboard_ai_live.png`**: Dedicated NVIDIA Nemotron AI Security Analysis view showing the left-hand finding selector and right-hand structured analysis deck.

---

## 2. Visual Comparison: User's Previous View vs. Active Rebuild

| Visual Element | User's Previous View (Stale Process) | Current Active Rebuild (`v1.2.0-phase5-prod`) |
|---|---|---|
| **Sidebar Items** | 6 items only | **9 items** (Overview, New Scan, History, Findings, **AI Security Analysis**, Verification, **Notifications**, Reports, **Settings**) |
| **AI Hub Navigation** | Not present | **Dedicated `AI Security Analysis` tab with bright `+ AI` badge** |
| **Header Title** | Hardcoded to "Security Overview" on all pages | **Dynamic page title** matching the active tab |
| **Live Stream Badge** | Not present | **Green `● LIVE STREAM` badge** indicating real-time SSE stream |
| **Notification Center** | Not present | **Bell icon with live badge counter** and slide-out notification drawer |
| **Build Identity Badge** | Missing | **Persistent `v1.2.0-phase5-prod` badge** in sidebar footer |
| **Vulnerability Cards** | Collapsed rows requiring manual click | **Auto-expanded first card** with prominent AI Explanation Box |
| **Nemotron Integration** | Hidden inside collapsed accordion | **Directly visible on Overview, Findings, and Dedicated AI Hub** |

---

## 3. Real Server Verification

All three application layers are verified active and responding:

```text
Port 8001 (Healthcare Demo API):  HTTP/1.1 200 OK (Uvicorn PID Daemon)
Port 8000 (FastAPI Core Backend): HTTP/1.1 200 OK (Uvicorn PID Daemon)
Port 5173 (React Vite Dev Server): HTTP/1.1 200 OK (Vite PID Daemon)
```
