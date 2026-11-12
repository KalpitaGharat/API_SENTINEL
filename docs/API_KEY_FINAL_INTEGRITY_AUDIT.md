# API Sentinel — Final Dataset Integrity & Benchmark Audit

**Project:** API Sentinel  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Git Branch:** `feature/api-key-dataset`  
**Audit Date:** 2026-11-11  
**Audit Standard:** Independent Code, Dataset & Protocol Verification  

---

## Executive Audit Summary

An independent audit was conducted on the API Key Detection Dataset and Benchmark Module on branch `feature/api-key-dataset`. The audit evaluated sample counts, data leakage risks, third-party licensing boundaries, detection benchmark independence, and frontend integration.

| Audit Area | Status | Key Finding |
|---|:---:|---|
| **1. Synthetic Sample Count** | **PASS** | Exactly 10,000 records: 9,994 synthetic (99.94%) and 6 de-identified Nightfall samples (0.06%). |
| **2. Data Leakage** | **PARTIAL** | Zero exact duplicate leakage between train and test splits (0 overlap). However, random sample-level splitting shares generative templates, limiting generalization claims to in-distribution evaluation. |
| **3. Nightfall Licensing** | **PARTIAL** | Upstream terms authorize DLP evaluation/testing, but lack an explicit open-source redistribution license. Active token properly quarantined. |
| **4. Benchmark Independence** | **PASS** | Detection engine processes sample text independently with zero access to ground-truth labels. Metrics calculated dynamically. |
| **5. Frontend Functionality** | **PASS** | Initial loading, provider filtering, label filtering, sample masking, and live benchmark execution verified operational. |

---

## 1. Synthetic Sample Count Audit

### Status: `PASS`

### Exact Files Inspected
* `dataset/api_keys_master.jsonl`
* `dataset/api_keys_master.csv`
* `metadata/dataset_cleaning_report.json`
* `metadata/dataset_split_metadata.json`
* `docs/API_KEY_DATASET_GUIDE.md`

### Actual Test Performed
A programmatic line-by-line inspection was executed across `dataset/api_keys_master.jsonl` to parse every JSON object and verify:
1. Total record count.
2. Value of `is_synthetic` (`True` vs `False`).
3. Value of `source` (`custom_synthetic` vs `nightfall_sample_data`).
4. Consistency across metadata reports and documentation.

### Evidence
```
Total Records in Master: 10,000
is_synthetic == True:    9,994 (99.94%)
is_synthetic == False:   6 (0.06%)
source == 'custom_synthetic':      9,994
source == 'nightfall_sample_data': 6
Other sources: 0
```
* **Metadata Alignment:** `metadata/dataset_cleaning_report.json` explicitly records `synthetic_count: 9994` and `original_source_count: 6`.
* **Split Alignment:** `dataset_split_metadata.json` records `total: 10000`, `train: 7000`, `validation: 1500`, `test: 1500`.
* **Documentation Consistency:** All figures in `docs/API_KEY_DATASET_GUIDE.md` align with actual file counts.

### Remaining Limitations
Because the Nightfall API key demo dataset only yielded 6 usable de-identified snippets (after quarantining potentially active tokens), 99.94% of the dataset is synthetic.

---

## 2. Data Leakage Audit

### Status: `PARTIAL`

### Exact Files Inspected
* `backend/scripts/generate_api_key_dataset.py`
* `dataset/splits/api_keys_train.jsonl`
* `dataset/splits/api_keys_validation.jsonl`
* `dataset/splits/api_keys_test.jsonl`
* `metadata/dataset_split_metadata.json`

### Actual Test Performed
1. SHA-256 hashes were calculated for the stripped `sample` field of every record in `train` (7,000), `validation` (1,500), and `test` (1,500).
2. Set intersections were evaluated between all split pairs.
3. Generator logic was analyzed to inspect shared structural wrappers and token generation templates.
4. Sequence similarity probes (SequenceMatcher) were conducted between random test samples and training samples.

