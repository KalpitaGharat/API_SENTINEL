"""Unit and integration tests for All-Time Security Analytics aggregation."""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Scan, Finding, Evidence, ScanRecord, FindingRecord
from app.main import app
from app.services.analytics_service import AnalyticsService


@pytest.fixture(name="test_db")
def fixture_test_db():
    """In-memory SQLite database for isolated test execution."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(test_db):
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestAllTimeAnalytics:
    """Test suite for all-time security analytics aggregation and deduplication."""

    def test_empty_database_returns_safe_zeros(self, test_db, client):
        """Empty database must return zeroed metrics without crashing or division-by-zero."""
        analytics = AnalyticsService.get_all_time_analytics(test_db)
        assert analytics["total_scans"] == 0
        assert analytics["total_unique_findings"] == 0
        assert analytics["total_occurrences"] == 0
        assert analytics["resolved_findings"] == 0
        assert analytics["unresolved_findings"] == 0
        assert analytics["severity_distribution"]["critical"] == 0
        assert analytics["severity_distribution"]["high"] == 0
        assert analytics["severity_percentages"]["critical"] == 0.0

        # Verify HTTP endpoint
        resp = client.get("/api/findings/analytics/all-time")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_scans"] == 0
        assert data["total_unique_findings"] == 0

    def test_all_time_aggregation_across_multiple_scans(self, test_db):
        """Findings from multiple historical scans must be aggregated into cumulative metrics."""
        scan1 = ScanRecord(
            id="scan-001",
            target_url="https://api.sentinel-test.com/v1",
            status="Completed",
            total_findings=2,
        )
        scan2 = ScanRecord(
            id="scan-002",
            target_url="https://api.sentinel-test.com/v1",
            status="Completed",
            total_findings=1,
        )
        test_db.add_all([scan1, scan2])
        test_db.commit()

        f1 = FindingRecord(
            id="f-001",
            scan_id="scan-001",
            vulnerability="Broken Object Level Authorization (BOLA)",
            category="BOLA",
            endpoint="/api/v1/patients/101",
            severity="Critical",
            description="BOLA vulnerability detected",
            recommendation="Enforce auth checks",
            status="Open",
        )
        f2 = FindingRecord(
            id="f-002",
            scan_id="scan-001",
            vulnerability="Missing Security Headers",
            category="HEADERS",
            endpoint="/api/v1/patients/101",
            severity="Low",
            description="Missing X-Frame-Options",
            recommendation="Add header",
            status="Open",
        )
        f3 = FindingRecord(
            id="f-003",
            scan_id="scan-002",
            vulnerability="SQL Injection Risk",
            category="AUTH",
            endpoint="/api/v1/search",
            severity="High",
            description="Parameter vulnerable",
            recommendation="Use parameterized queries",
            status="Resolved",
        )
        test_db.add_all([f1, f2, f3])
        test_db.commit()

        analytics = AnalyticsService.get_all_time_analytics(test_db)
        assert analytics["total_scans"] == 2
        assert analytics["total_unique_findings"] == 3
        assert analytics["total_occurrences"] == 3
        assert analytics["severity_distribution"]["critical"] == 1
        assert analytics["severity_distribution"]["high"] == 1
        assert analytics["severity_distribution"]["low"] == 1
        assert analytics["resolved_findings"] == 1
        assert analytics["unresolved_findings"] == 2

    def test_repeated_findings_deduplicated_by_fingerprint(self, test_db):
        """Repeated detections of the same finding across scans must not inflate unique count."""
        scan1 = ScanRecord(id="scan-101", target_url="https://demo.api/v1", status="Completed")
        scan2 = ScanRecord(id="scan-102", target_url="https://demo.api/v1", status="Completed")
        scan3 = ScanRecord(id="scan-103", target_url="https://demo.api/v1", status="Completed")
        test_db.add_all([scan1, scan2, scan3])
        test_db.commit()

        # Same vulnerability on same endpoint detected across 3 distinct scan runs
        f_run1 = FindingRecord(
            id="f-101",
            scan_id="scan-101",
            vulnerability="Broken Token Signature",
            category="AUTH",
            endpoint="/api/admin/metrics",
            severity="Critical",
            description="Token signature bypass",
            recommendation="Verify cryptographic signature",
            status="Open",
        )
        f_run2 = FindingRecord(
            id="f-102",
            scan_id="scan-102",
            vulnerability="Broken Token Signature",
            category="AUTH",
            endpoint="/api/admin/metrics",
            severity="Critical",
            description="Token signature bypass",
            recommendation="Verify cryptographic signature",
            status="Still Vulnerable",
        )
        f_run3 = FindingRecord(
            id="f-103",
            scan_id="scan-103",
            vulnerability="Broken Token Signature",
            category="AUTH",
            endpoint="/api/admin/metrics",
            severity="Critical",
            description="Token signature bypass",
            recommendation="Verify cryptographic signature",
            status="Resolved",  # Finally resolved in scan 3
        )
        test_db.add_all([f_run1, f_run2, f_run3])
        test_db.commit()

        analytics = AnalyticsService.get_all_time_analytics(test_db)
        assert analytics["total_scans"] == 3
        assert analytics["total_unique_findings"] == 1  # Deduplicated from 3 detections
        assert analytics["total_occurrences"] == 3       # Raw occurrences preserved
        assert analytics["severity_distribution"]["critical"] == 1
        assert analytics["resolved_findings"] == 1       # Latest state is resolved
        assert analytics["unresolved_findings"] == 0

    def test_missing_or_variant_severity_normalization(self, test_db):
        """Severities with mixed casing, abbreviations, or missing values normalize cleanly."""
        scan = ScanRecord(id="scan-norm", target_url="https://norm.api", status="Completed")
        test_db.add(scan)
        test_db.commit()

        findings = [
            FindingRecord(id="fn-1", scan_id="scan-norm", vulnerability="V1", category="C", endpoint="/e1", severity="CRITICAL", description="d", recommendation="r"),
            FindingRecord(id="fn-2", scan_id="scan-norm", vulnerability="V2", category="C", endpoint="/e2", severity="high", description="d", recommendation="r"),
            FindingRecord(id="fn-3", scan_id="scan-norm", vulnerability="V3", category="C", endpoint="/e3", severity="Med", description="d", recommendation="r"),
            FindingRecord(id="fn-4", scan_id="scan-norm", vulnerability="V4", category="C", endpoint="/e4", severity="Informational", description="d", recommendation="r"),
            FindingRecord(id="fn-5", scan_id="scan-norm", vulnerability="V5", category="C", endpoint="/e5", severity="unknown_custom", description="d", recommendation="r"),
        ]
        test_db.add_all(findings)
        test_db.commit()

        analytics = AnalyticsService.get_all_time_analytics(test_db)
        assert analytics["total_unique_findings"] == 5
        assert analytics["severity_distribution"]["critical"] == 1
        assert analytics["severity_distribution"]["high"] == 1
        assert analytics["severity_distribution"]["medium"] == 1
        assert analytics["severity_distribution"]["informational"] == 1
        assert analytics["severity_distribution"]["low"] == 1  # unknown fallback to low

    def test_endpoints_return_consistent_analytics(self, test_db, client):
        """Both /api/findings/analytics/all-time and /api/scans/analytics/all-time must work."""
        scan = ScanRecord(id="scan-api", target_url="https://api.test", status="Completed")
        test_db.add(scan)
        test_db.commit()

        f = FindingRecord(
            id="f-api",
            scan_id="scan-api",
            vulnerability="Permissive CORS",
            category="CONFIG",
            endpoint="/api/data",
            severity="Medium",
            description="Wildcard CORS",
            recommendation="Restrict origins",
            status="Open",
        )
        test_db.add(f)
        test_db.commit()

        resp1 = client.get("/api/findings/analytics/all-time")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["total_scans"] == 1
        assert data1["total_unique_findings"] == 1
        assert data1["severity_distribution"]["medium"] == 1

        resp2 = client.get("/api/scans/analytics/all-time")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2 == data1
