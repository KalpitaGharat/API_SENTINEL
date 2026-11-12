"""Automated Test Suite for API Key Detection Benchmark Service."""

import pytest
from app.services.api_key_benchmark import (
    ApiKeyDetectionEngine,
    ApiKeyBenchmarkService,
    mask_credential,
    shannon_entropy,
)


def test_detection_engine_positives():
    """Verify detection engine identifies valid provider patterns."""
    cases = [
        ("export AWS_ACCESS_KEY_ID='AKIA_MOCK_IOSFODNN7EXAMPL9'", "aws"),
        ("const key = 'sk-mock-abc123def456ghi789jkl012mno345pqr678stu901vwx';", "openai"),
        ("nvapi-mock-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", "nvidia"),
        ("ghp_mock_1234567890abcdefghijklmnopqrstuvwxyz", "github"),
        ("AIza_MOCK_1234567890abcdefghijklmnopqrstuv", "google_cloud"),
        ("sk_test_mock_1234567890abcdefghijklmn", "stripe"),
        ("AccountKey=abcdefghijklmnopqrstuvwxyz0123456789+/abcdefghijklmnopqrstuvwxyz0123456789+/abcdefgh==", "azure"),
        ("xoxb-mock-123456789012-1234567890123-abcdefghijklmnopqrstuvwx", "slack"),
        ("SK_MOCK_1234567890abcdef1234567890abcdef", "twilio"),
    ]

    for sample, expected_provider in cases:
        result = ApiKeyDetectionEngine.detect(sample)
        assert result is not None, f"Failed to detect positive sample: {sample}"
        provider, token = result
        assert provider == expected_provider, f"Expected {expected_provider}, got {provider} for {sample}"


def test_detection_engine_negatives():
    """Verify negative lookalikes, placeholders, and UUIDs are rejected."""
    negatives = [
        "d3b07384-d113-46ec-9cdb-1e7fffe50fba",
        "AKIAIOSFODNN7EXAMPLE",  # Placeholder
        "sk-proj-YOUR_API_KEY_HERE_1234567890",  # Placeholder
        "YOUR_AWS_ACCESS_KEY_ID",
        "ghp_YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE",
        "class='btn-primary-action'",
        "https://cdn.example.com/assets/img/icon-32.png",
        "const OPENAI_API_KEY_ENV_NAME = 'OPENAI_API_KEY';",
        "c3fa6cfd12b5a0d51e9cfe1ae83ad1065221fdec5f89bfdaaff51076140cd",  # sha256
    ]

    for neg in negatives:
        result = ApiKeyDetectionEngine.detect(neg)
        assert result is None, f"False positive triggered for negative sample: {neg}"


def test_benchmark_runner_and_formulas():
    """Verify benchmark service executes against test split and calculates metrics correctly."""
    res = ApiKeyBenchmarkService.run_benchmark()

    assert "benchmark_id" in res
    assert "timestamp" in res
    assert "metrics" in res
    assert "per_provider" in res
    assert res["total_samples"] == 1500

    metrics = res["metrics"]
    tp = metrics["tp"]
    fp = metrics["fp"]
    tn = metrics["tn"]
    fn = metrics["fn"]

    assert tp + fp + tn + fn == 1500

    # Test formula calculations
    expected_prec = round((tp / (tp + fp)) * 100, 2)
    expected_rec = round((tp / (tp + fn)) * 100, 2)
    expected_f1 = round((2 * (expected_prec * expected_rec) / (expected_prec + expected_rec)), 2)
    expected_acc = round(((tp + tn) / 1500) * 100, 2)

    assert metrics["precision"] == expected_prec
    assert metrics["recall"] == expected_rec
    assert metrics["f1"] == expected_f1
    assert metrics["accuracy"] == expected_acc

    # Per-provider counts
    assert len(res["per_provider"]) == 10


def test_mask_credential():
    """Verify credentials are safely masked."""
    assert mask_credential("sk-proj-1234567890abcdefghijklmnopqrstuvwxyz") == "sk-proj-...wxyz"
    assert mask_credential("nvapi-1234567890abcdef1234567890abcdef") == "nvapi-...cdef"
    assert mask_credential("ghp_1234567890abcdef") == "ghp_...cdef"
    assert mask_credential("short") == "****"
    assert mask_credential("AKIA1234567890ABCDEF") == "AKIA...CDEF"


def test_shannon_entropy():
    """Verify Shannon entropy computation."""
    assert shannon_entropy("") == 0.0
    assert shannon_entropy("aaaaaa") == 0.0
    # High entropy random string
    h = shannon_entropy("abcdefghijklmnopqrstuvwxyz0123456789")
    assert h > 4.5
