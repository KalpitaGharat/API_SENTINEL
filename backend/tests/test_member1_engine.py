"""Comprehensive Test Suite for Member 1 Real Security Testing Engine.

Validates:
1. Real BOLA / IDOR detection against vulnerable Healthcare Demo API.
2. Prevention of false positives on secured Healthcare Demo API.
3. Distinction between confirmed vulnerabilities and non-vulnerable / inconclusive responses.
4. Detection of missing HTTP security headers and API configuration weaknesses.
5. Detection of authentication bypasses / unprotected sensitive routes.
6. Verification and retesting workflow (Still Vulnerable -> Resolved -> Retest Failed).
7. Credential and token redaction in reproducible evidence payloads.
8. Seamless integration with FastAPI backend database and scan services.
"""

import sys
from pathlib import Path

# Add project root to sys.path so demo_api is discoverable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import httpx
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from demo_api.main import app as demo_app
from demo_api.config import settings as demo_settings
from demo_api.transport import DemoApiTransport
from app.database import Base
from app.models import Scan, Finding
from app.schemas import ScanCreateRequest, RetestRequest
from app.routes.scans import create_scan, get_scan_findings
from app.routes.retesting import retest_scan_findings
from app.security_engine.member1_engine import EngineAdapter
from app.security_engine.integration import (
    get_security_engine,
    set_security_engine_override,
    reset_security_engine,
)

# In-memory SQLite session for integration tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def reset_engine_state():
    """Ensure engine state and demo API settings are clean before and after each test."""
    reset_security_engine()
    demo_settings.DEMO_VULNERABLE_MODE = True
    demo_settings.ENABLE_SECURITY_HEADERS = False
    yield
    reset_security_engine()
    demo_settings.DEMO_VULNERABLE_MODE = True
    demo_settings.ENABLE_SECURITY_HEADERS = False


