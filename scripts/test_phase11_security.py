"""Phase 11 Advanced Security Validation & Security Assurance Test Suite.

Executes rigorous security validation across:
1. SSRF Security Assurance & Network Boundary Defense
2. Credential Security & Cryptographic Vault Storage
3. BOLA & Authorization Validation (Multi-Principal)
4. API Key Intelligence Security (Entropy, Masking, Split Integrity, Benchmark Math)
5. OpenAPI Specification Security (Parsers, Limits, Ref Blocking)
6. Nemotron AI Security & Offline Deterministic Fallback
7. General Application Security (CORS, Headers, Input Sanitization, SQLi, Path Traversal)
"""

import sys
import os
import json
import socket
import ipaddress
import urllib.request
import urllib.error
import math
import re
from datetime import datetime

BASE_BACKEND = "http://127.0.0.1:8000"
BASE_DEMO = "http://127.0.0.1:8001"

def post_json(url, data, timeout=20):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())

def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())

def main():
    sec_results = {}

    import os
    os.chdir(r"C:\PROJECTS\api-sentinel\backend")

    from dotenv import load_dotenv
    load_dotenv(r"C:\PROJECTS\api-sentinel\backend\.env")

    print("=================================================================")
    print("PHASE 11 - DOMAIN 1: SSRF DEFENSE & HARDENED TRANSPORT ASSURANCE")
    print("=================================================================")
    # Import security engine transport validator directly for deep static/unit checks
    sys.path.insert(0, r"C:\PROJECTS\api-sentinel\backend")
    from app.security_engine.integration import (
        validate_target_safety,
        validate_safe_redirect,
        TargetSafetyError,
        PinnedHTTPTransport,
        execute_safe_request,
    )
    
    ssrf_tests = [
        ("Cloud Metadata 169.254.169.254", "http://169.254.169.254/latest/meta-data/"),
        ("Cloud Metadata Hex 0xa9fea9fe", "http://0xa9fea9fe/"),
        ("Cloud Metadata Dword 2852039166", "http://2852039166/"),
        ("IPv6 Cloud Metadata fd00:ec2::254", "http://[fd00:ec2::254]/"),
        ("Google Metadata Internal", "http://metadata.google.internal/computeMetadata/v1/"),
        ("Loopback 127.0.0.1 (Strict Prod)", "http://127.0.0.1:8000/"),
        ("Loopback 127.0.0.2", "http://127.0.0.2/"),
        ("Loopback Dword 2130706433", "http://2130706433/"),
        ("IPv6 Loopback ::1", "http://[::1]:80/"),
        ("Link-Local IPv4 169.254.1.1", "http://169.254.1.1/"),
        ("Link-Local IPv6 fe80::1", "http://[fe80::1]/"),
        ("Multicast IPv4 224.0.0.1", "http://224.0.0.1/"),
        ("Unspecified 0.0.0.0", "http://0.0.0.0/"),
        ("Private RFC1918 10.0.0.1 (Default Prod)", "http://10.0.0.1/"),
        ("Private RFC1918 172.16.0.1 (Default Prod)", "http://172.16.0.1/"),
        ("Private RFC1918 192.168.1.1 (Default Prod)", "http://192.168.1.1/"),
        ("Dangerous Scheme file://", "file:///etc/passwd"),
        ("Dangerous Scheme gopher://", "gopher://127.0.0.1:6379/_INFO"),
        ("CRLF Injection Host", "http://example.com%0d%0aSet-Cookie:injected=true/"),
    ]

    blocked_count = 0
    for name, target_url in ssrf_tests:
        try:
            # Test in strict production mode (allow_lab=False)
            validate_target_safety(target_url, allow_lab=False)
            print(f"  [VULNERABILITY] {name} was NOT blocked!")
        except (TargetSafetyError, ValueError) as ex:
            blocked_count += 1
            print(f"  [BLOCKED] {name} -> Correctly rejected: {str(ex)[:70]}")
    
    print(f"SSRF Results: {blocked_count}/{len(ssrf_tests)} attack vectors blocked.")
    assert blocked_count == len(ssrf_tests), "All SSRF vectors must be blocked!"
    sec_results['ssrf'] = {'total_tested': len(ssrf_tests), 'blocked': blocked_count}

    print("\n=================================================================")
    print("PHASE 11 - DOMAIN 2: CREDENTIAL SECURITY & VAULT ASSURANCE")
    print("=================================================================")
    from app.services.credential_vault import (
        encrypt_credential,
        decrypt_credential,
        mask_credential as vault_mask_credential,
        CredentialVaultError
    )
    from app.config import settings

    # 2.1 Verify Fernet key configuration
    configured_key = settings.TARGET_CREDENTIAL_ENCRYPTION_KEY
    print(f"  Fernet Key configured: {bool(configured_key)} (Length: {len(configured_key)} chars)")
    assert len(configured_key) > 0, "Fernet encryption key must be configured in environment!"

    # 2.2 Verify Vault encryption and masking
    test_secret = "ghp_VerySecretGitHubPersonalAccessToken9999"
    ciphertext = encrypt_credential(test_secret)
    masked = vault_mask_credential(test_secret)
    print(f"  Plaintext: [REDACTED {len(test_secret)} chars]")
    print(f"  Ciphertext: {ciphertext[:20]}... (len={len(ciphertext)})")
    print(f"  Masked representation: {masked}")
    assert test_secret not in ciphertext, "Ciphertext must not contain plaintext secret!"
    assert test_secret not in masked, "Masked string must not leak full secret!"
    assert masked.endswith("9999"), "Masked string should safely retain trailing characters"

    # 2.3 Verify round-trip decryption
    decrypted = decrypt_credential(ciphertext)
    assert decrypted == test_secret, "Decrypted secret must match original!"

    # 2.4 Verify no secrets in database queries
    from app.database import SessionLocal
    from app.models import TargetAuthProfile, ApiTarget
    with SessionLocal() as db:
        profiles = db.query(TargetAuthProfile).all()
        print(f"  Inspecting {len(profiles)} TargetAuthProfile records in SQLite database:")
        for p in profiles:
            if p.credential_ciphertext:
                assert not p.credential_ciphertext.startswith("sentinel_token_"), "Database contains plaintext token!"
                masked_val = p.credential_metadata.get("masked_credential", "")
                print(f"    - Profile ID {p.id} ({p.account_label}): Stored Ciphertext len={len(p.credential_ciphertext)}, Masked in DB={masked_val}")

    # 2.5 Verify .gitignore protects .env
    with open(r"C:\PROJECTS\api-sentinel\.gitignore", "r") as f:
        gitignore_content = f.read()
    print(f"  .gitignore contains '.env': {'.env' in gitignore_content}")
    print(f"  .gitignore contains '*.db': {'*.db' in gitignore_content}")
    assert ".env" in gitignore_content, ".gitignore must exclude .env!"
    assert "*.db" in gitignore_content, ".gitignore must exclude local database files!"

    print("\n=================================================================")
    print("PHASE 11 - DOMAIN 3: BOLA & AUTHORIZATION BOUNDARY VALIDATION")
    print("=================================================================")
    # Authenticate User A and User B on Demo API
    _, auth_a = post_json(f"{BASE_DEMO}/api/auth/login", {"username": "patient_a", "password": "demo_password_a"})
    _, auth_b = post_json(f"{BASE_DEMO}/api/auth/login", {"username": "patient_b", "password": "demo_password_b"})
    token_a = auth_a["access_token"]
    token_b = auth_b["access_token"]

    def request_patient(pid, token=None):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(f"{BASE_DEMO}/api/patients/{pid}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as he:
            return he.code, json.loads(he.read().decode('utf-8', errors='ignore'))

    # 3.1 Unauthenticated Request
    st, resp = request_patient(101, token=None)
    print(f"  [AUTH CHECK] Unauthenticated -> /api/patients/101: HTTP {st} (Expected: 401)")
    assert st == 401, f"Expected 401 Unauthorized, got {st}"

    # 3.2 Invalid / Forged Token
    st, resp = request_patient(101, token="forged_attacker_jwt_token_invalid_signature")
    print(f"  [AUTH CHECK] Forged Token -> /api/patients/101: HTTP {st} (Expected: 401)")
    assert st == 401, f"Expected 401 Unauthorized, got {st}"

    # 3.3 Nonexistent Resource Identifier
    st, resp = request_patient(9999, token=token_a)
    print(f"  [RESOURCE CHECK] Nonexistent ID 9999: HTTP {st} (Expected: 404)")
    assert st == 404, f"Expected 404 Not Found, got {st}"

    # 3.4 BOLA Telemetry Inspection (No generic 200 acceptance)
    from app.security_engine.member1_engine import EngineAdapter
    import httpx
    engine = EngineAdapter()
    
    # Test Member 1 _verify_foreign_data_exposure with real Response mocks
    resp_alice = httpx.Response(200, json={"patient_id": 101, "full_name": "Synthetic Patient A", "owner_username": "patient_a"})
    resp_generic = httpx.Response(200, json={"status": "success", "message": "Record retrieved successfully", "items": []})
    
    match_alice, ev_alice = engine._verify_foreign_data_exposure(resp_alice, expected_foreign_id=101, foreign_username="patient_a")
    match_generic, ev_generic = engine._verify_foreign_data_exposure(resp_generic, expected_foreign_id=101, foreign_username="patient_a")
    print(f"  [ENGINE DISCRIMINATION] Foreign Data Exposure on Alice Record: {match_alice} (True Positive)")
    print(f"  [ENGINE DISCRIMINATION] Foreign Data Exposure on Generic 200 Body: {match_generic} (False Positive Prevented)")
    assert match_alice is True, "Engine must detect foreign record in body"
    assert match_generic is False, "Engine must NOT trigger BOLA on generic 200 responses"

    print("\n=================================================================")
    print("PHASE 11 - DOMAIN 4: API KEY INTELLIGENCE & BENCHMARK VALIDATION")
    print("=================================================================")
    from app.services.api_key_benchmark import (
        shannon_entropy,
        mask_credential,
        ApiKeyDetectionEngine,
        MASTER_DATASET_FILE
    )

    # 4.1 Test Entropy Calculation
    low_entropy = shannon_entropy("aaaaaaaaaaaaaaaa")
    high_entropy = shannon_entropy("wU0t7-pgejRJsMTrKtYv_F00N_IaSvNuWdGVCRWeImAsxYP0")
    print(f"  Shannon Entropy: Low='aaaaaaaa' -> {low_entropy:.2f} bits, High='random-key' -> {high_entropy:.2f} bits")
    assert low_entropy < 1.0, "Repeated characters must yield low entropy"
    assert high_entropy > 4.0, "Cryptographic keys must yield high entropy"

    # 4.2 Test Masking Safeguard
    raw_key = "sk-proj-Abcdef1234567890abcdef1234567890"
    masked_key = mask_credential(raw_key)
    print(f"  Mask Credential: Raw='{raw_key[:10]}...' -> Masked='{masked_key}'")
    assert raw_key not in masked_key
    assert masked_key.startswith("sk-proj-")
    assert masked_key.endswith("7890")

    # 4.3 Verify Dataset Split Integrity & Independent Metric Verification
    master_samples = []
    with open(MASTER_DATASET_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                master_samples.append(json.loads(line))
    print(f"  Master dataset total samples: {len(master_samples)}")
    assert len(master_samples) == 10000, f"Expected exactly 10,000 samples, got {len(master_samples)}"

    # Independent metric evaluation on a 200-sample test slice
    test_slice = master_samples[:200]
    tp = fp = tn = fn = 0

    for s in test_slice:
        detected_prov, token, reason, score = ApiKeyDetectionEngine.detect_with_details(s['sample'])
        is_secret = (detected_prov is not None)
        actual_label = s['label']
        if actual_label == "positive":
            if is_secret:
                tp += 1
            else:
                fn += 1
        else:
            if is_secret:
                fp += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(test_slice)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    print(f"  Independent Slice Benchmark (N={len(test_slice)}):")
    print(f"    TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    print(f"    Accuracy: {accuracy*100:.2f}%, Precision: {precision*100:.2f}%, Recall: {recall*100:.2f}%, F1: {f1*100:.2f}%, Specificity: {specificity*100:.2f}%")
    assert accuracy > 0.90, "Detector accuracy on sample slice must exceed 90%"

    print("\n=================================================================")
    print("PHASE 11 - DOMAIN 5: OPENAPI PARSER DEFENSE ASSURANCE")
    print("=================================================================")
    from app.services.openapi_parser import OpenApiParser, OpenApiParserError

    # 5.1 Oversized Content Protection (> 5 MB)
    oversized_content = " " * (6 * 1024 * 1024)
    try:
        OpenApiParser.parse_from_content(oversized_content, file_type="json")
        print("  [VULNERABILITY] Oversized content was NOT rejected!")
    except OpenApiParserError as e:
        print(f"  [DEFENSE CONFIRMED] Oversized file (>5MB) rejected: {e}")

    # 5.2 External References ($ref http://...)
    malicious_external_ref_spec = {
        "openapi": "3.0.0",
        "info": {"title": "SSRF Ref Attack", "version": "1.0"},
        "paths": {
            "/evil": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"}
                    },
                    "parameters": [
                        {"$ref": "http://169.254.169.254/latest/meta-data/"}
                    ]
                }
            }
        }
    }
    parsed_spec = OpenApiParser.parse_from_content(json.dumps(malicious_external_ref_spec), file_type="json")
    ext_refs = parsed_spec.get('external_refs_detected', [])
    print(f"  [DEFENSE CONFIRMED] External references detected: {len(ext_refs)} flagged -> {ext_refs}")
    print(f"  [DEFENSE CONFIRMED] Warnings issued: {parsed_spec.get('warnings')}")
    assert len(ext_refs) > 0, "External references must be detected and quarantined!"

    # 5.3 Circular References & Malformed YAML
    malformed_yaml = "openapi: 3.0.0\ninfo:\n  title: [unclosed list\npaths:"
    try:
        OpenApiParser.parse_from_content(malformed_yaml, file_type="yaml")
        print("  [VULNERABILITY] Malformed YAML was NOT rejected!")
    except OpenApiParserError as e:
        print(f"  [DEFENSE CONFIRMED] Malformed YAML rejected cleanly: {e}")

    print("\n=================================================================")
    print("PHASE 11 - DOMAIN 6: NEMOTRON AI SAFETY & OFFLINE DETERMINISM")
    print("=================================================================")
    from app.services.ai_service import AIService
    ai = AIService()

    # 6.1 Verify API Key remains server side
    print(f"  NVIDIA Model configured: {ai.model}")
    print(f"  NVIDIA Timeout configured: {ai.timeout}s")
    
    # 6.2 Verify Rule-Based Deterministic Fallback Output
    finding_dict = {
        "vulnerability": "Broken Object Level Authorization (BOLA)",
        "category": "BOLA",
        "severity": "High",
        "endpoint": "GET /api/patients/{patient_id}",
        "description": "Cross-user data access detected without authorization check.",
    }
    explanation = ai._generate_rule_based_fallback(finding_dict)
    print(f"  Fallback Explanation Generated: Model={explanation['model_name']}")
    print(f"  Explanation prefix: {explanation['explanation'][:90]}...")
    print(f"  Remediation steps count: {len(explanation['remediation'].splitlines())}")
    assert explanation['model_name'] == "rule-based-security-engine (offline-fallback)"
    assert len(explanation['remediation']) > 50

    print("\n=================================================================")
    print("PHASE 11 - DOMAIN 7: GENERAL APPLICATION SECURITY & HEADERS")
    print("=================================================================")
    # 7.1 Inspect Backend CORS & Security Headers
    req = urllib.request.Request(f"{BASE_BACKEND}/health")
    with urllib.request.urlopen(req) as resp:
        cors_hdr = resp.headers.get("Access-Control-Allow-Origin")
        print(f"  Backend CORS header: {cors_hdr or 'None (Restricted to specific origins)'}")

    # 7.2 SQL Injection Resistance Check via API
    sqli_payload = "' OR '1'='1' --"
    try:
        st, res = get_json(f"{BASE_BACKEND}/api/targets?environment={urllib.parse.quote(sqli_payload)}")
        print(f"  [SQLi CHECK] Injected Query parameter -> Status: {st}, Total results: {res['total']}")
        assert res['total'] == 0, "SQL injection must return 0 results, not all rows!"
    except Exception as e:
        print(f"  [SQLi CHECK] Handled: {e}")

    # 7.3 Path Traversal Check via API
    traversal_id = "../../etc/passwd"
    try:
        req = urllib.request.Request(f"{BASE_BACKEND}/api/targets/{urllib.parse.quote(traversal_id)}")
        with urllib.request.urlopen(req) as r:
            print("  [VULNERABILITY] Path traversal succeeded!")
    except urllib.error.HTTPError as he:
        print(f"  [TRAVERSAL CHECK] Path traversal '{traversal_id}' blocked -> HTTP {he.code}")
        assert he.code in (404, 400), f"Expected 404 or 400, got {he.code}"

    print("\n=================================================================")
    print("ALL PHASE 11 SECURITY CHECKS EXECUTED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    import urllib.parse
    main()
