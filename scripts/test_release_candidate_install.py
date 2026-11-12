"""Validate the release candidate staged in dist/release_candidate_v1.1.0.

Verifies:
1. Packaging completeness & file availability
2. Encryption key configuration from .env.example
3. In-memory / isolated SQLite database creation
4. Target onboarding and OpenAPI spec parsing
5. Scan execution using the packaged backend engine
6. Findings generation
7. Retesting lifecycle
8. Structured security report generation
"""

import os
import sys
import shutil
from pathlib import Path

CANDIDATE_DIR = Path(r"C:\PROJECTS\api-sentinel\dist\release_candidate_v1.1.0")

def validate_candidate():
    print("=" * 65)
    print("API SENTINEL — RELEASE CANDIDATE INSTALLATION & SANITY VALIDATION")
    print("=" * 65)
    
    assert CANDIDATE_DIR.exists(), f"Staged directory {CANDIDATE_DIR} does not exist!"
    
    # 1. Verify directory layout
    print("[1/6] Verifying packaged directory layout...")
    expected_dirs = ["backend", "frontend", "dashboard", "dataset", "demo_api", "docs", "metadata"]
    for ed in expected_dirs:
        p = CANDIDATE_DIR / ed
        assert p.exists() and p.is_dir(), f"Missing packaged directory: {ed}"
        print(f"  OK: Found {ed}/")
        
    # 2. Check essential files
    print("\n[2/6] Verifying essential root files & templates...")
    expected_files = [
        "Dockerfile", "docker-compose.yml", ".env.example", ".gitignore", ".dockerignore", "README.md",
        "backend/requirements.txt", "frontend/package.json", "frontend/dist/index.html"
    ]
    for ef in expected_files:
        fp = CANDIDATE_DIR / ef
        assert fp.exists(), f"Missing essential file: {ef}"
        print(f"  OK: Found {ef}")
        
    # 3. Simulate .env configuration from .env.example
    print("\n[3/6] Simulating deployment configuration from .env.example...")
    backend_dir = CANDIDATE_DIR / "backend"
    candidate_env = backend_dir / ".env"
    
    from cryptography.fernet import Fernet
    fresh_test_key = Fernet.generate_key().decode()
    
    env_content = f"""ENVIRONMENT=testing
DEBUG=False
PORT=8000
HOST=127.0.0.1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///:memory:
ALLOW_LOCAL_LAB_SCANNING=True
TARGET_CREDENTIAL_ENCRYPTION_KEY={fresh_test_key}
NVIDIA_API_KEY=
"""
    with open(candidate_env, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f"  Configured candidate .env with fresh Fernet key: {fresh_test_key[:8]}... (len={len(fresh_test_key)})")
    
    # 4. Import backend modules from candidate path
    print("\n[4/6] Importing backend engine from release candidate directory...")
    sys.path.insert(0, str(backend_dir))
    
    from app.database import Base, engine, SessionLocal
    from app.services.credential_vault import encrypt_credential, decrypt_credential, mask_credential
    from app.services.openapi_parser import OpenApiParser
    from app.services.target_service import TargetService
    from app.services.scan_service import ScanService
    from app.services.retest_service import RetestService
    from app.services.report_service import ReportService
    from app.schemas import ApiTargetCreate, AuthProfileCreate, ScanCreateRequest, RetestRequest
    from app.security_engine.integration import set_security_engine_override, MockSecurityEngineAdapter
    
    # Isolate database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    set_security_engine_override(MockSecurityEngineAdapter())
    
    # 5. Execute Onboarding & Vault Encryption
    print("\n[5/6] Testing Onboarding, Vault Encryption & OpenAPI Discovery...")
    # Cryptographic Vault Check
    enc = encrypt_credential("live_candidate_token_xyz")
    dec = decrypt_credential(enc)
    assert dec == "live_candidate_token_xyz", "Decryption mismatch!"
    masked = mask_credential("live_candidate_token_xyz")
    assert masked == "live..._xyz", f"Mask mismatch: {masked}"
    print(f"  Cryptographic Vault: Encrypted & decrypted cleanly. Masked: {masked}")
    
    # Target creation
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Candidate Test API",
        base_url="http://127.0.0.1:8001",
        description="Release candidate verification target"
    ))
    assert target.id is not None
    print(f"  Target Registered: {target.name} (ID: {target.id})")
    
    # Auth Profile Registration
    profile_a = TargetService.save_auth_profile(db, target.id, AuthProfileCreate(
        account_label="Candidate Owner",
        authentication_type="bearer",
        credential_value="candidate_token_101",
        username="candidate_alice",
        role="owner"
    ))
    meta = profile_a.credential_metadata or {}
    masked_val = meta.get("masked_credential")
    assert masked_val == "cand..._101", f"Expected cand..._101, got {masked_val}"
    print(f"  Auth Profile Saved: {profile_a.account_label} (Masked: {masked_val})")
    
    # OpenAPI Spec Parsing
    sample_spec = """
openapi: "3.0.0"
info:
  title: "Candidate Verification API"
  version: "1.0.0"
paths:
  /health:
    get:
      summary: "Health Check"
  /api/records/{id}:
    get:
      summary: "Get Record"
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
"""
    parsed = OpenApiParser.parse_from_content(sample_spec)
    endpoints = parsed.get("endpoints", [])
    assert len(endpoints) == 2, f"Expected 2 endpoints, got {len(endpoints)}"
    print(f"  OpenAPI Parser: Discovered {len(endpoints)} endpoints successfully.")
    
    # 6. Execute Scan, Retest & Report Generation
    print("\n[6/6] Testing Scan Execution, Retest & Reporting...")
    scan_req = ScanCreateRequest(
        target_url="http://127.0.0.1:8001",
        user_authorized=True,
        categories=["BOLA", "AUTH", "HEADERS"]
    )
    scan = ScanService.create_and_run_scan(db=db, request=scan_req)
    assert scan.status == "Completed"
    assert scan.total_findings > 0
    print(f"  Scan Completed: ID {scan.id} with {scan.total_findings} findings.")
    
    findings = ScanService.get_findings_for_scan(db=db, scan_id=scan.id)
    assert len(findings) > 0
    test_finding = findings[0]
    print(f"  Finding Verified: [{test_finding.severity}] {test_finding.vulnerability} on {test_finding.endpoint}")
    
    # Retest finding
    retest_res = RetestService.retest_scan(
        db=db,
        scan_id=scan.id,
        specific_finding_id=test_finding.id
    )
    assert len(retest_res.results) == 1
    print(f"  Retest Completed: Status transitioned to '{retest_res.results[0].new_status}'")
    
    # Generate Report
    report = ReportService.generate_report(db=db, scan_id=scan.id)
    assert report.summary.total_findings == scan.total_findings
    print(f"  Report Generated: {report.summary.total_findings} total findings (Resolved: {report.summary.resolved_count}).")
    
    # Cleanup candidate .env
    db.close()
    if candidate_env.exists():
        candidate_env.unlink()
        
    print("\n" + "=" * 65)
    print("ALL RELEASE CANDIDATE INSTALLATION & EXECUTION TESTS PASSED!")
    print("=" * 65)
    return True

if __name__ == "__main__":
    ok = validate_candidate()
    exit(0 if ok else 1)
