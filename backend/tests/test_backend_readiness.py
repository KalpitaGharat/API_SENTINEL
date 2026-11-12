"""Comprehensive Test Suite for Phase 3: Database, AI Integration, Docker & Production Readiness.

Validates:
1. SQLite connection timeout, WAL mode, and busy timeout PRAGMAs.
2. Persistence after engine restart and disposal.
3. Concurrent database read/write safety.
4. Transaction rollback and status handling on failed scan operations.
5. Transaction safety during retesting.
6. Append-only RetestHistory immutability across multiple retests.
7. GET /api/findings/{finding_id}/history endpoint correctness.
8. AIExplanationOutput strict schema validation (valid, empty, missing, malformed, wrong types).
9. AI error handling (401, 403, 429, 500, timeout, connection errors, missing key fallback).
10. AI cache preservation and force_refresh behavior.
11. Dockerfile and Compose static configuration verification.
"""

import json
import os
import sqlite3
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app
from app.models import AIExplanation, Evidence, Finding, RetestHistory, Scan
from app.schemas import (
    RetestHistoryItemResponse,
    RetestHistoryListResponse,
    ScanCreateRequest,
)
from app.services.ai_service import (
    AIExplanationOutput,
    AIService,
    ai_service,
)
from app.services.retest_service import RetestService
from app.services.scan_service import ScanService
from app.routes.findings import get_finding_retest_history, explain_finding


# =============================================================================
# 1. SQLite Reliability, WAL Mode, and Persistence Tests
# =============================================================================

