"""Comprehensive Backend Test Suite for API Sentinel.

Tests health, database operations, scan execution, target safety controls,
finding extraction, AI explanation fallback, retest verification, and reporting.
"""

import pytest
from app.config import settings
from app.security_engine.integration import (
    validate_target_safety, 
    TargetSafetyError,
    set_security_engine_override,
    reset_security_engine,
    MockSecurityEngineAdapter,
)


@pytest.fixture(autouse=True)
def setup_mock_engine_for_unit_tests():
    """Ensure offline route unit tests with synthetic .local/.test domains use mock adapter."""
    set_security_engine_override(MockSecurityEngineAdapter())
    yield
    reset_security_engine()


def test_health_endpoints(client):
    """Verify both /health and /api/health return HTTP 200 and healthy status."""
    resp1 = client.get("/health")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "healthy"
    assert data1["database"] == "connected"

    resp2 = client.get("/api/health")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "healthy"
    assert data2["database"] == "connected"


def test_scan_requires_authorization(client):
    """Enforce Section 11 safety control: user MUST confirm authorization."""
    payload = {
        "target_url": "https://api.example.com",
        "user_authorized": False,  # Should fail validation
        "categories": ["BOLA", "AUTH"],
    }
    resp = client.post("/api/scans", json=payload)
    assert resp.status_code == 422


def test_scan_validates_url_format(client):
    """Validate that target_url must start with http:// or https://."""
    payload = {
        "target_url": "ftp://malicious.example.com",
        "user_authorized": True,
    }
    resp = client.post("/api/scans", json=payload)
    assert resp.status_code == 422


def test_cloud_metadata_blocking():
    """Verify SSRF protection blocks cloud metadata endpoints."""
    with pytest.raises(TargetSafetyError):
        validate_target_safety("http://169.254.169.254/latest/meta-data/", allow_lab=True)


def test_create_and_run_scan(client):
    """Create and execute a full scan, verifying findings and evidence persistence."""
    payload = {
        "target_url": "https://api.student-health.local",
        "user_authorized": True,
        "categories": ["BOLA", "AUTH", "HEADERS"],
        "auth_token": "secret_token_12345",
    }
    resp = client.post("/api/scans", json=payload)
    assert resp.status_code == 201
    scan_data = resp.json()

    assert scan_data["status"] == "Completed"
    assert scan_data["total_findings"] >= 1
    assert scan_data["target_url"] == payload["target_url"]
    # Check that secrets are redacted from stored configuration
    assert scan_data["scan_configuration"]["auth_token"] == "[REDACTED_FOR_SECURITY]"

    scan_id = scan_data["id"]

    # Retrieve scan by ID
    get_resp = client.get(f"/api/scans/{scan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == scan_id

    # Retrieve findings for scan
    findings_resp = client.get(f"/api/scans/{scan_id}/findings")
    assert findings_resp.status_code == 200
    findings = findings_resp.json()
    assert len(findings) == scan_data["total_findings"]

    first_finding = findings[0]
    assert "evidence" in first_finding
    assert first_finding["evidence"]["observed_status"] is not None


def test_scan_pagination_and_filter(client):
    """Verify GET /api/scans pagination and status filtering."""
    # Create two scans
    client.post("/api/scans", json={"target_url": "https://api1.test", "user_authorized": True})
    client.post("/api/scans", json={"target_url": "https://api2.test", "user_authorized": True})

    list_resp = client.get("/api/scans?limit=10&status=Completed")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_ai_explanation_and_caching(client):
    """Verify AI explanation generation and deterministic SQLite caching."""
    # Create a scan to obtain a finding
    scan_resp = client.post(
        "/api/scans",
        json={"target_url": "https://api.test", "user_authorized": True},
    )
    scan_id = scan_resp.json()["id"]
    findings = client.get(f"/api/scans/{scan_id}/findings").json()
    finding_id = findings[0]["id"]

    # Request AI explanation
    explain_resp = client.post(f"/api/findings/{finding_id}/explain")
    assert explain_resp.status_code == 200
    explanation = explain_resp.json()

    assert explanation["finding_id"] == finding_id
    assert len(explanation["explanation"]) > 0
    assert len(explanation["impact"]) > 0
    assert len(explanation["remediation"]) > 0
    assert explanation["is_ai_generated"] is True

    # Call again to verify cached explanation is returned
    cached_resp = client.post(f"/api/findings/{finding_id}/explain")
    assert cached_resp.status_code == 200
    assert cached_resp.json()["id"] == explanation["id"]


def test_retest_and_verification_workflow(client):
    """Test re-testing workflow for verifying remediation."""
    # 1. Create scan
    scan_resp = client.post(
        "/api/scans",
        json={"target_url": "https://api.test", "user_authorized": True},
    )
    scan_id = scan_resp.json()["id"]
    findings = client.get(f"/api/scans/{scan_id}/findings").json()
    finding_id = findings[0]["id"]

    # 2. Retest without simulated fix -> remains Still Vulnerable
    retest_resp1 = client.post(
        f"/api/scans/{scan_id}/retest",
        json={"finding_id": finding_id},
    )
    assert retest_resp1.status_code == 200
    res1 = retest_resp1.json()["results"][0]
    assert res1["new_status"] == "Still Vulnerable"
    assert res1["verified"] is False

    # Check updated finding status
    finding_check = client.get(f"/api/findings/{finding_id}").json()
    assert finding_check["status"] == "Still Vulnerable"


def test_generate_report(client):
    """Verify security report generation and summary metric calculation."""
    scan_resp = client.post(
        "/api/scans",
        json={"target_url": "https://api.test", "user_authorized": True},
    )
    scan_id = scan_resp.json()["id"]

    report_resp = client.get(f"/api/scans/{scan_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()

    assert "scan" in report
    assert "summary" in report
    assert "findings" in report
    assert report["summary"]["total_findings"] > 0
    assert report["summary"]["open_count"] > 0
    assert isinstance(report["summary"]["severity_breakdown"], dict)
