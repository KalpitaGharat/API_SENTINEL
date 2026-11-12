"""Tests for Attack Demonstration & Evidence Inspector backend components.

Validates:
1. Evidence export endpoint (/api/findings/{id}/export-evidence)
2. SHA-256 cryptographic digest calculation and repeatability
3. Tamper-detection: altering response body, request header, or finding ID invalidates digest
4. Forensics telemetry structure (cURL command, masked headers, latency, timeline)
5. AI Service explainability payload with remediation disclaimer
"""

import json
import hashlib
import uuid
import copy
import pytest
from app.models import Scan, Finding, Evidence
from app.services.ai_service import AIService


@pytest.fixture
def sample_finding_with_evidence(db_session):
    """Fixture providing a persisted finding and technical evidence record."""
    scan = Scan(
        id=str(uuid.uuid4()),
        target_url="http://127.0.0.1:8001",
        status="Completed",
        total_findings=1,
    )
    db_session.add(scan)
    db_session.commit()

    finding = Finding(
        id=str(uuid.uuid4()),
        scan_id=scan.id,
        vulnerability="Broken Object Level Authorization (BOLA)",
        category="API1:2023",
        severity="Critical",
        endpoint="/api/patients/{patient_id}",
        description="Patient A accessed confidential medical records belonging to Patient B.",
        recommendation="Validate object-level ownership before returning database records.",
        status="Open",
    )
    db_session.add(finding)
    db_session.commit()

    req_details = {
        "method": "GET",
        "url": "http://127.0.0.1:8001/api/patients/102",
        "headers": {
            "Host": "127.0.0.1:8001",
            "Authorization": "Bearer sent..._101"
        },
        "duration_ms": 15.4,
        "curl_command": 'curl -X GET "http://127.0.0.1:8001/api/patients/102" -H "Authorization: Bearer sent..._101"',
        "timeline": [
            {"step": 1, "action": "Target Registration", "status": "completed"},
            {"step": 2, "action": "Exploit Dispatch", "status": "completed"}
        ],
        "exposed_fields": ["diagnosis", "prescriptions"],
        "security_observations": ["Cross-tenant boundary breach: patient_a accessed patient_b record"],
    }

    resp_details = {
        "status_code": 200,
        "headers": {"content-type": "application/json"},
        "body": {
            "id": 102,
            "name": "Bob Smith",
            "diagnosis": "Arrhythmia"
        },
        "duration_ms": 15.4,
        "exposed_fields": ["diagnosis", "prescriptions"],
    }

    evidence = Evidence(
        id=str(uuid.uuid4()),
        finding_id=finding.id,
        test_user="patient_a",
        requested_resource="/api/patients/102",
        observed_status=200,
        expected_status=403,
        request_details=req_details,
        response_details=resp_details,
    )
    db_session.add(evidence)
    db_session.commit()

    return finding