def test_sqlite_pragmas_and_wal_mode():
    """Verify busy_timeout, foreign_keys, and WAL mode are activated on file databases."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False, "timeout": 30.0},
        )

        @event.listens_for(engine, "connect")
        def set_pragmas(dbapi_conn, record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA busy_timeout=30000;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.close()

        with engine.connect() as conn:
            busy = conn.execute(text("PRAGMA busy_timeout;")).scalar()
            fk = conn.execute(text("PRAGMA foreign_keys;")).scalar()
            journal = conn.execute(text("PRAGMA journal_mode;")).scalar()

            assert busy == 30000, f"Expected busy_timeout=30000, got {busy}"
            assert fk == 1, f"Expected foreign_keys=1, got {fk}"
            assert journal.upper() == "WAL", f"Expected journal_mode=WAL, got {journal}"
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_database_persistence_across_engine_restart():
    """Verify scan and finding records persist after closing session, disposing engine, and recreating."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Step 1: Create database, tables, and write data
        engine1 = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine1)
        Session1 = sessionmaker(bind=engine1)
        db1 = Session1()

        scan = Scan(
            id="persistent-scan-1",
            target_url="http://127.0.0.1:8001",
            status="Completed",
            total_findings=1,
            scan_configuration={"test": True},
        )
        finding = Finding(
            id="persistent-finding-1",
            scan_id=scan.id,
            vulnerability="Test BOLA",
            category="BOLA",
            endpoint="/api/patients/102",
            severity="High",
            description="BOLA test",
            recommendation="Fix BOLA",
            status="Open",
        )
        db1.add(scan)
        db1.add(finding)
        db1.commit()
        db1.close()
        engine1.dispose()

        # Step 2: Open entirely fresh engine and session on the same database file
        engine2 = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Session2 = sessionmaker(bind=engine2)
        db2 = Session2()

        loaded_scan = db2.query(Scan).filter(Scan.id == "persistent-scan-1").first()
        loaded_finding = db2.query(Finding).filter(Finding.id == "persistent-finding-1").first()

        assert loaded_scan is not None
        assert loaded_scan.status == "Completed"
        assert loaded_finding is not None
        assert loaded_finding.vulnerability == "Test BOLA"
        assert loaded_finding.scan_id == loaded_scan.id

        db2.close()
        engine2.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_concurrent_reads_and_writes_with_wal():
    """Verify multiple concurrent database threads can read and write without database locked errors."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False, "timeout": 30.0},
        )

        @event.listens_for(engine, "connect")
        def set_wal(dbapi_conn, _):
            c = dbapi_conn.cursor()
            c.execute("PRAGMA journal_mode=WAL;")
            c.execute("PRAGMA busy_timeout=30000;")
            c.close()

        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)

        errors = []

        def worker(idx):
            db = Session()
            try:
                for i in range(5):
                    scan = Scan(
                        id=f"thread-{idx}-scan-{i}",
                        target_url="http://127.0.0.1:8001",
                        status="Completed",
                        total_findings=0,
                        scan_configuration={},
                    )
                    db.add(scan)
                    db.commit()
                    # Perform read
                    count = db.query(Scan).count()
                    assert count > 0
            except Exception as e:
                errors.append(e)
            finally:
                db.close()

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent workers experienced errors: {errors}"
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# =============================================================================
# 2. Transaction Safety & Rollback Tests
# =============================================================================

def test_scan_service_transaction_rollback_on_engine_failure():
    """Simulate engine crash during scan: verify transaction rolls back and scan status transitions to Failed."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        mock_engine = MagicMock()
        mock_engine.engine_name = "test_engine"
        mock_engine.is_simulated = False
        mock_engine.run_scan.side_effect = RuntimeError("Simulated engine internal fault")

        req = ScanCreateRequest(
            target_url="http://127.0.0.1:8001",
            user_authorized=True,
            categories=["BOLA"],
        )

        with patch("app.services.scan_service.get_security_engine", return_value=mock_engine):
            with pytest.raises(Exception) as excinfo:
                ScanService.create_and_run_scan(db, req)

            assert "Simulated engine internal fault" in str(excinfo.value)

        # Confirm scan record is marked as 'Failed' and no ghost findings exist
        scans = db.query(Scan).all()
        assert len(scans) == 1
        assert scans[0].status == "Failed"
        assert db.query(Finding).count() == 0

        db.close()
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_retest_service_transaction_rollback_on_commit_error():
    """Verify that a database commit failure during retesting rolls back cleanly without dirty state."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        scan = Scan(
            id="retest-scan-1",
            target_url="http://127.0.0.1:8001",
            status="Completed",
            total_findings=1,
            scan_configuration={"test": True},
        )
        finding = Finding(
            id="retest-finding-1",
            scan_id=scan.id,
            vulnerability="BOLA",
            category="BOLA",
            endpoint="/api/patients/102",
            severity="High",
            description="desc",
            recommendation="rec",
            status="Open",
        )
        db.add(scan)
        db.add(finding)
        db.commit()

        # Simulate database commit error
        with patch.object(db, "commit", side_effect=sqlite3.OperationalError("Simulated disk full")):
            with pytest.raises(Exception):
                RetestService.retest_scan(db, scan_id=scan.id, specific_finding_id=finding.id)

        # After rollback, finding status remains 'Open' and no retest history is committed
        db.rollback()
        fresh_finding = db.query(Finding).filter(Finding.id == finding.id).first()
        assert fresh_finding.status == "Open"
        assert db.query(RetestHistory).count() == 0

        db.close()
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# =============================================================================
# 3. Retest History Immutability & Endpoint Tests
# =============================================================================

def test_retest_history_append_only_immutability():
    """Verify multiple retests append chronological records without overwriting previous history."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        scan = Scan(id="retest-imm-scan", target_url="http://127.0.0.1:8001", status="Completed", total_findings=1, scan_configuration={})
        finding = Finding(
            id="retest-imm-finding",
            scan_id=scan.id,
            vulnerability="BOLA",
            category="BOLA",
            endpoint="/api/patients/102",
            severity="High",
            description="desc",
            recommendation="rec",
            status="Open",
        )
        db.add(scan)
        db.add(finding)
        db.commit()

        mock_engine = MagicMock()
        mock_engine.retest_finding.side_effect = [
            {"verified": False, "new_status": "Still Vulnerable", "observed_result": {"attempt": 1}},
            {"verified": True, "new_status": "Resolved", "observed_result": {"attempt": 2}},
        ]

        with patch("app.services.retest_service.get_security_engine", return_value=mock_engine):
            # Retest 1: Still Vulnerable
            r1 = RetestService.retest_scan(db, scan_id=scan.id, specific_finding_id=finding.id)
            assert r1.results[0].new_status == "Still Vulnerable"

            # Retest 2: Resolved
            r2 = RetestService.retest_scan(db, scan_id=scan.id, specific_finding_id=finding.id)
            assert r2.results[0].new_status == "Resolved"

        # Check RetestHistory table: MUST contain 2 rows
        history = db.query(RetestHistory).filter(RetestHistory.finding_id == finding.id).order_by(RetestHistory.retested_at.asc()).all()
        assert len(history) == 2
        assert history[0].previous_status == "Open"
        assert history[0].new_status == "Still Vulnerable"
        assert history[0].verified is False

        assert history[1].previous_status == "Still Vulnerable"
        assert history[1].new_status == "Resolved"
        assert history[1].verified is True

        db.close()
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_get_finding_retest_history_endpoint():
    """Verify GET /api/findings/{finding_id}/history handles 404, empty history, and populated history."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        scan = Scan(id="hist-scan", target_url="http://127.0.0.1:8001", status="Completed", total_findings=1, scan_configuration={})
        finding = Finding(
            id="hist-finding-1",
            scan_id=scan.id,
            vulnerability="Headers",
            category="HEADERS",
            endpoint="/health",
            severity="Medium",
            description="desc",
            recommendation="rec",
            status="Open",
        )
        db.add(scan)
        db.add(finding)
        db.commit()

        # 1. 404 for unknown finding ID
        with pytest.raises(HTTPException) as exc:
            get_finding_retest_history(finding_id="nonexistent-uuid", db=db)
        assert exc.value.status_code == 404

        # 2. 200 with empty list for untested finding
        res_empty = get_finding_retest_history(finding_id=finding.id, db=db)
        assert res_empty.finding_id == finding.id
        assert res_empty.total_retests == 0
        assert res_empty.history == []

        # 3. Add retest history and verify response
        retest_rec = RetestHistory(
            id="rh-1",
            scan_id=scan.id,
            finding_id=finding.id,
            previous_status="Open",
            new_status="Resolved",
            observed_result={"status": 200, "token": "[REDACTED]"},
            verified=True,
            retested_at=datetime.now(timezone.utc),
        )
        db.add(retest_rec)
        db.commit()

        res_populated = get_finding_retest_history(finding_id=finding.id, db=db)
        assert res_populated.total_retests == 1
        assert len(res_populated.history) == 1
        assert res_populated.history[0].new_status == "Resolved"
        assert res_populated.history[0].verified is True

        db.close()
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# =============================================================================
# 4. AI Explanation Schema Validation & Failure Mode Tests
# =============================================================================

def test_ai_explanation_output_schema_validation():
    """Verify AIExplanationOutput accepts valid dicts and rejects empty or malformed fields."""
    # Valid output
    valid_data = {
        "explanation": "Valid explanation text",
        "impact": "Valid impact description",
        "remediation": "Valid remediation steps",
        "model_name": "nvidia/nemotron",
    }
    validated = AIExplanationOutput.model_validate(valid_data)
    assert validated.explanation == "Valid explanation text"

    # Reject empty string
    with pytest.raises(ValidationError):
        AIExplanationOutput.model_validate({**valid_data, "explanation": "   "})

    # Reject missing field
    with pytest.raises(ValidationError):
        AIExplanationOutput.model_validate({
            "explanation": "Valid",
            "impact": "Valid",
        })

    # Reject non-string type
    with pytest.raises(ValidationError):
        AIExplanationOutput.model_validate({**valid_data, "remediation": 12345})


def test_ai_service_markdown_fenced_json_parsing():
    """Verify AIService cleans markdown ```json fences and returns valid output."""
    svc = AIService()
    svc.client = MagicMock()

    mock_choice = MagicMock()
    mock_choice.message.content = (
        "```json\n"
        "{\n"
        '  "explanation": "Fenced explanation",\n'
        '  "impact": "Fenced impact",\n'
        '  "remediation": "Fenced remediation"\n'
        "}\n"
        "```"
    )
    svc.client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    res = svc._call_nemotron({"vulnerability": "BOLA"})
    assert res is not None
    assert res["explanation"] == "Fenced explanation"
    assert res["impact"] == "Fenced impact"
    assert "Fenced remediation" in res["remediation"]


