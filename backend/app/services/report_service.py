"""Security Report Generation Service."""

from datetime import datetime, timezone
from typing import Dict
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models import Scan, Finding
from app.schemas import ReportResponse, ReportSummary, ScanResponse, FindingResponse


class ReportService:
    """Compiles complete scan metrics and audit findings into structured reports."""

    @staticmethod
    def generate_report(db: Session, scan_id: str) -> ReportResponse:
        """Compile comprehensive security report for a completed or historical scan."""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan with ID '{scan_id}' not found.",
            )

        findings = (
            db.query(Finding)
            .filter(Finding.scan_id == scan_id)
            .options(
                joinedload(Finding.evidence),
                joinedload(Finding.ai_explanation),
            )
            .all()
        )

        # Aggregate statistics
        total_findings = len(findings)
        open_count = sum(1 for f in findings if f.status in ("Open", "Still Vulnerable", "Needs Review"))
        resolved_count = sum(1 for f in findings if f.status == "Resolved")

        severity_breakdown: Dict[str, int] = {}
        category_breakdown: Dict[str, int] = {}

        for f in findings:
            severity_breakdown[f.severity] = severity_breakdown.get(f.severity, 0) + 1
            category_breakdown[f.category] = category_breakdown.get(f.category, 0) + 1

        summary = ReportSummary(
            total_findings=total_findings,
            open_count=open_count,
            resolved_count=resolved_count,
            severity_breakdown=severity_breakdown,
            category_breakdown=category_breakdown,
        )

        return ReportResponse(
            scan=ScanResponse.model_validate(scan),
            summary=summary,
            findings=[FindingResponse.model_validate(f) for f in findings],
            generated_at=datetime.now(timezone.utc),
        )
