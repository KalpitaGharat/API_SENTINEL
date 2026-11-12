"""Scan Service: Handles scan orchestration, storage, and retrieval."""

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models import Scan, Finding, Evidence
from app.schemas import ScanCreateRequest
from app.config import settings
from app.services.event_service import event_broadcaster
from app.security_engine.integration import (
    validate_target_safety,
    get_security_engine,
    TargetSafetyError,
)

logger = logging.getLogger(__name__)

SENSITIVE_KEY_PATTERN = re.compile(
    r"(authorization|bearer|token|secret|password|api[-_]?key|credential|cookie|passwd)",
    re.IGNORECASE,
)


def redact_sensitive_credentials(data: Any) -> Any:
    """Recursively redacts passwords, tokens, API keys, cookies, and auth headers from scan config."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if SENSITIVE_KEY_PATTERN.search(str(key)):
                sanitized[key] = "[REDACTED_FOR_SECURITY]"
            else:
                sanitized[key] = redact_sensitive_credentials(value)
        return sanitized
    elif isinstance(data, list):
        return [redact_sensitive_credentials(item) for item in data]
    return data


class ScanService:
    """Coordinates API security testing sessions and database persistence."""

    @staticmethod
    def create_and_run_scan(db: Session, request: ScanCreateRequest) -> Scan:
        """Validate safety, launch engine scan, and persist all findings."""
        # 1. Target URL Safety Validation (SSRF / IP controls)
        try:
            validate_target_safety(
                request.target_url,
                allow_lab=settings.ALLOW_LOCAL_LAB_SCANNING,
            )
        except TargetSafetyError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security Policy Violation: {str(err)}",
            )

        # 2. Resolve active security testing engine and sanitize configuration before persistence
        engine = get_security_engine()
        sanitized_config = redact_sensitive_credentials(request.model_dump())
        sanitized_config["engine_name"] = getattr(engine, "engine_name", "member1_engine")
        sanitized_config["is_simulated"] = getattr(engine, "is_simulated", False)

        # 3. Create Scan database record
        scan = Scan(
            target_url=request.target_url,
            status="Running",
            scan_configuration=sanitized_config,
            created_at=datetime.now(timezone.utc),
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Broadcast scan_created event to connected live dashboards
        event_broadcaster.publish_event("scan_created", {
            "scan_id": scan.id,
            "target_url": scan.target_url,
            "status": "Running",
            "created_at": scan.created_at.isoformat(),
        })

        # 4. Invoke Security Testing Engine
        try:
            # Pass original request configuration for scanning
            findings_data = engine.run_scan(request.target_url, request.model_dump())

            # 5. Persist each detected finding and its evidence
            for finding_item in findings_data:
                finding = Finding(
                    scan_id=scan.id,
                    vulnerability=finding_item.vulnerability,
                    category=finding_item.category,
                    endpoint=finding_item.endpoint,
                    severity=finding_item.severity,
                    description=finding_item.description,
                    recommendation=finding_item.recommendation,
                    status=finding_item.status,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(finding)
                db.flush()  # Populates finding.id

                if finding_item.evidence:
                    ev_data = finding_item.evidence
                    evidence = Evidence(
                        finding_id=finding.id,
                        test_user=ev_data.test_user,
                        requested_resource=ev_data.requested_resource,
                        observed_status=ev_data.observed_status,
                        expected_status=ev_data.expected_status,
                        request_details=ev_data.request_details,
                        response_details=ev_data.response_details,
                    )
                    db.add(evidence)

                # Broadcast critical finding alert immediately if severity is Critical or High
                if str(finding.severity).lower() in ("critical", "high"):
                    event_broadcaster.publish_event("critical_finding", {
                        "finding_id": finding.id,
                        "scan_id": scan.id,
                        "vulnerability": finding.vulnerability,
                        "endpoint": finding.endpoint,
                        "severity": finding.severity,
                        "category": finding.category,
                        "description": finding.description,
                        "recommendation": finding.recommendation,
                        "created_at": finding.created_at.isoformat(),
                    })

            # 6. Finalize scan status
            scan.status = "Completed"
            scan.total_findings = len(findings_data)
            scan.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(scan)

            # Broadcast scan_completed event
            event_broadcaster.publish_event("scan_completed", {
                "scan_id": scan.id,
                "target_url": scan.target_url,
                "status": "Completed",
                "total_findings": scan.total_findings,
                "completed_at": scan.completed_at.isoformat(),
            })

            return scan

        except Exception as scan_err:
            logger.exception("Error executing security scan for %s: %s", request.target_url, scan_err)
            # Broadcast scan_failed event
            event_broadcaster.publish_event("scan_failed", {
                "scan_id": scan.id,
                "target_url": request.target_url,
                "status": "Failed",
                "error": str(scan_err),
            })
            # 1. Roll back the aborted transaction to discard uncommitted partial finding/evidence records
            try:
                db.rollback()
            except Exception as rb_err:
                logger.warning("Error during transaction rollback: %s", rb_err)

            # 2. Update scan status to 'Failed' in a clean, isolated transaction
            try:
                failed_scan = db.query(Scan).filter(Scan.id == scan.id).first()
                if failed_scan:
                    failed_scan.status = "Failed"
                    failed_scan.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception as update_err:
                logger.warning("Secondary failure updating scan status to Failed: %s", update_err)
                try:
                    db.rollback()
                except Exception:
                    pass

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Security testing engine execution failed: {str(scan_err)}",
            )

    @staticmethod
    def get_scans(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Scan], int]:
        """Retrieve paginated scan history with optional status filter."""
        query = db.query(Scan)
        if status_filter:
            query = query.filter(Scan.status == status_filter)

        total = query.count()
        items = query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_scan_by_id(db: Session, scan_id: str) -> Scan:
        """Fetch individual scan record by ID."""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan with ID '{scan_id}' not found.",
            )
        return scan

    @staticmethod
    def get_findings_for_scan(db: Session, scan_id: str) -> List[Finding]:
        """Fetch all findings belonging to a scan, including evidence and AI explanation."""
        # Ensure scan exists
        ScanService.get_scan_by_id(db, scan_id)

        findings = (
            db.query(Finding)
            .filter(Finding.scan_id == scan_id)
            .options(
                joinedload(Finding.evidence),
                joinedload(Finding.ai_explanation),
            )
            .order_by(Finding.created_at.asc())
            .all()
        )
        return findings
