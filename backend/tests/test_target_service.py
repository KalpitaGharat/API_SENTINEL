"""Automated Test Suite for API Target Management Service.

Tests target registration, retrieval, listing, deletion, OpenAPI spec import,
endpoint selection, authenticated Fernet credential encryption, credential masking,
and historical scan preservation using an isolated in-memory SQLite database.
"""

import json
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import ApiTarget, DiscoveredEndpoint, TargetAuthProfile, Scan, Finding
from app.schemas import ApiTargetCreate, ApiTargetUpdate, AuthProfileCreate
from app.services.target_service import TargetService, TargetServiceError
from app.services.credential_vault import encrypt_credential, decrypt_credential, CredentialVaultError


# Create isolated in-memory test database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Create fresh database tables for each test and tear down cleanly."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


SAMPLE_OPENAPI = json.dumps({
    "openapi": "3.0.0",
    "info": {
        "title": "Hospital Management Service",
        "description": "Electronic Health Record API",
        "version": "1.4.0"
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
                "summary": "Get individual patient record",
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
})


def test_target_registration_and_retrieval(db):
    """Verify registering a valid target and retrieving it by ID."""
    req = ApiTargetCreate(
        name="Demo Healthcare Portal",
        base_url="http://127.0.0.1:8001",
        environment="development",
        description="Local demonstration API",
        api_type="REST",
        api_version="1.0.0"
    )
    target = TargetService.create_target(db, req)
    assert target.id is not None
    assert target.name == "Demo Healthcare Portal"
    assert target.base_url == "http://127.0.0.1:8001"

    # Fetch by ID
    fetched = TargetService.get_target_by_id(db, target.id)
    assert fetched is not None
    assert fetched.id == target.id
    assert fetched.name == target.name


def test_target_registration_invalid_url(db):
    """Verify target registration rejects malformed URLs."""
    req = ApiTargetCreate(
        name="Bad URL Target",
        base_url="ftp://invalid-scheme.local",
    )
    with pytest.raises(TargetServiceError, match="must begin with http:// or https://"):
        TargetService.create_target(db, req)


def test_target_listing_and_filtering(db):
    """Verify target listing returns paginated results with endpoint count aggregates."""
    t1 = TargetService.create_target(db, ApiTargetCreate(
        name="Target Dev",
        base_url="http://127.0.0.1:8001",
        environment="development"
    ))
    t2 = TargetService.create_target(db, ApiTargetCreate(
        name="Target Staging",
        base_url="http://127.0.0.1:8001",
        environment="staging"
    ))

    targets, total = TargetService.list_targets(db)
    assert total == 2
    assert len(targets) == 2

    dev_targets, dev_total = TargetService.list_targets(db, environment="development")
    assert dev_total == 1
    assert dev_targets[0]["name"] == "Target Dev"


def test_target_metadata_update(db):
    """Verify updating target name, description, and base URL."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Original Name",
        base_url="http://127.0.0.1:8001"
    ))
    updated = TargetService.update_target(db, target.id, ApiTargetUpdate(
        name="Updated Name",
        description="New description"
    ))
    assert updated.name == "Updated Name"
    assert updated.description == "New description"


def test_openapi_spec_import_persistence(db):
    """Verify importing OpenAPI spec creates DiscoveredEndpoint records transactionally."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Hospital API",
        base_url="http://127.0.0.1:8001"
    ))

    summary = TargetService.import_openapi_spec(db, target.id, SAMPLE_OPENAPI, file_type="json")
    assert summary["total_discovered"] == 3  # GET /patients, POST /patients, GET /patients/{id}
    assert summary["sensitive_candidates"] >= 1  # /api/patients/{patient_id}

    # Verify target metadata updated
    refreshed_target = TargetService.get_target_by_id(db, target.id)
    assert "OpenAPI 3.0" in refreshed_target.specification_version

    # Query endpoints
    endpoints, total = TargetService.get_target_endpoints(db, target.id)
    assert total == 3
    paths = [e.path for e in endpoints]
    assert "/api/patients" in paths
    assert "/api/patients/{patient_id}" in paths


