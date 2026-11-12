# API Sentinel — API Key Benchmark Guide

## 1. Benchmark Architecture & Methodology

The **API Sentinel Detection Benchmark** evaluates pattern-matching accuracy, false-positive resistance, and provider-specific detection coverage against the held-out test split (`dataset/splits/api_keys_test.jsonl`).

### Core Benchmark Principles:
1. **Zero Test-Label Tuning**: Detection rules and heuristics are developed strictly against provider specifications and training data; test labels are never used to train or adjust detection parameters.
2. **Format Detection vs. Live Validity**: A match indicates a valid structural format matching documented patterns; it does NOT verify whether a key is active, authorized, or functional.
3. **No External Network Probing**: All evaluations execute locally and in-memory; no credentials are ever transmitted across the network.

---

## 2. Evaluation Metrics & Mathematical Formulas

The benchmark computes standard classification metrics globally and for each individual provider. All formulas include division-by-zero guards:

### Precision
Measures the proportion of detected positive samples that were truly positive:
$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$

### Recall (Sensitivity)
Measures the proportion of actual positive samples that were successfully detected:
$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$

### F1 Score
The harmonic mean of Precision and Recall:
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

### Overall Accuracy
The proportion of total classifications (positive and negative) that were correct:
$$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$

---

## 3. Baseline Performance Results (Held-Out Test Split)

Evaluated across **1,500 samples** (750 positive, 750 negative) from `api_keys_test.jsonl`:

| Metric | Score | Details |
|---|---:|---|
| **Overall Accuracy** | **87.53%** | 1,313 / 1,500 correct decisions |
| **Precision** | **83.96%** | Low false-positive rate across negative lookalikes |
| **Recall** | **92.80%** | High sensitivity for documented key formats |
| **F1 Score** | **88.16** | Balanced detection across positive and negative classes |
| **Evaluation Time** | **~29.5 ms** | In-memory regex and Shannon entropy pipeline |

### Per-Provider Performance Breakdown:

| Provider | Samples | TP | FP | Precision | Recall | F1 Score | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Slack** | 150 | 75 | 0 | 100.0% | 100.0% | **100.0** | 100.0% |
| **Azure** | 150 | 74 | 0 | 100.0% | 98.67% | **99.33** | 99.33% |
| **Stripe** | 150 | 75 | 5 | 93.75% | 100.0% | **96.77** | 96.67% |
| **GitHub** | 150 | 75 | 6 | 92.59% | 100.0% | **96.15** | 96.00% |
| **Google Cloud** | 150 | 74 | 7 | 91.36% | 98.67% | **94.87** | 94.67% |
| **Twilio** | 150 | 75 | 13 | 85.23% | 100.0% | **92.03** | 91.33% |
| **AWS** | 150 | 75 | 17 | 81.52% | 100.0% | **89.82** | 88.67% |
| **NVIDIA** | 150 | 75 | 23 | 76.53% | 100.0% | **86.70** | 84.67% |
| **OpenAI** | 150 | 75 | 27 | 73.53% | 100.0% | **84.75** | 82.00% |
| **Generic API Key** | 150 | 23 | 35 | 39.66% | 30.67% | **34.59** | 42.00% |

---

## 4. Running the Benchmark

### Via CLI Script
```bash
python backend/scripts/test_benchmark_service.py
```

### Via FastAPI Endpoint
```bash
# Trigger benchmark run asynchronously
curl -X POST http://127.0.0.1:8000/api/dataset/benchmark/run

# Fetch latest cached results
curl http://127.0.0.1:8000/api/dataset/benchmark
```

### Via React Dashboard
1. Open the **API Key Intelligence** tab in the sidebar.
2. Click the **"RUN API KEY BENCHMARK"** button.
3. The dashboard executes the asynchronous probe and updates all KPI cards and per-provider tables automatically.

---

## 5. Benchmark Suite vs. Batch Testing (Mode B)

API Sentinel distinguishes between two evaluation workflows:

| Feature | Full Benchmark Suite | Batch Testing (Mode B) |
|---|---|---|
| **Scope** | Fixed 1,500 held-out test samples | Flexible slice (10 to 500 samples) |
| **Targeting** | All 10 providers simultaneously | Filterable to specific provider or category |
| **Splits** | Strictly `test` split | Configurable across `test`, `validation`, `train` |
| **Persistence** | Overwrites `benchmark_results.json` | Creates tracked audit record in `dataset_test_sessions` |
| **Sample Inspection** | Summary aggregated per provider | Full paginated record explorer for every single tested token |

### Interpreting the 2x2 Confusion Matrix:
- **True Positive (TP)**: The sample contains a real/valid API key signature format and the detection engine flagged it correctly.
- **False Positive (FP)**: The sample is a negative lookalike, dummy token, or documentation placeholder, but was flagged as a credential. Lowering FP is critical to prevent alert fatigue.
- **True Negative (TN)**: The sample is a non-secret lookalike and the detection engine correctly rejected it.
- **False Negative (FN)**: The sample contains a valid credential format that the detection engine failed to detect. Lowering FN is critical for preventing security breaches.

