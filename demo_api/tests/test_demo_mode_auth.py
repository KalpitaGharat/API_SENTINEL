"""Focused Security & Authorization Tests for Healthcare Demo API.

Verifies:
1. Secure mode is the default state on startup.
2. Mode toggle endpoint (/api/demo/mode) requires valid DEMO_ADMIN_TOKEN.
3. Unauthorized attempts (missing token, invalid token, unconfigured server token) are strictly blocked (401).
4. Constant-time token comparison allows authorized administrative changes via:
   - 'X-Demo-Admin-Token' header
   - 'Authorization: Bearer <token>' header
   - 'admin_token' JSON payload field
5. Controlled BOLA vulnerability behavior is preserved:
   - Vulnerable mode: cross-user patient access succeeds (200 OK).
   - Secure mode: cross-user patient access is blocked (403 Forbidden).
6. Synthetic patient data integrity (zero real patient records).
"""

import pytest
from fastapi.testclient import TestClient

from demo_api.main import app as demo_app, SYNTHETIC_RECORDS
from demo_api.config import settings as demo_settings


@pytest.fixture(autouse=True)
def reset_demo_settings():
    """Reset demo settings before and after each test."""
    original_mode = demo_settings.DEMO_VULNERABLE_MODE
    original_headers = demo_settings.ENABLE_SECURITY_HEADERS
    original_token = demo_settings.DEMO_ADMIN_TOKEN

    # Default to secure mode
    demo_settings.DEMO_VULNERABLE_MODE = False
    demo_settings.ENABLE_SECURITY_HEADERS = True
    demo_settings.DEMO_ADMIN_TOKEN = "test-demo-admin-token-secret-999"

    yield

    demo_settings.DEMO_VULNERABLE_MODE = original_mode
    demo_settings.ENABLE_SECURITY_HEADERS = original_headers
    demo_settings.DEMO_ADMIN_TOKEN = original_token


@pytest.fixture
def client():
    """Test client for Healthcare Demo API."""
    return TestClient(demo_app)


@pytest.fixture
def patient_tokens(client):
    """Authenticate synthetic patients and retrieve bearer tokens."""
    resp_a = client.post("/api/auth/login", json={"username": "patient_a", "password": "demo_password_a"})
    resp_b = client.post("/api/auth/login", json={"username": "patient_b", "password": "demo_password_b"})
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    return {
        "patient_a": resp_a.json()["access_token"],
        "patient_b": resp_b.json()["access_token"],
    }


# =============================================================================
# 1. Default Secure Mode Verification
# =============================================================================

def test_default_mode_is_secure(client, patient_tokens):
    """Verify demo API defaults to secure mode with security headers applied."""
    health = client.get("/health")
    assert health.status_code == 200
    data = health.json()
    assert data["vulnerable_mode"] is False
    assert data["security_headers"] is True
    assert data["admin_auth_configured"] is True

    # In secure mode, cross-user access to patient 102 by patient A is forbidden (403)
    res = client.get(
        "/api/patients/102",
        headers={"Authorization": f"Bearer {patient_tokens['patient_a']}"},
    )
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


# =============================================================================
# 2. Unauthorized Mode Change Protection
# =============================================================================

def test_mode_toggle_rejected_without_token(client):
    """Verify unauthenticated requests cannot toggle mode."""
    res = client.post("/api/demo/mode", json={"vulnerable": True})
    assert res.status_code == 401
    assert "Unauthorized" in res.json()["detail"]
    assert demo_settings.DEMO_VULNERABLE_MODE is False  # Mode was not altered


def test_mode_toggle_rejected_with_invalid_token(client):
    """Verify requests with incorrect admin tokens are rejected (401)."""
    # 1. Invalid X-Demo-Admin-Token header
    res1 = client.post(
        "/api/demo/mode",
        json={"vulnerable": True},
        headers={"X-Demo-Admin-Token": "incorrect-token-xyz"},
    )
    assert res1.status_code == 401
    assert "Invalid demo admin token" in res1.json()["detail"]

    # 2. Invalid Authorization header
    res2 = client.post(
        "/api/demo/mode",
        json={"vulnerable": True},
        headers={"Authorization": "Bearer wrong-token-123"},
    )
    assert res2.status_code == 401

    # 3. Invalid admin_token in body
    res3 = client.post(
        "/api/demo/mode",
        json={"vulnerable": True, "admin_token": "wrong-token-abc"},
    )
    assert res3.status_code == 401
    assert demo_settings.DEMO_VULNERABLE_MODE is False


