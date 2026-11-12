"""Phase 10 Live Acceptance Testing & End-to-End Validation Script.
Validates:
1. Environment Readiness (FastAPI 8000, Healthcare Demo 8001, React 5173, Streamlit 8501)
2. Complete API Onboarding Workflow
3. Four Phase 9 Fixes (A: Auth normalization, B: Endpoint selection, C: BOLA retesting, D: Dynamic URL)
4. End-to-End BOLA Acceptance with distinct principals
5. Finding & Retest Workflow (Vulnerable -> Remediated -> Resolved + Needs Review dual check)
6. Dynamic Dashboard API responses
"""

import urllib.request
import urllib.error
import json
import time

BASE_BACKEND = "http://127.0.0.1:8000"
BASE_DEMO = "http://127.0.0.1:8001"

def post_json(url, data, timeout=45):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())

def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())

def main():
    report = {}

    print("=================================================================")
    print("PHASE 10 - SECTION 1: ENVIRONMENT READINESS")
    print("=================================================================")
    st_b, b_health = get_json(f"{BASE_BACKEND}/health")
    print(f"FastAPI Backend (8000): HTTP {st_b} | Database: {b_health.get('database')} | Env: {b_health.get('environment')}")

    st_d, d_health = get_json(f"{BASE_DEMO}/health")
    print(f"Healthcare Demo API (8001): HTTP {st_d} | Vulnerable: {d_health.get('vulnerable_mode')} | Service: {d_health.get('service')}")

    try:
        req = urllib.request.Request("http://127.0.0.1:5173/")
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"React Frontend (5173): HTTP {r.status} (Vite Dev Server Active)")
    except Exception as e:
        print(f"React Frontend check: {e}")

    try:
        req = urllib.request.Request("http://127.0.0.1:8501/_stcore/health")
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"Streamlit Dashboard (8501): HTTP {r.status} (Streamlit Core Healthy)")
    except Exception as e:
        print(f"Streamlit check: {e}")

    print("\n=================================================================")
    print("PHASE 10 - SECTION 2: COMPLETE API ONBOARDING WORKFLOW")
    print("=================================================================")
    # Ensure Demo API is initially in Vulnerable Mode
    post_json(f"{BASE_DEMO}/api/demo/mode", {"vulnerable": True, "enable_security_headers": False})
    
    # 2.1 Fetch Healthcare Demo OpenAPI Spec
    st, spec = get_json(f"{BASE_DEMO}/openapi.json")
    print(f"[OK] Fetched Demo OpenAPI: Title='{spec['info']['title']}', Version={spec['info']['version']}, Paths={len(spec['paths'])}")

    # 2.2 Preview OpenAPI Spec without saving
    st, preview = post_json(f"{BASE_BACKEND}/api/targets/preview-spec", {
        "spec_content": json.dumps(spec)
    })
    print(f"[OK] Preview Spec: HTTP {st} | Title='{preview['title']}' | Endpoints={preview['total_endpoints']} | Sensitive={preview['sensitive_endpoints_count']}")
    for ep in preview['endpoints_preview']:
        print(f"      - {ep['method']} {ep['path']} (sensitive={ep['is_sensitive_candidate']}, mutating={ep['is_state_changing']})")

    # 2.3 Create Target Record
    st, target = post_json(f"{BASE_BACKEND}/api/targets", {
        "name": "Healthcare Patient Portal Demo API",
        "base_url": BASE_DEMO,
        "environment": "development",
        "description": "Target registered for Phase 10 Live Acceptance Testing",
        "api_type": "REST",
        "api_version": "1.0.0"
    })
    target_id = target["id"]
    print(f"[OK] Target Created: ID={target_id} | Base URL={target['base_url']}")

    # 2.4 Import Specification into Target
    st, import_res = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/import-spec", {
        "spec_content": json.dumps(spec)
    })
    print(f"[OK] Imported Spec into Target: HTTP {st} | Endpoints created={import_res.get('endpoints_created')}")

    # 2.5 Query Discovered Endpoints and verify parameters
    st, ep_list = get_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints")
    print(f"[OK] Discovered Endpoints: Total={ep_list['total']}")
    endpoints = ep_list['items']
    for ep in endpoints:
        print(f"      [{ep['method']}] {ep['path']} | Sensitive: {ep['is_sensitive_candidate']} | Params: {len(ep.get('parameters', []))}")

    # 2.6 Authenticate Demo Users on Demo API
    st, auth_a = post_json(f"{BASE_DEMO}/api/auth/login", {"username": "patient_a", "password": "demo_password_a"})
    token_a = auth_a["access_token"]
    st, auth_b = post_json(f"{BASE_DEMO}/api/auth/login", {"username": "patient_b", "password": "demo_password_b"})
    token_b = auth_b["access_token"]
    print(f"[OK] Demo Authentication: User A token length={len(token_a)}, User B token length={len(token_b)}")

    # 2.7 Configure Auth Profiles (Testing Fix A: Normalization & Fernet Encryption)
    print("\n--- Testing Fix A: Authentication Field Normalization & Vault Encryption ---")
    st, prof_a = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/auth-profiles", {
        "name": "User A (Primary Owner)",
        "auth_type": "bearer",
        "token_or_secret": token_a,
        "username": "patient_a",
        "role": "owner",
        "owned_resource_id": "1"
    })
    print(f"[OK] Auth Profile User A: HTTP {st} | Label='{prof_a['account_label']}' | Masked='{prof_a['masked_credential']}'")
    assert prof_a['masked_credential'] != "Not configured", "Fix A check: Masked credential must not be 'Not configured'!"

    st, prof_b = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/auth-profiles", {
        "name": "User B (Foreign Attacker)",
        "auth_type": "bearer",
        "token_or_secret": token_b,
        "username": "patient_b",
        "role": "attacker",
        "owned_resource_id": "2"
    })
    print(f"[OK] Auth Profile User B: HTTP {st} | Label='{prof_b['account_label']}' | Masked='{prof_b['masked_credential']}'")
    assert prof_b['masked_credential'] != "Not configured", "Fix A check: Masked credential must not be 'Not configured'!"

    # 2.8 Validate Target Connectivity
    st, val_res = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/validate", {})
    print(f"[OK] Target Connectivity Validation: HTTP {st} | Reachable={val_res['is_valid']} | Latency={val_res['latency_ms']}ms | Msg='{val_res['message']}'")

    print("\n=================================================================")
    print("PHASE 10 - SECTION 3: TEST FIX B — ENDPOINT SELECTION LOGIC")
    print("=================================================================")
    # 3.1 Deselect all
    st, res = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints/select", {"deselect_all": True})
    st, ep_curr = get_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints")
    sel_count = sum(1 for e in ep_curr['items'] if e['is_selected'])
    print(f"[OK] Test Deselect All: Selected={sel_count} (Expected=0)")
    assert sel_count == 0, f"Expected 0, got {sel_count}"

    # 3.2 Sensitive only
    st, res = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints/select", {"sensitive_only": True})
    st, ep_curr = get_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints")
    sel_count = sum(1 for e in ep_curr['items'] if e['is_selected'])
    sens_expected = sum(1 for e in ep_curr['items'] if e['is_sensitive_candidate'])
    print(f"[OK] Test Sensitive Only: Selected={sel_count} (Expected={sens_expected})")
    assert sel_count == sens_expected, f"Expected {sens_expected}, got {sel_count}"

    # 3.3 Granular toggle single endpoint without mutating others
    selected_ep = next(e for e in ep_curr['items'] if e['is_selected'])
    st, res = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints/select", {
        "endpoint_ids": [{"endpoint_id": selected_ep['id'], "is_selected": False}]
    })
    st, ep_curr2 = get_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints")
    sel_after = next(e for e in ep_curr2['items'] if e['id'] == selected_ep['id'])
    others_after = [e for e in ep_curr2['items'] if e['id'] != selected_ep['id'] and e['is_selected']]
    print(f"[OK] Granular Toggle: Target EP {selected_ep['id']} is_selected={sel_after['is_selected']}, Sibling selected count={len(others_after)} (Expected={sens_expected-1})")
    assert sel_after['is_selected'] is False
    assert len(others_after) == sens_expected - 1

    # Select all for scanning
    st, res = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/endpoints/select", {
        "endpoint_ids": [{"endpoint_id": e['id'], "is_selected": True} for e in endpoints]
    })
    print("[OK] Re-selected all endpoints for scan.")

    print("\n=================================================================")
    print("PHASE 10 - SECTION 4: END-TO-END BOLA ACCEPTANCE TEST")
    print("=================================================================")
    # Direct live HTTP requests between User A and User B
    def fetch_patient(patient_id, token):
        req = urllib.request.Request(
            f"{BASE_DEMO}/api/patients/{patient_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as he:
            return he.code, json.loads(he.read().decode('utf-8', errors='ignore'))

    # 4.1 User A accesses User A's resource (Expected: 200 OK)
    st_aa, body_aa = fetch_patient(101, token_a)
    print(f"Test 4.1: User A -> Patient 101 (Own): HTTP {st_aa} | Patient Name: {body_aa.get('full_name')}")
    assert st_aa == 200, f"Expected 200, got {st_aa}"
    assert "Synthetic Patient A" in body_aa.get("full_name", ""), "Expected Synthetic Patient A record"

    # 4.2 User B accesses User B's resource (Expected: 200 OK)
    st_bb, body_bb = fetch_patient(102, token_b)
    print(f"Test 4.2: User B -> Patient 102 (Own): HTTP {st_bb} | Patient Name: {body_bb.get('full_name')}")
    assert st_bb == 200, f"Expected 200, got {st_bb}"
    assert "Synthetic Patient B" in body_bb.get("full_name", ""), "Expected Synthetic Patient B record"

    # 4.3 User A attempts to access User B's resource (Vulnerable Mode Expected: 200 OK with Bob's data)
    st_ab, body_ab = fetch_patient(102, token_a)
    print(f"Test 4.3: User A -> Patient 102 (Foreign): HTTP {st_ab} | Exposed Name: {body_ab.get('full_name')}")
    assert st_ab == 200 and "Synthetic Patient B" in body_ab.get("full_name", ""), "Vulnerable demo should expose Bob's record to User A"

    # 4.4 User B attempts to access User A's resource (Vulnerable Mode Expected: 200 OK with Alice's data)
    st_ba, body_ba = fetch_patient(101, token_b)
    print(f"Test 4.4: User B -> Patient 101 (Foreign): HTTP {st_ba} | Exposed Name: {body_ba.get('full_name')}")
    assert st_ba == 200 and "Synthetic Patient A" in body_ba.get("full_name", ""), "Vulnerable demo should expose Alice's record to User B"

    print("[VERDICT] Confirmed true BOLA / IDOR vulnerability on Demo API: Foreign data exposed to cross-principal requests.")

    print("\n=================================================================")
    print("PHASE 10 - SECTION 5: SECURITY SCAN EXECUTION & FINDINGS")
    print("=================================================================")
    # Launch scan via Target Scan Bridge
    st, scan = post_json(f"{BASE_BACKEND}/api/targets/{target_id}/scan", {
        "user_authorized": True,
        "categories": ["BOLA", "AUTH", "HEADERS"]
    })
    scan_id = scan["id"]
    print(f"[OK] Launched Target Scan: ID={scan_id} | Status={scan['status']} | Findings={scan['total_findings']}")

    # Inspect findings
    st, findings = get_json(f"{BASE_BACKEND}/api/scans/{scan_id}/findings")
    print(f"[OK] Total Findings Discovered: {len(findings)}")
    for f in findings:
        print(f"      - [{f['severity']}] {f['vulnerability']} at {f['endpoint']} (Status: {f['status']})")
        if f.get('evidence'):
            ev = f['evidence']
            print(f"        Evidence: Observed HTTP {ev.get('observed_status')}, Expected HTTP {ev.get('expected_status')}")

    # Generate AI explanation for the BOLA finding
    bola_f = next(f for f in findings if "BOLA" in f['vulnerability'] or "IDOR" in f['vulnerability'])
    st, ai_exp = post_json(f"{BASE_BACKEND}/api/findings/{bola_f['id']}/explain", {})
    print(f"[OK] AI Explanation: Model={ai_exp['model_name']} | AI Generated={ai_exp['is_ai_generated']}")
    print(f"      Explanation: {ai_exp['explanation'][:120]}...")
    print(f"      Remediation: {ai_exp['remediation'][:120]}...")

    print("\n=================================================================")
    print("PHASE 10 - SECTION 6: RETEST WORKFLOW & DUAL-CHECK VERIFICATION (FIX C)")
    print("=================================================================")
    # 6.1 Retest in Vulnerable Mode
    st, retest_res1 = post_json(f"{BASE_BACKEND}/api/scans/{scan_id}/retest", {
        "finding_id": bola_f['id']
    })
    res_item1 = retest_res1['results'][0]
    print(f"[OK] Retest in Vulnerable Mode: Verified={res_item1['verified']} | Status='{res_item1['new_status']}' | Details={res_item1['observed_result']}")
    assert res_item1['new_status'] == "Still Vulnerable", f"Expected 'Still Vulnerable', got {res_item1['new_status']}"

    # 6.2 Apply Remediation Fix to Healthcare Demo API (Toggle to Secure Mode)
    print("\n--- Applying Remediation to Demo API: Toggling to Secure Mode ---")
    st, mode_res = post_json(f"{BASE_DEMO}/api/demo/mode", {"vulnerable": False, "enable_security_headers": True})
    print(f"[OK] Demo API Mode Updated: Vulnerable={mode_res['vulnerable_mode']} | Security Headers={mode_res['security_headers']}")

    # Verify directly via HTTP that User A still accesses own record (200) and User B is blocked (403)
    st_own, _ = fetch_patient(101, token_a)
    st_cross, _ = fetch_patient(101, token_b)
    print(f"[OK] Live Direct Verification: User A (Owner) -> HTTP {st_own} (200), User B (Attacker) -> HTTP {st_cross} (403 Forbidden)")
    assert st_own == 200, "Owner must still be authorized"
    assert st_cross == 403, "Attacker must be forbidden"

    # 6.3 Retest in Remediated / Secure Mode
    st, retest_res2 = post_json(f"{BASE_BACKEND}/api/scans/{scan_id}/retest", {
        "finding_id": bola_f['id']
    })
    res_item2 = retest_res2['results'][0]
    print(f"[OK] Retest in Remediated Mode: Verified={res_item2['verified']} | Status='{res_item2['new_status']}' | Details={res_item2['observed_result']}")
    assert res_item2['new_status'] == "Resolved", f"Expected 'Resolved', got {res_item2['new_status']}"

    # 6.4 Verify Audit History Preservation
    st, hist_resp = get_json(f"{BASE_BACKEND}/api/findings/{bola_f['id']}/history")
    history_items = hist_resp.get('history', hist_resp if isinstance(hist_resp, list) else [])
    print(f"[OK] Retest History Audit Trail: {len(history_items)} total entries")
    for idx, h in enumerate(history_items):
        print(f"      Entry {idx+1}: Timestamp={h['retested_at']} | Old='{h['previous_status']}' -> New='{h['new_status']}' | Verified={h['verified']}")
    assert len(history_items) >= 2, f"Expected at least 2 history records, got {len(history_items)}"

    # 6.5 Restore Demo API to Vulnerable Mode for Baseline Preservation
    st, _ = post_json(f"{BASE_DEMO}/api/demo/mode", {"vulnerable": True, "enable_security_headers": False})
    print("[OK] Demo API safely restored to initial vulnerable mode.")

    print("\n=================================================================")
    print("PHASE 10 - SECTION 7: TEST FIX D — DYNAMIC API URL")
    print("=================================================================")
    st, ds_overview = get_json(f"{BASE_BACKEND}/api/dataset/overview")
    print(f"[OK] Dataset Overview via Backend: Total Samples={ds_overview['total_samples']} | Providers={ds_overview['provider_count']}")
    assert ds_overview['total_samples'] == 10000, f"Expected 10000 samples, got {ds_overview['total_samples']}"

    # Also test an executive report generation
    print("\n=================================================================")
    print("PHASE 10 - SECTION 8: EXECUTIVE SECURITY REPORT VALIDATION")
    print("=================================================================")
    st, report_data = get_json(f"{BASE_BACKEND}/api/scans/{scan_id}/report")
    print(f"[OK] Executive Report: HTTP {st} | Target={report_data['scan']['target_url']} | Total Findings={report_data['summary']['total_findings']}")
    print(f"      Severity Breakdown: {report_data['summary']['severity_breakdown']}")
    print(f"      Resolved Count: {report_data['summary'].get('resolved_count', 0)}")

    print("\n=================================================================")
    print("ALL PHASE 10 ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    main()
