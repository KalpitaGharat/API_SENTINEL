"""Reports API Router: Endpoints for generating structured security reports."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/scans", tags=["Reports"])


@router.get(
    "/{scan_id}/report",
    response_model=ReportResponse,
    summary="Generate comprehensive security report",
    description="Aggregates scan metadata, findings, technical evidence, AI explanations, and retest metrics.",
)
def get_scan_report(
    scan_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve structured security report."""
    return ReportService.generate_report(db=db, scan_id=scan_id)
