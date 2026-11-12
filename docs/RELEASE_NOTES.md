# API SENTINEL — RELEASE NOTES

**Release Version:** v1.1.0 (Release Candidate 1)  
**Release Date:** November 11, 2026  
**Git Branch:** `feature/api-key-dataset`  
**Baseline Git Checkpoint:** `50b1b6eb5b05b85c2e82ea013d55c5bf2ef00a93` (v1.0.0 Release Baseline Preserved)  
**Tagline:** *Find it. Understand it. Fix it. Verify it.*

---

## 1. RELEASE HIGHLIGHTS & MAJOR CAPABILITIES

API Sentinel v1.1.0 builds upon the initial v1.0.0 foundation, introducing full end-to-end API onboarding, OpenAPI 3.0 specification parsing, an AES-128 cryptographic credential vault, a 10,000-sample API key intelligence dataset, and a dual-probe automated retest verification engine.

### Key New Features in v1.1.0:
1. **API Onboarding & OpenAPI Discovery Engine:**
   - Ingests OpenAPI 3.0 and Swagger JSON/YAML definitions.
   - Automatically parses paths, HTTP methods, route parameters (`{patient_id}`), and query fields.
   - Identifies candidate sensitive endpoints for focused security audits.
   - Supports granular endpoint selection and bulk actions (`Sensitive Only`, `Select All`, `Deselect All`).
2. **Cryptographic Credential Vault:**
   - Secure storage for dual test accounts (Resource Owner and Unauthorized Attacker).
   - AES-128-CBC encryption with HMAC-SHA256 authentication (Fernet).
   - Masked credentials in UI responses (`sent..._101`) with zero plaintext storage in the database.
3. **Multi-Principal BOLA Detection with Content Verification:**
   - Re-engineered Member 1 engine eliminates false positives by requiring verified foreign record content matching (`expected_foreign_id` or `foreign_username`) inside the response body before flagging vulnerabilities.
4. **Dual-Probe Retest Verification:**
   - Mathematically verifies vulnerability remediation by verifying legitimate owner access (`200 OK`) and unauthorized attacker rejection (`403 Forbidden`).
   - Automatically transitions finding status from `Open` to **`Resolved`**.
5. **API Key Intelligence & Benchmark Suite:**
   - Curated master dataset of 10,000 synthetic tokens across OpenAI, AWS, GitHub, Slack, and Stripe.
   - Multi-factor detection combining provider prefix heuristics with Shannon entropy (>= 3.0 bits).
   - Audited test benchmark delivering **100.00% Precision** and **99.75% F1-score**.
6. **Multi-Format Security Audit Reporting:**
   - Instant client-side generation and download of complete audit reports in both **JSON** and **Markdown** formats with automatic credential redaction.

---

## 2. REGRESSION STATUS & QUALITY ASSURANCE

- **Backend Pytest Suite:** **125 of 125 tests passing** (`100% PASS`).
- **Frontend Test Suite:** **10 of 10 tests passing** (`100% PASS`).
- **SSRF Defense Assurance:** 19 of 19 hostile evasion vectors blocked.
- **Database Integrity:** Zero plaintext secrets across all 17 live authorization profiles.

---

## 3. RELEASE ASSET INVENTORY

- Release Archive: `dist/API_Sentinel_v1.1.0_Release_Candidate.zip` (2.12 MB)
- Staging Directory: `dist/release_candidate_v1.1.0/`
- Zero prohibited files (`.env`, `*.db`, `node_modules`, `__pycache__`) verified in package audit.
