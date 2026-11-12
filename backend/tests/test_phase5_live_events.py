"""Phase 5: Real-time Live Events & SSE Telemetry Tests.

Validates the EventBroadcaster pub/sub system, SSE endpoint, live telemetry events,
and critical alert triggers.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app
from app.services.event_service import EventBroadcaster, event_broadcaster
from app.services.scan_service import ScanService
from app.services.retest_service import RetestService
from app.schemas import ScanCreateRequest
from app.security_engine.integration import (
    set_security_engine_override,
    reset_security_engine,
    MockSecurityEngineAdapter,
)

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = SessionLocal()
    set_security_engine_override(MockSecurityEngineAdapter())
    try:
        yield session
    finally:
        reset_security_engine()
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_event_broadcaster_subscribe_and_publish():
    """Verify EventBroadcaster registers subscribers, publishes events, and cleans up."""
    broadcaster = EventBroadcaster()
    assert broadcaster.subscriber_count() == 0

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # 1. Add subscriber
        q = loop.run_until_complete(broadcaster.add_subscriber())
        assert broadcaster.subscriber_count() == 1

        # 2. Publish event
        broadcaster.publish_event("scan_created", {"scan_id": "SCAN-TEST-01", "status": "Running"})

        # 3. Verify message delivered to queue
        assert not q.empty()
        msg = q.get_nowait()
        assert msg["event"] == "scan_created"
        assert msg["data"]["scan_id"] == "SCAN-TEST-01"
        assert "timestamp" in msg

        # 4. Remove subscriber
        loop.run_until_complete(broadcaster.remove_subscriber(q))
        assert broadcaster.subscriber_count() == 0
    finally:
        loop.close()


def test_events_status_endpoint():
    """Verify GET /api/events/status returns operational metadata."""
    client = TestClient(app)
    response = client.get("/api/events/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["protocol"] == "Server-Sent Events (SSE)"
    assert "active_subscribers" in data
    assert "timestamp" in data


def test_scan_lifecycle_publishes_live_events(db):
    """Verify ScanService publishes scan_created, critical_finding, and scan_completed events."""
    captured_events = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        q = loop.run_until_complete(event_broadcaster.add_subscriber())

        request = ScanCreateRequest(
            target_url="http://127.0.0.1:8001",
            user_authorized=True,
            categories=["BOLA", "AUTH"],
        )
        scan = ScanService.create_and_run_scan(db=db, request=request)
        assert scan.status == "Completed"

        # Drain queue
        while not q.empty():
            captured_events.append(q.get_nowait())

        loop.run_until_complete(event_broadcaster.remove_subscriber(q))

        event_types = [e["event"] for e in captured_events]
        assert "scan_created" in event_types
        assert "scan_completed" in event_types

        # Verify scan_completed event has accurate summary
        completed_evt = next(e for e in captured_events if e["event"] == "scan_completed")
        assert completed_evt["data"]["scan_id"] == scan.id
        assert completed_evt["data"]["status"] == "Completed"
        assert completed_evt["data"]["total_findings"] == scan.total_findings

        # Verify critical_finding alert is emitted for critical/high findings
        critical_evts = [e for e in captured_events if e["event"] == "critical_finding"]
        assert len(critical_evts) > 0
        for ce in critical_evts:
            assert ce["data"]["severity"].lower() in ("critical", "high")
            assert "finding_id" in ce["data"]
            assert "vulnerability" in ce["data"]

    finally:
        loop.close()


def test_retest_publishes_live_event(db):
    """Verify RetestService publishes retest_completed event to active dashboard clients."""
    captured_events = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        q = loop.run_until_complete(event_broadcaster.add_subscriber())

        request = ScanCreateRequest(
            target_url="http://127.0.0.1:8001",
            user_authorized=True,
            categories=["BOLA"],
        )
        scan = ScanService.create_and_run_scan(db=db, request=request)

        # Clear initial scan events
        while not q.empty():
            q.get_nowait()

        # Run retest
        retest_res = RetestService.retest_scan(db=db, scan_id=scan.id)
        assert len(retest_res.results) > 0

        # Drain queue for retest event
        while not q.empty():
            captured_events.append(q.get_nowait())

        loop.run_until_complete(event_broadcaster.remove_subscriber(q))

        event_types = [e["event"] for e in captured_events]
        assert "retest_completed" in event_types
        retest_evt = next(e for e in captured_events if e["event"] == "retest_completed")
        assert retest_evt["data"]["scan_id"] == scan.id
        assert "verified_count" in retest_evt["data"]
        assert retest_evt["data"]["total_retested"] == len(retest_res.results)

    finally:
        loop.close()
