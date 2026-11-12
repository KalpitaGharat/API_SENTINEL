"""Scans API Router: Endpoints for triggering, monitoring, and listing scans."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ScanCreateRequest,
    ScanResponse,
    ScanListResponse,
    FindingResponse,
)
from app.services.scan_service import ScanService

router = APIRouter(prefix="/api/scans", tags=["Scans"])


@router.post(
    "",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a new security scan",
    description="Validates target API, enforces authorization confirmation, and triggers security testing checks.",
)
def create_scan(
    payload: ScanCreateRequest,
    db: Session = Depends(get_db),
):
    """Start an authorized security scan."""
    return ScanService.create_and_run_scan(db=db, request=payload)


@router.get(
    "",
    response_model=ScanListResponse,
    summary="Retrieve scan history",
    description="Returns paginated list of scans with optional status filtering.",
)
def list_scans(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by scan status (Pending, Running, Completed, Failed)"),
    db: Session = Depends(get_db),
):
    """List historical scans."""
    items, total = ScanService.get_scans(db=db, skip=skip, limit=limit, status_filter=status)
    return ScanListResponse(
        total=total,
        items=[ScanResponse.model_validate(item) for item in items],
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    summary="Retrieve individual scan details",
)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
):
    """Get metadata for a specific scan."""
    return ScanService.get_scan_by_id(db=db, scan_id=scan_id)


@router.get(
    "/{scan_id}/findings",
    response_model=List[FindingResponse],
    summary="Retrieve all findings for a scan",
    description="Returns all security findings belonging to the scan, including technical evidence.",
)
def get_scan_findings(
    scan_id: str,
    db: Session = Depends(get_db),
):
    """Get all findings associated with a scan."""
    findings = ScanService.get_findings_for_scan(db=db, scan_id=scan_id)
    return [FindingResponse.model_validate(f) for f in findings]
