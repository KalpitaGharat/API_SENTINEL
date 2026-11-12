# API Sentinel — Dataset Source Attribution & Licensing

## 1. Upstream Sources & Licensing

The API Key Detection Dataset utilizes three distinct sources adhering strictly to licensing, fair evaluation usage, and data privacy principles:

### Source 1: Nightfall AI Sample Dataset
- **Upstream Resource**: [Nightfall AI Policy Templates & Sample Data](https://help.nightfall.ai/nightfall_policy_templates/sample_data)
- **License**: Nightfall AI De-identified Evaluation Data
- **Usage Scope**: Sample evaluation snippets for API key detection benchmarking and negative lookalikes.
- **Attribution Notice**: Sample data originated from Nightfall AI's public DLP policy templates and evaluation packages.
- **Quarantine Action**: Upstream files containing active-labeled tokens (e.g., `api_key--aws_ACTIVE.txt`) were quarantined immediately; raw unredacted credential strings are excluded from the distributable dataset.

### Source 2: GitHub Supported Secret Scanning Patterns
- **Upstream Resource**: [GitHub Secret Scanning Partner Documentation](https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns)
- **License**: CC BY 4.0 (GitHub Documentation)
- **Usage Scope**: Structural format rules, token lengths, character sets, and documented regex patterns for AWS, OpenAI, NVIDIA, GitHub, Google Cloud, Stripe, Azure, Slack, and Twilio.
- **Attribution Notice**: Regular expression signatures and token format specifications are attributed to the GitHub Secret Scanning Partner Pattern Catalog.

### Source 3: API Sentinel Synthetic Generator
- **Generation Method**: Deterministic pseudo-random generation using Python's `random.Random(42)`.
- **License**: Internal Synthetic Dataset (API Sentinel Evaluation License).
- **Scope**: 9,994 unique, deliberately nonfunctional positive and negative samples crafted with realistic context wrappers (JSON, YAML, env vars, HTTP headers, code snippets).
- **Attribution Notice**: Generated locally; no live secrets, credentials, or private keys were utilized.

---

## 2. Source Attribution Summary Table

| Source | Samples in Master | License / Terms | Scope |
|---|---:|---|---|
| **Nightfall AI** | 6 (sanitized) | De-identified Evaluation Data | Code snippets & negative lookalikes |
| **GitHub Secret Patterns** | N/A (Rules) | CC BY 4.0 Documentation | Provider regex & format specifications |
| **API Sentinel Synthetic** | 9,994 | API Sentinel Evaluation License | Balanced synthetic positive & negative records |
| **TOTAL ACCEPTED** | **10,000** | — | Cleaned, validated, non-duplicate records |
