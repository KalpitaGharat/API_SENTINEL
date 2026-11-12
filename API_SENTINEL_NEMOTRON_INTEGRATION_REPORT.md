# API Sentinel — NVIDIA Nemotron AI Integration & Explainability Report

**Module:** AI Security Intelligence & Explanations  
**Workspace:** `C:\PROJECTS\api-sentinel`  
**Date:** November 11, 2026  

---

## 1. System Architecture & Safety Guarantees

The NVIDIA Nemotron AI integration in API Sentinel provides developers with contextual, explainable vulnerability breakdowns and remediation code while adhering to strict application security constraints:

1. **Deterministic Veracity:** The Security Testing Engine alone decides if an endpoint is vulnerable based on raw HTTP telemetry. The AI model **never** overrides scanner verdicts or modifies raw request/response evidence.
2. **Strict Output Validation:** All LLM responses are parsed through `AIExplanationOutput` (Pydantic v2). Empty fields, missing sections, and malformed markdown are rejected before persistence.
3. **Multi-Tier Fallback:** If NVIDIA credentials are missing, expired (401), rate-limited (429), or offline, the system seamlessly uses deterministic, expert-crafted rule-based remediation templates.
4. **Transparent Status Badges:** The UI explicitly displays:
   - `NVIDIA Nemotron (Live AI)` when remote inference succeeded.
   - `Deterministic Rule Engine` when offline fallback generated the content.
   - `Cached in SQLite` when served from database cache.
5. **Zero Secret Leakage:** All inference calls route through FastAPI (`POST /api/findings/{id}/explain`). No API keys or tokens are bundled into the client build.

---

## 2. Interactive Features in React Frontend (`AiExplanationPanel.jsx`)

### 1. Title Banner:
- `AI-POWERED SECURITY ANALYSIS`
- Glowing purple/cyan accent border.

### 2. Actions:
- **`✨ Explain with Nemotron AI`:** Calls `POST /api/findings/{id}/explain` (defaults to cached if available).
- **`🔄 Regenerate AI Analysis`:** Calls `POST /api/findings/{id}/explain?force_refresh=true` to generate fresh analysis.

### 3. Three Structured Tabs:
1. **Vulnerability Breakdown:** Explains what the vulnerability is and why the application code failed.
2. **Attack Scenarios & Impact:** Details realistic exploit steps, threat modeling, and regulatory liability (HIPAA, GDPR, PCI-DSS).
3. **Step-by-Step Remediation:** Provides copy-pasteable Python/FastAPI code snippets, database ownership checks, and verification test commands.

---

## 3. Endpoints

| Endpoint | Method | Purpose | Cache Behavior |
|---|---|---|---|
| `/api/findings/{id}/explain` | `POST` | Request or retrieve AI explanation | Returns cached explanation if exists |
| `/api/findings/{id}/explain?force_refresh=true` | `POST` | Force fresh explanation generation | Bypasses cache and updates database record |
| `/api/findings/{id}/history` | `GET` | Audit trail of verification attempts | Chronological list of retests |