### Evidence
* **Exact Duplicate Overlap:**
  * Train $\cap$ Validation: **0** samples (0.0%)
  * Train $\cap$ Test: **0** samples (0.0%)
  * Validation $\cap$ Test: **0** samples (0.0%)
* **Stratification Balance:** Positive and negative samples are distributed at exactly 50/50 across all splits (Train: 3,500 pos / 3,500 neg; Test: 750 pos / 750 neg).

### Limitations of Random Sample-Level Splitting
1. **Shared Generation Templates:** The generator applies a fixed set of 10 context wrapping templates (e.g., `export {VAR}="{key}"`, `Authorization: Bearer {key}`, `{"api_name": "...", "{var}": "{key}"}`) across both training and test sets.
2. **Identical Provider Signatures:** The test set samples were drawn from the same pseudo-random generation distributions (identical prefixes: `sk-proj-`, `nvapi-`, `AKIA`, `AIza`, `ghp_`, `xoxb-`) as the training set.
3. **Generalization Scope:** Random sample-level splitting verifies that the pattern detection engine accurately recognizes **in-distribution** variations of known formats. It does **not** evaluate out-of-distribution (OOD) generalization against completely novel secret formats, undocumented third-party providers, or anomalous delimiter structures.

---

## 3. Nightfall Licensing Audit

### Status: `PARTIAL / ATTRIBUTED WITH RESTRICTIONS`

### Exact Files Inspected
* `https://help.nightfall.ai/nightfall_policy_templates/sample_data.md`
* `nightfall_ai_api_key_demo_dataset/READ_ME.txt` (extracted from upstream archive)
* `metadata/nightfall_source_attribution.json`
* `metadata/quarantine_report.json`
* `docs/DATASET_SOURCE_ATTRIBUTION.md`

### Actual Test Performed
1. Inspected upstream documentation, GitBook source endpoints, and bundled `READ_ME.txt` for explicit open-source licenses (MIT, Apache, CC-BY).
2. Evaluated permissible usage under copyright and vendor terms of service.
3. Verified quarantine handling of potentially active upstream credentials.

### Evidence
* **Upstream Evaluation Authorization:** The bundled `READ_ME.txt` states:
  > *"This sample dataset demonstrates Nightfall's advanced API key detection capabilities. The data has been fully de-identified and can be used to test key detection on any data loss prevention platform."*
* **Absence of Open-Source Grant:** Nightfall does **not** attach an open-source or Creative Commons license to these sample files. They are provided as evaluation material for testing DLP capabilities.
* **Redistribution Rights Ambiguity:** Public documentation does not grant explicit commercial redistribution rights.
* **Quarantine Enforcement:** One upstream sample (`api_key--aws_ACTIVE.txt`) was marked as `ACTIVE` in documentation. The raw credential string (`AKIA2OGYBAH6UREMKH4Q`) was quarantined and excluded from Git and the distributable dataset (`metadata/quarantine_report.json`).

### Remaining Limitations & Recommendations
Redistribution of the 6 de-identified Nightfall samples cannot be established under a permissive open-source license. For internal benchmarking and evaluation, their use is aligned with the vendor's stated testing purpose. However, for public distribution of the platform, these 6 samples should either be isolated as non-redistributable evaluation data or replaced with 100% synthetic counterparts.

---

## 4. Benchmark Independence Audit

### Status: `PASS`

### Exact Files Inspected
* `backend/app/services/api_key_benchmark.py`
* `backend/app/security_engine/member1_engine.py`
* `backend/tests/test_api_key_benchmark.py`

### Actual Test Performed
1. Traced execution flow of `ApiKeyBenchmarkService.run_benchmark()`.
2. Verified whether ground-truth labels (`rec["label"]`) or provider labels (`rec["provider"]`) are provided to the detection function.
3. Checked if predictions are derived from sample labels or computed independently.
4. Evaluated whether the test split is used to tune regex patterns or thresholds.
5. Audited relationship with Member 1's engine.

