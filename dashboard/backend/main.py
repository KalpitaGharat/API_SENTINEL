"""
API Sentinel - FastAPI Enterprise Backend Server
"""

import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Ensure project root is in sys.path to access services
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.mock_data import (
    KPI_METRICS,
    SEVERITY_DISTRIBUTION,
    get_14_day_scan_activity,
    RECENT_FINDINGS,
    get_all_37_findings,
    LAST_SCAN_SUMMARY,
    SCAN_HISTORY_LOG,
)

app = FastAPI(title="API Sentinel Backend", version="1.0.0")

# Enable CORS for React frontend (port 5173 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    target_url: str
    scan_profile: str
    headers: Optional[Dict[str, str]] = None

@app.get("/metrics/summary")
def get_kpi_metrics():
    return KPI_METRICS

@app.get("/findings/distribution")
def get_distribution():
    return SEVERITY_DISTRIBUTION

@app.get("/scans/activity")
def get_activity():
    return get_14_day_scan_activity()

@app.get("/findings/recent")
def get_recent():
    return RECENT_FINDINGS

@app.get("/findings")
def get_all():
    return get_all_37_findings()

@app.get("/scans/last")
def get_last_scan():
    return LAST_SCAN_SUMMARY

@app.post("/scans/trigger")
def trigger_scan(req: ScanRequest):
    return {
        "scan_id": "SCAN-2026-LIVE-01",
        "target": req.target_url,
        "profile": req.scan_profile,
        "status": "QUEUED",
        "estimated_duration": "3m 26s"
    }

@app.get("/scans/history")
def get_history():
    return SCAN_HISTORY_LOG

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
