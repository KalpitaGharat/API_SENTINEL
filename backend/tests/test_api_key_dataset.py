"""Automated Test Suite for API Key Dataset Generation, Validation & Splits."""

import os
import json
import hashlib
import pytest

DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset"))
SPLITS_DIR = os.path.join(DATASET_DIR, "splits")
METADATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "metadata"))

REQUIRED_FIELDS = [
    "sample_id", "sample", "provider", "key_type", "label",
    "is_synthetic", "format_valid", "source", "source_reference",
    "license", "notes"
]

EXPECTED_PROVIDERS = {
    "aws", "openai", "nvidia", "github", "google_cloud",
    "stripe", "azure", "slack", "twilio", "generic_api_key"
}


def test_master_dataset_exists_and_schema_valid():
    """Verify api_keys_master.jsonl exists and strictly satisfies normalized schema."""
    master_path = os.path.join(DATASET_DIR, "api_keys_master.jsonl")
    assert os.path.exists(master_path), f"Master dataset not found at {master_path}"

    count = 0
    with open(master_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            count += 1
            rec = json.loads(line)

            # Check all required fields present and non-empty
            for field in REQUIRED_FIELDS:
                assert field in rec, f"Missing field '{field}' at line {line_num}"
                assert rec[field] is not None, f"Field '{field}' is None at line {line_num}"

            # Validate enum types
            assert rec["label"] in ("positive", "negative"), f"Invalid label at line {line_num}: {rec['label']}"
            assert rec["key_type"] in ("api_key", "api_token"), f"Invalid key_type at line {line_num}: {rec['key_type']}"
            assert isinstance(rec["is_synthetic"], bool), f"is_synthetic not bool at line {line_num}"
            assert isinstance(rec["format_valid"], bool), f"format_valid not bool at line {line_num}"
            assert rec["provider"] in EXPECTED_PROVIDERS, f"Unexpected provider at line {line_num}: {rec['provider']}"

    assert count == 10000, f"Expected exactly 10,000 samples, got {count}"


def test_no_duplicate_samples_in_master():
    """Verify zero duplicate sample strings exist in master dataset."""
    master_path = os.path.join(DATASET_DIR, "api_keys_master.jsonl")
    seen_hashes = set()
    duplicates = 0

    with open(master_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            h = hashlib.sha256(rec["sample"].strip().encode("utf-8")).hexdigest()
            if h in seen_hashes:
                duplicates += 1
            seen_hashes.add(h)

    assert duplicates == 0, f"Found {duplicates} duplicate samples in master dataset!"


def test_positive_and_negative_class_balance():
    """Verify exact 50/50 balance between positive API keys and hard negative lookalikes."""
    master_path = os.path.join(DATASET_DIR, "api_keys_master.jsonl")
    pos_count = 0
    neg_count = 0
    provider_counts = {p: {"pos": 0, "neg": 0} for p in EXPECTED_PROVIDERS}

    with open(master_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            p = rec["provider"]
            if rec["label"] == "positive":
                pos_count += 1
                provider_counts[p]["pos"] += 1
            else:
                neg_count += 1
                provider_counts[p]["neg"] += 1

    assert pos_count == 5000, f"Expected 5,000 positive samples, got {pos_count}"
    assert neg_count == 5000, f"Expected 5,000 negative samples, got {neg_count}"

    # Verify each provider has 1,000 samples (500 pos, 500 neg)
    for p, c in provider_counts.items():
        assert c["pos"] == 500, f"Provider {p} pos count != 500: {c['pos']}"
        assert c["neg"] == 500, f"Provider {p} neg count != 500: {c['neg']}"


def test_splits_and_leakage_prevention():
    """Verify 70/15/15 splits exist with zero sample leakage across splits."""
    train_path = os.path.join(SPLITS_DIR, "api_keys_train.jsonl")
    val_path = os.path.join(SPLITS_DIR, "api_keys_validation.jsonl")
    test_path = os.path.join(SPLITS_DIR, "api_keys_test.jsonl")

    assert os.path.exists(train_path), "Train split missing"
    assert os.path.exists(val_path), "Validation split missing"
    assert os.path.exists(test_path), "Test split missing"

    def load_hashes(path):
        hashes = set()
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
                    rec = json.loads(line)
                    h = hashlib.sha256(rec["sample"].strip().encode("utf-8")).hexdigest()
                    hashes.add(h)
        return count, hashes

    train_count, train_hashes = load_hashes(train_path)
    val_count, val_hashes = load_hashes(val_path)
    test_count, test_hashes = load_hashes(test_path)

    assert train_count == 7000, f"Expected 7,000 in train, got {train_count}"
    assert val_count == 1500, f"Expected 1,500 in validation, got {val_count}"
    assert test_count == 1500, f"Expected 1,500 in test, got {test_count}"

    # Verify zero leakage / zero set intersection
    train_val_overlap = train_hashes.intersection(val_hashes)
    assert len(train_val_overlap) == 0, f"Train and Validation overlap by {len(train_val_overlap)} samples!"

    train_test_overlap = train_hashes.intersection(test_hashes)
    assert len(train_test_overlap) == 0, f"Train and Test overlap by {len(train_test_overlap)} samples!"

    val_test_overlap = val_hashes.intersection(test_hashes)
    assert len(val_test_overlap) == 0, f"Validation and Test overlap by {len(val_test_overlap)} samples!"


def test_quarantined_credentials_isolated():
    """Verify active upstream credentials are quarantined and not present in raw distributable files."""
    quarantine_path = os.path.join(METADATA_DIR, "quarantine_report.json")
    assert os.path.exists(quarantine_path), "Quarantine report missing"

    with open(quarantine_path, "r", encoding="utf-8") as f:
        q_data = json.load(f)

    assert q_data["verified_clean"] is True
    assert len(q_data["quarantined_items"]) >= 1

    # Ensure raw active token from Nightfall is NOT in master dataset
    master_path = os.path.join(DATASET_DIR, "api_keys_master.jsonl")
    with open(master_path, "r", encoding="utf-8") as f:
        master_content = f.read()

    # Raw unredacted token from Nightfall active test file
    assert "AKIA2OGYBAH6UREMKH4Q" not in master_content, "Raw quarantined AWS token found in master dataset!"
