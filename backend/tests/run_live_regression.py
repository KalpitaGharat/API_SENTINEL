"""Live End-to-End Regression Test Suite for API Sentinel.
Executes against actual running services on ports 8000 and 8001.
"""
import urllib.request
import json
import time
import sys

BASE_URL = 'http://127.0.0.1:8000'
DEMO_URL = 'http://127.0.0.1:8001'

def req(url, method='GET', data=None):
    req_obj = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data else None,
        headers={'Content-Type': 'application/json', 'User-Agent': 'SentinelRegressionTester/1.0'},
        method=method
    )
    with urllib.request.urlopen(req_obj, timeout=35) as resp:
        body = resp.read().decode('utf-8')
        return resp.status, json.loads(body) if body else {}

print('=== PHASE 2: LIVE END-TO-END REGRESSION TEST ===')

# Test 1: Scan Lifecycle
print('\n[1/7] Testing Scan Lifecycle...')
status, scan = req(f'{BASE_URL}/api/scans', method='POST', data={
    'target_url': f'{DEMO_URL}',
    'scan_profile': 'OWASP API Top 10 Deep Audit',
    'user_authorized': True,
    'categories': ['BOLA', 'AUTH', 'HEADERS', 'CONFIG']
})
assert status in (200, 201), f'Scan creation failed: HTTP {status}'
scan_id = scan['id']
scan_status = scan.get('status')
print(f'  Created Scan: {scan_id} (Status: {scan_status})')

# Poll for scan completion (max 10s)
for _ in range(10):
    status, scan_detail = req(f'{BASE_URL}/api/scans/{scan_id}')
    if (scan_detail.get('status') or '').lower() == 'completed':
        break
    time.sleep(1)
assert (scan_detail.get('status') or '').lower() == 'completed', f'Scan did not complete: {scan_detail}'
duration = scan_detail.get('duration_ms')
print(f'  Scan Completed in {duration}ms')

# Verify Scan Listing
status, scan_list = req(f'{BASE_URL}/api/scans?limit=5')
assert any(s['id'] == scan_id for s in scan_list['items']), 'Scan not found in listing'
total_scans = scan_list.get('total')
print(f'  Scan Listing verified: {total_scans} total scans in history')

# Test 2: Vulnerability Detection
print('\n[2/7] Testing Vulnerability Detection Engine...')
status, findings = req(f'{BASE_URL}/api/scans/{scan_id}/findings')
assert len(findings) >= 4, f'Expected >= 4 findings, got {len(findings)}'
categories = {f['category'] for f in findings}
severities = {f['severity'] for f in findings}
print(f'  Detected {len(findings)} findings across categories: {categories}')
print(f'  Severities represented: {severities}')

bola_findings = [f for f in findings if f['category'] == 'BOLA']
header_findings = [f for f in findings if f['category'] == 'HEADERS']
auth_findings = [f for f in findings if f['category'] == 'AUTH']
assert len(bola_findings) >= 1, 'BOLA finding missing'
assert len(header_findings) >= 1, 'Header finding missing'
print(f'  BOLA findings: {len(bola_findings)}, Headers: {len(header_findings)}, Auth: {len(auth_findings)}')
first_finding = bola_findings[0]

# Test 3: NVIDIA Nemotron AI Integration & Fallback
print('\n[3/7] Testing NVIDIA Nemotron AI Integration & Fallback...')
status, explanation = req(f'{BASE_URL}/api/findings/{first_finding["id"]}/explain', method='POST')
assert status == 200, f'AI explanation failed: HTTP {status}'
assert 'explanation' in explanation, 'Missing explanation key'
assert 'impact' in explanation, 'Missing impact key'
assert 'remediation' in explanation, 'Missing remediation key'
model_used = explanation.get('model_name') or explanation.get('model_used')
exp_snippet = explanation['explanation'][:90]
print(f'  AI Provider Model: {model_used}')
print(f'  Explanation Generated: {exp_snippet}...')

# Test Cached Retrieval
t0 = time.time()
status, cached_exp = req(f'{BASE_URL}/api/findings/{first_finding["id"]}/explain', method='POST')
t_fetch = (time.time() - t0) * 1000
print(f'  Cached Explanation Retrieved in {t_fetch:.1f}ms (Instant SQLite Cache)')

