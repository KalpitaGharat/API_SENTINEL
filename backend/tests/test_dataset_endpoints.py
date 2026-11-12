"""Automated Test Suite for FastAPI Dataset Endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_dataset_overview():
    """Test GET /api/dataset/overview."""
    res = client.get("/api/dataset/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_samples"] == 10000
    assert data["positive_samples"] == 5000
    assert data["negative_samples"] == 5000
    assert data["synthetic_samples"] >= 9900
    assert data["provider_count"] == 10


def test_get_dataset_providers():
    """Test GET /api/dataset/providers."""
    res = client.get("/api/dataset/providers")
    assert res.status_code == 200
    data = res.json()
    assert data["total_providers"] == 10
    assert len(data["providers"]) == 10
    p_names = [p["provider"] for p in data["providers"]]
    assert "aws" in p_names
    assert "openai" in p_names
    assert "nvidia" in p_names


def test_get_dataset_statistics():
    """Test GET /api/dataset/statistics."""
    res = client.get("/api/dataset/statistics")
    assert res.status_code == 200
    data = res.json()
    assert "cleaning_report" in data
    assert "splits" in data
    assert "licensing" in data


def test_get_benchmark_and_run():
    """Test GET /api/dataset/benchmark and POST /api/dataset/benchmark/run."""
    # GET
    res_get = client.get("/api/dataset/benchmark")
    assert res_get.status_code == 200
    b_data = res_get.json()
    assert "metrics" in b_data
    assert "precision" in b_data["metrics"]

    # POST run
    res_post = client.post("/api/dataset/benchmark/run")
    assert res_post.status_code == 200
    post_data = res_post.json()
    assert "benchmark_id" in post_data
    assert post_data["total_samples"] == 1500


def test_get_benchmark_history():
    """Test GET /api/dataset/benchmark/history."""
    res = client.get("/api/dataset/benchmark/history")
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    assert len(history) >= 1


def test_get_dataset_samples_pagination_and_masking():
    """Test GET /api/dataset/samples with pagination, provider filter, and masking."""
    # 1. Basic pagination
    res = client.get("/api/dataset/samples?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["limit"] == 10
    assert len(data["items"]) == 10
    for item in data["items"]:
        # Verify credential masking
        assert "..." in item["masked_sample"] or "****" in item["masked_sample"]
        assert item["label"] in ("positive", "negative")

    # 2. Filter by provider
    res_prov = client.get("/api/dataset/samples?provider=openai&limit=5")
    assert res_prov.status_code == 200
    prov_data = res_prov.json()
    assert len(prov_data["items"]) == 5
    for item in prov_data["items"]:
        assert item["provider"] == "openai"

    # 3. Filter by label
    res_lbl = client.get("/api/dataset/samples?label=positive&limit=5")
    assert res_lbl.status_code == 200
    lbl_data = res_lbl.json()
    for item in lbl_data["items"]:
        assert item["label"] == "positive"
