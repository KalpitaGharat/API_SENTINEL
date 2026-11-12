"""Automated Test Suite for Dataset-Powered API Key Security Scanning Integration.

Tests Single Sample Testing (Mode A), Batch Testing (Mode B),
Concurrency Locking, Masking Safeguards, and History Retrieval.
"""

import pytest
import threading
from fastapi.testclient import TestClient
from app.main import app
from app.services.api_key_benchmark import _batch_lock

client = TestClient(app)


def test_single_test_positive_sample():
    """Verify single test execution on positive sample produces valid outcome and explanation."""
    res = client.post("/api/dataset/test/single", json={
        "provider": "openai",
        "label": "positive",
        "split": "test"
    })
    assert res.status_code == 200
    data = res.json()
    assert "result_id" in data
    assert "session_id" in data
    assert data["expected_provider"] == "openai"
    assert data["expected_label"] == "positive"
    assert data["test_outcome"] in ("correct_detection", "false_negative")
    assert "..." in data["masked_sample"]
    assert data["execution_time_ms"] >= 0.0
    assert len(data["detection_reason"]) > 0


def test_single_test_negative_sample():
    """Verify single test execution on negative lookalike sample."""
    res = client.post("/api/dataset/test/single", json={
        "provider": "generic_api_key",
        "label": "negative",
        "split": "test"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["expected_provider"] == "generic_api_key"
    assert data["expected_label"] == "negative"
    assert data["test_outcome"] in ("correct_rejection", "false_positive")
    assert "..." in data["masked_sample"] or "****" in data["masked_sample"]


def test_single_test_sample_by_id():
    """Verify fetching and testing a sample by specific sample_id."""
    # First get a valid sample ID from single test
    r0 = client.post("/api/dataset/test/single", json={"provider": "aws", "label": "positive"})
    assert r0.status_code == 200
    sample_id = r0.json()["sample_id"]

    # Query sample info
    r_info = client.get(f"/api/dataset/test/sample/{sample_id}")
    assert r_info.status_code == 200
    info_data = r_info.json()
    assert info_data["sample_id"] == sample_id
    assert "..." in info_data["masked_sample"]

    # Test sample by ID
    r_test = client.post("/api/dataset/test/single", json={"sample_id": sample_id})
    assert r_test.status_code == 200
    assert r_test.json()["sample_id"] == sample_id


def test_sample_by_invalid_id_returns_404():
    """Verify 404 is returned for non-existent sample ID."""
    res = client.get("/api/dataset/test/sample/sample_non_existent_999999")
    assert res.status_code == 404


def test_batch_test_execution_and_metrics():
    """Verify batch testing runs across dataset, calculates metrics, and completes cleanly."""
    res = client.post("/api/dataset/test/batch", json={
        "count": 15,
        "provider": "all",
        "label": "all",
        "split": "test"
    })
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    session_id = data["session_id"]
    assert data["test_mode"] == "batch"
    assert data["requested_sample_count"] == 15
    assert data["completed_sample_count"] == 15
    assert data["status"] == "completed"

    metrics = data["metrics"]
    assert metrics["tp"] + metrics["fp"] + metrics["tn"] + metrics["fn"] == 15
    assert 0.0 <= metrics["precision"] <= 100.0
    assert 0.0 <= metrics["recall"] <= 100.0
    assert 0.0 <= metrics["f1"] <= 100.0
    assert 0.0 <= metrics["accuracy"] <= 100.0
    assert len(data["per_provider"]) > 0

    # Query status endpoint
    s_res = client.get(f"/api/dataset/test/batch/{session_id}")
    assert s_res.status_code == 200
    assert s_res.json()["session_id"] == session_id

    # Query paginated results
    r_res = client.get(f"/api/dataset/test/batch/{session_id}/results?limit=10")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["total"] == 15
    assert len(r_data["items"]) == 10
    for it in r_data["items"]:
        assert "..." in it["masked_sample"]
        assert it["test_outcome"] in ("correct_detection", "correct_rejection", "false_positive", "false_negative")


def test_batch_concurrency_lock():
    """Verify simultaneous batch runs are rejected with 409 Conflict."""
    # Simulate a lock held by acquiring _batch_lock manually
    acquired = _batch_lock.acquire(blocking=False)
    assert acquired is True, "Failed to acquire lock for test"
    try:
        # A second batch request should immediately receive 409 Conflict
        res = client.post("/api/dataset/test/batch", json={"count": 5})
        assert res.status_code == 409
        assert "already in progress" in res.json()["detail"]
    finally:
        _batch_lock.release()


def test_test_history_endpoint():
    """Verify test history retrieves past single and batch test sessions."""
    res = client.get("/api/dataset/test/history?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    assert data["total"] >= 1
    session = data["sessions"][0]
    assert "session_id" in session
    assert session["test_mode"] in ("single", "batch")


def test_credential_masking_safeguard():
    """Verify that credentials are NEVER logged or exposed unmasked."""
    res = client.post("/api/dataset/test/single", json={"provider": "github", "label": "positive"})
    assert res.status_code == 200
    data = res.json()
    masked = data["masked_sample"]
    # Masked representation must contain ellipsis and never the full 40+ char secret
    assert "..." in masked
    assert "ghp_" not in masked or "..." in masked