def test_endpoint_filtering_and_search(db):
    """Verify filtering endpoints by method, sensitivity, and text search."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Filter Test API",
        base_url="http://127.0.0.1:8001"
    ))
    TargetService.import_openapi_spec(db, target.id, SAMPLE_OPENAPI)

    # Filter by method
    get_eps, get_tot = TargetService.get_target_endpoints(db, target.id, method="GET")
    assert get_tot == 2

    post_eps, post_tot = TargetService.get_target_endpoints(db, target.id, method="POST")
    assert post_tot == 1

    # Filter by sensitivity candidate
    sens_eps, sens_tot = TargetService.get_target_endpoints(db, target.id, is_sensitive=True)
    assert sens_tot >= 1
    assert any("{patient_id}" in e.path for e in sens_eps)

    # Search by path
    search_eps, search_tot = TargetService.get_target_endpoints(db, target.id, search="patient_id")
    assert search_tot == 1


def test_endpoint_selection_toggle(db):
    """Verify toggling individual endpoints and select-all/deselect-all."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Selection Test API",
        base_url="http://127.0.0.1:8001"
    ))
    TargetService.import_openapi_spec(db, target.id, SAMPLE_OPENAPI)

    endpoints, _ = TargetService.get_target_endpoints(db, target.id)
    first_id = endpoints[0].id

    # Select only first endpoint
    sel_count, total = TargetService.update_endpoint_selection(db, target.id, endpoint_ids=[first_id])
    assert sel_count == 1
    assert total == 3

    # Select all
    sel_all, _ = TargetService.update_endpoint_selection(db, target.id, select_all=True)
    assert sel_all == 3

    # Deselect all
    desel_all, _ = TargetService.update_endpoint_selection(db, target.id, select_all=False)
    assert desel_all == 0


def test_auth_profile_encryption_and_masking(db):
    """Verify target authentication profiles are encrypted at rest and returned masked."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Auth Test API",
        base_url="http://127.0.0.1:8001"
    ))

    # User A Profile
    p_a = TargetService.save_auth_profile(db, target.id, AuthProfileCreate(
        account_label="User A",
        authentication_type="bearer",
        credential_value="Bearer super_secret_jwt_token_1234567890",
        username="alice",
        owned_resource_id="101"
    ))
    assert p_a.id is not None
    # Raw value must NOT be in DB plaintext
    assert "super_secret_jwt_token" not in (p_a.credential_ciphertext or "")
    # Masked credential in metadata
    assert "Bearer supe...7890" in p_a.credential_metadata["masked_credential"]

    # User B Profile (Two-Principal Separation)
    p_b = TargetService.save_auth_profile(db, target.id, AuthProfileCreate(
        account_label="User B",
        authentication_type="bearer",
        credential_value="Bearer foreign_user_token_abcdef123456",
        username="bob",
        owned_resource_id="102"
    ))
    assert p_b.id is not None

    # Retrieve masked profiles via public method
    profiles = TargetService.get_auth_profiles(db, target.id)
    assert len(profiles) == 2
    for p in profiles:
        # Verify plaintext token is NEVER returned
        assert "super_secret" not in p["masked_credential"]
        assert "foreign_user" not in p["masked_credential"]
        assert "..." in p["masked_credential"]

    # Verify internal decryptor works for engine
    dec_a = TargetService.get_decrypted_auth_profile(db, target.id, "User A")
    assert dec_a is not None
    assert dec_a["credential_value"] == "Bearer super_secret_jwt_token_1234567890"
    assert dec_a["username"] == "alice"


def test_target_cascade_deletion(db):
    """Verify target deletion deletes discovered endpoints and auth profiles."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Delete Cascade Target",
        base_url="http://127.0.0.1:8001"
    ))
    TargetService.import_openapi_spec(db, target.id, SAMPLE_OPENAPI)
    TargetService.save_auth_profile(db, target.id, AuthProfileCreate(
        account_label="User A",
        authentication_type="bearer",
        credential_value="test_token_123"
    ))

    # Delete target
    deleted = TargetService.delete_target(db, target.id)
    assert deleted is True

    # Verify target gone
    assert TargetService.get_target_by_id(db, target.id) is None
    # Verify endpoints cleaned up
    remaining_eps = db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.target_id == target.id).count()
    assert remaining_eps == 0
    # Verify auth profiles cleaned up
    remaining_auth = db.query(TargetAuthProfile).filter(TargetAuthProfile.target_id == target.id).count()
    assert remaining_auth == 0


