"""Phase 4 End-to-End Integration Test Suite.

Validates the full lifecycle requested in Phase 5:
- Vulnerable mode scanning on Healthcare Demo API
- Detection of BOLA/IDOR with technical HTTP evidence
- AI Nemotron / fallback explanation generation
- Transition to Secure Mode
- Verification retesting triggering HTTP 403 Forbidden
- Status promotion from 'Open' to 'Resolved'
- Preservation of append-only RetestHistory audit records
- Comprehensive security report synthesis
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Scan, Finding, RetestHistory
from app.routes.scans import create_scan
from app.routes.findings import explain_finding, get_finding_retest_history
from app.routes.retesting import retest_scan_findings
from app.routes.reports import get_scan_report
from app.schemas import ScanCreateRequest, RetestRequest
from demo_api.main import app as demo_app
from demo_api.config import settings as demo_settings


@pytest.fixture
def clean_db(db_session):
    """Ensure clean database session for end-to-end lifecycle."""
    yield db_session


def test_phase4_complete_vulnerable_and_secure_retest_lifecycle(clean_db):
    """End-to-End Test: Vulnerable Demo Scan -> Finding Evidence -> AI Explain -> Secure Mode -> Retest -> Resolved."""
    db = clean_db
    settings.ALLOW_LOCAL_LAB_SCANNING = True

    # -------------------------------------------------------------------------
    # PART A: Vulnerable Mode Execution
    # -------------------------------------------------------------------------
    demo_settings.DEMO_VULNERABLE_MODE = True
    demo_settings.ENABLE_SECURITY_HEADERS = False

    demo_client = TestClient(demo_app)

    # 1. Verify Demo API in vulnerable mode
    health_resp = demo_client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["vulnerable_mode"] is True

    # 2. Authenticate synthetic users
    login_a = demo_client.post("/api/auth/login", json={"username": "patient_a", "password": "demo_password_a"})
    assert login_a.status_code == 200
    token_a = login_a.json()["access_token"]

    login_b = demo_client.post("/api/auth/login", json={"username": "patient_b", "password": "demo_password_b"})
    assert login_b.status_code == 200
    token_b = login_b.json()["access_token"]

    # 3. Demonstrate Vulnerable Cross-User Access (BOLA/IDOR)
    cross_access = demo_client.get("/api/patients/102", headers={"Authorization": f"Bearer {token_a}"})
    assert cross_access.status_code == 200
    assert cross_access.json()["patient_id"] == 102
    assert cross_access.json()["owner_username"] == "patient_b"

    # 4. Trigger Real Scan via API Sentinel Scan Endpoint
    scan_req = ScanCreateRequest(
        target_url="http://127.0.0.1:8001",
        scan_profile="OWASP API Top 10 Deep Audit",
        user_authorized=True,
        categories=["BOLA", "AUTH", "HEADERS"],
    )

    # Use in-process transport hook for Member 1 engine testing
    from app.security_engine.member1_engine import EngineAdapter
    from demo_api.transport import DemoApiTransport
    from app.security_engine.integration import set_security_engine_override, reset_security_engine

    adapter = EngineAdapter(transport=DemoApiTransport())
    set_security_engine_override(adapter)

    try:
        scan_res = create_scan(payload=scan_req, db=db)
        assert scan_res.status == "Completed"
        assert scan_res.total_findings >= 1

        # 5. Verify Findings and Technical HTTP Evidence
        findings = db.query(Finding).filter(Finding.scan_id == scan_res.id).all()
        bola_finding = next((f for f in findings if "BOLA" in f.category or "BOLA" in f.vulnerability), None)
        assert bola_finding is not None
        assert bola_finding.status == "Open"
        assert "/api/patients" in bola_finding.endpoint
        assert bola_finding.evidence is not None
        assert bola_finding.evidence.observed_status == 200

        # 6. Request AI Explanation (Nemotron with schema validation & caching)
        from unittest.mock import patch
        from app.services.ai_service import ai_service

        mock_output = {
            "explanation": "BOLA allows user A to access user B records.",
            "impact": "Unauthorized access to confidential patient medical records.",
            "remediation": "Implement strict object-level authorization checks in patient endpoint.",
            "model_name": "nvidia/nemotron-3.5-lightning-30b-a3b",
        }

        with patch.object(ai_service, "explain_vulnerability", return_value=mock_output):
            exp = explain_finding(finding_id=bola_finding.id, db=db)
            assert exp.finding_id == bola_finding.id
            assert "BOLA" in exp.explanation
            assert len(exp.impact) > 10
            assert len(exp.remediation) > 10
            assert exp.is_ai_generated is True

        # Verify explanation is cached in SQLite (does not re-invoke LLM)
        exp_cached = explain_finding(finding_id=bola_finding.id, db=db)
        assert exp_cached.id == exp.id

        # ---------------------------------------------------------------------
        # PART B: Transition to Secure Mode & Verification Retesting
        # ---------------------------------------------------------------------
        demo_settings.DEMO_VULNERABLE_MODE = False
        demo_settings.ENABLE_SECURITY_HEADERS = True

        # Verify secure mode rejection on cross-user access
        secure_cross_access = demo_client.get("/api/patients/102", headers={"Authorization": f"Bearer {token_a}"})
        assert secure_cross_access.status_code == 403
        assert "Forbidden" in secure_cross_access.json()["detail"]

        # 7. Execute Retesting via POST /api/scans/{id}/retest
        retest_req = RetestRequest(finding_id=bola_finding.id)
        retest_output = retest_scan_findings(scan_id=scan_res.id, payload=retest_req, db=db)

        assert len(retest_output.results) == 1
        assert retest_output.results[0].finding_id == bola_finding.id
        assert retest_output.results[0].new_status == "Resolved"
        assert retest_output.results[0].verified is True

        # 8. Verify Status Transition in Database
        db.refresh(bola_finding)
        assert bola_finding.status == "Resolved"

        # 9. Verify Append-Only RetestHistory
        history = get_finding_retest_history(finding_id=bola_finding.id, db=db)
        assert history.total_retests == 1
        assert history.history[0].previous_status == "Open"
        assert history.history[0].new_status == "Resolved"
        assert "403" in str(history.history[0].observed_result)

        # 10. Generate Security Posture Report
        report = get_scan_report(scan_id=scan_res.id, db=db)
        assert report.summary.total_findings >= 1
        assert report.summary.resolved_count >= 1
        assert report.scan.id == scan_res.id

    finally:
        reset_security_engine()
        # Reset demo settings
        demo_settings.DEMO_VULNERABLE_MODE = True
        demo_settings.ENABLE_SECURITY_HEADERS = False
