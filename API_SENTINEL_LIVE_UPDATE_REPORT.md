# API Sentinel — Real-Time Live Update & SSE Architecture Report

**Component:** Live Dashboard Telemetry & Server-Sent Events (SSE)  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Date:** November 11, 2026  

---

## 1. Architectural Overview

Security scanning platforms cannot require operators to manually refresh the page to detect completed audits, failures, or critical vulnerabilities.

API Sentinel implements an asynchronous **Server-Sent Events (SSE)** architecture:
- **Backend Broadcaster:** `app/services/event_service.py` (`EventBroadcaster`)
- **Telemetry Streaming Route:** `app/routes/events.py` (`GET /api/events`)
- **Frontend Consumer:** `frontend/src/context/ScanContext.jsx` via HTML5 `EventSource`

```
  +-------------------------------------------------------+
  |              FastAPI Security Core Engine             |
  +-------------------------------------------------------+
         |                        |                     |
   (Scan Created)           (Critical Finding)     (Scan Completed)
         |                        |                     |
         v                        v                     v
  +-------------------------------------------------------+
  |          EventBroadcaster (Pub/Sub Async Queues)      |
  +-------------------------------------------------------+
                              |
                     SSE Stream (/api/events)
                              |
                              v
  +-------------------------------------------------------+
  |            React Frontend ScanContext (SSE)           |
  |  - Auto-refreshes Scans & Findings                    |
  |  - Triggers In-App Critical Alert Modal               |
  |  - Updates Notification Center Feed                   |
  |  - Updates KPI Stats & Health Scores                  |
  +-------------------------------------------------------+
```

---

## 2. Event Specifications & Schemas

### `connected`
Sent immediately upon client connection establishment.
```json
{
  "status": "connected",
  "timestamp": "2026-11-11T05:45:00.000Z",
  "channel": "api_sentinel_live_telemetry"
}
```

### `scan_created`
Broadcast when a scan transaction is initialized in SQLite.
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_url": "http://127.0.0.1:8001",
  "status": "Running",
  "created_at": "2026-11-11T05:45:01.000Z"
}
```

### `critical_finding`
Broadcast immediately when a vulnerability with `severity` of `Critical` or `High` is discovered during a scan session.
```json
{
  "finding_id": "7b2c918a-f331-4e2b-a256-4298110b91e2",
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "vulnerability": "Broken Object Level Authorization (BOLA)",
  "endpoint": "GET /api/v1/patients/{patient_id}",
  "severity": "Critical",
  "category": "BOLA",
  "description": "Endpoint returns patient medical record without validating caller ownership.",
  "created_at": "2026-11-11T05:45:04.000Z"
}
```

### `scan_completed`
Broadcast when the testing engine finishes and all findings are committed.
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_url": "http://127.0.0.1:8001",
  "status": "Completed",
  "total_findings": 5,
  "completed_at": "2026-11-11T05:45:08.000Z"
}
```

### `retest_completed`
Broadcast when verification probes finish against targeted endpoints.
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "retested_at": "2026-11-11T05:46:12.000Z",
  "verified_count": 1,
  "total_retested": 1
}
```

---

## 3. Resilience & Connection Recovery

1. **Keep-Alive Heartbeats:** A `: ping\n\n` comment is streamed every 15 seconds to prevent intermediate proxy timeouts.
2. **Auto-Reconnect:** If disconnected, `EventSource` auto-reconnects with an exponential backoff strategy (6s reconnect cycle).
3. **Heartbeat Polling Fallback:** In the event that a corporate firewall or proxy terminates SSE, a 12-second background poll acts as a safety net.
4. **Subscriber Cleanup:** Disconnected client queues are automatically purged via `request.is_disconnected()` checks, preventing memory leaks.
