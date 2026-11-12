"""Automated Integration Test Suite for API Target & Onboarding Routes.

Tests target lifecycle, OpenAPI preview & import, endpoint filtering/selection,
Fernet auth profile encryption and masking, target connectivity validation,
and scan execution bridging to Member 1's detection engine.
"""

import json
import pytest
from app.config import settings
from app.security_engine.integration import (
    set_security_engine_override,
    reset_security_engine,
    MockSecurityEngineAdapter,
)

SAMPLE_OPENAPI_SPEC = json.dumps({
    "openapi": "3.0.0",
    "info": {
        "title": "Hospital Management Service",
        "version": "1.0.0"
    },
    "servers": [{"url": "http://127.0.0.1:8001"}],
    "paths": {
        "/api/patients": {
            "get": {
                "operationId": "listPatients",
                "summary": "List patients",
                "responses": {"200": {"description": "OK"}}
            },
            "post": {
                "operationId": "createPatient",
                "summary": "Create patient",
                "responses": {"201": {"description": "Created"}}
            }
        },
        "/api/patients/{patient_id}": {
            "parameters": [
                {"name": "patient_id", "in": "path", "required": True, "type": "integer"}
            ],
            "get": {
                "operationId": "getPatient",
                "summary": "Get patient details",
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
})


def test_target_crud_lifecycle(client):
    """Verify target registration, listing, retrieval, update, and deletion."""
    # 1. Create target
    res_create = client.post("/api/targets", json={
        "name": "Clinic Portal API",
        "base_url": "http://127.0.0.1:8001",
        "environment": "development",
        "description": "Clinic management service",
        "api_type": "REST",
        "api_version": "1.0.0"
    })
    assert res_create.status_code == 201
    target = res_create.json()
    target_id = target["id"]
    assert target["name"] == "Clinic Portal API"
    assert target["base_url"] == "http://127.0.0.1:8001"

    # 2. List targets
    res_list = client.get("/api/targets")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    assert any(t["id"] == target_id for t in list_data["items"])

    # 3. Retrieve target details
    res_get = client.get(f"/api/targets/{target_id}")
    assert res_get.status_code == 200
    detail = res_get.json()
    assert detail["id"] == target_id
    assert "endpoints" in detail
    assert "auth_profiles" in detail

    # 4. Update target
    res_put = client.put(f"/api/targets/{target_id}", json={
        "name": "Clinic Portal API Updated",
        "description": "Updated notes"
    })
    assert res_put.status_code == 200
    assert res_put.json()["name"] == "Clinic Portal API Updated"

    # 5. Delete target
    res_del = client.delete(f"/api/targets/{target_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True

    # 6. Verify 404 after deletion
    res_404 = client.get(f"/api/targets/{target_id}")
    assert res_404.status_code == 404


def test_openapi_spec_preview_without_persistence(client):
    """Verify in-memory spec preview parses without saving target."""
    res = client.post("/api/targets/import-spec", json={
        "spec_content": SAMPLE_OPENAPI_SPEC,
        "file_type": "json"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Hospital Management Service"
    assert data["total_endpoints"] == 3
    assert data["sensitive_endpoints_count"] >= 1
    assert len(data["endpoints_preview"]) >= 1


def test_openapi_spec_import_and_endpoints_query(client):
    """Verify importing spec into target creates filterable discovered endpoints."""
    # Register target
    t_res = client.post("/api/targets", json={
        "name": "Spec Target",
        "base_url": "http://127.0.0.1:8001"
    })
    target_id = t_res.json()["id"]

    try:
        # Import spec
        imp_res = client.post(f"/api/targets/{target_id}/import-spec", json={
            "spec_content": SAMPLE_OPENAPI_SPEC,
            "file_type": "json"
        })
        assert imp_res.status_code == 200
        summary = imp_res.json()
        assert summary["total_discovered"] == 3

        # Query all endpoints
        ep_res = client.get(f"/api/targets/{target_id}/endpoints")
        assert ep_res.status_code == 200
        ep_data = ep_res.json()
        assert ep_data["total"] == 3
        items = ep_data["items"]

        # Filter by method GET
        get_res = client.get(f"/api/targets/{target_id}/endpoints?method=GET")
        assert get_res.status_code == 200
        assert get_res.json()["total"] == 2

        # Filter by sensitive candidate
        sens_res = client.get(f"/api/targets/{target_id}/endpoints?is_sensitive=true")
        assert sens_res.status_code == 200
        assert sens_res.json()["total"] >= 1

        # Search by keyword
        search_res = client.get(f"/api/targets/{target_id}/endpoints?search=patient_id")
        assert search_res.status_code == 200
        assert search_res.json()["total"] == 1
    finally:
        client.delete(f"/api/targets/{target_id}")


def test_endpoint_selection_toggle_endpoints(client):
    """Verify bulk selection and individual endpoint selection."""
    t_res = client.post("/api/targets", json={"name": "Select Target", "base_url": "http://127.0.0.1:8001"})
    target_id = t_res.json()["id"]

    try:
        client.post(f"/api/targets/{target_id}/import-spec", json={"spec_content": SAMPLE_OPENAPI_SPEC})
        eps = client.get(f"/api/targets/{target_id}/endpoints").json()["items"]
        first_id = eps[0]["id"]

        # 1. Deselect all
        r_desel = client.put(f"/api/targets/{target_id}/endpoints/selection", json={"select_all": False})
        assert r_desel.status_code == 200
        assert r_desel.json()["selected_count"] == 0

        # 2. Select only first endpoint
        r_first = client.put(f"/api/targets/{target_id}/endpoints/selection", json={"endpoint_ids": [first_id]})
        assert r_first.status_code == 200
        assert r_first.json()["selected_count"] == 1

        # 3. Select all
        r_all = client.put(f"/api/targets/{target_id}/endpoints/selection", json={"select_all": True})
        assert r_all.status_code == 200
        assert r_all.json()["selected_count"] == 3

        # 4. POST /endpoints/select alias with deselect_all
        r_post_desel = client.post(f"/api/targets/{target_id}/endpoints/select", json={"deselect_all": True})
        assert r_post_desel.status_code == 200
        assert r_post_desel.json()["selected_count"] == 0

        # 5. POST /endpoints/select with sensitive_only
        r_post_sens = client.post(f"/api/targets/{target_id}/endpoints/select", json={"sensitive_only": True})
        assert r_post_sens.status_code == 200
        assert r_post_sens.json()["selected_count"] == 3

        # 6. Granular dict toggle via POST
        r_post_dict = client.post(f"/api/targets/{target_id}/endpoints/select", json={
            "endpoint_ids": [{"endpoint_id": first_id, "is_selected": True}]
        })
        assert r_post_dict.status_code == 200
    finally:
        client.delete(f"/api/targets/{target_id}")


def test_auth_profile_encryption_and_masking(client):
    """Verify configuring User A and User B profiles and strictly masking secrets."""
    t_res = client.post("/api/targets", json={"name": "Auth API", "base_url": "http://127.0.0.1:8001"})
    target_id = t_res.json()["id"]

    try:
        # Create User A profile
        res_a = client.post(f"/api/targets/{target_id}/auth-profiles", json={
            "account_label": "User A",
            "authentication_type": "bearer",
            "credential_value": "Bearer secret_jwt_token_for_user_a",
            "username": "alice",
            "owned_resource_id": "101"
        })
        assert res_a.status_code == 200
        p_a = res_a.json()
        assert p_a["account_label"] == "User A"
        # Verify raw credential is masked
        assert "secret_jwt" not in p_a["masked_credential"]
        assert "Bearer se...er_a" in p_a["masked_credential"] or "..." in p_a["masked_credential"]

        # Create User B profile
        res_b = client.post(f"/api/targets/{target_id}/auth-profiles", json={
            "account_label": "User B",
            "authentication_type": "bearer",
            "credential_value": "Bearer foreign_token_for_user_b",
            "username": "bob",
            "owned_resource_id": "102"
        })
        assert res_b.status_code == 200
        assert "foreign_token" not in res_b.json()["masked_credential"]

        # Query profiles list
        list_auth = client.get(f"/api/targets/{target_id}/auth-profiles")
        assert list_auth.status_code == 200
        profiles = list_auth.json()
        assert len(profiles) == 2
        for p in profiles:
            assert "..." in p["masked_credential"]
    finally:
        client.delete(f"/api/targets/{target_id}")


def test_target_validation_endpoint(client):
    """Verify safe non-destructive target validation check."""
    # 1. Valid local target (allowed in lab mode)
    t_res = client.post("/api/targets", json={"name": "Lab Target", "base_url": "http://127.0.0.1:8001"})
    target_id = t_res.json()["id"]

    try:
        v_res = client.post(f"/api/targets/{target_id}/validate")
        assert v_res.status_code == 200
        data = v_res.json()
        assert data["safety_status"] == "safe"
        assert data["is_valid"] is True
        assert data["status_code"] in (200, 404, 401, 405)
    finally:
        client.delete(f"/api/targets/{target_id}")


def test_scan_bridge_execution_and_historical_preservation(client):
    """Verify launching a targeted scan executes Member 1's engine and preserves historical scans."""
    settings.ALLOW_LOCAL_LAB_SCANNING = True
    set_security_engine_override(MockSecurityEngineAdapter())
    try:
        t_res = client.post("/api/targets", json={"name": "Scan Demo Target", "base_url": "http://127.0.0.1:8001"})
        target_id = t_res.json()["id"]

        # Import spec
        client.post(f"/api/targets/{target_id}/import-spec", json={"spec_content": SAMPLE_OPENAPI_SPEC})

        # Launch targeted scan
        scan_res = client.post(f"/api/targets/{target_id}/scan", json={
            "user_authorized": True,
            "categories": ["HEADERS", "CONFIG"],
            "scan_profile": "Targeted Audit Test"
        })
        assert scan_res.status_code == 201
        scan_data = scan_res.json()
        assert "id" in scan_data
        scan_id = scan_data["id"]
        assert scan_data["status"] == "Completed"

        # Verify target's last_scan_at was updated
        target_info = client.get(f"/api/targets/{target_id}").json()
        assert target_info["last_scan_at"] is not None

        # Delete target
        del_res = client.delete(f"/api/targets/{target_id}")
        assert del_res.status_code == 200

        # Verify scan still exists in historical scans!
        s_check = client.get(f"/api/scans/{scan_id}")
        assert s_check.status_code == 200
        assert s_check.json()["id"] == scan_id
    finally:
        reset_security_engine()