def test_export_evidence_not_found(client):
    """Attempting to export evidence for a non-existent finding returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/api/findings/{fake_id}/export-evidence")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_export_evidence_success_and_sha256_integrity(client, sample_finding_with_evidence):
    """Evidence export returns canonical structure with valid SHA-256 digest."""
    finding = sample_finding_with_evidence

    resp = client.get(f"/api/findings/{finding.id}/export-evidence")
    assert resp.status_code == 200

    data = resp.json()
    assert data["export_version"] == "1.1.0"
    assert "exported_at" in data
    assert "sha256_digest" in data
    assert len(data["sha256_digest"]) == 64

    # Verify SHA-256 cryptographic digest integrity
    reported_digest = data["sha256_digest"]
    
    # Reconstruct the digest payload independently (exclude sha256_digest)
    verifiable_copy = {k: v for k, v in data.items() if k != "sha256_digest"}
    canonical_bytes = json.dumps(verifiable_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected_digest = hashlib.sha256(canonical_bytes).hexdigest()

    assert reported_digest == expected_digest, "Exported SHA-256 digest must match canonical hash exactly"

    # Verify nested request / response structure
    req_out = data["request"]
    resp_out = data["response"]
    assert "sent..._101" in req_out["curl_command"]
    assert resp_out["body"]["diagnosis"] == "Arrhythmia"
    assert resp_out["duration_ms"] == 15.4

    # Also verify alias route works and computes valid self-contained digest
    resp_alias = client.get(f"/api/findings/{finding.id}/evidence/export")
    assert resp_alias.status_code == 200
    alias_data = resp_alias.json()
    alias_verifiable = {k: v for k, v in alias_data.items() if k != "sha256_digest"}
    alias_bytes = json.dumps(alias_verifiable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert alias_data["sha256_digest"] == hashlib.sha256(alias_bytes).hexdigest()


def test_sha256_tamper_detection_tampered_response_body(client, sample_finding_with_evidence):
    """Altering a single response body field causes SHA-256 digest verification to fail."""
    finding = sample_finding_with_evidence
    resp = client.get(f"/api/findings/{finding.id}/export-evidence")
    data = resp.json()
    original_digest = data["sha256_digest"]

    # Deliberately tamper with response body
    tampered = copy.deepcopy(data)
    del tampered["sha256_digest"]
    tampered["response"]["body"]["diagnosis"] = "Fabricated Medical Diagnosis (Tampered)"

    canonical_tampered = json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tampered_digest = hashlib.sha256(canonical_tampered).hexdigest()

    assert original_digest != tampered_digest, "Digest MUST change when response body is modified"


def test_sha256_tamper_detection_tampered_request_header(client, sample_finding_with_evidence):
    """Altering request headers causes SHA-256 digest verification to fail."""
    finding = sample_finding_with_evidence
    resp = client.get(f"/api/findings/{finding.id}/export-evidence")
    data = resp.json()
    original_digest = data["sha256_digest"]

    # Deliberately tamper with request header
    tampered = copy.deepcopy(data)
    del tampered["sha256_digest"]
    tampered["request"]["headers"]["Authorization"] = "Bearer injected_rogue_token_999"

    canonical_tampered = json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tampered_digest = hashlib.sha256(canonical_tampered).hexdigest()

    assert original_digest != tampered_digest, "Digest MUST change when request headers are modified"


def test_sha256_tamper_detection_tampered_finding_id(client, sample_finding_with_evidence):
    """Altering finding identifier causes SHA-256 digest verification to fail."""
    finding = sample_finding_with_evidence
    resp = client.get(f"/api/findings/{finding.id}/export-evidence")
    data = resp.json()
    original_digest = data["sha256_digest"]

    # Deliberately tamper with finding_id
    tampered = copy.deepcopy(data)
    del tampered["sha256_digest"]
    tampered["finding_id"] = str(uuid.uuid4())

    canonical_tampered = json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tampered_digest = hashlib.sha256(canonical_tampered).hexdigest()

    assert original_digest != tampered_digest, "Digest MUST change when finding ID is modified"


def test_evidence_export_secrets_sanitized(client, sample_finding_with_evidence):
    """Exported evidence must never leak raw tokens or sensitive auth secrets."""
    finding = sample_finding_with_evidence
    resp = client.get(f"/api/findings/{finding.id}/export-evidence")
    data = resp.json()
    export_str = json.dumps(data)

    assert "sent_demo_token_101" not in export_str, "Raw token must not appear in export"
    assert "demo_password_" not in export_str, "Passwords must not appear in export"
    assert "sent..._101" in export_str, "Export must contain masked authorization token"


def test_ai_service_includes_remediation_disclaimer():
    """Rule-based and LLM remediation text must include the disclaimer."""
    ai_service = AIService()
    finding_dict = {
        "vulnerability": "Broken Object Level Authorization (BOLA)",
        "category": "API1:2023",
        "description": "Cross-tenant access.",
        "endpoint": "/api/patients/{id}",
    }
    result = ai_service._generate_rule_based_fallback(finding_dict)
    
    disclaimer = "*Suggested remediation — not automatically applied or verified.*"
    assert disclaimer in result["remediation"], "Remediation must contain explicit advisory disclaimer"
    assert "explanation" in result
    assert "impact" in result
