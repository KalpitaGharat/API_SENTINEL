# API Sentinel — Deferred Features & Modularization Strategy

**Date:** 2026-11-12  
**Baseline Git Commit:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93`  
**Classification:** Product Simplification & Architecture Boundary Specification

---

## 1. Executive Rationale for Feature Deferral

API Sentinel's primary mission is **deterministic, explainable API security testing for developers and SMBs**. To maximize execution speed, maintain zero-dependency operational reliability, and keep the user experience focused, several secondary modules have been intentionally classified as **Deferred Features**.

These features remain completely functional and non-breaking within the existing repository, but are logically decoupled from the core scanning, evidence generation, and retesting loop.

---

## 2. Catalog of Deferred Features

```mermaid
graph TD
    subgraph Core Product [Core API Sentinel Engine]
        direction TB
        T[Target Onboarding] --> S[Deterministic Scanner]
        S --> E[Attack Evidence Inspector]
        E --> R[Retest Verification Engine]
        R --> H[Audit History]
    end

    subgraph Deferred Features [Deferred & Modular Capabilities]
        direction TB
        D1[API Key Intelligence Dataset]
        D2[API Key Benchmarking Suite]
        D3[Streamlit Alternate Dashboard]
        D4[External Cloud Reporting Webhooks]
    end

    Core Product -.->|Decoupled Architecture| Deferred Features
```

### 2.1 API Key Intelligence Dataset & Verification
- **Files:** `backend/app/routes/dataset.py`, `backend/app/services/dataset_service.py` (if applicable), dataset test fixtures in `backend/tests/test_api_key_dataset.py` and `test_dataset_endpoints.py`.
- **Purpose:** Analyzing patterns of synthetic API keys, estimating entropy, and validating provider-specific formats (e.g., Stripe, GitHub, AWS).
- **Reason for Deferral:** API key discovery is an orthogonal secret-scanning problem. Bundling secret analysis with active DAST vulnerability scanning dilutes the core product focus (BOLA, authentication bypass, security headers).
- **Current Operational Status:** Fully implemented and operational. Routes remain mounted in `backend/app/main.py` without impacting core scanning performance.
- **Future Extraction Path:** Can be packaged into a standalone plugin or CLI utility (`sentinel-secret-scanner`).

---

### 2.2 LLM & Regex API Key Benchmarking Suite
- **Files:** `backend/app/services/api_key_benchmark.py`, `metadata/benchmark_history.json`, `metadata/benchmark_results.json`, `docs/API_KEY_BENCHMARK_GUIDE.md`.
- **Purpose:** Compares the precision, recall, and inference latency of regular expressions versus LLM models (e.g., Llama 3, Mistral, GPT-4) when detecting leaked credentials.
- **Reason for Deferral:** Research and benchmarking are developer evaluation tasks, not production security scanning tasks. Running benchmarks consumes compute and API tokens unnecessarily during security audits.
- **Current Operational Status:** Preserved in repository for academic and research evaluation.
- **Future Extraction Path:** Move to a separate evaluation repository (`api-sentinel-benchmarks`).

---

### 2.3 Secondary Streamlit Dashboard
- **Files:** `dashboard/app.py`, `dashboard/config.py`, `dashboard/views/`
- **Purpose:** Legacy Python Streamlit frontend initially built during early prototyping.
- **Reason for Deferral:** The primary, modern production frontend is the React 18 single-page application (`frontend/`). Maintaining two separate frontends introduces unnecessary cognitive load.
- **Current Operational Status:** Configured to run on port 8501 as a backup presentation option, but designated as secondary.
- **Future Extraction Path:** Archive or retire once React frontend deployment is completely containerized.

---

### 2.4 External Notification Webhooks & Cloud Reporting
- **Scope:** Slack/Discord notifications, JIRA ticket generation, S3 report storage.
- **Reason for Deferral:** Student developers and small businesses prioritize local, secure, zero-cloud data leakage. Adding external webhooks introduces third-party credential management and network egress requirements.
- **Current Operational Status:** Documented in roadmap; not part of the v1.0.0 core delivery.

---

## 3. Decoupling & Stability Safeguards

To prevent regressions while keeping the codebase stable:
1. **Zero Abrupt Code Deletions:** No routes, services, or models have been removed. Abrupt deletions risk breaking imports, database schemas, or existing test runners.
2. **Clear Namespace Isolation:** Core scanning components (`member1_engine.py`, `scan_service.py`, `retest_service.py`, `targets.py`, `findings.py`) have zero runtime dependency on `api_key_benchmark.py` or `dataset.py`.
3. **Database Schema Independence:** Core tables (`scans`, `findings`, `ai_explanations`, `retest_history`, `targets`) do not contain foreign key constraints to any dataset or benchmark tables.