def test_mode_toggle_rejected_when_server_token_not_configured(client):
    """Verify mode modification is strictly disabled when server has no DEMO_ADMIN_TOKEN."""
    demo_settings.DEMO_ADMIN_TOKEN = ""

    res = client.post(
        "/api/demo/mode",
        json={"vulnerable": True, "admin_token": "any-token"},
        headers={"X-Demo-Admin-Token": "any-token"},
    )
    assert res.status_code == 401
    assert "DEMO_ADMIN_TOKEN is not configured" in res.json()["detail"]
    assert demo_settings.DEMO_VULNERABLE_MODE is False


# =============================================================================
# 3. Authorized Mode Change Verification
# =============================================================================

def test_mode_toggle_authorized_via_custom_header(client):
    """Verify admin can toggle mode using X-Demo-Admin-Token."""
    res = client.post(
        "/api/demo/mode",
        json={"vulnerable": True, "enable_security_headers": False},
        headers={"X-Demo-Admin-Token": "test-demo-admin-token-secret-999"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "updated"
    assert data["vulnerable_mode"] is True
    assert demo_settings.DEMO_VULNERABLE_MODE is True


def test_mode_toggle_authorized_via_bearer_header(client):
    """Verify admin can toggle mode using Authorization: Bearer <token>."""
    res = client.post(
        "/api/demo/mode",
        json={"vulnerable": True},
        headers={"Authorization": "Bearer test-demo-admin-token-secret-999"},
    )
    assert res.status_code == 200
    assert res.json()["vulnerable_mode"] is True
    assert demo_settings.DEMO_VULNERABLE_MODE is True


def test_mode_toggle_authorized_via_json_payload(client):
    """Verify admin can toggle mode using admin_token field in JSON body."""
    res = client.post(
        "/api/demo/mode",
        json={"vulnerable": True, "admin_token": "test-demo-admin-token-secret-999"},
    )
    assert res.status_code == 200
    assert res.json()["vulnerable_mode"] is True
    assert demo_settings.DEMO_VULNERABLE_MODE is True


# =============================================================================
# 4. Controlled BOLA Vulnerability Testing
# =============================================================================

def test_bola_vulnerability_behavior_in_both_modes(client, patient_tokens):
    """Verify BOLA is reproduced in vulnerable mode and prevented in secure mode."""
    token_a = patient_tokens["patient_a"]

    # 1. Switch to Vulnerable Mode with Admin Token
    toggle_res = client.post(
        "/api/demo/mode",
        json={"vulnerable": True, "admin_token": "test-demo-admin-token-secret-999"},
    )
    assert toggle_res.status_code == 200
    assert demo_settings.DEMO_VULNERABLE_MODE is True

    # 2. In vulnerable mode: Patient A accesses Patient B's record 102 (BOLA reproduced)
    res_vuln = client.get(
        "/api/patients/102",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_vuln.status_code == 200
    assert res_vuln.json()["patient_id"] == 102
    assert res_vuln.json()["owner_username"] == "patient_b"

    # 3. Switch back to Secure Mode with Admin Token
    toggle_sec = client.post(
        "/api/demo/mode",
        json={"vulnerable": False, "admin_token": "test-demo-admin-token-secret-999"},
    )
    assert toggle_sec.status_code == 200
    assert demo_settings.DEMO_VULNERABLE_MODE is False

    # 4. In secure mode: Patient A is blocked from record 102 (BOLA remediated)
    res_sec = client.get(
        "/api/patients/102",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_sec.status_code == 403
    assert "Forbidden" in res_sec.json()["detail"]

    # 5. But Patient A can still access their own record 101
    res_own = client.get(
        "/api/patients/101",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_own.status_code == 200
    assert res_own.json()["patient_id"] == 101


# =============================================================================
# 5. Synthetic Medical Data Verification (Zero Real Patient Data)
# =============================================================================

def test_synthetic_data_guarantees():
    """Verify all patient records are explicitly marked synthetic."""
    for pid, rec in SYNTHETIC_RECORDS.items():
        assert "synthetic" in rec["full_name"].lower() or "synthetic" in rec["diagnosis"].lower()
        assert "synthetic" in rec["attending_physician"].lower()
