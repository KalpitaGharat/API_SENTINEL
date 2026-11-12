"""NVIDIA Nemotron AI Service for Explaining Vulnerabilities and Remediations.

Provides explainable security analysis using NVIDIA's hosted Nemotron LLM
with OpenAI-compatible API client, timeout safeguards, and a comprehensive
rule-based fallback when offline or during hackathon demonstrations without keys.

IMPORTANT SAFETY CONSTRAINTS:
1. The Security Testing Engine alone decides if a vulnerability exists.
2. AI explanations ONLY explain verified findings and suggest remediation.
3. AI never overrides scanner verdicts or modifies raw telemetry.
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)


class AIExplanationOutput(BaseModel):
    """Strict validation schema for LLM-generated vulnerability explanations."""
    explanation: str = Field(..., description="Plain-language vulnerability breakdown")
    impact: str = Field(..., description="Attack scenarios and business impact")
    remediation: str = Field(..., description="Step-by-step remediation advice")
    model_name: str = Field(..., description="Model identifier used for generation")

    @field_validator("explanation", "impact", "remediation", "model_name")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"Field '{info.field_name}' must be a non-empty string.")
        return v.strip()


class AIService:
    """Service wrapping NVIDIA Nemotron LLM with fallback capabilities."""

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.timeout = settings.AI_TIMEOUT_SECONDS

        self.client: Optional[OpenAI] = None
        if self.api_key and self.api_key.strip():
            try:
                # 25s timeout allows reasoning model to complete thinking while still protecting server
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key.strip(),
                    timeout=min(float(self.timeout), 25.0),
                    max_retries=0,
                )
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client for NVIDIA: %s", e)
                self.client = None

    def explain_vulnerability(self, finding: Dict[str, Any]) -> Dict[str, str]:
        """Generate structured explanation, impact analysis, and remediation advice.

        Args:
            finding: Dictionary containing vulnerability details and evidence.

        Returns:
            Dictionary with keys: 'explanation', 'impact', 'remediation', 'model_name'
        """
        # If client is available, attempt remote inference via NVIDIA Nemotron
        if self.client:
            try:
                ai_result = self._call_nemotron(finding)
                if ai_result:
                    return ai_result
            except Exception as err:
                # Sanitize error to prevent leaking secrets or bearer tokens in logs
                clean_err = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1[REDACTED]", str(err))
                clean_err = re.sub(r"(nvapi-[A-Za-z0-9_\-]+)", "[REDACTED_KEY]", clean_err)
                logger.error("Nemotron API call failed: %s. Falling back to deterministic rule engine.", clean_err)

        # Fallback to expert rule-based explanations
        return self._generate_rule_based_fallback(finding)

    def _call_nemotron(self, finding: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Call NVIDIA Nemotron API with strict prompt instructions and Pydantic schema validation."""
        prompt = (
            f"You are API Sentinel's Senior Application Security Architect. "
            f"Analyze this verified vulnerability detected in an API security scan and generate an explainable, "
            f"actionable breakdown for student developers and small business engineering teams.\n\n"
            f"VULNERABILITY: {finding.get('vulnerability')}\n"
            f"CATEGORY: {finding.get('category')}\n"
            f"ENDPOINT: {finding.get('endpoint')}\n"
            f"SEVERITY: {finding.get('severity')}\n"
            f"DESCRIPTION: {finding.get('description')}\n"
            f"RECOMMENDATION: {finding.get('recommendation')}\n"
            f"EVIDENCE: {json.dumps(finding.get('evidence', {}))}\n\n"
            f"Respond strictly in valid JSON with these exact 3 keys:\n"
            f"1. 'explanation': Plain English breakdown of what this vulnerability means and how it occurs.\n"
            f"2. 'impact': Why it is dangerous, real-world attack scenarios, and business/data risk.\n"
            f"3. 'remediation': Clear, step-by-step remediation guide with code examples and verification advice.\n"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a specialized cybersecurity assistant for API Sentinel. "
                        "You explain detected API vulnerabilities with clarity, precision, and code-level remediation. "
                        "Always return pure valid JSON.\n\n"
                        f"{prompt}"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=3072,
        )

        content = response.choices[0].message.content
        if not content or not content.strip():
            logger.warning("Nemotron returned empty response. Falling back to rule-based engine.")
            return None

        # Clean JSON markdown fences if present
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        if clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        clean_content = clean_content.strip()

        try:
            parsed = json.loads(clean_content)
            if not isinstance(parsed, dict):
                logger.warning("Nemotron response is not a JSON object. Falling back to rule engine.")
                return None
            if "model_name" not in parsed:
                parsed["model_name"] = self.model

            # Validate against strict Pydantic model
            validated = AIExplanationOutput.model_validate(parsed)
            result_dict = validated.model_dump()
            if "Suggested remediation" not in result_dict["remediation"]:
                result_dict["remediation"] += "\n\n*Suggested remediation — not automatically applied or verified.*"
            return result_dict

        except (json.JSONDecodeError, ValidationError) as val_err:
            logger.warning("Nemotron JSON failed schema validation (%s). Falling back to rule-based engine.", val_err)
            return None

    def _generate_rule_based_fallback(self, finding: Dict[str, Any]) -> Dict[str, str]:
        """Generate high-quality, pre-compiled security advice when AI API is unavailable."""
        category = (finding.get("category") or "").upper()
        vulnerability = finding.get("vulnerability") or ""
        endpoint = finding.get("endpoint") or ""

        if "BOLA" in category or "IDOR" in vulnerability.upper():
            res = {
                "explanation": (
                    f"Broken Object Level Authorization (BOLA/IDOR) occurs on `{endpoint}` because the API "
                    "accepts an object identifier from the client and retrieves the record without validating whether "
                    "the currently authenticated user is authorized to view or edit that specific record."
                ),
                "impact": (
                    "High risk of massive data breaches and privacy violations. Malicious users or compromised student accounts "
                    "can iterate through numerical or predictable IDs (e.g. 1001, 1002) to download records belonging to "
                    "other users or administrators without triggering traditional authentication defenses."
                ),
                "remediation": (
                    "1. Never rely on client-supplied IDs alone.\n"
                    "2. Extract current user ID directly from the validated session/JWT claims.\n"
                    "3. Query the database using compound filters, e.g.:\n"
                    "   `SELECT * FROM records WHERE id = :record_id AND owner_user_id = :current_user_id;`\n"
                    "4. If the record does not belong to the user, return HTTP 403 Forbidden or HTTP 404 Not Found."
                ),
                "model_name": "rule-based-security-engine (offline-fallback)",
            }

        elif "HEADER" in category:
            res = {
                "explanation": (
                    f"The endpoint `{endpoint}` responded without essential HTTP security headers. Browsers rely on these "
                    "headers to enforce defense-in-depth protections like MIME sniffing prevention, frame sandboxing, "
                    "and mandatory HTTPS transport."
                ),
                "impact": (
                    "Leaves web clients interacting with this API vulnerable to MIME-confused Cross-Site Scripting (XSS), "
                    "clickjacking framing attacks, and unencrypted Man-in-the-Middle (MitM) credential interception."
                ),
                "remediation": (
                    "Add security header middleware to your API framework. In FastAPI / Starlette:\n"
                    "```python\n"
                    "@app.middleware('http')\n"
                    "async def add_security_headers(request, call_next):\n"
                    "    response = await call_next(request)\n"
                    "    response.headers['X-Content-Type-Options'] = 'nosniff'\n"
                    "    response.headers['X-Frame-Options'] = 'DENY'\n"
                    "    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'\n"
                    "    return response\n"
                    "```"
                ),
                "model_name": "rule-based-security-engine (offline-fallback)",
            }

        elif "AUTH" in category:
            res = {
                "explanation": (
                    f"The endpoint `{endpoint}` was successfully accessed without providing valid authentication tokens, "
                    "or with an invalid/expired credential that was not rejected by the server."
                ),
                "impact": (
                    "Critical threat. An attacker can invoke internal business logic, read sensitive telemetry, or modify "
                    "system state without ever needing an account."
                ),
                "remediation": (
                    "Protect the route using centralized authentication dependencies:\n"
                    "```python\n"
                    "from fastapi import Depends, HTTPException, status\n"
                    "\n"
                    "async def get_current_user(token: str = Depends(oauth2_scheme)):\n"
                    "    credentials_exception = HTTPException(status_code=401, detail='Could not validate credentials')\n"
                    "    return verify_jwt_token(token, credentials_exception)\n"
                    "```"
                ),
                "model_name": "rule-based-security-engine (offline-fallback)",
            }

        else:
            res = {
                "explanation": (
                    f"A security weakness ({vulnerability}) was identified on `{endpoint}`. The server behavior deviated "
                    "from standard secure API design patterns."
                ),
                "impact": (
                    "Security misconfigurations weaken overall defense-in-depth and can serve as stepping stones for deeper "
                    "network compromise or data leakage."
                ),
                "remediation": (
                    finding.get("recommendation")
                    or "Follow OWASP API Security Top 10 guidelines and conduct code review on the impacted route."
                ),
                "model_name": "rule-based-security-engine (offline-fallback)",
            }

        if "Suggested remediation" not in res["remediation"]:
            res["remediation"] += "\n\n*Suggested remediation — not automatically applied or verified.*"
        return res


ai_service = AIService()
