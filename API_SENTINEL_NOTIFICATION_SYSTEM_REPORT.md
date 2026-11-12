# API Sentinel — Security Alert & Notification System Report

**Feature:** Critical Vulnerability In-App Modal & Notification Center  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Date:** November 11, 2026  

---

## 1. Executive Overview

API Sentinel features a two-tiered alert architecture designed to notify developers and security operators of critical security incidents without disrupting their workflow:

1. **Immediate In-App Modal Alert:** High-impact popup for newly discovered `Critical` vulnerabilities.
2. **Persistent Notification Center Drawer:** Slide-down notification tray tracking historical security telemetry, scan lifecycle events, and acknowledgements.

---

## 2. In-App Modal Alert (`CriticalAlertModal.jsx`)

### Visual Design:
- **Cyber Dark Backdrop:** `rgba(2, 6, 18, 0.78)` with `backdrop-filter: blur(8px)`.
- **Pulsing Neon Alert Border:** `#FF4D5E` (Crimson) for Critical alerts, with glowing box shadow `0 0 35px rgba(255, 77, 94, 0.45)`.
- **Top Scanline Animation:** CSS linear scanline moving across the modal banner.
- **Vulnerability Telemetry Display:**
  - Vulnerability name (e.g. *Broken Object Level Authorization (BOLA)*)
  - Affected endpoint in monospace (e.g. `GET /api/v1/patients/{patient_id}`)
  - OWASP category pill
  - Plain-English breakdown
  - Severity pill: `CRITICAL ALERT`

### Interactive Controls:
- **`[ Inspect Finding with AI ]`:**
  - Automatically acknowledges the alert.
  - Switches dashboard view to `Vulnerability Findings`.
  - Auto-expands the specific finding.
  - Displays the NVIDIA Nemotron AI explanation panel immediately.
- **`[ Acknowledge & Dismiss ]`:**
  - Marks the finding as acknowledged in `ScanContext`.
  - Persists finding ID into `localStorage` (`apisentinel_acknowledged_alerts`).
  - Closes the modal and prevents duplicate popups on future page refreshes.

---

## 3. Persistent Notification Center (`NotificationCenter.jsx`)

### Access:
- Click the **Bell Icon** in the top navigation header (`Header.jsx`).
- An active alert count badge displays in bold crimson (e.g. `3 Active`).

### Capabilities:
- Displays all recent security alerts and system telemetry events.
- Color-coded borders based on severity (`Critical` = Red, `High` = Orange, `Info` = Cyan).
- **"Inspect Finding"** direct jump button on each vulnerability alert.
- **"Acknowledge All"** single-click button to clear active badges.
- Clean empty state when all notifications have been reviewed.