@pytest.fixture(scope="function")
def db():
    """Provide clean database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def real_engine():
    """Member 1 Engine Adapter wired to the in-memory DemoApiTransport."""
    transport = DemoApiTransport()
    return EngineAdapter(transport=transport)


# -----------------------------------------------------------------------------
# 1. BOLA / IDOR Testing Suite
# -----------------------------------------------------------------------------

def test_bola_detection_on_vulnerable_demo_api(real_engine):
    """Verify scanner detects BOLA on GET /api/patients/{patient_id} in vulnerable mode."""
    demo_settings.DEMO_VULNERABLE_MODE = True

    findings = real_engine.run_scan(
        target_url="http://testserver",
        config={
            "categories": ["BOLA"],
            "allow_lab": True,
            "test_accounts": {
                "patient_a": {"username": "patient_a", "password": "demo_password_a", "id": 101, "owned_id": 101},
                "patient_b": {"username": "patient_b", "password": "demo_password_b", "id": 102, "owned_id": 102},
            },
        },
    )

    bola_findings = [f for f in findings if f.category == "BOLA"]
    assert len(bola_findings) == 1

    f = bola_findings[0]
    assert f.vulnerability == "Broken Object Level Authorization (BOLA)"
    assert f.severity == "High"
    assert "/api/patients/" in f.endpoint
    assert f.status == "Open"

    # Verify structured evidence
    evidence = f.evidence
    assert evidence.observed_status == 200
    assert evidence.expected_status == 403
    assert evidence.requested_resource == "/api/patients/102"
    assert "patient_a" in evidence.test_user.lower()
    assert "patient_b" in str(evidence.response_details)

    # Verify token redaction in evidence
    req_details = evidence.request_details
    auth_val = req_details.get("authorization") or req_details.get("headers", {}).get("Authorization", "")
    assert "demo_password" not in str(req_details)
    assert "[REDACTED" in auth_val


def test_bola_prevention_on_secure_mode(real_engine):
    """Verify scanner produces ZERO BOLA findings when demo API operates in secure mode."""
    demo_settings.DEMO_VULNERABLE_MODE = False  # Remediation applied

    findings = real_engine.run_scan(
        target_url="http://testserver",
        config={
            "categories": ["BOLA"],
            "allow_lab": True,
            "test_accounts": {
                "patient_a": {"username": "patient_a", "password": "demo_password_a", "id": 101, "owned_id": 101},
                "patient_b": {"username": "patient_b", "password": "demo_password_b", "id": 102, "owned_id": 102},
            },
        },
    )

    bola_findings = [f for f in findings if f.category == "BOLA"]
    assert len(bola_findings) == 0


def test_generic_200_does_not_trigger_false_positive_bola(real_engine):
    """Verify that a 200 response with generic message does not trigger false positive BOLA."""
    # Build a synthetic response without foreign data
    mock_resp = httpx.Response(
        status_code=200,
        json={"status": "ok", "message": "Generic response with no PII or foreign identifiers"},
        request=httpx.Request("GET", "http://testserver/api/patients/102"),
    )
    is_foreign, details = real_engine._verify_foreign_data_exposure(mock_resp, 102, "patient_b")
    assert is_foreign is False
    assert details == {}


# -----------------------------------------------------------------------------
# 2. HTTP Security Headers & Configuration Testing Suite
# -----------------------------------------------------------------------------

def test_missing_security_headers_detection(real_engine):
    """Verify scanner flags missing HSTS, nosniff, frame-options, and CSP in vulnerable mode."""
    demo_settings.DEMO_VULNERABLE_MODE = True
    demo_settings.ENABLE_SECURITY_HEADERS = False

    findings = real_engine.run_scan(
        target_url="http://testserver",
        config={"categories": ["HEADERS"], "allow_lab": True},
    )

    header_findings = [f for f in findings if f.category == "HEADERS"]
    vuln_names = [f.vulnerability for f in header_findings]

    assert any("HSTS" in v for v in vuln_names)
    assert any("X-Content-Type-Options" in v for v in vuln_names)
    assert any("X-Frame-Options" in v for v in vuln_names)
    assert any("Content-Security-Policy" in v or "CSP" in v for v in vuln_names)


def test_security_headers_remediated_mode(real_engine):
    """Verify scanner detects clean headers when security headers are enabled."""
    demo_settings.DEMO_VULNERABLE_MODE = False
    demo_settings.ENABLE_SECURITY_HEADERS = True

    findings = real_engine.run_scan(
        target_url="http://testserver",
        config={"categories": ["HEADERS"], "allow_lab": True},
    )

    header_findings = [f for f in findings if f.category == "HEADERS"]
    assert len(header_findings) == 0


# -----------------------------------------------------------------------------
# 3. Authentication Weaknesses Testing Suite
# -----------------------------------------------------------------------------

def test_authentication_checks_on_protected_endpoints(real_engine):
    """Verify auth probing detects broken token signature validation on /api/admin/metrics."""
    findings = real_engine.run_scan(
        target_url="http://testserver",
        config={"categories": ["AUTH"], "allow_lab": True},
    )

    auth_findings = [f for f in findings if f.category == "AUTH"]
    # The scanner correctly detects that /api/admin/metrics accepts invalid tokens
    assert len(auth_findings) == 1
    f = auth_findings[0]
    assert f.vulnerability == "Broken Token Signature Validation"
    assert f.endpoint == "GET /api/admin/metrics"
    assert f.severity == "High"
    assert f.evidence.observed_status == 200
    assert f.evidence.expected_status == 401


# -----------------------------------------------------------------------------
# 4. Retesting & Verification Workflow Suite
# -----------------------------------------------------------------------------

def test_retesting_lifecycle_vulnerable_then_resolved(real_engine, db):
    """Full lifecycle: Detect BOLA -> Retest as Still Vulnerable -> Fix -> Retest as Resolved."""
    set_security_engine_override(real_engine)

    # Step 1: Scan vulnerable API
    demo_settings.DEMO_VULNERABLE_MODE = True
    req = ScanCreateRequest(
        target_url="http://testserver",
        user_authorized=True,
        categories=["BOLA"],
        allow_lab=True,
    )
    scan = create_scan(payload=req, db=db)
    findings = get_scan_findings(scan_id=scan.id, db=db)
    assert len(findings) == 1
    f = findings[0]
    assert f.status == "Open"

    # Step 2: Retest while API is still vulnerable
    retest_1 = retest_scan_findings(scan_id=scan.id, payload=RetestRequest(finding_id=f.id), db=db)
    res_1 = retest_1.results[0]
    assert res_1.new_status == "Still Vulnerable"
    assert res_1.verified is False

    # Step 3: Apply fix in API (switch to secure mode)
    demo_settings.DEMO_VULNERABLE_MODE = False

    # Step 4: Retest again -> Must be marked Resolved
    retest_2 = retest_scan_findings(scan_id=scan.id, payload=RetestRequest(finding_id=f.id), db=db)
    res_2 = retest_2.results[0]
    assert res_2.new_status == "Resolved"
    assert res_2.verified is True
    assert res_2.observed_result["observed_status"] in (403, 404)


def test_retest_failure_on_unreachable_target(db):
    """Verify network connection failures during retesting return 'Retest Failed'."""
    # Real engine without custom client pointing to non-existent endpoint
    engine = EngineAdapter()
    set_security_engine_override(engine)

    result = engine.retest_finding(
        target_url="https://non-existent-server-12345.test",
        finding_data={
            "id": 999,
            "category": "BOLA",
            "endpoint": "GET /api/patients/102",
        },
        config={"allow_lab": True},
    )

    assert result["verified"] is False
    assert result["new_status"] == "Retest Failed"
    assert "error" in result["observed_result"]


def test_bola_retest_returns_needs_review_when_owner_access_is_broken(db):
    """Verify that a generic 403 does NOT resolve BOLA if the legitimate owner is also denied access."""
    mock_client = MagicMock()
    # Owner request to /api/patients/101 returns 403 (e.g. broken auth or total block)
    resp_owner = MagicMock()
    resp_owner.status_code = 403
    mock_client.get.return_value = resp_owner

    engine = EngineAdapter(client=mock_client)
    res = engine.retest_finding(
        target_url="http://127.0.0.1:8001",
        finding_data={"id": 1, "category": "BOLA", "endpoint": "GET /api/patients/102"},
        config={
            "allow_lab": True,
            "test_accounts": {
                "patient_a": {"username": "patient_a", "token": "token_a", "id": 101},
                "patient_b": {"username": "patient_b", "token": "token_b", "id": 102},
            }
        }
    )

    assert res["verified"] is False
    assert res["new_status"] == "Needs Review"
    assert "Verification Inconclusive" in res["observed_result"]["message"]


# -----------------------------------------------------------------------------
# 5. Backend Dynamic Discovery and Integration
# -----------------------------------------------------------------------------

def test_backend_discovers_member1_engine_by_default():
    """Verify that get_security_engine() automatically loads Member 1's real engine."""
    reset_security_engine()
    engine = get_security_engine()

    assert engine.engine_name == "api_sentinel_real_detection_engine"
    assert engine.is_simulated is False
