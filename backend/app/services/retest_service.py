"""Retesting & Verification Service for API Sentinel.

Re-executes targeted security probes against remediated endpoints,
evaluates whether vulnerabilities have genuinely been mitigated,
and commits an immutable audit trail into RetestHistory.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Scan, Finding, RetestHistory
from app.schemas import RetestResultItem, RetestResponse
from app.services.event_service import event_broadcaster
from app.security_engine.integration import get_security_engine

logger = logging.getLogger(__name__)


class RetestService:
    """Manages verification workflow and comparison between pre/post-fix states."""

    @staticmethod
    def retest_scan(
        db: Session,
        scan_id: str,
        specific_finding_id: Optional[str] = None,
    ) -> RetestResponse:
        """Execute verification check for one or all findings in a scan."""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan with ID '{scan_id}' not found.",
            )

        query = db.query(Finding).filter(Finding.scan_id == scan_id)
        if specific_finding_id:
            query = query.filter(Finding.id == specific_finding_id)

        findings_to_test = query.all()
        if not findings_to_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No matching findings found to retest.",
            )

        engine = get_security_engine()
        retest_results: List[RetestResultItem] = []
        now = datetime.now(timezone.utc)

        for finding in findings_to_test:
            prev_status = finding.status
            finding_dict = {
                "id": finding.id,
                "vulnerability": finding.vulnerability,
                "category": finding.category,
                "endpoint": finding.endpoint,
                "severity": finding.severity,
            }

            try:
                # Security engine re-tests the endpoint
                result_probe = engine.retest_finding(
                    target_url=scan.target_url,
                    finding_data=finding_dict,
                    config=scan.scan_configuration,
                )

                verified = result_probe.get("verified", False)
                new_status = result_probe.get("new_status", "Still Vulnerable")
                observed_result = result_probe.get("observed_result", {})

            except Exception as probe_err:
                logger.warning("Retest probe failed for finding %s: %s", finding.id, probe_err)
                verified = False
                new_status = "Retest Failed"
                observed_result = {"error": str(probe_err)}

            # Update finding status in database
            finding.status = new_status

            # Record retest event in audit history
            audit_record = RetestHistory(
                scan_id=scan.id,
                finding_id=finding.id,
                previous_status=prev_status,
                new_status=new_status,
                observed_result=observed_result,
                verified=verified,
                retested_at=now,
            )
            db.add(audit_record)

            retest_results.append(
                RetestResultItem(
                    finding_id=finding.id,
                    vulnerability=finding.vulnerability,
                    endpoint=finding.endpoint,
                    previous_status=prev_status,
                    new_status=new_status,
                    observed_result=observed_result,
                    verified=verified,
                    retested_at=now,
                )
            )

        try:
            db.commit()
            # Broadcast retest_completed event to live dashboards
            event_broadcaster.publish_event("retest_completed", {
                "scan_id": scan.id,
                "retested_at": now.isoformat(),
                "verified_count": sum(1 for r in retest_results if r.verified),
                "total_retested": len(retest_results),
            })
        except Exception as commit_err:
            db.rollback()
            logger.exception("Failed to commit retest transaction for scan %s: %s", scan_id, commit_err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist retest transaction: {str(commit_err)}",
            )

        return RetestResponse(
            scan_id=scan.id,
            retested_at=now,
            results=retest_results,
        )