def test_ai_service_malformed_json_triggers_rule_fallback():
    """Verify malformed JSON from LLM gracefully triggers deterministic rule-based fallback."""
    svc = AIService()
    svc.client = MagicMock()

    mock_choice = MagicMock()
    mock_choice.message.content = "This is not valid JSON at all!"
    svc.client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    finding = {
        "category": "BOLA",
        "vulnerability": "Broken Object Level Authorization",
        "endpoint": "/api/patients/{id}",
    }
    res = svc.explain_vulnerability(finding)
    assert res is not None
    assert "Broken Object Level Authorization" in res["explanation"]
    assert "rule-based-security-engine" in res["model_name"]


def test_ai_service_nvidia_api_errors_trigger_fallback():
    """Verify that 401, 403, 429, 500, timeout, and connection errors fallback gracefully."""
    svc = AIService()
    svc.client = MagicMock()

    error_types = [
        Exception("401 Unauthorized: Invalid API Key"),
        Exception("403 Forbidden"),
        Exception("429 Too Many Requests: Rate limit exceeded"),
        Exception("500 Internal Server Error"),
        TimeoutError("Connection timed out after 30s"),
        ConnectionError("Failed to resolve host integrate.api.nvidia.com"),
    ]

    finding = {
        "category": "AUTH",
        "vulnerability": "Unauthenticated Access",
        "endpoint": "/api/admin/metrics",
    }

    for err in error_types:
        svc.client.chat.completions.create.side_effect = err
        result = svc.explain_vulnerability(finding)

        assert result is not None
        assert "Unauthenticated" in result["explanation"] or "endpoint" in result["explanation"]
        assert "rule-based-security-engine" in result["model_name"]


