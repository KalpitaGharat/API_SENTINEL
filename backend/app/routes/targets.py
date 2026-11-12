"""Target Management & OpenAPI Discovery API Router for API Sentinel.

Provides REST endpoints for:
- API target registration, retrieval, listing, update, and deletion.
- OpenAPI specification import and live preview (JSON, YAML, remote URL).
- Discovered endpoint exploration, filtering, search, and selection toggles.
- Two-principal authentication profile management with Fernet encryption and masking.
- Non-destructive target connectivity validation with SSRF protection.
- Scan execution bridge integrating onboarding data with Member 1's detection engine.
"""

import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiTarget, DiscoveredEndpoint, TargetAuthProfile, utc_now
from app.schemas import (
    ApiTargetCreate,
    ApiTargetUpdate,
    ApiTargetResponse,
    ApiTargetDetail,
    ApiTargetListResponse,
    DiscoveredEndpointItem,
    DiscoveredEndpointsListResponse,
    OpenAPIImportRequest,
    OpenAPIImportPreview,
    EndpointSelectionRequest,
    EndpointSelectionResponse,
    AuthProfileCreate,
    AuthProfileResponse,
    TargetValidateResponse,
    TargetScanRequest,
    ScanResponse,
    ScanCreateRequest,
)
from app.services.target_service import TargetService, TargetServiceError
from app.services.openapi_parser import OpenApiParser, OpenApiParserError
from app.services.scan_service import ScanService
from app.security_engine.integration import (
    validate_target_safety,
    create_safe_http_client,
    execute_safe_request,
    TargetSafetyError,
)
from app.config import settings

logger = logging.getLogger("api_sentinel.routes.targets")

router = APIRouter(prefix="/api/targets", tags=["API Onboarding & Targets"])


# =============================================================================
# 1. Target Management Endpoints
# =============================================================================

