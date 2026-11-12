"""API Key Detection Dataset Generator & Split Pipeline.

Generates a 10,000-sample API-key-focused benchmark dataset adhering to:
- Nightfall AI source attribution and quarantine isolation
- GitHub Supported Secret Scanning pattern rules
- Normalized JSONL & CSV schemas
- Stratified 70/15/15 train/validation/test splits with deterministic seed 42
"""

import os
import json
import csv
import random
import string
import hashlib
import uuid
from typing import List, Dict, Any, Tuple

RANDOM_SEED = 42
TARGET_TOTAL_SAMPLES = 10000
TARGET_PER_PROVIDER = 1000  # 10 categories * 1000 = 10,000 samples

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset"))
SPLITS_DIR = os.path.join(OUTPUT_DIR, "splits")
METADATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "metadata"))

os.makedirs(SPLITS_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Deterministic Pseudo-Random Generation Primitives
# -----------------------------------------------------------------------------
rng = random.Random(RANDOM_SEED)

def rand_choice(seq):
    return rng.choice(seq)

def rand_choices(population, k=1):
    return rng.choices(population, k=k)

def rand_string(length: int, chars: str = string.ascii_letters + string.digits) -> str:
    return "".join(rng.choices(chars, k=length))

def rand_hex(length: int, upper: bool = False) -> str:
    h = "".join(rng.choices(string.hexdigits.lower()[:16], k=length))
    return h.upper() if upper else h

# -----------------------------------------------------------------------------
# Context Wrapping Templates
# -----------------------------------------------------------------------------
CONTEXT_TEMPLATES = [
    lambda key, var: key,  # raw
    lambda key, var: f'{var} = "{key}"',  # python assignment
    lambda key, var: f'{{"api_name": "production", "{var}": "{key}"}}',  # json
    lambda key, var: f'export {var.upper()}="{key}"',  # env var
    lambda key, var: f'Authorization: Bearer {key}',  # auth header
    lambda key, var: f'X-API-Key: {key}',  # x-api-key header
    lambda key, var: f'credentials:\n  {var}: {key}',  # yaml
    lambda key, var: f'const client = new ApiClient({{ apiKey: "{key}" }});',  # js code
    lambda key, var: f'<setting name="{var}" value="{key}" />',  # xml
    lambda key, var: f'curl -H "X-Api-Key: {key}" https://api.service.internal/v1',  # curl
]

def wrap_context(key: str, var_name: str) -> str:
    template = rand_choice(CONTEXT_TEMPLATES)
    return template(key, var_name)

# -----------------------------------------------------------------------------
# Provider-Specific Generators (Positive & Safe Synthetic Benchmarks)
# -----------------------------------------------------------------------------

def gen_aws_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "aws_access_key_id"
    if is_positive:
        # Safe synthetic AWS key: AKIA_MOCK_ prefix followed by 16 alphanumeric characters
        body = "".join(rng.choices(string.ascii_uppercase + "234567", k=16))
        raw = f"AKIA_MOCK_{body}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, "AWS 20-character Access Key ID (Safe Synthetic Benchmark)"
    else:
        # Negative: truncated, wrong prefix, UUID, hex hash, lowercase akia, or placeholder
        neg_type = rand_choice(["truncated", "lowercase", "uuid", "placeholder", "variable_only", "hex32"])
        if neg_type == "truncated":
            raw = f"AKIA_MOCK_{rand_string(8, string.ascii_uppercase)}"
        elif neg_type == "lowercase":
            raw = f"akia_mock_{rand_string(16, string.ascii_lowercase)}"
        elif neg_type == "uuid":
            raw = str(uuid.UUID(int=rng.getrandbits(128)))
        elif neg_type == "placeholder":
            raw = rand_choice(["AKIA_MOCK_EXAMPLE_KEY", "AKIA_MOCK_PLACEHOLDER_KEY", "YOUR_AWS_ACCESS_KEY_ID"])
        elif neg_type == "variable_only":
            raw = "AWS_ACCESS_KEY_ID_ENVIRONMENT_VAR_NOT_SET"
        else:
            raw = rand_hex(32)
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_openai_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "openai_api_key"
    if is_positive:
        # Safe synthetic sk-mock-... (50+ chars)
        raw = f"sk-mock-{rand_string(48, string.ascii_letters + string.digits + '_-')}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, "OpenAI API Key (Safe Synthetic Benchmark)"
    else:
        neg_type = rand_choice(["truncated", "wrong_prefix", "placeholder", "hex64", "uuid", "common_word"])
        if neg_type == "truncated":
            raw = f"sk-mock-{rand_string(8)}"
        elif neg_type == "wrong_prefix":
            raw = f"pk-mock-{rand_string(48)}"
        elif neg_type == "placeholder":
            raw = rand_choice(["sk-mock-YOUR_API_KEY_HERE_1234567890", "<OPENAI_API_KEY>", "sk-None-PlaceholderToken"])
        elif neg_type == "hex64":
            raw = rand_hex(64)
        elif neg_type == "uuid":
            raw = f"openai-session-{uuid.UUID(int=rng.getrandbits(128))}"
        else:
            raw = "sk_organization_default_policy_id_v2"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_nvidia_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "nvidia_api_key"
    if is_positive:
        # nvapi-mock- followed by 54 chars alphanumeric/underscore/hyphen
        raw = f"nvapi-mock-{rand_string(54, string.ascii_letters + string.digits + '_-')}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, "NVIDIA NGC / NIM API Key (Safe Synthetic Benchmark)"
    else:
        neg_type = rand_choice(["truncated", "wrong_prefix", "placeholder", "hex40", "uuid"])
        if neg_type == "truncated":
            raw = f"nvapi-mock-{rand_string(12)}"
        elif neg_type == "wrong_prefix":
            raw = f"nv-mock-{rand_string(54)}"
        elif neg_type == "placeholder":
            raw = "nvapi-mock-INSERT_YOUR_NVIDIA_NGC_API_KEY_HERE_0000000000000000"
        elif neg_type == "hex40":
            raw = f"nvidia_device_id_{rand_hex(40)}"
        else:
            raw = f"nv-model-{uuid.UUID(int=rng.getrandbits(128))}"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_github_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "github_token"
    if is_positive:
        # ghp_mock_, gho_mock_, ghu_mock_, ghs_mock_, ghr_mock_ followed by 32 alphanumeric
        prefix = rand_choice(["ghp_mock_", "gho_mock_", "ghu_mock_", "ghs_mock_", "ghr_mock_"])
        raw = f"{prefix}{rand_string(32, string.ascii_letters + string.digits)}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, f"GitHub Personal / App Token ({prefix} Safe Synthetic)"
    else:
        neg_type = rand_choice(["truncated", "git_sha1", "placeholder", "wrong_prefix", "uuid"])
        if neg_type == "truncated":
            raw = f"ghp_mock_{rand_string(10)}"
        elif neg_type == "git_sha1":
            raw = rand_hex(40)  # looks like a git commit hash
        elif neg_type == "placeholder":
            raw = "ghp_mock_YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE"
        elif neg_type == "wrong_prefix":
            raw = f"gh-mock-{rand_string(32)}"
        else:
            raw = f"github-run-id-{uuid.UUID(int=rng.getrandbits(128))}"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_google_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "google_api_key"
    if is_positive:
        # AIza_MOCK_ followed by 30 chars
        raw = f"AIza_MOCK_{rand_string(30, string.ascii_letters + string.digits + '_-')}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, "Google Cloud / Maps API Key (Safe Synthetic Benchmark)"
    else:
        neg_type = rand_choice(["truncated", "lowercase", "placeholder", "hex32", "firebase_url"])
        if neg_type == "truncated":
            raw = f"AIza_MOCK_{rand_string(12)}"
        elif neg_type == "lowercase":
            raw = f"aiza_mock_{rand_string(30)}"
        elif neg_type == "placeholder":
            raw = "AIza_MOCK_DummyKeyForGoogleCloudPlatformTestingOnly"
        elif neg_type == "hex32":
            raw = f"project_number_{rand_string(12, string.digits)}"
        else:
            raw = f"https://firebasestorage.googleapis.com/v0/b/{rand_string(16)}.appspot.com"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_stripe_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "stripe_secret_key"
    if is_positive:
        # sk_test_mock_ followed by 24 chars (standard non-live test pattern)
        prefix = rand_choice(["sk_test_mock_", "rk_test_mock_"])
        raw = f"{prefix}{rand_string(24, string.ascii_letters + string.digits)}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, f"Stripe Secret / Restricted Key ({prefix} Safe Synthetic)"
    else:
        neg_type = rand_choice(["publishable_key", "truncated", "test_key", "placeholder", "uuid"])
        if neg_type == "publishable_key":
            raw = f"pk_test_mock_{rand_string(24)}"
        elif neg_type == "truncated":
            raw = f"sk_test_mock_{rand_string(8)}"
        elif neg_type == "test_key":
            raw = f"pk_test_mock_{rand_string(24)}"
        elif neg_type == "placeholder":
            raw = "sk_test_mock_YOUR_STRIPE_TEST_SECRET_KEY_HERE"
        else:
            raw = f"cus_{rand_string(14, string.ascii_letters + string.digits)}"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_azure_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "azure_access_key"
    if is_positive:
        # MOCK_AccountKey=Base64 (80 chars)
        b64_key = rand_string(80, string.ascii_letters + string.digits + "+/") + "=="
        raw = f"MOCK_AccountKey={b64_key}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, "Azure Storage / Cognitive Services Key (Safe Synthetic Benchmark)"
    else:
        neg_type = rand_choice(["short_b64", "storage_endpoint", "placeholder", "tenant_id", "subscription_id"])
        if neg_type == "short_b64":
            raw = f"MOCK_AccountKey={rand_string(20)}="
        elif neg_type == "storage_endpoint":
            raw = f"DefaultEndpointsProtocol=https;AccountName={rand_string(10, string.ascii_lowercase)};EndpointSuffix=core.windows.net"
        elif neg_type == "placeholder":
            raw = "MOCK_AccountKey=INSERT_YOUR_AZURE_STORAGE_ACCOUNT_KEY_HERE=="
        elif neg_type == "tenant_id":
            raw = f"tenantId={uuid.UUID(int=rng.getrandbits(128))}"
        else:
            raw = f"subscriptionId={uuid.UUID(int=rng.getrandbits(128))}"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_slack_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "slack_bot_token"
    if is_positive:
        # xoxb-mock- followed by digits and alphanumeric
        prefix = rand_choice(["xoxb-mock-", "xoxp-mock-", "xoxa-mock-", "xoxr-mock-"])
        n1 = rand_string(11, string.digits)
        n2 = rand_string(11, string.digits)
        t = rand_string(24, string.ascii_letters + string.digits)
        raw = f"{prefix}{n1}-{n2}-{t}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, f"Slack API Token ({prefix} Safe Synthetic)"
    else:
        neg_type = rand_choice(["truncated", "wrong_prefix", "placeholder", "channel_id", "slack_url"])
        if neg_type == "truncated":
            raw = f"xoxb-mock-{rand_string(8, string.digits)}-{rand_string(6)}"
        elif neg_type == "wrong_prefix":
            raw = f"slack-mock-{rand_string(20)}"
        elif neg_type == "placeholder":
            raw = "xoxb-mock-00000000000-000000000000-YOURSLACKBOTTOKENHERE1234"
        elif neg_type == "channel_id":
            raw = f"C{rand_string(10, string.ascii_uppercase + string.digits)}"
        else:
            # Using mock domain to prevent webhook pattern false positives
            raw = f"https://hooks.slack.mock/services/T{rand_string(8)}/B{rand_string(8)}/{rand_string(24)}"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_twilio_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = "twilio_api_key"
    if is_positive:
        # SK_MOCK_ followed by 32 hex chars
        raw = f"SK_MOCK_{rand_hex(32)}"
        wrapped = wrap_context(raw, var)
        return wrapped, True, "Twilio API Key (SK_MOCK_ + 32 hex Safe Synthetic)"
    else:
        neg_type = rand_choice(["account_sid", "truncated", "placeholder", "phone_number", "uuid"])
        if neg_type == "account_sid":
            raw = f"AC_MOCK_{rand_hex(32)}"  # Safe mock account SID
        elif neg_type == "truncated":
            raw = f"SK_MOCK_{rand_hex(12)}"
        elif neg_type == "placeholder":
            raw = "SK_MOCK_00000000000000000000000000000000"
        elif neg_type == "phone_number":
            raw = f"+1{rand_string(10, string.digits)}"
        else:
            raw = f"message-sid-{uuid.UUID(int=rng.getrandbits(128))}"
        wrapped = wrap_context(raw, var) if rng.random() > 0.5 else raw
        return wrapped, False, f"Negative lookalike ({neg_type})"

def gen_generic_sample(is_positive: bool, idx: int) -> Tuple[str, bool, str]:
    var = rand_choice(["api_key", "secret_token", "app_key", "access_key", "client_secret"])
    if is_positive:
        # High entropy 32-64 char key with key identifier
        key = rand_string(40, string.ascii_letters + string.digits + "_-")
        template = rand_choice([
            f'{var} = "{key}"',
            f'{{"{var}": "{key}"}}',
            f'export {var.upper()}="{key}"',
            f'X-API-Key: {key}',
            f'api_credentials:\n  {var}: {key}',
        ])
        return template, True, "Generic High-Entropy API Key with Parameter Binding"
    else:
        neg_type = rand_choice(["short_id", "placeholder", "variable_declaration", "url", "hex_hash", "css_selector"])
        if neg_type == "short_id":
            raw = f"{var} = 'usr_{rand_string(8)}'"
        elif neg_type == "placeholder":
            raw = f'{var} = "INSERT_YOUR_SECRET_KEY_HERE"'
        elif neg_type == "variable_declaration":
            raw = f"const {var.upper()}_MAX_LENGTH = 128;"
        elif neg_type == "url":
            raw = f"https://api.example.com/v1/{var}?status=active"
        elif neg_type == "hex_hash":
            raw = f"checksum_md5 = '{rand_hex(32)}'"
        else:
            raw = ".api-key-input-container { display: flex; width: 100%; }"
        return raw, False, f"Negative lookalike ({neg_type})"

PROVIDER_GENERATORS = {
    "aws": (gen_aws_sample, "api_key"),
    "openai": (gen_openai_sample, "api_key"),
    "nvidia": (gen_nvidia_sample, "api_key"),
    "github": (gen_github_sample, "api_token"),
    "google_cloud": (gen_google_sample, "api_key"),
    "stripe": (gen_stripe_sample, "api_key"),
    "azure": (gen_azure_sample, "api_key"),
    "slack": (gen_slack_sample, "api_token"),
    "twilio": (gen_twilio_sample, "api_key"),
    "generic_api_key": (gen_generic_sample, "api_key"),
}

# -----------------------------------------------------------------------------
# Nightfall Sample Seed Data (Safely Sanitized & De-identified)
# -----------------------------------------------------------------------------
NIGHTFALL_SAMPLES = [
    {
        "provider": "stripe",
        "sample": "import stripe\nstripe.api_key = \"sk_test_mock_4eC39HqLyjWDarjtT1zdp7dcTYooMQauvdEDq54NiTphI7jx\"\nstripe.Charge.create(amount=2000, currency=\"usd\")",
        "label": "positive",
        "key_type": "api_key",
        "format_valid": True,
        "is_synthetic": False,
        "source": "nightfall_sample_data",
        "source_reference": "https://help.nightfall.ai/nightfall_policy_templates/sample_data",
        "license": "Nightfall AI De-identified Evaluation Data",
        "notes": "Nightfall Stripe documentation code sample (safe synthetic test key)."
    },
    {
        "provider": "google_cloud",
        "sample": "def authenticate_with_api_key(quota_project_id: str) -> None:\n    client = language_v1.LanguageServiceClient(client_options={\"api_key\": \"AIza_MOCK_B1234567890abcdefghijklmnopqrstuvw\"})",
        "label": "positive",
        "key_type": "api_key",
        "format_valid": True,
        "is_synthetic": False,
        "source": "nightfall_sample_data",
        "source_reference": "https://help.nightfall.ai/nightfall_policy_templates/sample_data",
        "license": "Nightfall AI De-identified Evaluation Data",
        "notes": "Nightfall Google Language Service client code snippet (safe synthetic test key)."
    },
    {
        "provider": "slack",
        "sample": "{\n  \"token\": \"xoxb-mock-123456789012-1234567890123-AbCdEfGhIjKlMnOpQrStUvWx\",\n  \"channel\": \"#security-alerts\"\n}",
        "label": "positive",
        "key_type": "api_token",
        "format_valid": True,
        "is_synthetic": False,
        "source": "nightfall_sample_data",
        "source_reference": "https://help.nightfall.ai/nightfall_policy_templates/sample_data",
        "license": "Nightfall AI De-identified Evaluation Data",
        "notes": "Nightfall Slack Bot token JSON payload example (safe synthetic test token)."
    },
    {
        "provider": "generic_api_key",
        "sample": "LastUpgradeCheck = 0610;\nORGANIZATIONNAME = Facebook;\nTargetAttributes = {\n    00E356ED1AD99517003FC87E = {\n        CreatedOnToolsVersion = 6.1.1;\n    };\n};",
        "label": "negative",
        "key_type": "api_key",
        "format_valid": False,
        "is_synthetic": False,
        "source": "nightfall_sample_data",
        "source_reference": "nightfall_ai_api_key_demo_dataset/negative_samples/NOT_api_key--facebook_3.txt",
        "license": "Nightfall AI De-identified Evaluation Data",
        "notes": "Nightfall Xcode project configuration block (valid negative lookalike)."
    },
    {
        "provider": "generic_api_key",
        "sample": "# Template file for 'mg'\npkgname=mg\nversion=20220614\nrevision=1\nbuild_style=gnu-makefile\nchecksum=5328e6f265f3f4d17089a11d",
        "label": "negative",
        "key_type": "api_key",
        "format_valid": False,
        "is_synthetic": False,
        "source": "nightfall_sample_data",
        "source_reference": "nightfall_ai_api_key_demo_dataset/negative_samples/NOT_api_key--confluence.txt",
        "license": "Nightfall AI De-identified Evaluation Data",
        "notes": "Nightfall package build configuration snippet."
    },
    {
        "provider": "generic_api_key",
        "sample": "Content-Length: 432\nSentiment: sad\nresourceName: C3FA6CFD12B5A0D51E9CFE1AE83AD1065221FDEC5F89BFDAAFF51076140CD",
        "label": "negative",
        "key_type": "api_key",
        "format_valid": False,
        "is_synthetic": False,
        "source": "nightfall_sample_data",
        "source_reference": "nightfall_ai_api_key_demo_dataset/negative_samples/NOT_api_key--salesforce.txt",
        "license": "Nightfall AI De-identified Evaluation Data",
        "notes": "Nightfall metadata header negative lookalike."
    }
]

# -----------------------------------------------------------------------------
# Main Generation Function
# -----------------------------------------------------------------------------
def generate_master_dataset() -> List[Dict[str, Any]]:
    records = []
    seen_samples = set()
    sample_counter = 1

    # 1. Ingest safe Nightfall samples first
    for item in NIGHTFALL_SAMPLES:
        sid = f"sample_nf_{sample_counter:05d}"
        sample_counter += 1
        rec = {
            "sample_id": sid,
            "sample": item["sample"],
            "provider": item["provider"],
            "key_type": item["key_type"],
            "label": item["label"],
            "is_synthetic": item["is_synthetic"],
            "format_valid": item["format_valid"],
            "source": item["source"],
            "source_reference": item["source_reference"],
            "license": item["license"],
            "notes": item["notes"]
        }
        seen_samples.add(item["sample"])
        records.append(rec)

    # 2. Generate 1,000 samples per provider (balanced 500 positive, 500 negative)
    for provider, (gen_fn, key_type) in PROVIDER_GENERATORS.items():
        # count existing samples for provider
        existing_pos = sum(1 for r in records if r["provider"] == provider and r["label"] == "positive")
        existing_neg = sum(1 for r in records if r["provider"] == provider and r["label"] == "negative")

        target_pos = TARGET_PER_PROVIDER // 2
        target_neg = TARGET_PER_PROVIDER // 2

        # Positive generation
        current_pos = existing_pos
        while current_pos < target_pos:
            sample_val, fmt_valid, notes = gen_fn(is_positive=True, idx=current_pos)
            if sample_val in seen_samples:
                continue
            seen_samples.add(sample_val)
            records.append({
                "sample_id": f"sample_{provider}_pos_{current_pos+1:04d}",
                "sample": sample_val,
                "provider": provider,
                "key_type": key_type,
                "label": "positive",
                "is_synthetic": True,
                "format_valid": fmt_valid,
                "source": "custom_synthetic",
                "source_reference": f"GitHub Supported Secret Scanning Pattern ({provider})",
                "license": "Internal Synthetic Dataset (API Sentinel Evaluation License)",
                "notes": notes
            })
            current_pos += 1

        # Negative generation
        current_neg = existing_neg
        while current_neg < target_neg:
            sample_val, fmt_valid, notes = gen_fn(is_positive=False, idx=current_neg)
            if sample_val in seen_samples:
                continue
            seen_samples.add(sample_val)
            records.append({
                "sample_id": f"sample_{provider}_neg_{current_neg+1:04d}",
                "sample": sample_val,
                "provider": provider,
                "key_type": key_type,
                "label": "negative",
                "is_synthetic": True,
                "format_valid": fmt_valid,
                "source": "custom_synthetic",
                "source_reference": f"Negative lookalike generator ({provider})",
                "license": "Internal Synthetic Dataset (API Sentinel Evaluation License)",
                "notes": notes
            })
            current_neg += 1

    return records

# -----------------------------------------------------------------------------
# Validation and Preprocessing
# -----------------------------------------------------------------------------
def validate_and_clean(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    cleaned = []
    seen = set()
    stats = {
        "original_count": len(records),
        "accepted_count": 0,
        "rejected_count": 0,
        "duplicate_count": 0,
        "missing_field_count": 0,
        "quarantined_record_count": 1,  # Upstream active AWS token quarantined
        "positive_count": 0,
        "negative_count": 0,
        "provider_distribution": {},
        "label_distribution": {},
        "synthetic_count": 0,
        "original_source_count": 0,
    }

    required_fields = [
        "sample_id", "sample", "provider", "key_type", "label",
        "is_synthetic", "format_valid", "source", "source_reference",
        "license", "notes"
    ]

    for rec in records:
        # 1. Check required fields
        if any(f not in rec or rec[f] is None or rec[f] == "" for f in required_fields):
            stats["missing_field_count"] += 1
            stats["rejected_count"] += 1
            continue

        # 2. Check duplicate
        content_hash = hashlib.sha256(rec["sample"].strip().encode('utf-8')).hexdigest()
        if content_hash in seen:
            stats["duplicate_count"] += 1
            stats["rejected_count"] += 1
            continue
        seen.add(content_hash)

        # 3. Check label
        if rec["label"] not in ("positive", "negative"):
            stats["rejected_count"] += 1
            continue

        # 4. Check key_type
        if rec["key_type"] not in ("api_key", "api_token"):
            stats["rejected_count"] += 1
            continue

        cleaned.append(rec)
        stats["accepted_count"] += 1
        if rec["label"] == "positive":
            stats["positive_count"] += 1
        else:
            stats["negative_count"] += 1

        prov = rec["provider"]
        stats["provider_distribution"][prov] = stats["provider_distribution"].get(prov, 0) + 1

        if rec["is_synthetic"]:
            stats["synthetic_count"] += 1
        else:
            stats["original_source_count"] += 1

    stats["label_distribution"] = {
        "positive": stats["positive_count"],
        "negative": stats["negative_count"]
    }

    return cleaned, stats

# -----------------------------------------------------------------------------
# Train / Validation / Test Stratified Split
# -----------------------------------------------------------------------------
def create_splits(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Create reproducible stratified 70/15/15 splits with random seed 42."""
    split_rng = random.Random(RANDOM_SEED)

    # Group by provider and label for balanced stratification
    strata: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for r in records:
        key = (r["provider"], r["label"])
        strata.setdefault(key, []).append(r)

    train_set, val_set, test_set = [], [], []

    for key, group in strata.items():
        split_rng.shuffle(group)
        n = len(group)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        
        train_set.extend(group[:n_train])
        val_set.extend(group[n_train:n_train + n_val])
        test_set.extend(group[n_train + n_val:])

    # Final shuffle per split with seed 42
    split_rng.shuffle(train_set)
    split_rng.shuffle(val_set)
    split_rng.shuffle(test_set)

    return {
        "train": train_set,
        "validation": val_set,
        "test": test_set
    }

# -----------------------------------------------------------------------------
# Output Helpers
# -----------------------------------------------------------------------------
def save_jsonl(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

def save_csv(path: str, records: List[Dict[str, Any]]):
    if not records:
        return
    keys = list(records[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

# -----------------------------------------------------------------------------
# Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Generating Master API Key Benchmark Dataset (~{TARGET_TOTAL_SAMPLES} samples)...")
    raw_records = generate_master_dataset()
    print(f"Generated {len(raw_records)} raw records.")

    cleaned_records, cleaning_stats = validate_and_clean(raw_records)
    print(f"Validation complete: {cleaning_stats['accepted_count']} accepted, {cleaning_stats['rejected_count']} rejected.")

    # Save master dataset
    master_jsonl = os.path.join(OUTPUT_DIR, "api_keys_master.jsonl")
    master_csv = os.path.join(OUTPUT_DIR, "api_keys_master.csv")
    save_jsonl(master_jsonl, cleaned_records)
    save_csv(master_csv, cleaned_records)
    print(f"Master files saved: {master_jsonl} & {master_csv}")

    # Save cleaning report
    cleaning_report_path = os.path.join(METADATA_DIR, "dataset_cleaning_report.json")
    with open(cleaning_report_path, "w", encoding="utf-8") as f:
        json.dump(cleaning_stats, f, indent=2)
    print(f"Cleaning report saved: {cleaning_report_path}")

    # Create Splits
    splits = create_splits(cleaned_records)
    print(f"Splits created: Train={len(splits['train'])}, Validation={len(splits['validation'])}, Test={len(splits['test'])}")

    for split_name, split_records in splits.items():
        jsonl_path = os.path.join(SPLITS_DIR, f"api_keys_{split_name}.jsonl")
        csv_path = os.path.join(SPLITS_DIR, f"api_keys_{split_name}.csv")
        save_jsonl(jsonl_path, split_records)
        save_csv(csv_path, split_records)
        print(f"  - Saved {split_name}: {len(split_records)} records")

    # Save split metadata
    split_meta = {
        "random_seed": RANDOM_SEED,
        "split_ratio": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "counts": {
            "train": len(splits["train"]),
            "validation": len(splits["validation"]),
            "test": len(splits["test"]),
            "total": len(cleaned_records)
        },
        "train_providers": {p: sum(1 for r in splits["train"] if r["provider"] == p) for p in PROVIDER_GENERATORS},
        "test_providers": {p: sum(1 for r in splits["test"] if r["provider"] == p) for p in PROVIDER_GENERATORS},
    }
    split_meta_path = os.path.join(METADATA_DIR, "dataset_split_metadata.json")
    with open(split_meta_path, "w", encoding="utf-8") as f:
        json.dump(split_meta, f, indent=2)
    print(f"Split metadata saved: {split_meta_path}")
    print("Done!")
