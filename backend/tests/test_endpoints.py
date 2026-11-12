"""Direct Endpoint & Unit Test Suite for API Sentinel.

Tests health checks, scan creation, target safety validation, findings retrieval,
AI explanation fallback, retest verification, and report aggregation
without socket loopback dependencies.
"""

import pytest
from datetime import datetime
from fastapi import HTTPException
from pydantic import ValidationError

from app.database import Base
from app.routes.scans import create_scan, list_scans, get_scan, get_scan_findings
from app.routes.findings import get_finding, explain_finding
from app.routes.retesting import retest_scan_findings
from app.routes.reports import get_scan_report
from app.main import root_health, api_health
from app.schemas import ScanCreateRequest, RetestRequest
from app.security_engine.integration import (
    validate_target_safety,
    TargetSafetyError,
    set_security_engine_override,
    reset_security_engine,
    MockSecurityEngineAdapter,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# Isolated in-memory database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Create fresh tables for each test and tear down, ensuring mock adapter isolation."""
    Base.metadata.create_all(bind=test_engine)
    session = SessionLocal()
    set_security_engine_override(MockSecurityEngineAdapter())
    try:
        yield session
    finally:
        reset_security_engine()
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_health_endpoints(db):
    """Test /health and /api/health handlers."""
    r1 = root_health()
    assert r1.status == "healthy"
    assert r1.database == "connected"

    r2 = api_health(db=db)
    assert r2.status == "healthy"
    assert r2.database == "connected"


def test_authorization_default_and_enforcement():
    """Verify that user_authorized defaults to False and is rejected when omitted or False."""
    # 1. When omitted, defaults to False and fails validation
    with pytest.raises(ValidationError):
        ScanCreateRequest(target_url="https://api.example.com")

    # 2. When explicitly False, fails validation
    with pytest.raises(ValidationError):
        ScanCreateRequest(
            target_url="https://api.example.com",
            user_authorized=False,
            categories=["BOLA"],
        )


def test_url_scheme_and_crlf_validation():
    """Verify that target_url must start with http:// or https:// and cannot contain CRLF injection."""
    with pytest.raises(ValidationError):
        ScanCreateRequest(
            target_url="ftp://api.example.com",
            user_authorized=True,
        )

    # Rejects newline / carriage return injection
    with pytest.raises(ValidationError):
        ScanCreateRequest(
            target_url="https://api.example.com\r\nX-Injected-Header: evil",
            user_authorized=True,
        )


def test_cloud_metadata_and_link_local_blocking():
    """Verify SSRF protection strictly blocks cloud metadata and link-local IPs even in lab mode."""
    # Cloud metadata IP (blocked in standard mode and lab mode)
    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://169.254.169.254/latest/meta-data/", allow_lab=False)

    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://169.254.169.254/latest/meta-data/", allow_lab=True)

    # IPv6 and IPv4-mapped IPv6 cloud metadata
    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://[fd00:ec2::254]/latest/meta-data/", allow_lab=True)

    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://[::ffff:169.254.169.254]/latest/meta-data/", allow_lab=True)

    # Google cloud metadata hostname
    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://metadata.google.internal/computeMetadata/v1/", allow_lab=True)

    # Link-local IP range
    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://169.254.10.20/status", allow_lab=True)


def test_redirect_ssrf_validation(monkeypatch):
    """Verify that HTTP redirect target URLs are validated against SSRF before following."""
    import socket
    from app.security_engine.integration import validate_safe_redirect

    # Mock getaddrinfo for deterministic unit testing without external DNS dependency
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "api.example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        elif host == "10.0.0.1":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 80))]
        elif host == "169.254.169.254":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))]
        raise socket.gaierror(f"Unknown host {host}")

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    # Safe relative redirect
    safe_target = validate_safe_redirect("https://api.example.com/v1/auth", "/v1/login", allow_lab=False)
    assert safe_target == "https://api.example.com/v1/login"

    # Malicious redirect to cloud metadata
    with pytest.raises(TargetSafetyError):
        validate_safe_redirect("https://api.example.com/v1", "http://169.254.169.254/latest/meta-data/", allow_lab=True)

    # Malicious redirect to internal private IP when lab mode is False
    with pytest.raises(TargetSafetyError):
        validate_safe_redirect("https://api.example.com/v1", "http://10.0.0.1/admin", allow_lab=False)