@router.post(
    "",
    response_model=ApiTargetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new API target",
    description="Registers an API boundary, performs pre-flight SSRF safety check on base URL, and initializes catalog record."
)
def register_target(payload: ApiTargetCreate, db: Session = Depends(get_db)):
    """Register a new API target."""
    try:
        target = TargetService.create_target(db=db, data=payload)
        return ApiTargetResponse.model_validate(target)
    except TargetServiceError as tse:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(tse))
    except Exception as err:
        logger.error("Failed to register target: %s", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Target creation failed: {str(err)}")


@router.get(
    "",
    response_model=ApiTargetListResponse,
    summary="List registered API targets",
    description="Returns paginated targets enriched with endpoint counts, sensitive candidate counts, and auth profile status."
)
def list_targets(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    environment: Optional[str] = Query(None, description="Filter by environment (development, staging, production)"),
    db: Session = Depends(get_db),
):
    """Retrieve list of registered API targets."""
    items, total = TargetService.list_targets(db=db, skip=skip, limit=limit, environment=environment)
    return ApiTargetListResponse(
        total=total,
        items=[ApiTargetResponse(**it) for it in items]
    )


@router.get(
    "/{target_id}",
    response_model=ApiTargetDetail,
    summary="Get target details",
    description="Returns target metadata, all discovered endpoints, and masked authentication profiles."
)
def get_target(target_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed target record."""
    target = TargetService.get_target_by_id(db=db, target_id=target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")

    endpoints, _ = TargetService.get_target_endpoints(db=db, target_id=target_id, limit=500)
    auth_profiles = TargetService.get_auth_profiles(db=db, target_id=target_id)

    # Calculate counts
    total_ep = len(endpoints)
    sel_ep = sum(1 for e in endpoints if e.is_selected)
    sens_ep = sum(1 for e in endpoints if e.is_sensitive_candidate)

    return ApiTargetDetail(
        id=target.id,
        name=target.name,
        description=target.description,
        base_url=target.base_url,
        environment=target.environment,
        api_type=target.api_type,
        api_version=target.api_version,
        specification_version=target.specification_version,
        total_endpoints=total_ep,
        selected_endpoints=sel_ep,
        sensitive_endpoints=sens_ep,
        auth_profiles_count=len(auth_profiles),
        created_at=target.created_at,
        updated_at=target.updated_at,
        last_scan_at=target.last_scan_at,
        endpoints=[DiscoveredEndpointItem.model_validate(e) for e in endpoints],
        auth_profiles=[AuthProfileResponse(**p) for p in auth_profiles],
    )


@router.put(
    "/{target_id}",
    response_model=ApiTargetResponse,
    summary="Update target metadata",
    description="Updates name, description, environment, version, or base URL (with SSRF re-validation)."
)
def update_target(target_id: str, payload: ApiTargetUpdate, db: Session = Depends(get_db)):
    """Update target configuration."""
    try:
        updated = TargetService.update_target(db=db, target_id=target_id, data=payload)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")
        return ApiTargetResponse.model_validate(updated)
    except TargetServiceError as tse:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(tse))


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete API target",
    description="Deletes target, its discovered endpoints, and auth profiles. Preserves historical scans, findings, and reports."
)
def delete_target(target_id: str, db: Session = Depends(get_db)):
    """Delete an API target."""
    deleted = TargetService.delete_target(db=db, target_id=target_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")
    return {"deleted": True, "target_id": target_id}


# =============================================================================
# 2. OpenAPI Specification Import & Preview Endpoints
# =============================================================================

@router.post(
    "/import-spec",
    response_model=OpenAPIImportPreview,
    summary="Preview parsed OpenAPI specification",
    description="Parses an uploaded JSON or YAML specification without saving or registering a target."
)
@router.post(
    "/preview-spec",
    response_model=OpenAPIImportPreview,
    summary="Preview parsed OpenAPI specification (alias)",
    description="Parses an uploaded JSON or YAML specification without saving or registering a target."
)
@router.post(
    "/preview",
    response_model=OpenAPIImportPreview,
    summary="Preview parsed OpenAPI specification (alias)",
    description="Parses an uploaded JSON or YAML specification without saving or registering a target."
)
def preview_spec(payload: OpenAPIImportRequest):
    """Parse and preview an OpenAPI/Swagger specification in-memory."""
    try:
        if payload.spec_url:
            parsed = OpenApiParser.parse_from_url(
                payload.spec_url,
                allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING
            )
        elif payload.spec_content:
            parsed = OpenApiParser.parse_from_content(
                payload.spec_content,
                file_type=payload.file_type
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide either spec_content or spec_url.")

        endpoints_preview = []
        for ep in parsed.get("endpoints", [])[:30]:  # First 30 for preview
            endpoints_preview.append({
                "path": ep["path"],
                "method": ep["method"],
                "operation_id": ep.get("operation_id"),
                "summary": ep.get("summary"),
                "is_sensitive_candidate": ep.get("is_sensitive_candidate", False),
                "is_state_changing": ep.get("is_state_changing", False),
            })

        return OpenAPIImportPreview(
            title=parsed.get("title", "Untitled API"),
            description=parsed.get("description", ""),
            version=parsed.get("version", "1.0.0"),
            spec_version=parsed.get("spec_version", "Unknown"),
            base_url=parsed.get("base_url", ""),
            total_endpoints=parsed.get("total_endpoints", 0),
            sensitive_endpoints_count=parsed.get("sensitive_endpoints_count", 0),
            state_changing_count=parsed.get("state_changing_count", 0),
            security_schemes=parsed.get("security_schemes", []),
            endpoints_preview=endpoints_preview,
            warnings=parsed.get("warnings", []),
        )
    except OpenApiParserError as ope:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ope))
    except Exception as err:
        logger.error("Failed to parse OpenAPI preview: %s", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to preview specification: {str(err)}")


@router.post(
    "/{target_id}/import-spec",
    summary="Import specification into target",
    description="Parses specification content (JSON/YAML) and saves discovered endpoints to target."
)
def import_spec_into_target(
    target_id: str,
    payload: OpenAPIImportRequest,
    update_base_url: bool = Query(False, description="Whether to update target's base URL with server URL extracted from spec"),
    db: Session = Depends(get_db)
):
    """Import an OpenAPI/Swagger specification into an existing target."""
    if not payload.spec_content and not payload.spec_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide either spec_content or spec_url.")

    try:
        if payload.spec_url:
            summary = TargetService.import_openapi_from_url(
                db=db,
                target_id=target_id,
                spec_url=payload.spec_url,
                allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING,
                update_base_url=update_base_url
            )
        else:
            summary = TargetService.import_openapi_spec(
                db=db,
                target_id=target_id,
                spec_content=payload.spec_content,
                file_type=payload.file_type,
                update_base_url=update_base_url
            )
        return summary
    except (OpenApiParserError, TargetServiceError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post(
    "/{target_id}/import-spec-url",
    summary="Fetch and import remote specification URL",
    description="Safely downloads remote specification via hardened HTTP transport and persists discovered endpoints."
)
def import_spec_url(
    target_id: str,
    spec_url: str = Body(..., embed=True, description="Remote URL to OpenAPI/Swagger specification"),
    update_base_url: bool = Query(False, description="Whether to update target's base URL"),
    db: Session = Depends(get_db)
):
    """Download remote specification and import endpoints into target."""
    try:
        summary = TargetService.import_openapi_from_url(
            db=db,
            target_id=target_id,
            spec_url=spec_url,
            allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING,
            update_base_url=update_base_url
        )
        return summary
    except (OpenApiParserError, TargetServiceError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# =============================================================================
# 3. Discovered Endpoints & Selection Endpoints
# =============================================================================

@router.get(
    "/{target_id}/endpoints",
    response_model=DiscoveredEndpointsListResponse,
    summary="List discovered endpoints for a target",
    description="Filter endpoints by HTTP method, sensitivity candidate status, selection state, or path text search."
)
def list_endpoints(
    target_id: str,
    method: Optional[str] = Query(None, description="Filter by method (GET, POST, etc.)"),
    is_sensitive: Optional[bool] = Query(None, description="Filter by sensitivity candidate status"),
    is_selected: Optional[bool] = Query(None, description="Filter by selection state"),
    search: Optional[str] = Query(None, description="Search path or summary text"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Query discovered endpoints for an API target."""
    target = TargetService.get_target_by_id(db=db, target_id=target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")

    endpoints, total = TargetService.get_target_endpoints(
        db=db,
        target_id=target_id,
        method=method,
        is_sensitive=is_sensitive,
        search=search,
        is_selected=is_selected,
        skip=skip,
        limit=limit,
    )
    return DiscoveredEndpointsListResponse(
        target_id=target_id,
        total=total,
        items=[DiscoveredEndpointItem.model_validate(e) for e in endpoints]
    )


@router.get(
    "/{target_id}/endpoints/{endpoint_id}",
    response_model=DiscoveredEndpointItem,
    summary="Get details of a discovered endpoint",
    description="Returns parameter schemas, request body schema, and security requirements."
)
def get_endpoint_detail(target_id: str, endpoint_id: str, db: Session = Depends(get_db)):
    """Retrieve full details of an individual discovered endpoint."""
    endpoint = db.query(DiscoveredEndpoint).filter(
        DiscoveredEndpoint.id == endpoint_id,
        DiscoveredEndpoint.target_id == target_id
    ).first()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint '{endpoint_id}' not found under target '{target_id}'."
        )
    return DiscoveredEndpointItem.model_validate(endpoint)


@router.put(
    "/{target_id}/endpoints/selection",
    response_model=EndpointSelectionResponse,
    summary="Update endpoint selection for testing",
    description="Toggle individual endpoints or bulk select/deselect all endpoints for a target."
)
@router.post(
    "/{target_id}/endpoints/selection",
    response_model=EndpointSelectionResponse,
    include_in_schema=False
)
@router.post(
    "/{target_id}/endpoints/select",
    response_model=EndpointSelectionResponse,
    summary="Update endpoint selection (POST alias)"
)
def update_endpoint_selection(
    target_id: str,
    payload: EndpointSelectionRequest,
    db: Session = Depends(get_db)
):
    """Update which endpoints are selected for active scanning."""
    try:
        selected_count, total_count = TargetService.update_endpoint_selection(
            db=db,
            target_id=target_id,
            endpoint_ids=payload.endpoint_ids,
            select_all=payload.select_all,
            deselect_all=payload.deselect_all,
            sensitive_only=payload.sensitive_only,
        )
        return EndpointSelectionResponse(
            target_id=target_id,
            selected_count=selected_count,
            total_count=total_count
        )
    except TargetServiceError as tse:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(tse))


# =============================================================================
# 4. Authentication Profiles Endpoints
# =============================================================================

@router.post(
    "/{target_id}/auth-profiles",
    response_model=AuthProfileResponse,
    summary="Configure authentication profile (User A or User B)",
    description="Saves User A or User B credentials with Fernet encryption. Returns masked summary only."
)
def save_auth_profile(
    target_id: str,
    payload: AuthProfileCreate,
    db: Session = Depends(get_db)
):
    """Configure or update authentication credentials for User A or User B."""
    try:
        profile = TargetService.save_auth_profile(db=db, target_id=target_id, profile_data=payload)
        meta = profile.credential_metadata or {}
        return AuthProfileResponse(
            id=profile.id,
            target_id=profile.target_id,
            account_label=profile.account_label,
            authentication_type=profile.authentication_type,
            header_name=meta.get("header_name", "Authorization"),
            header_prefix=meta.get("header_prefix", "Bearer"),
            masked_credential=meta.get("masked_credential", "Not configured"),
            username=meta.get("username"),
            owned_resource_id=meta.get("owned_resource_id"),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except TargetServiceError as tse:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(tse))


@router.get(
    "/{target_id}/auth-profiles",
    response_model=List[AuthProfileResponse],
    summary="Get authentication profiles for target",
    description="Returns masked summaries for configured profiles. Plaintext credentials are never returned."
)
def get_auth_profiles(target_id: str, db: Session = Depends(get_db)):
    """Retrieve masked authentication profiles for a target."""
    target = TargetService.get_target_by_id(db=db, target_id=target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")

    profiles = TargetService.get_auth_profiles(db=db, target_id=target_id)
    return [AuthProfileResponse(**p) for p in profiles]


# =============================================================================
# 5. Target Validation Endpoint
# =============================================================================

@router.post(
    "/{target_id}/validate",
    response_model=TargetValidateResponse,
    summary="Safe non-destructive target connectivity check",
    description="Validates target URL safety boundaries (SSRF) and performs non-destructive connectivity probe."
)
def validate_target_connectivity(target_id: str, db: Session = Depends(get_db)):
    """Perform non-destructive pre-flight connectivity probe using hardened transport."""
    target = TargetService.get_target_by_id(db=db, target_id=target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")

    # 1. SSRF Safety Policy Check
    try:
        validate_target_safety(target.base_url, allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING)
    except TargetSafetyError as tse:
        return TargetValidateResponse(
            target_id=target.id,
            base_url=target.base_url,
            is_valid=False,
            status_code=None,
            latency_ms=None,
            server_header=None,
            safety_status="unsafe",
            message=f"SSRF Security Violation: {str(tse)}"
        )

    # 2. Non-destructive HTTP Probe
    t0 = time.time()
    try:
        with create_safe_http_client(allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING, timeout=6.0, target_url=target.base_url) as client:
            resp = execute_safe_request(
                client,
                method="GET",
                url=target.base_url,
                allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING,
                max_redirects=2
            )
            elapsed = round((time.time() - t0) * 1000, 2)
            server_hdr = resp.headers.get("Server") or resp.headers.get("server")

            return TargetValidateResponse(
                target_id=target.id,
                base_url=target.base_url,
                is_valid=True,
                status_code=resp.status_code,
                latency_ms=elapsed,
                server_header=server_hdr,
                safety_status="safe",
                message=f"Target responded with HTTP {resp.status_code} in {elapsed} ms"
            )
    except TargetSafetyError as tse:
        return TargetValidateResponse(
            target_id=target.id,
            base_url=target.base_url,
            is_valid=False,
            status_code=None,
            latency_ms=None,
            server_header=None,
            safety_status="unsafe",
            message=f"SSRF Redirect Violation: {str(tse)}"
        )
    except Exception as ex:
        elapsed = round((time.time() - t0) * 1000, 2)
        return TargetValidateResponse(
            target_id=target.id,
            base_url=target.base_url,
            is_valid=False,
            status_code=None,
            latency_ms=elapsed,
            server_header=None,
            safety_status="safe",  # Safe destination, but network connection failed
            message=f"Connection failed: {str(ex)}"
        )


# =============================================================================
# 6. Scan Execution Bridge Endpoint
# =============================================================================

@router.post(
    "/{target_id}/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Launch security scan for target",
    description="Bridges onboarded target, selected endpoints, and decrypted test accounts to existing Member 1 scanning engine."
)
def launch_target_scan(
    target_id: str,
    payload: TargetScanRequest,
    db: Session = Depends(get_db)
):
    """Launch scan using configured target metadata, selected endpoints, and auth profiles."""
    target = TargetService.get_target_by_id(db=db, target_id=target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{target_id}' not found.")

    if not payload.user_authorized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Safety safeguard: You must explicitly confirm authorization before initiating an active security scan."
        )

    # 1. Resolve selected endpoints
    query = db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.target_id == target_id)
    if payload.selected_endpoint_ids is not None:
        # Validate that all requested IDs belong to this target
        query = query.filter(DiscoveredEndpoint.id.in_(payload.selected_endpoint_ids))
    else:
        # Default to all currently selected endpoints
        query = query.filter(DiscoveredEndpoint.is_selected == True)

    selected_endpoints = query.all()
    if not selected_endpoints:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No endpoints selected for scanning. Please select at least one endpoint in target onboarding."
        )

    # 2. Filter out state-changing methods unless explicitly authorized
    executable_endpoints = []
    for ep in selected_endpoints:
        if ep.is_state_changing and not payload.allow_state_changing:
            logger.info("Excluding state-changing endpoint '%s %s' (allow_state_changing=False)", ep.method, ep.path)
            continue
        executable_endpoints.append(ep)

    if not executable_endpoints:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All selected endpoints were state-changing operations (POST/PUT/DELETE). Enable 'allow_state_changing' to test them."
        )

    # 3. Handle Authentication Profiles & Two-Principal BOLA Setup
    categories = [c.upper() for c in payload.categories]
    test_accounts = {}
    primary_token = None
    custom_headers = {}

    auth_a = TargetService.get_decrypted_auth_profile(db=db, target_id=target_id, account_label="User A")
    auth_b = TargetService.get_decrypted_auth_profile(db=db, target_id=target_id, account_label="User B")

    if "BOLA" in categories:
        # BOLA strictly requires User A (owner) and User B (cross-user probe)
        has_cred_a = auth_a and (auth_a.get("credential_value") or auth_a.get("username"))
        has_cred_b = auth_b and (auth_b.get("credential_value") or auth_b.get("username"))

        # In local lab demo, fallback to synthetic demo accounts is permitted by Member 1's engine
        is_demo_target = target.base_url.rstrip("/") in ("http://127.0.0.1:8001", "http://localhost:8001")
        if not (has_cred_a and has_cred_b) and not is_demo_target:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BOLA / IDOR testing requires two configured test identities (User A and User B). Please configure authentication profiles for both users."
            )

    if auth_a:
        cred_val_a = auth_a.get("credential_value") or ""
        token_a = cred_val_a[7:] if cred_val_a.lower().startswith("bearer ") else cred_val_a
        owned_id_a = auth_a.get("owned_resource_id") or 101

        # Map to both patient_a and user_a for full engine compatibility
        user_a_dict = {
            "username": auth_a.get("username") or "user_a",
            "token": token_a or None,
            "auth_token": token_a or None,
            "owned_id": owned_id_a,
            "id": owned_id_a,
        }
        test_accounts["patient_a"] = user_a_dict
        test_accounts["user_a"] = user_a_dict

        if token_a:
            primary_token = token_a

    if auth_b:
        cred_val_b = auth_b.get("credential_value") or ""
        token_b = cred_val_b[7:] if cred_val_b.lower().startswith("bearer ") else cred_val_b
        owned_id_b = auth_b.get("owned_resource_id") or 102

        user_b_dict = {
            "username": auth_b.get("username") or "user_b",
            "token": token_b or None,
            "auth_token": token_b or None,
            "owned_id": owned_id_b,
            "id": owned_id_b,
        }
        test_accounts["patient_b"] = user_b_dict
        test_accounts["user_b"] = user_b_dict

    # 4. Resolve Candidate BOLA Endpoint
    sensitive_candidates = [e.path for e in executable_endpoints if e.is_sensitive_candidate and e.method == "GET"]
    bola_path = sensitive_candidates[0] if sensitive_candidates else None

    # 5. Construct existing ScanCreateRequest
    try:
        scan_req = ScanCreateRequest(
            target_url=target.base_url,
            user_authorized=True,
            categories=categories,
            custom_headers=custom_headers or None,
            auth_token=primary_token,
            test_accounts=test_accounts or None,
        )
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid scan configuration: {str(err)}")

    # 6. Execute scan through existing ScanService
    try:
        scan_record = ScanService.create_and_run_scan(db=db, request=scan_req)

        # Update target's last_scan_at timestamp
        target.last_scan_at = utc_now()
        db.commit()

        return ScanResponse.model_validate(scan_record)
    except HTTPException:
        raise
    except Exception as err:
        logger.error("Scan execution failed: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan execution failed: {str(err)}"
        )
