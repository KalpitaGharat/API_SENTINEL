# API SENTINEL – SECURITY ENGINE INTEGRATION SPECIFICATION (MEMBER 1)

This document specifies the exact contract, data structures, and security controls required to integrate Member 1's vulnerability detection engine with the API Sentinel FastAPI backend.

---

## 1. File Location & Class Naming

Place your engine module at:
```
backend/app/security_engine/member1_engine.py
```

The backend factory function `get_security_engine()` in `backend/app/security_engine/integration.py` looks directly for:
```python
from app.security_engine.member1_engine import EngineAdapter
```

Your adapter class must inherit from `BaseSecurityEngineAdapter`:
```python
from typing import Dict, List, Any
from app.security_engine.integration import BaseSecurityEngineAdapter
from app.schemas import FindingCreate, EvidenceCreate


class EngineAdapter(BaseSecurityEngineAdapter):
    engine_name: str = "api_sentinel_real_engine"
    is_simulated: bool = False

    def run_scan(self, target_url: str, config: Dict[str, Any]) -> List[FindingCreate]:
        ...

    def retest_finding(
        self,
        target_url: str,
        finding_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...
```

---

## 2. Scan Function Specification

### Signature
```python
def run_scan(self, target_url: str, config: Dict[str, Any]) -> List[FindingCreate]:
```

### Arguments
- `target_url` (`str`): Base URL of target API to scan (e.g. `https://api.student-lab.local`).
- `config` (`Dict[str, Any]`): Scan options dictionary containing:
  - `categories` (`List[str]`): Categories requested, e.g. `["BOLA", "AUTH", "HEADERS", "CONFIG"]`.
  - `auth_token` (`Optional[str]`): Active token for authenticated probes (e.g. `Bearer eyJ...`).
  - `custom_headers` (`Optional[Dict[str, str]]`): Custom headers (e.g. `{"X-Tenant-Id": "1001"}`).
  - `test_accounts` (`Optional[Dict[str, Any]]`): Controlled test credentials for authorization/BOLA comparison (e.g. `{"user_a": {...}, "user_b": {...}}`).

### Return Type
- `List[FindingCreate]`: List of Pydantic models conforming to `app.schemas.FindingCreate`.

---

## 3. Retest Function Specification

### Signature
```python
def retest_finding(
    self,
    target_url: str,
    finding_data: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
```

### Arguments
- `target_url` (`str`): Target API URL.
- `finding_data` (`Dict[str, Any]`): Finding dictionary with keys: `id`, `vulnerability`, `category`, `endpoint`, `severity`.
- `config` (`Dict[str, Any]`): The scan configuration dictionary stored during original scan.

### Return Type
Return a dictionary with these exact keys:
```python
{
    "verified": bool,           # True if vulnerability is genuinely fixed; False if still present
    "new_status": str,          # "Resolved", "Still Vulnerable", or "Retest Failed"
    "observed_result": dict,    # Telemetry details (HTTP status, probe message, timestamp)
}
```

---

## 4. Standard Finding & Evidence Data Structure

Every detected vulnerability must be returned as an instance of `FindingCreate`:

```python
FindingCreate(
    vulnerability="Broken Object Level Authorization (BOLA)",
    category="BOLA",                         # BOLA | AUTH | HEADERS | CONFIG
    endpoint="GET /api/records/{id}",        # HTTP method and route
    severity="High",                         # Critical | High | Medium | Low | Informational
    description="Endpoint allows user A to read user B record without ownership validation.",
    recommendation="Enforce server-side ownership checks matching token claims to resource owner.",
    status="Open",                           # Always "Open" for newly detected findings
    evidence=EvidenceCreate(
        test_user="Patient_A (Token A)",
        requested_resource="/api/records/patient_b_991",
        observed_status=200,                 # Status observed during unauthorized probe
        expected_status=403,                 # Expected secure status
        request_details={
            "method": "GET",
            "url": "https://api.lab.local/api/records/patient_b_991",
            "destination_ip": "192.168.1.10", # Destination IP actually connected to
        },
        response_details={
            "status_code": 200,
            "snippet": "{\"id\": \"patient_b_991\", \"data\": \"sensitive\"}",
        },
    ),
)
```

---

## 5. Security & Safety Requirements for Member 1

1. **Use Provided Safe HTTP Client:**  
   Import and use `create_safe_http_client` from `app.security_engine.integration`:
   ```python
   from app.security_engine.integration import create_safe_http_client, validate_safe_redirect
   ```
   - Automatically enforces connect timeouts (5s) and overall timeouts (10s).
   - Disables automatic redirects (`follow_redirects=False`) to prevent redirect-based SSRF.

2. **Validate All HTTP Redirects:**  
   If an endpoint returns a `3xx` redirect, you MUST validate the destination before following:
   ```python
   if response.is_redirect:
       redirect_url = response.headers.get("location")
       safe_target = validate_safe_redirect(target_url, redirect_url, allow_lab=allow_lab)
       # Now safe to request safe_target
   ```

3. **Never Access Cloud Metadata Endpoints:**  
   Do not probe `169.254.169.254`, `metadata.google.internal`, `instance-data`, or `fd00:ec2::254`. These are blocked by the safety layer.

4. **Non-Destructive Testing:**  
   Do not execute SQL drop queries, mass deletions, or denial-of-service payloads. Testing should observe access control violations using `GET`, safe `OPTIONS`, or read-only probes.

5. **Credential Redaction in Evidence:**  
   Do not dump raw JWT secrets or passwords into `request_details` or `response_details`. Use `[REDACTED_TOKEN]` placeholders in evidence snippets.

---

## 6. Template Starter Code for Member 1

```python
"""Member 1 Security Detection Engine Adapter.

Implements BOLA, Broken Auth, and Security Headers detection checks.
"""

from typing import List, Dict, Any
from app.security_engine.integration import (
    BaseSecurityEngineAdapter,
    create_safe_http_client,
    validate_safe_redirect,
)
from app.schemas import FindingCreate, EvidenceCreate


class EngineAdapter(BaseSecurityEngineAdapter):
    engine_name = "api_sentinel_core_detection_engine"
    is_simulated = False

    def run_scan(self, target_url: str, config: Dict[str, Any]) -> List[FindingCreate]:
        findings: List[FindingCreate] = []
        allow_lab = config.get("allow_lab", False)

        with create_safe_http_client(allow_lab=allow_lab) as client:
            # 1. Header checks
            if "HEADERS" in config.get("categories", []):
                # Execute probe and append FindingCreate
                pass

            # 2. BOLA checks
            if "BOLA" in config.get("categories", []):
                # Execute probe and append FindingCreate
                pass

            # 3. Auth checks
            if "AUTH" in config.get("categories", []):
                # Execute probe and append FindingCreate
                pass

        return findings

    def retest_finding(
        self,
        target_url: str,
        finding_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        allow_lab = config.get("allow_lab", False)
        with create_safe_http_client(allow_lab=allow_lab) as client:
            # Re-execute targeted probe
            # Return dict with "verified", "new_status", "observed_result"
            return {
                "verified": False,
                "new_status": "Still Vulnerable",
                "observed_result": {"status_code": 200},
            }
```