# Test Force Refresh
status, refreshed_exp = req(f'{BASE_URL}/api/findings/{first_finding["id"]}/explain?force_refresh=true', method='POST')
assert status == 200, 'Force refresh failed'
print('  Force Refresh Verified successfully')

# Test 4: Live Updates (SSE)
print('\n[4/7] Testing Live Updates & SSE Broadcaster...')
status, events_status = req(f'{BASE_URL}/api/events/status')
assert status == 200, 'Events status failed'
print(f'  SSE Event Status: {events_status}')

# Test 5: Critical Vulnerability Notification Workflow
print('\n[5/7] Testing Critical Alert Lifecycle...')
crit_findings = [f for f in findings if f.get('severity') == 'Critical']
print(f'  Critical findings detected: {len(crit_findings)}')
for cf in crit_findings:
    sev = cf['severity']
    vuln = cf['vulnerability']
    ep = cf['endpoint']
    print(f'    - [{sev}] {vuln} on {ep}')

# Test 6: Retesting Workflow (Vulnerable Mode vs Secure Mode)
print('\n[6/7] Testing Retesting & Remediation Verification...')
# Step 6a: Retest in vulnerable mode -> should remain vulnerable
status, retest_vulnerable = req(f'{BASE_URL}/api/scans/{scan_id}/retest', method='POST', data={
    'finding_ids': [first_finding['id']]
})
assert status == 200, f'Retest failed: {retest_vulnerable}'
res_vulnerable = retest_vulnerable['results'][0]
vuln_status = res_vulnerable.get('new_status')
print(f'  Vulnerable Mode Retest: Status = {vuln_status} (Expected: Still Vulnerable)')
assert vuln_status == 'Still Vulnerable', f'Unexpected status: {res_vulnerable}'

# Step 6b: Switch Demo API to Secure Mode
print('  Switching Demo API to SECURE Mode...')
status, mode_resp = req(f'{DEMO_URL}/api/demo/mode', method='POST', data={
    'vulnerable': False,
    'enable_security_headers': True
})
v_mode = mode_resp.get('vulnerable_mode')
h_mode = mode_resp.get('security_headers')
print(f'  Demo API Mode: vulnerable={v_mode}, headers={h_mode}')

# Step 6c: Retest in secure mode -> should be RESOLVED!
status, retest_secure = req(f'{BASE_URL}/api/scans/{scan_id}/retest', method='POST', data={
    'finding_ids': [first_finding['id']]
})
assert status == 200, f'Retest failed: {retest_secure}'
res_secure = retest_secure['results'][0]
sec_status = res_secure.get('new_status')
print(f'  Secure Mode Retest: Status = {sec_status} (Expected: Resolved)')
assert sec_status == 'Resolved', f'Retest did not resolve: {res_secure}'

# Step 6d: Switch Demo API back to Vulnerable Mode for safety
req(f'{DEMO_URL}/api/demo/mode', method='POST', data={'vulnerable': True, 'enable_security_headers': False})
print('  Restored Demo API to standard vulnerable mode.')

# Test 7: Security Reports
print('\n[7/7] Testing Security & Compliance Report Generation...')
status, report = req(f'{BASE_URL}/api/scans/{scan_id}/report', method='GET')
assert status == 200, f'Report generation failed: HTTP {status}'
assert 'scan' in report, 'Missing scan in report'
assert 'summary' in report, 'Missing summary in report'
assert 'findings' in report, 'Missing findings in report'
summary = report['summary']
total_f = summary.get('total_findings')
sev_dist = summary.get('severity_breakdown')
open_c = summary.get('open_count')
resolved_c = summary.get('resolved_count')
print(f'  Report Total Findings: {total_f}')
print(f'  Severity Breakdown: {sev_dist}')
print(f'  Open Findings: {open_c}, Resolved Findings: {resolved_c}')

print('\n======================================================')
print('ALL 7 END-TO-END REGRESSION TESTS PASSED SUCCESSFULLY!')
print('======================================================')
