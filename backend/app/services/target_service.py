"""Target Management Service for API Sentinel.

Orchestrates API target onboarding, OpenAPI specification import, endpoint discovery,
selection management, and authenticated encryption for test account profiles.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import ApiTarget, DiscoveredEndpoint, TargetAuthProfile, utc_now
from app.schemas import (
    ApiTargetCreate,
    ApiTargetUpdate,
    AuthProfileCreate,
)
from app.services.openapi_parser import OpenApiParser, OpenApiParserError
from app.services.credential_vault import (
    encrypt_credential,
    decrypt_credential,
    mask_credential,
    CredentialVaultError,
)
from app.security_engine.integration import (
    validate_target_safety,
    TargetSafetyError,
)
from app.config import settings

logger = logging.getLogger("api_sentinel.target_service")


class TargetServiceError(ValueError):
    """Raised when target registration, spec import, or profile configuration fails."""
    pass


class TargetService:
    """Core service for managing API targets, discovered endpoints, and authentication."""

    @staticmethod
    def create_target(db: Session, data: ApiTargetCreate) -> ApiTarget:
        """Register a new API target with URL safety verification."""
        clean_url = data.base_url.strip().rstrip("/")
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            raise TargetServiceError("Base URL must begin with http:// or https://")

        # Validate URL safety (SSRF guard)
        try:
            validate_target_safety(clean_url, allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING)
        except TargetSafetyError as tse:
            raise TargetServiceError(f"Target URL security policy violation: {str(tse)}")

        target = ApiTarget(
            name=data.name.strip(),
            base_url=clean_url,
            environment=data.environment.lower().strip(),
            description=data.description.strip() if data.description else None,
            api_type=data.api_type.strip(),
            api_version=data.api_version.strip() if data.api_version else "1.0.0",
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def get_target_by_id(db: Session, target_id: str) -> Optional[ApiTarget]:
        """Fetch target by UUID."""
        return db.query(ApiTarget).filter(ApiTarget.id == target_id).first()

    @staticmethod
    def list_targets(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        environment: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve paginated targets enriched with endpoint counts and auth status."""
        query = db.query(ApiTarget)
        if environment:
            query = query.filter(ApiTarget.environment == environment.lower().strip())

        total = query.count()
        targets = query.order_by(ApiTarget.created_at.desc()).offset(skip).limit(limit).all()

        results = []
        for t in targets:
            # Aggregate counts for this target
            total_ep = db.query(func.count(DiscoveredEndpoint.id)).filter(DiscoveredEndpoint.target_id == t.id).scalar() or 0
            sel_ep = db.query(func.count(DiscoveredEndpoint.id)).filter(
                DiscoveredEndpoint.target_id == t.id,
                DiscoveredEndpoint.is_selected == True
            ).scalar() or 0
            sens_ep = db.query(func.count(DiscoveredEndpoint.id)).filter(
                DiscoveredEndpoint.target_id == t.id,
                DiscoveredEndpoint.is_sensitive_candidate == True
            ).scalar() or 0
            auth_count = db.query(func.count(TargetAuthProfile.id)).filter(TargetAuthProfile.target_id == t.id).scalar() or 0

            results.append({
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "base_url": t.base_url,
                "environment": t.environment,
                "api_type": t.api_type,
                "api_version": t.api_version,
                "specification_version": t.specification_version,
                "total_endpoints": total_ep,
                "selected_endpoints": sel_ep,
                "sensitive_endpoints": sens_ep,
                "auth_profiles_count": auth_count,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "last_scan_at": t.last_scan_at,
            })

        return results, total

    @staticmethod
    def update_target(db: Session, target_id: str, data: ApiTargetUpdate) -> Optional[ApiTarget]:
        """Update target metadata with URL safety re-validation if base_url changes."""
        target = db.query(ApiTarget).filter(ApiTarget.id == target_id).first()
        if not target:
            return None

        if data.name is not None and data.name.strip():
            target.name = data.name.strip()
        if data.description is not None:
            target.description = data.description.strip()
        if data.environment is not None and data.environment.strip():
            target.environment = data.environment.lower().strip()
        if data.api_version is not None and data.api_version.strip():
            target.api_version = data.api_version.strip()

        if data.base_url is not None and data.base_url.strip():
            new_url = data.base_url.strip().rstrip("/")
            if not new_url.startswith("http://") and not new_url.startswith("https://"):
                raise TargetServiceError("Base URL must begin with http:// or https://")
            try:
                validate_target_safety(new_url, allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING)
            except TargetSafetyError as tse:
                raise TargetServiceError(f"Target URL security policy violation: {str(tse)}")
            target.base_url = new_url

        target.updated_at = utc_now()
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def delete_target(db: Session, target_id: str) -> bool:
        """Delete target with cascade to discovered endpoints and auth profiles.

        Preserves historical scans, findings, and reports!
        """
        target = db.query(ApiTarget).filter(ApiTarget.id == target_id).first()
        if not target:
            return False

        # SQLite cascade handles endpoints and auth profiles via ondelete="CASCADE"
        db.delete(target)
        db.commit()
        return True

    # -------------------------------------------------------------------------
    # OpenAPI Specification Import & Endpoints Discovery
    # -------------------------------------------------------------------------

    @staticmethod
    def import_openapi_spec(
        db: Session,
        target_id: str,
        spec_content: str,
        file_type: str = "auto",
        update_base_url: bool = False
    ) -> Dict[str, Any]:
        """Parse specification and transactionally persist discovered endpoints into target."""
        target = db.query(ApiTarget).filter(ApiTarget.id == target_id).first()
        if not target:
            raise TargetServiceError(f"Target with ID '{target_id}' not found.")

        parsed_spec = OpenApiParser.parse_from_content(spec_content, file_type=file_type)
        return TargetService._persist_parsed_spec(db, target, parsed_spec, update_base_url=update_base_url)

    @staticmethod
    def import_openapi_from_url(
        db: Session,
        target_id: str,
        spec_url: str,
        allow_lab: bool = False,
        update_base_url: bool = False
    ) -> Dict[str, Any]:
        """Fetch remote specification using hardened transport and persist discovered endpoints."""
        target = db.query(ApiTarget).filter(ApiTarget.id == target_id).first()
        if not target:
            raise TargetServiceError(f"Target with ID '{target_id}' not found.")

        parsed_spec = OpenApiParser.parse_from_url(spec_url, allow_lab=allow_lab)
        return TargetService._persist_parsed_spec(db, target, parsed_spec, update_base_url=update_base_url)

    @staticmethod
    def _persist_parsed_spec(
        db: Session,
        target: ApiTarget,
        parsed_spec: Dict[str, Any],
        update_base_url: bool = False
    ) -> Dict[str, Any]:
        """Atomically persist parsed metadata and endpoints with rollback protection."""
        try:
            # 1. Update target metadata
            target.specification_version = parsed_spec.get("spec_version")
            if parsed_spec.get("version"):
                target.api_version = parsed_spec["version"]
            if parsed_spec.get("description") and not target.description:
                target.description = parsed_spec["description"]

            # If requested and server URL extracted, update base URL after validation
            if update_base_url and parsed_spec.get("base_url"):
                extracted_url = parsed_spec["base_url"].rstrip("/")
                if extracted_url.startswith("http://") or extracted_url.startswith("https://"):
                    try:
                        validate_target_safety(extracted_url, allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING)
                        target.base_url = extracted_url
                    except Exception:
                        pass

            target.updated_at = utc_now()

            # 2. Clear existing discovered endpoints for this target before re-import
            db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.target_id == target.id).delete()

            # 3. Insert newly discovered endpoints
            endpoints_to_add = []
            for ep in parsed_spec.get("endpoints", []):
                endpoint_record = DiscoveredEndpoint(
                    target_id=target.id,
                    path=ep["path"],
                    method=ep["method"],
                    operation_id=ep.get("operation_id"),
                    summary=ep.get("summary"),
                    description=ep.get("description"),
                    tags=ep.get("tags", []),
                    parameters=ep.get("parameters", []),
                    request_schema=ep.get("request_schema"),
                    responses=ep.get("responses"),
                    security_requirements=ep.get("security_requirements"),
                    is_sensitive_candidate=ep.get("is_sensitive_candidate", False),
                    is_state_changing=ep.get("is_state_changing", False),
                    is_selected=ep.get("is_selected", True),
                    created_at=utc_now(),
                )
                endpoints_to_add.append(endpoint_record)

            db.add_all(endpoints_to_add)
            db.commit()
            db.refresh(target)

            return {
                "target_id": target.id,
                "title": parsed_spec.get("title"),
                "spec_version": parsed_spec.get("spec_version"),
                "total_discovered": len(endpoints_to_add),
                "sensitive_candidates": parsed_spec.get("sensitive_endpoints_count", 0),
                "state_changing_count": parsed_spec.get("state_changing_count", 0),
                "security_schemes": parsed_spec.get("security_schemes", []),
                "warnings": parsed_spec.get("warnings", []),
            }
        except Exception as err:
            db.rollback()
            logger.error("Failed to persist imported OpenAPI specification: %s", err)
            raise TargetServiceError(f"Database error during specification persistence: {str(err)}")

    # -------------------------------------------------------------------------
    # Discovered Endpoints Querying & Selection
    # -------------------------------------------------------------------------

    @staticmethod
    def get_target_endpoints(
        db: Session,
        target_id: str,
        method: Optional[str] = None,
        is_sensitive: Optional[bool] = None,
        search: Optional[str] = None,
        is_selected: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DiscoveredEndpoint], int]:
        """Query and filter discovered endpoints for a target."""
        query = db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.target_id == target_id)

        if method:
            query = query.filter(DiscoveredEndpoint.method == method.upper().strip())
        if is_sensitive is not None:
            query = query.filter(DiscoveredEndpoint.is_sensitive_candidate == is_sensitive)
        if is_selected is not None:
            query = query.filter(DiscoveredEndpoint.is_selected == is_selected)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                (DiscoveredEndpoint.path.ilike(search_pattern)) |
                (DiscoveredEndpoint.summary.ilike(search_pattern)) |
                (DiscoveredEndpoint.operation_id.ilike(search_pattern))
            )

        total = query.count()
        endpoints = query.order_by(DiscoveredEndpoint.path.asc(), DiscoveredEndpoint.method.asc()).offset(skip).limit(limit).all()
        return endpoints, total

    @staticmethod
    def update_endpoint_selection(
        db: Session,
        target_id: str,
        endpoint_ids: Optional[List[Any]] = None,
        select_all: Optional[bool] = None,
        deselect_all: Optional[bool] = None,
        sensitive_only: Optional[bool] = None,
    ) -> Tuple[int, int]:
        """Update selection state of endpoints. Returns (selected_count, total_count)."""
        target = db.query(ApiTarget).filter(ApiTarget.id == target_id).first()
        if not target:
            raise TargetServiceError(f"Target '{target_id}' not found.")

        total_count = db.query(func.count(DiscoveredEndpoint.id)).filter(DiscoveredEndpoint.target_id == target_id).scalar() or 0

        if deselect_all:
            select_all = False

        if sensitive_only:
            db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.target_id == target_id).update(
                {"is_selected": False}, synchronize_session="fetch"
            )
            db.query(DiscoveredEndpoint).filter(
                DiscoveredEndpoint.target_id == target_id,
                DiscoveredEndpoint.is_sensitive_candidate == True
            ).update({"is_selected": True}, synchronize_session="fetch")
        elif select_all is not None:
            # Bulk select or bulk deselect
            db.query(DiscoveredEndpoint).filter(DiscoveredEndpoint.target_id == target_id).update(
                {"is_selected": bool(select_all)},
                synchronize_session="fetch"
            )
        elif endpoint_ids is not None:
            # Check if elements are dicts e.g. [{"endpoint_id": "...", "is_selected": True}]
            if endpoint_ids and isinstance(endpoint_ids[0], dict):
                for item in endpoint_ids:
                    ep_id = item.get("endpoint_id") or item.get("id")
                    sel = item.get("is_selected", True)
                    if ep_id:
                        db.query(DiscoveredEndpoint).filter(
                            DiscoveredEndpoint.target_id == target_id,
                            DiscoveredEndpoint.id == ep_id
                        ).update({"is_selected": bool(sel)}, synchronize_session="fetch")
            else:
                # Set selected for given IDs, unselect others
                str_ids = [str(x) for x in endpoint_ids]
                db.query(DiscoveredEndpoint).filter(
                    DiscoveredEndpoint.target_id == target_id,
                    DiscoveredEndpoint.id.in_(str_ids)
                ).update({"is_selected": True}, synchronize_session="fetch")

                db.query(DiscoveredEndpoint).filter(
                    DiscoveredEndpoint.target_id == target_id,
                    ~DiscoveredEndpoint.id.in_(str_ids)
                ).update({"is_selected": False}, synchronize_session="fetch")

        db.commit()

        selected_count = db.query(func.count(DiscoveredEndpoint.id)).filter(
            DiscoveredEndpoint.target_id == target_id,
            DiscoveredEndpoint.is_selected == True
        ).scalar() or 0

        return selected_count, total_count

    # -------------------------------------------------------------------------
    # Authentication Profiles & Credential Encryption
    # -------------------------------------------------------------------------

    @staticmethod
    def save_auth_profile(
        db: Session,
        target_id: str,
        profile_data: AuthProfileCreate
    ) -> TargetAuthProfile:
        """Create or update authentication profile with authenticated encryption for credential value."""
        target = db.query(ApiTarget).filter(ApiTarget.id == target_id).first()
        if not target:
            raise TargetServiceError(f"Target '{target_id}' not found.")

        label = profile_data.account_label.strip()
        auth_type = profile_data.authentication_type.lower().strip()

        # Check existing profile for this target + label
        existing = db.query(TargetAuthProfile).filter(
            TargetAuthProfile.target_id == target_id,
            TargetAuthProfile.account_label == label
        ).first()

        raw_cred = profile_data.credential_value
        ciphertext = None
        masked_preview = "Not configured"

        if raw_cred and raw_cred.strip():
            # Encrypt raw credential via Fernet authenticated encryption
            ciphertext = encrypt_credential(raw_cred.strip())
            masked_preview = mask_credential(raw_cred.strip(), auth_type=auth_type)
        elif existing:
            # Preserve existing ciphertext if not being overwritten
            ciphertext = existing.credential_ciphertext
            masked_preview = existing.credential_metadata.get("masked_credential", "Configured (Encrypted)")

        meta = {
            "masked_credential": masked_preview,
            "header_name": profile_data.header_name,
            "header_prefix": profile_data.header_prefix,
            "username": profile_data.username,
            "owned_resource_id": profile_data.owned_resource_id,
        }

        if existing:
            existing.authentication_type = auth_type
            existing.credential_ciphertext = ciphertext
            existing.credential_metadata = meta
            existing.updated_at = utc_now()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_profile = TargetAuthProfile(
                target_id=target_id,
                account_label=label,
                authentication_type=auth_type,
                credential_ciphertext=ciphertext,
                credential_metadata=meta,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            return new_profile

    @staticmethod
    def get_auth_profiles(db: Session, target_id: str) -> List[Dict[str, Any]]:
        """Retrieve masked authentication profiles for a target. Never returns plaintext credentials or ciphertext."""
        profiles = db.query(TargetAuthProfile).filter(TargetAuthProfile.target_id == target_id).all()
        results = []
        for p in profiles:
            meta = p.credential_metadata or {}
            results.append({
                "id": p.id,
                "target_id": p.target_id,
                "account_label": p.account_label,
                "authentication_type": p.authentication_type,
                "header_name": meta.get("header_name", "Authorization"),
                "header_prefix": meta.get("header_prefix", "Bearer"),
                "masked_credential": meta.get("masked_credential", "Not configured"),
                "username": meta.get("username"),
                "owned_resource_id": meta.get("owned_resource_id"),
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            })
        return results

    @staticmethod
    def get_decrypted_auth_profile(db: Session, target_id: str, account_label: str) -> Optional[Dict[str, Any]]:
        """Internal helper for scanning engine to decrypt credential for authorized active testing."""
        profile = db.query(TargetAuthProfile).filter(
            TargetAuthProfile.target_id == target_id,
            TargetAuthProfile.account_label == account_label
        ).first()
        if not profile:
            return None

        raw_cred = None
        if profile.credential_ciphertext:
            raw_cred = decrypt_credential(profile.credential_ciphertext)

        meta = profile.credential_metadata or {}
        return {
            "account_label": profile.account_label,
            "authentication_type": profile.authentication_type,
            "header_name": meta.get("header_name", "Authorization"),
            "header_prefix": meta.get("header_prefix", "Bearer"),
            "username": meta.get("username"),
            "owned_resource_id": meta.get("owned_resource_id"),
            "credential_value": raw_cred,
        }