def test_full_scan_creation_and_credential_redaction(db):
    """Create a scan and verify all credentials, headers, and tokens are recursively redacted in DB."""
    req = ScanCreateRequest(
        target_url="https://api.local-lab.test",
        user_authorized=True,
        categories=["BOLA", "AUTH", "HEADERS"],
        auth_token="super_secret_token_abc",
        custom_headers={
            "Authorization": "Bearer raw_jwt_secret_token",
            "X-Api-Key": "live_api_key_999",
            "Content-Type": "application/json",
        },
        test_accounts={
            "patient_a": {"username": "alice", "password": "super_secret_password_a"},
            "patient_b": {"username": "bob", "auth_token": "token_b_secret"},
        },
    )
    scan = create_scan(payload=req, db=db)
    assert scan.id is not None
    assert scan.status == "Completed"
    assert scan.total_findings >= 3

    # Verify ALL credentials and secrets are redacted from stored configuration
    stored_config = scan.scan_configuration
    assert stored_config["auth_token"] == "[REDACTED_FOR_SECURITY]"
    assert stored_config["custom_headers"]["Authorization"] == "[REDACTED_FOR_SECURITY]"
    assert stored_config["custom_headers"]["X-Api-Key"] == "[REDACTED_FOR_SECURITY]"
    # Non-sensitive header preserved
    assert stored_config["custom_headers"]["Content-Type"] == "application/json"

    # Verify nested test accounts redacted
    assert stored_config["test_accounts"]["patient_a"]["username"] == "alice"
    assert stored_config["test_accounts"]["patient_a"]["password"] == "[REDACTED_FOR_SECURITY]"
    assert stored_config["test_accounts"]["patient_b"]["auth_token"] == "[REDACTED_FOR_SECURITY]"

    # Verify engine metadata explicitly labels mock execution
    assert stored_config.get("is_simulated") is True
    assert stored_config.get("engine_name") == "mock_adapter"

    # Verify retrieval by ID
    fetched_scan = get_scan(scan_id=scan.id, db=db)
    assert fetched_scan.id == scan.id

    # Verify findings retrieval and explicit mock labeling
    findings = get_scan_findings(scan_id=scan.id, db=db)
    assert len(findings) == scan.total_findings

    first = findings[0]
    assert "[SIMULATED MOCK]" in first.vulnerability
    assert "[SIMULATED MOCK FINDING" in first.description
    assert first.evidence is not None
    assert first.evidence.observed_status is not None
    assert "simulation_notice" in first.evidence.request_details


def test_scan_listing_and_filtering(db):
    """Test pagination and scan history retrieval."""
    for i in range(3):
        req = ScanCreateRequest(
            target_url=f"https://api{i}.local-lab.test",
            user_authorized=True,
        )
        create_scan(payload=req, db=db)

    list_resp = list_scans(skip=0, limit=2, status="Completed", db=db)
    assert list_resp.total == 3
    assert len(list_resp.items) == 2


def test_ai_explanation_generation_and_caching(db):
    """Test AI explanation service with rule-based fallback and SQLite caching."""
    req = ScanCreateRequest(
        target_url="https://api.local-lab.test",
        user_authorized=True,
        categories=["BOLA"],
    )
    scan = create_scan(payload=req, db=db)
    findings = get_scan_findings(scan_id=scan.id, db=db)
    finding_id = findings[0].id

    # First request: generates explanation
    exp1 = explain_finding(finding_id=finding_id, db=db)
    assert exp1.finding_id == finding_id
    assert len(exp1.explanation) > 0
    assert len(exp1.impact) > 0
    assert len(exp1.remediation) > 0
    assert exp1.is_ai_generated is True

    # Second request: returns cached explanation
    exp2 = explain_finding(finding_id=finding_id, db=db)
    assert exp2.id == exp1.id