def test_historical_scans_preserved_on_target_deletion(db):
    """Verify historical scans are NOT deleted when an API target is removed."""
    target = TargetService.create_target(db, ApiTargetCreate(
        name="Scan Preservation Target",
        base_url="http://127.0.0.1:8001"
    ))

    # Create a historical scan record
    scan = Scan(
        target_url=target.base_url,
        status="Completed",
        total_findings=1,
        scan_configuration={"target_name": target.name}
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    scan_id = scan.id

    # Now delete target
    TargetService.delete_target(db, target.id)

    # Verify scan record still exists intact in scans table
    persisted_scan = db.query(Scan).filter(Scan.id == scan_id).first()
    assert persisted_scan is not None
    assert persisted_scan.id == scan_id
    assert persisted_scan.status == "Completed"


def test_endpoint_selection_granular_dict_toggle_and_bulk_filters(db):
    """Verify granular dict-based toggle, deselect_all, and sensitive_only filters."""
    target = TargetService.create_target(db, ApiTargetCreate(name="Bulk Target", base_url="http://127.0.0.1:8001"))
    TargetService.import_openapi_spec(db, target.id, SAMPLE_OPENAPI)

    # 1. deselect_all
    sel, tot = TargetService.update_endpoint_selection(db, target.id, deselect_all=True)
    assert sel == 0
    assert tot == 3

    # 2. sensitive_only
    sel_sens, _ = TargetService.update_endpoint_selection(db, target.id, sensitive_only=True)
    assert sel_sens == 3  # All endpoints under /api/patients are flagged as sensitive IDOR candidates

    # 3. Granular dict toggle of a single endpoint without wiping others
    endpoints, _ = TargetService.get_target_endpoints(db, target.id)
    first_ep = endpoints[0]
    initial_sel = first_ep.is_selected

    sel_dict, _ = TargetService.update_endpoint_selection(
        db, target.id,
        endpoint_ids=[{"endpoint_id": first_ep.id, "is_selected": not initial_sel}]
    )
    # Check that first endpoint toggled
    refreshed_first = db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.id == first_ep.id).first()
    assert refreshed_first.is_selected == (not initial_sel)


def test_auth_profile_alias_normalization_and_encryption(db):
    """Verify auth_type and token_or_secret aliases normalize and encrypt properly."""
    target = TargetService.create_target(db, ApiTargetCreate(name="Alias Target", base_url="http://127.0.0.1:8001"))
    
    profile_data = AuthProfileCreate(
        account_label="User A",
        auth_type="bearer",
        token_or_secret="super_secret_alias_token_xyz",
        username="alice_test",
        role="owner"
    )
    assert profile_data.authentication_type == "bearer"
    assert profile_data.credential_value == "super_secret_alias_token_xyz"

    profile = TargetService.save_auth_profile(db, target.id, profile_data)
    assert profile.credential_ciphertext is not None
    assert "super_secret_alias_token_xyz" not in profile.credential_ciphertext

    # Decrypt and verify
    decrypted = TargetService.get_decrypted_auth_profile(db, target.id, "User A")
    assert decrypted["credential_value"] == "super_secret_alias_token_xyz"
    assert decrypted["username"] == "alice_test"
