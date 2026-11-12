"""Live HTTP Integration & End-to-End Audit Script for Member 1 Engine.

Spins up the real demo_api on http://127.0.0.1:8001 and backend on http://127.0.0.1:8000
using real TCP sockets, executing live HTTP requests end-to-end.
"""

import sys
import time
import threading
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import httpx
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from demo_api.main import app as demo_app
from demo_api.config import settings as demo_settings
from app.main import app as backend_app
from app.config import settings as backend_settings
from app.database import Base, SessionLocal
from app.security_engine.integration import (
    get_security_engine,
    BaseSecurityEngineAdapter,
    validate_target_safety,
    TargetSafetyError,
)
from app.security_engine.member1_engine import EngineAdapter
from app.models import Scan, Finding, RetestHistory


def start_server(app, port):
    """Run uvicorn in a daemon thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    return server


def wait_for_ready(url, max_attempts=30):
    for _ in range(max_attempts):
        try:
            r = httpx.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def run_audit():
    print("=" * 70)
    print("API SENTINEL – MEMBER 1 REAL ENGINE INTEGRATION AUDIT")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Phase 1 – Inspect Integration Contract
    # -------------------------------------------------------------------------
    print("\n--- PHASE 1: INSPECT INTEGRATION CONTRACT ---")
    engine = get_security_engine()
    print(f"Discovered Engine Class: {type(engine).__name__}")
    print(f"Engine Name: {engine.engine_name}")
    print(f"Is Simulated: {engine.is_simulated}")

    assert issubclass(EngineAdapter, BaseSecurityEngineAdapter), "EngineAdapter must inherit BaseSecurityEngineAdapter"
    assert isinstance(engine, EngineAdapter), "get_security_engine() must return Member 1 EngineAdapter"
    assert engine.engine_name == "api_sentinel_real_detection_engine", f"Wrong engine_name: {engine.engine_name}"
    assert engine.is_simulated is False, "is_simulated must be False for real engine"
    print("[OK] Phase 1 Passed: EngineAdapter correctly implements and registers BaseSecurityEngineAdapter")

    # -------------------------------------------------------------------------
    # Start Real HTTP Servers (TCP Sockets)
    # -------------------------------------------------------------------------
    print("\nStarting live servers on real TCP ports (127.0.0.1:8001 and 127.0.0.1:8000)...")
    demo_settings.DEMO_VULNERABLE_MODE = True
    demo_settings.ENABLE_SECURITY_HEADERS = False
    backend_settings.ALLOW_LOCAL_LAB_SCANNING = True

    demo_server = start_server(demo_app, 8001)
    backend_server = start_server(backend_app, 8000)

    assert wait_for_ready("http://127.0.0.1:8001/health"), "Demo API failed to bind on port 8001"
    assert wait_for_ready("http://127.0.0.1:8000/health"), "Backend API failed to bind on port 8000"
    print("[OK] Live servers online.")

    client = httpx.Client(timeout=15.0)

    try:
        # ---------------------------------------------------------------------
        # Phase 2 – Real HTTP Scanning in Vulnerable Mode
        # ---------------------------------------------------------------------
        print("\n--- PHASE 2: REAL HTTP SCANNING IN VULNERABLE MODE ---")
        scan_payload = {
            "target_url": "http://127.0.0.1:8001",
            "user_authorized": True,
            "categories": ["BOLA", "AUTH", "HEADERS"],
            "test_accounts": {
                "patient_a": {"username": "patient_a", "password": "demo_password_a", "id": 101, "owned_id": 101},
                "patient_b": {"username": "patient_b", "password": "demo_password_b", "id": 102, "owned_id": 102},
            },
        }

        resp_scan = client.post("http://127.0.0.1:8000/api/scans", json=scan_payload)
        print("POST /api/scans status:", resp_scan.status_code)
        assert resp_scan.status_code == 201, f"Failed to create scan: {resp_scan.text}"
        scan_data = resp_scan.json()
        scan_id = scan_data["id"]
        print(f"Scan Created: ID={scan_id}, Status={scan_data['status']}, Total Findings={scan_data['total_findings']}")

        # Verify scan config recorded in SQLite
        assert scan_data["scan_configuration"]["engine_name"] == "api_sentinel_real_detection_engine"
        assert scan_data["scan_configuration"]["is_simulated"] is False
        assert scan_data["scan_configuration"]["test_accounts"]["patient_a"]["password"] == "[REDACTED_FOR_SECURITY]"
        print("[OK] Scan metadata correctly recorded in SQLite with redacted credentials.")

        # Fetch findings
        resp_findings = client.get(f"http://127.0.0.1:8000/api/scans/{scan_id}/findings")
        assert resp_findings.status_code == 200
        findings = resp_findings.json()
        print(f"Retrieved {len(findings)} findings from /api/scans/{scan_id}/findings")

        bola_findings = [f for f in findings if f["category"] == "BOLA"]
        assert len(bola_findings) >= 1, "Expected at least 1 BOLA finding in vulnerable mode!"
        bola = bola_findings[0]
        bola_id = bola["id"]

        print(f"  BOLA Finding ID: {bola_id}")
        print(f"  Vulnerability: {bola['vulnerability']}")
        print(f"  Endpoint: {bola['endpoint']}")
        print(f"  Severity: {bola['severity']}")
        print(f"  Status: {bola['status']}")

        assert "[SIMULATED" not in bola["vulnerability"], "Real finding must NOT contain mock tags!"
        assert bola["vulnerability"] == "Broken Object Level Authorization (BOLA)"
        assert bola["severity"] == "High"
        assert bola["status"] == "Open"

        # Verify evidence
        ev = bola["evidence"]
        print(f"  Evidence: Observed={ev['observed_status']}, Expected={ev['expected_status']}, Resource={ev['requested_resource']}")
        assert ev["observed_status"] == 200
        assert ev["expected_status"] == 403
        assert ev["requested_resource"] == "/api/patients/102"
        assert "patient_a" in ev["test_user"].lower()
        assert "demo_password" not in str(ev)
        print("[OK] Phase 2 Passed: Real BOLA detected over HTTP with verified foreign data exposure and redacted evidence.")

        # ---------------------------------------------------------------------
        # Phase 3 – Test Secure Mode
        # ---------------------------------------------------------------------
        print("\n--- PHASE 3: TEST SECURE MODE (REMEDIATION VERIFICATION) ---")
        # Toggle demo API to secure mode
        resp_mode = client.post("http://127.0.0.1:8001/api/demo/mode", json={"vulnerable": False, "enable_security_headers": True})
        assert resp_mode.status_code == 200
        print("Demo API toggled to SECURE mode (DEMO_VULNERABLE_MODE=False).")

        # Verify patient ownership isolation directly
        # Login Patient A
        r_login_a = client.post("http://127.0.0.1:8001/api/auth/login", json={"username": "patient_a", "password": "demo_password_a"})
        tok_a = r_login_a.json()["access_token"]

        # Patient A accesses own record -> 200 OK
        r_own = client.get("http://127.0.0.1:8001/api/patients/101", headers={"Authorization": f"Bearer {tok_a}"})
        assert r_own.status_code == 200, f"Expected 200 accessing own record, got {r_own.status_code}"
        print("  Direct test: Patient A accessing own record (101) -> HTTP 200 OK")

        # Patient A accesses Patient B's record -> 403 Forbidden
        r_cross = client.get("http://127.0.0.1:8001/api/patients/102", headers={"Authorization": f"Bearer {tok_a}"})
        assert r_cross.status_code == 403, f"Expected 403 accessing cross record, got {r_cross.status_code}"
        print("  Direct test: Patient A accessing Patient B record (102) -> HTTP 403 Forbidden")

        # Run fresh scan against secure mode API
        resp_scan_sec = client.post("http://127.0.0.1:8000/api/scans", json=scan_payload)
        scan_sec_data = resp_scan_sec.json()
        resp_sec_findings = client.get(f"http://127.0.0.1:8000/api/scans/{scan_sec_data['id']}/findings")
        sec_findings = resp_sec_findings.json()
        sec_bola = [f for f in sec_findings if f["category"] == "BOLA"]
        print(f"  Secure Scan BOLA Findings count: {len(sec_bola)}")
        assert len(sec_bola) == 0, "Secure mode API must produce 0 BOLA findings!"
        print("[OK] Phase 3 Passed: Secure mode correctly enforced, cross-user access denied, 0 BOLA findings reported.")

        # ---------------------------------------------------------------------
        # Phase 4 – Retesting Workflow
        # ---------------------------------------------------------------------
        print("\n--- PHASE 4: RETESTING & VERIFICATION WORKFLOW ---")
        # Test Case A: Retest original BOLA finding while API is in SECURE mode -> Resolved
        print("Test 4A: Retesting original BOLA finding while API is SECURE...")
        retest_payload = {"finding_id": bola_id}
        resp_retest_1 = client.post(f"http://127.0.0.1:8000/api/scans/{scan_id}/retest", json=retest_payload)
        assert resp_retest_1.status_code == 200, f"Retest failed: {resp_retest_1.text}"
        retest_1_data = resp_retest_1.json()
        result_item_1 = retest_1_data["results"][0]

        print(f"  Retest Result: Status={result_item_1['new_status']}, Verified={result_item_1['verified']}")
        print(f"  Observed Result: {result_item_1['observed_result']}")
        assert result_item_1["new_status"] == "Resolved", f"Expected Resolved, got {result_item_1['new_status']}"
        assert result_item_1["verified"] is True

        # Verify DB finding was updated to Resolved
        with SessionLocal() as db:
            f_db = db.query(Finding).filter(Finding.id == bola_id).first()
            assert f_db.status == "Resolved", f"DB Finding status must be Resolved, got {f_db.status}"
            history_recs = db.query(RetestHistory).filter(RetestHistory.finding_id == bola_id).all()
            assert len(history_recs) >= 1
            print(f"  Audit trail in DB: {len(history_recs)} RetestHistory records confirmed.")
        print("[OK] 4A Passed: Finding transitioned to 'Resolved' and verified.")

        # Test Case B: Toggle API back to VULNERABLE mode and Retest -> Still Vulnerable
        print("\nTest 4B: Toggling back to VULNERABLE mode and retesting again...")
        client.post("http://127.0.0.1:8001/api/demo/mode", json={"vulnerable": True, "enable_security_headers": False})

        resp_retest_2 = client.post(f"http://127.0.0.1:8000/api/scans/{scan_id}/retest", json=retest_payload)
        assert resp_retest_2.status_code == 200
        retest_2_data = resp_retest_2.json()
        result_item_2 = retest_2_data["results"][0]

        print(f"  Retest Result: Status={result_item_2['new_status']}, Verified={result_item_2['verified']}")
        print(f"  Observed Result: {result_item_2['observed_result']}")
        assert result_item_2["new_status"] == "Still Vulnerable", f"Expected Still Vulnerable, got {result_item_2['new_status']}"
        assert result_item_2["verified"] is False

        with SessionLocal() as db:
            f_db = db.query(Finding).filter(Finding.id == bola_id).first()
            assert f_db.status == "Still Vulnerable"
        print("[OK] 4B Passed: Finding accurately identified as 'Still Vulnerable' when unpatched.")

        # ---------------------------------------------------------------------
        # Phase 5 – Security Verification
        # ---------------------------------------------------------------------
        print("\n--- PHASE 5: SECURITY VERIFICATION ---")
        # 1. Cloud metadata
        try:
            validate_target_safety("http://169.254.169.254/latest/meta-data", allow_lab=True)
            assert False, "Failed to block cloud metadata IP!"
        except TargetSafetyError:
            print("[OK] Cloud metadata endpoint blocked (even when allow_lab=True).")

        # 2. Local loopback blocked when allow_lab=False
        try:
            validate_target_safety("http://127.0.0.1:8001", allow_lab=False)
            assert False, "Failed to block loopback when allow_lab=False!"
        except TargetSafetyError:
            print("[OK] Local loopback blocked when allow_lab=False.")

        # 3. Invalid scheme
        try:
            validate_target_safety("ftp://api.example.com", allow_lab=True)
            assert False, "Failed to block FTP scheme!"
        except TargetSafetyError:
            print("[OK] Non-HTTP/HTTPS schemes blocked.")

        # 4. Mandatory Authorization confirmation
        r_unauth_scan = client.post("http://127.0.0.1:8000/api/scans", json={
            "target_url": "http://127.0.0.1:8001",
            "user_authorized": False,
        })
        assert r_unauth_scan.status_code == 422, "Missing authorization must return 422"
        print("[OK] Scan rejected when user_authorized is False or missing.")

        print("\n" + "=" * 70)
        print("ALL PHASES PASSED SUCCESSFULLY WITH REAL HTTP TCP TRAFFIC!")
        print("=" * 70)

    finally:
        demo_server.should_exit = True
        backend_server.should_exit = True


if __name__ == "__main__":
    run_audit()