### Evidence
* **Label Isolation:** `ApiKeyDetectionEngine.detect(sample_text)` accepts only `sample_text`. It receives no labels, provider identifiers, or ground-truth metadata.
* **Independent Prediction:** Detection occurs strictly via regular expressions, placeholder filtering, and Shannon entropy checks on the sample string.
* **Separation of Evaluation:** Comparison between predicted result and ground-truth label occurs only *after* detection:
  ```python
  is_pos = (rec.get("label") == "positive")
  detected = ApiKeyDetectionEngine.detect(sample_text)
  if is_pos and detected: tp += 1
  elif not is_pos and detected: fp += 1
  ```
* **Dynamic Metric Calculation:** Precision ($83.96\%$), Recall ($92.80\%$), F1 ($88.16$), and Accuracy ($87.53\%$) are computed dynamically from test split tallies ($TP=696, FP=133, TN=617, FN=54$) with division-by-zero guards.
* **Member 1 Engine Scope:** Member 1's engine (`member1_engine.py`) is an active network scanner auditing HTTP endpoints for BOLA/IDOR and missing headers over network sockets. The API key benchmark operates as an independent service evaluating static text patterns without modifying Member 1's network scan engine.

### Remaining Limitations
The benchmark engine evaluates structural syntax and pattern matching. It does not determine whether a key is valid, authorized, or revoked on provider cloud platforms.

---

## 5. Frontend Functionality Audit

### Status: `PASS`

### Exact Files Inspected
* `frontend/src/views/ApiKeyIntelligence.jsx`
* `frontend/src/components/Sidebar.jsx`
* `frontend/src/App.jsx`
* `backend/app/routes/dataset.py`

### Actual Test Performed
Live end-to-end HTTP requests and contract validations were executed against the running backend node (`http://127.0.0.1:8000`):
1. **Initial Data Loading:** `GET /api/dataset/overview`, `GET /api/dataset/benchmark`, `GET /api/dataset/providers`, `GET /api/dataset/statistics`.
2. **Provider Filtering:** `GET /api/dataset/samples?provider=openai&limit=10`.
3. **Label Filtering:** `GET /api/dataset/samples?label=positive` and `label=negative`.
4. **Sample Masking:** Checked that returned sample strings contain masking ellipses/stars.
5. **Benchmark Execution:** `POST /api/dataset/benchmark/run`.
6. **Error Handling:** Tested query parameters with invalid split names.

### Evidence
* **Initial Loading:** All 4 endpoints return HTTP 200 with valid JSON conforming to Pydantic v2 response schemas.
* **Provider Filtering:** Verified `provider=openai` returned exclusively OpenAI samples.
* **Label Filtering:** Verified `label=positive` returned exclusively positive samples and `label=negative` returned exclusively negative samples.
* **Sample Masking:** Verified 100% of tested samples are safely masked (e.g. `cred...yXGn`, `sk-proj-...****`).
* **Live Benchmark Execution:** `POST /api/dataset/benchmark/run` executed in 111.2 ms, generated dynamic benchmark ID (`bench_1794387290`), and returned real-time metrics ($F1=88.16$).
* **UI Build:** Production bundle compiled with Vite in 5.85s with zero syntax or bundling errors.

### Remaining Limitations
Browsers with persistent aggressive cache policies may require a hard refresh (`Ctrl + F5`) to invalidate previous cached JavaScript chunks and display the newly added sidebar navigation item.

---

## Final Audit Sign-Off

* **Total Tests Executed in Pytest:** 78 passed in 115.08s (62 regression baseline + 16 new dataset & benchmark tests).
* **Git Status:** Working tree clean on branch `feature/api-key-dataset` (`fe7f42d`).
* **Baseline Preservation:** v1.0.0 release baseline, Member 1 engine, and existing security controls remain untouched.
