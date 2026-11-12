# API Sentinel — Dataset Security & Zero-Live-Credential Compliance

## 1. Zero-Live-Credential Policy

API Sentinel adheres to a **Zero-Live-Credential Policy** across all dataset operations, benchmarking workflows, API endpoints, and user interfaces:

1. **No Real Leaked Credentials**:
   No real credentials leaked from public data breaches or external source code repositories are included.
2. **Deterministic Pseudo-Random Generation**:
   All synthetic keys are generated using deterministic pseudo-random sequences (`random.seed(42)`). They are syntactically well-formed to resemble provider formats, but mathematically nonfunctional.
3. **No Outbound Network Probing**:
   The engine does NOT perform outbound HTTP calls to third-party APIs (e.g., AWS, OpenAI, Stripe) to check whether keys authenticate. Pattern detection is pure syntax and entropy validation.
4. **Credential Redaction and Masking**:
   Any sensitive strings rendered in API responses (`GET /api/dataset/samples`) or displayed on the React and Streamlit dashboards are automatically masked:
   - OpenAI: `sk-proj-...1234`
   - AWS: `AKIA...5678`
   - NVIDIA: `nvapi-...abcd`
   - Stripe: `sk_live_...efgh`
   - GitHub: `ghp_...ijkl`

---

## 2. Nightfall Source Quarantine Architecture

During the reconnaissance phase of the Nightfall AI Demo Dataset, the file `api_key--aws_ACTIVE.txt` was identified with an explicit upstream label indicating an active AWS key.

In accordance with strict security requirements:
- The raw credential was **immediately quarantined**.
- The raw unredacted credential value was **excluded from Git and the distributable dataset**.
- A safe, nonfunctional synthetic replacement was substituted.
- The quarantine audit event was recorded in `metadata/quarantine_report.json`.
- The repository `.gitignore` was updated to prevent any `.quarantine` or quarantined files from being committed.

---

## 3. Safe Benchmark Interpretation

Users and evaluators must note:
- **Format Match vs. Account Access**: A positive match in the benchmark engine proves that a string matches the documented regular expression and entropy characteristics of an API key. It does NOT prove that the token has active permissions or valid account billing.
- **Air-Gapped Safety**: The benchmark runner operates completely offline and in-memory, making it safe for air-gapped CI/CD pipelines, classified evaluation environments, and educational laboratories.

---

## 4. Architectural Isolation & Storage Masking

### Complete Isolation from Live Security Scans
Dataset-powered API key testing is strictly decoupled from the live vulnerability scanning engine (Member 1's BOLA, SSRF, and authorization testing engine):
- Dataset tests operate solely on internal dataset JSONL slices.
- No HTTP probes, no network sockets, and no target URLs are touched during dataset evaluations.
- Production and demonstration API scan histories (`scans` and `findings` tables) remain entirely unaffected.

### Database Persistence Safeguards
When test sessions (Single Test or Batch Test) are persisted:
- **Strict Masking Before Write**: Raw sample text is never persisted. The backend invokes `mask_credential(sample_text)` prior to inserting into `dataset_test_results.masked_sample`.
- **Zero Log Exposure**: FastAPI logger and backend handlers never log unmasked credential strings.
- **Thread-Safe Concurrency**: `_batch_lock` guarantees that no conflicting batch sessions can execute concurrently, protecting both database integrity and CPU resources.

