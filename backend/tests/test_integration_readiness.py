"""Integration Readiness Test Suite for Member 1's Security Engine.

Verifies:
1. The pluggable architecture allows replacing the Mock adapter with Member 1's real engine.
2. Real findings strictly adhere to Pydantic FindingCreate and EvidenceCreate schemas.
3. Scans executed with a real engine are marked is_simulated: False with their engine_name.
4. Scans executed with the mock engine are marked is_simulated: True.
5. Retest verification updates finding status and records audit history.
6. The safe HTTP client helper enforces SSRF safeguards (disabled automatic redirects).
"""

import pytest
from typing import List, Dict, Any
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Scan, Finding
from app.schemas import ScanCreateRequest, FindingCreate, EvidenceCreate, RetestRequest
from app.routes.scans import create_scan, get_scan_findings
from app.routes.retesting import retest_scan_findings
from app.security_engine.integration import (
    BaseSecurityEngineAdapter,
    MockSecurityEngineAdapter,
    set_security_engine_override,
    reset_security_engine,
    get_security_engine,
    create_safe_http_client,
)

# In-memory SQLite for test isolation
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Create fresh database tables for test and tear down after."""
    Base.metadata.create_all(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        reset_security_engine()


class TestMember1RealEngine(BaseSecurityEngineAdapter):
    """Reference implementation simulating Member 1's real detection engine for readiness testing.

    Marks is_simulated = False and returns unbranded real vulnerability findings.
    """
    engine_name = "member1_real_detection_engine"
    is_simulated = False

    def run_scan(self, target_url: str, config: Dict[str, Any]) -> List[FindingCreate]:
        return [
            FindingCreate(
                vulnerability="Broken Object Level Authorization (BOLA)",
                category="BOLA",
                endpoint="GET /api/records/patient_4412",
                severity="High",
                description="Live probe revealed record access was permitted without matching token owner.",
                recommendation="Enforce server-side record ownership checks against token claims.",
                status="Open",
                evidence=EvidenceCreate(
                    test_user="Patient_A",
                    requested_resource="/api/records/patient_4412",
                    observed_status=200,
                    expected_status=403,
                    request_details={"probe": "GET /api/records/patient_4412", "destination_ip": "192.168.1.50"},
                    response_details={"status_code": 200, "patient_id": "patient_4412"},
                ),
            )
        ]

    def retest_finding(
        self,
        target_url: str,
        finding_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "verified": True,
            "new_status": "Resolved",
            "observed_result": {
                "http_status": 403,
                "message": "Live probe verified: request denied with HTTP 403 Forbidden.",
            },
        }


def test_real_adapter_substitution_and_metadata(db):
    """Verify that a real security engine replaces mock adapter, setting is_simulated: False."""
    # 1. Register Member 1's real engine adapter
    real_engine = TestMember1RealEngine()
    set_security_engine_override(real_engine)

    # 2. Run scan with real engine
    req = ScanCreateRequest(
        target_url="https://api.lab.test",
        user_authorized=True,
        categories=["BOLA"],
    )
    scan = create_scan(payload=req, db=db)

    # 3. Verify scan configuration records real engine metadata
    assert scan.scan_configuration["engine_name"] == "member1_real_detection_engine"
    assert scan.scan_configuration["is_simulated"] is False

    # 4. Verify findings do NOT carry mock tags
    findings = get_scan_findings(scan_id=scan.id, db=db)
    assert len(findings) == 1
    real_f = findings[0]
    assert "[SIMULATED" not in real_f.vulnerability
    assert real_f.vulnerability == "Broken Object Level Authorization (BOLA)"
    assert real_f.evidence.observed_status == 200
    assert real_f.evidence.expected_status == 403

    # 5. Verify retest updates status via real engine
    retest_res = retest_scan_findings(scan_id=scan.id, payload=RetestRequest(finding_id=real_f.id), db=db)
    assert retest_res.results[0].new_status == "Resolved"
    assert retest_res.results[0].verified is True


def test_mock_adapter_restoration_and_metadata(db):
    """Verify that setting mock adapter override marks is_simulated: True, and reset restores real engine."""
    set_security_engine_override(MockSecurityEngineAdapter())

    req = ScanCreateRequest(
        target_url="https://api.lab.test",
        user_authorized=True,
        categories=["BOLA"],
    )
    scan = create_scan(payload=req, db=db)

    assert scan.scan_configuration["engine_name"] == "mock_adapter"
    assert scan.scan_configuration["is_simulated"] is True

    findings = get_scan_findings(scan_id=scan.id, db=db)
    assert "[SIMULATED MOCK]" in findings[0].vulnerability

    # Verify reset restores discovered Member 1 engine
    reset_security_engine()
    engine = get_security_engine()
    assert engine.engine_name == "api_sentinel_real_detection_engine"
    assert engine.is_simulated is False


def test_real_finding_schema_validation():
    """Verify that FindingCreate strictly validates fields required from Member 1's engine."""
    # Valid finding
    valid = FindingCreate(
        vulnerability="Missing Security Headers",
        category="HEADERS",
        endpoint="GET /api/v1/health",
        severity="Medium",
        description="Missing Strict-Transport-Security header.",
        recommendation="Add HSTS middleware.",
        status="Open",
        evidence=EvidenceCreate(
            observed_status=200,
            expected_status=200,
        ),
    )
    assert valid.category == "HEADERS"

    # Missing mandatory field (endpoint) raises ValidationError
    with pytest.raises(ValidationError):
        FindingCreate(
            vulnerability="Broken Auth",
            category="AUTH",
            # endpoint missing
            severity="Critical",
            description="No auth",
            recommendation="Add auth",
        )


def test_safe_http_client_for_member1():
    """Verify safe HTTP client disables automatic redirects to prevent redirect SSRF."""
    client = create_safe_http_client(allow_lab=True, timeout=12.0)
    assert client.follow_redirects is False
    assert client.headers["User-Agent"] == "API-Sentinel-Security-Scanner/1.0"
    client.close()