def test_ai_service_missing_api_key_uses_rule_fallback():
    """When NVIDIA_API_KEY is unset or empty, explain_vulnerability uses rule fallback without error."""
    with patch("app.config.settings.NVIDIA_API_KEY", ""):
        svc = AIService()
        assert svc.client is None

        finding = {"category": "HEADERS", "vulnerability": "Missing HSTS", "endpoint": "/health"}
        res = svc.explain_vulnerability(finding)
        assert res is not None
        assert "rule-based-security-engine" in res["model_name"]
        assert "Strict-Transport-Security" in res["remediation"]


# =============================================================================
# 5. AI Cache & force_refresh Endpoint Tests
# =============================================================================

def test_explain_cache_and_force_refresh():
    """Verify POST /api/findings/{id}/explain serves cached explanation by default and refreshes with force_refresh=true."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        scan = Scan(id="cache-scan", target_url="http://127.0.0.1:8001", status="Completed", total_findings=1, scan_configuration={})
        finding = Finding(
            id="cache-finding-1",
            scan_id=scan.id,
            vulnerability="BOLA",
            category="BOLA",
            endpoint="/api/patients/102",
            severity="High",
            description="desc",
            recommendation="rec",
            status="Open",
        )
        db.add(scan)
        db.add(finding)
        db.commit()

        # 1. First call: Generates and persists explanation
        with patch.object(ai_service, "explain_vulnerability") as mock_ai:
            mock_ai.return_value = {
                "explanation": "First generation explanation",
                "impact": "First impact",
                "remediation": "First remediation",
                "model_name": "model-v1",
            }
            res1 = explain_finding(finding_id=finding.id, force_refresh=False, db=db)
            assert res1.explanation == "First generation explanation"
            assert mock_ai.call_count == 1

        # 2. Second call without force_refresh: MUST return cached result without calling AI service
        with patch.object(ai_service, "explain_vulnerability") as mock_ai_cached:
            res2 = explain_finding(finding_id=finding.id, force_refresh=False, db=db)
            assert res2.explanation == "First generation explanation"
            mock_ai_cached.assert_not_called()

        # 3. Third call WITH force_refresh=true: Calls AI service and updates cache
        with patch.object(ai_service, "explain_vulnerability") as mock_ai_refresh:
            mock_ai_refresh.return_value = {
                "explanation": "Updated fresh explanation",
                "impact": "Updated impact",
                "remediation": "Updated remediation",
                "model_name": "model-v2",
            }
            res3 = explain_finding(finding_id=finding.id, force_refresh=True, db=db)
            assert res3.explanation == "Updated fresh explanation"
            assert mock_ai_refresh.call_count == 1

        # 4. Verify database holds the updated record
        updated_exp = db.query(AIExplanation).filter(AIExplanation.finding_id == finding.id).first()
        assert updated_exp.explanation == "Updated fresh explanation"

        db.close()
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# =============================================================================
# 6. Docker & Deployment Static Configuration Tests
# =============================================================================

def test_dockerfile_and_compose_static_configuration():
    """Verify Dockerfile and docker-compose.yml security, volume, and service definitions."""
    project_root = Path(__file__).resolve().parent.parent.parent
    dockerfile_path = project_root / "Dockerfile"
    compose_path = project_root / "docker-compose.yml"
    dockerignore_path = project_root / ".dockerignore"

    assert dockerfile_path.exists(), "Dockerfile must exist"
    assert compose_path.exists(), "docker-compose.yml must exist"
    assert dockerignore_path.exists(), ".dockerignore must exist"

    # Verify Dockerfile: Non-root user and healthcheck
    df_content = dockerfile_path.read_text(encoding="utf-8")
    assert "USER sentinel" in df_content, "Dockerfile must run as non-root user 'sentinel'"
    assert "HEALTHCHECK" in df_content, "Dockerfile must define a HEALTHCHECK"
    assert "python:3.11-slim" in df_content, "Dockerfile must use python:3.11-slim base image"

    # Verify .dockerignore: Excludes sensitive files
    di_content = dockerignore_path.read_text(encoding="utf-8")
    assert ".env" in di_content, ".dockerignore must exclude .env"
    assert "*.db" in di_content, ".dockerignore must exclude SQLite db files"

    # Verify docker-compose.yml: backend and demo-api services, shared network, volume
    compose_content = compose_path.read_text(encoding="utf-8")
    assert "backend:" in compose_content, "Compose must define backend service"
    assert "demo-api:" in compose_content, "Compose must define demo-api service"
    assert "sentinel_data:" in compose_content, "Compose must declare sentinel_data volume"
    assert "sentinel_net:" in compose_content, "Compose must declare isolated sentinel_net bridge network"
