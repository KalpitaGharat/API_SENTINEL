"""Retesting API Router: Endpoints for running verification and re-test checks."""

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RetestRequest, RetestResponse
from app.services.retest_service import RetestService

router = APIRouter(prefix="/api/scans", tags=["Retesting"])


@router.post(
    "/{scan_id}/retest",
    response_model=RetestResponse,
    status_code=status.HTTP_200_OK,
    summary="Retest finding(s) to verify remediation",
    description=(
        "Re-executes security checks for one or all findings in a scan session, "
        "compares post-remediation behavior with original baseline, and records audit history."
    ),
)
def retest_scan_findings(
    scan_id: str,
    payload: Optional[RetestRequest] = None,
    db: Session = Depends(get_db),
):
    """Trigger security verification retest."""
    retest_payload = payload or RetestRequest()
    return RetestService.retest_scan(
        db=db,
        scan_id=scan_id,
        specific_finding_id=retest_payload.finding_id,
    )