def test_retest_and_verification_workflow(db):
    """Test retesting workflow verifying whether vulnerability is still present or resolved."""
    req = ScanCreateRequest(
        target_url="https://api.local-lab.test",
        user_authorized=True,
        categories=["BOLA"],
    )
    scan = create_scan(payload=req, db=db)
    findings = get_scan_findings(scan_id=scan.id, db=db)
    finding_id = findings[0].id

    # Retest without simulated fix -> remains Still Vulnerable
    retest_res = retest_scan_findings(
        scan_id=scan.id,
        payload=RetestRequest(finding_id=finding_id),
        db=db,
    )
    assert len(retest_res.results) == 1
    assert retest_res.results[0].new_status == "Still Vulnerable"
    assert retest_res.results[0].verified is False
    assert "simulation_notice" in retest_res.results[0].observed_result
    assert "[SIMULATED MOCK RETEST]" in retest_res.results[0].observed_result.get("message", "")

    # Verify finding status updated in DB
    updated_finding = get_finding(finding_id=finding_id, db=db)
    assert updated_finding.status == "Still Vulnerable"


def test_security_report_generation(db):
    """Verify security report aggregation and summary calculation."""
    req = ScanCreateRequest(
        target_url="https://api.local-lab.test",
        user_authorized=True,
        categories=["BOLA", "AUTH", "HEADERS"],
    )
    scan = create_scan(payload=req, db=db)
    report = get_scan_report(scan_id=scan.id, db=db)

    assert report.scan.id == scan.id
    assert report.summary.total_findings >= 3
    assert report.summary.open_count >= 3
    assert "High" in report.summary.severity_breakdown or "Critical" in report.summary.severity_breakdown
    assert len(report.findings) >= 3


def test_empty_retest_payload(db):
    """Verify retest endpoint accepts None / empty payload safely and retests all scan findings."""
    req = ScanCreateRequest(
        target_url="https://api.local-lab.test",
        user_authorized=True,
        categories=["BOLA", "AUTH"],
    )
    scan = create_scan(payload=req, db=db)
    # Invoke with payload=None (simulating empty JSON body from frontend)
    retest_res = retest_scan_findings(scan_id=scan.id, payload=None, db=db)
    assert len(retest_res.results) == 2
    for item in retest_res.results:
        assert item.new_status in ("Still Vulnerable", "Resolved", "Retest Failed")


def test_database_persistence_across_sessions(tmp_path):
    """Verify that records committed to SQLite persist on disk across session closures."""
    set_security_engine_override(MockSecurityEngineAdapter())
    try:
        db_file = tmp_path / "persistent_test.db"
        persistent_engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=persistent_engine)
        Session = sessionmaker(bind=persistent_engine)

        # Session 1: Create and commit a scan with findings
        with Session() as session1:
            req = ScanCreateRequest(
                target_url="https://api.local-lab.test",
                user_authorized=True,
                categories=["BOLA"],
            )
            scan = create_scan(payload=req, db=session1)
            scan_id = scan.id
            finding_id = scan.findings[0].id

            # Generate and save AI explanation
            explain_finding(finding_id=finding_id, db=session1)

        # Close session 1 completely and open a completely new session from disk
        with Session() as session2:
            reloaded_scan = get_scan(scan_id=scan_id, db=session2)
            assert reloaded_scan.id == scan_id
            assert reloaded_scan.status == "Completed"

            reloaded_findings = get_scan_findings(scan_id=scan_id, db=session2)
            assert len(reloaded_findings) >= 1
            assert reloaded_findings[0].evidence is not None
            assert reloaded_findings[0].ai_explanation is not None
            assert reloaded_findings[0].ai_explanation.is_ai_generated is True
    finally:
        reset_security_engine()
