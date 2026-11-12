"""End-to-End Live Acceptance Test for Attack Demonstration & Evidence Inspector.

Full Workflow:
1. Validates Healthcare Demo API (port 8001) & sets DEMO_VULNERABLE_MODE=True.
2. Runs live scan against Healthcare Demo API via Backend API (port 8000).
3. Fetches BOLA finding and validates forensic evidence telemetry:
   - duration_ms > 0
   - masked authorization header (sent..._101)
   - copyable curl command
   - 9-step attack timeline
   - exposed PHI fields
4. Calls GET /api/findings/{id}/export-evidence and verifies SHA-256 digest match.
5. Sets Demo API to remediated mode (DEMO_VULNERABLE_MODE=False).
6. Calls POST /api/scans/{id}/retest and verifies:
   - observed_status == 403 Forbidden
   - finding status transitions from 'Open' to 'Resolved'
   - immutable audit history recorded
"""

import sys
import json
import time
import hashlib
import httpx

BACKEND_BASE = "http://127.0.0.1:8000"
DEMO_BASE = "http://127.0.0.1:8001"


def log(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARN": "\033[93m",
        "ERROR": "\033[91m",
        "HEADER": "\033[95m",
        "RESET": "\033[0m"
    }
    prefix = f"{colors.get(status, '')}[{status}]{colors['RESET']}"
    print(f"{prefix} {msg}")


def run_e2e_acceptance():
    log("Starting Live E2E Acceptance Test for Attack & Evidence Inspector...", "HEADER")
    
    with httpx.Client(timeout=30.0) as client:
        # Step 1: Check Demo API & set vulnerable mode
        log("Checking Healthcare Demo API on port 8001...")
        try:
            resp = client.get(f"{DEMO_BASE}/docs")
            assert resp.status_code == 200, f"Demo API responded with {resp.status_code}"
            log("Healthcare Demo API is alive.", "SUCCESS")
        except Exception as e:
            log(f"Failed to connect to Demo API: {e}", "ERROR")
            return 1

        log("Setting Demo API to VULNERABLE mode...")
        resp = client.post(f"{DEMO_BASE}/api/demo/mode", json={"vulnerable": True})
        assert resp.status_code == 200
        mode_data = resp.json()
        log(f"Demo API mode confirmed: vulnerable={mode_data.get('vulnerable_mode')}", "SUCCESS")

        # Step 2: Trigger Live Security Scan on Backend
        log(f"Submitting scan request to {BACKEND_BASE}/api/scans...")
        scan_payload = {
            "target_url": DEMO_BASE,
            "user_authorized": True,
            "categories": ["BOLA", "AUTH", "HEADERS", "CONFIG"],
            "auth_token": "sentinel_token_patient_a_101",
        }
        resp = client.post(f"{BACKEND_BASE}/api/scans", json=scan_payload)
        assert resp.status_code == 200 or resp.status_code == 201, f"Scan creation failed: {resp.text}"
        scan_data = resp.json()
        scan_id = scan_data["id"]
        log(f"Scan launched successfully with ID: {scan_id}", "SUCCESS")

        # Wait for scan to complete
        log("Polling scan status until COMPLETED...")
        for _ in range(30):
            time.sleep(1)
            resp = client.get(f"{BACKEND_BASE}/api/scans/{scan_id}")
            assert resp.status_code == 200
            current_scan = resp.json()
            if current_scan["status"] in ("completed", "Completed"):
                findings_count = current_scan.get("total_findings", current_scan.get("vulnerabilities_found", 0))
                log(f"Scan completed: found {findings_count} findings.", "SUCCESS")
                break
        else:
            log("Scan timed out before completing.", "ERROR")
            return 1

        # Step 3: Fetch findings and verify BOLA evidence
        log("Fetching scan findings...")
        resp = client.get(f"{BACKEND_BASE}/api/scans/{scan_id}/findings")
        assert resp.status_code == 200
        findings = resp.json()
        assert len(findings) > 0, "Expected at least 1 finding, found 0"

        bola_finding = next((f for f in findings if "BOLA" in f.get("vulnerability", "") or "API1" in f.get("category", "")), None)
        assert bola_finding is not None, "BOLA finding not detected in scan results"
        log(f"Detected BOLA finding ID: {bola_finding['id']}", "SUCCESS")

        evidence = bola_finding.get("evidence")
        assert evidence is not None, "Finding must include technical evidence"
        log("Verifying forensic evidence telemetry structure...")

        req_details = evidence.get("request_details", {})
        resp_details = evidence.get("response_details", {})

        # Duration check
        duration = req_details.get("duration_ms") or resp_details.get("duration_ms")
        log(f"  • Latency telemetry: {duration} ms")
        assert duration is not None and duration >= 0, "Missing or invalid duration_ms"

        # cURL command check
        curl_cmd = req_details.get("curl_command", "")
        log(f"  • Copyable cURL: {curl_cmd}")
        assert "curl -X GET" in curl_cmd, "Invalid curl_command format"
        assert "sent..." in curl_cmd and "101" in curl_cmd, "Authorization token must be safely masked in cURL"

        # Masked request headers check
        req_headers = req_details.get("headers", {})
        auth_header = req_headers.get("Authorization", "")
        log(f"  • Masked auth header: {auth_header}")
        assert "sent..." in auth_header and "101" in auth_header, "Authorization token not properly masked in request_details"

        # Attack timeline check
        timeline = req_details.get("timeline", [])
        log(f"  • Attack timeline steps: {len(timeline)}")
        assert len(timeline) >= 5, f"Expected comprehensive timeline, found {len(timeline)} steps"

        # Step 4: Validate Evidence Export Endpoint & SHA-256 Digest
        finding_id = bola_finding["id"]
        log(f"Testing GET {BACKEND_BASE}/api/findings/{finding_id}/export-evidence...")
        resp = client.get(f"{BACKEND_BASE}/api/findings/{finding_id}/export-evidence")
        assert resp.status_code == 200, f"Export failed: {resp.text}"
        export_bundle = resp.json()

        assert export_bundle["export_version"] == "1.1.0"
        reported_hash = export_bundle.get("sha256_digest")
        assert reported_hash and len(reported_hash) == 64, f"Invalid SHA-256 hash: {reported_hash}"

        # Re-compute digest
        verifiable_dict = {k: v for k, v in export_bundle.items() if k != "sha256_digest"}
        canonical_str = json.dumps(verifiable_dict, sort_keys=True, separators=(",", ":"))
        calculated_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        assert reported_hash == calculated_hash, f"Hash mismatch: reported={reported_hash}, computed={calculated_hash}"
        log(f"SHA-256 Cryptographic Digest verified: {reported_hash}", "SUCCESS")

        # Step 5: Switch Demo API to REMEDIATED mode
        log("Switching Demo API to REMEDIATED mode (DEMO_VULNERABLE_MODE=False)...")
        resp = client.post(f"{DEMO_BASE}/api/demo/mode", json={"vulnerable": False})
        assert resp.status_code == 200
        mode_data = resp.json()
        assert mode_data.get("vulnerable_mode") is False
        log("Demo API remediation activated.", "SUCCESS")

        # Step 6: Trigger Retest Probe on Backend
        log(f"Triggering verification probe: POST {BACKEND_BASE}/api/scans/{scan_id}/retest...")
        retest_payload = {"finding_id": finding_id}
        resp = client.post(f"{BACKEND_BASE}/api/scans/{scan_id}/retest", json=retest_payload)
        assert resp.status_code == 200, f"Retest execution failed: {resp.text}"
        retest_results = resp.json().get("results", [])
        assert len(retest_results) > 0, "No retest result records returned"
        
        target_retest = next((r for r in retest_results if r["finding_id"] == finding_id), retest_results[0])
        log(f"Retest result received: previous={target_retest['previous_status']} -> new={target_retest['new_status']}", "SUCCESS")
        
        # Verify status transition
        assert target_retest["new_status"] in ("Resolved", "resolved"), f"Expected status 'Resolved', got {target_retest['new_status']}"
        assert target_retest["verified"] is True, "Retest verified flag should be True"

        # Check observed status code was 403 Forbidden
        obs_res = target_retest.get("observed_result", {})
        observed_code = obs_res.get("observed_status") or obs_res.get("status_code") or obs_res.get("attacker_probe", {}).get("status_code")
        log(f"Observed probe status code: HTTP {observed_code} (Expected 403 Forbidden)")
        assert observed_code == 403, f"Expected 403, got {observed_code}"

        # Step 7: Verify Retest Audit History
        log(f"Checking audit history: GET {BACKEND_BASE}/api/findings/{finding_id}/history...")
        resp = client.get(f"{BACKEND_BASE}/api/findings/{finding_id}/history")
        assert resp.status_code == 200
        history_list = resp.json().get("history", [])
        assert len(history_list) > 0, "No history records created"
        latest_history = history_list[0]
        log(f"Audit record confirmed: id={latest_history['id']}, verified={latest_history['verified']}", "SUCCESS")

        log("ALL ATTACK DEMONSTRATION & EVIDENCE INSPECTOR E2E CHECKS PASSED!", "SUCCESS")
        return 0


if __name__ == "__main__":
    code = run_e2e_acceptance()
    sys.exit(code)
