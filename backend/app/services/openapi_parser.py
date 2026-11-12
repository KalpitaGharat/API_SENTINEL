"""OpenAPI and Swagger Specification Parser for API Sentinel.

Supports OpenAPI 3.0.x, OpenAPI 3.1.x, and Swagger 2.0 specs in JSON or YAML.
Extracts normalized endpoint metadata, parameters, request/response definitions,
authentication schemes, and identifies candidate endpoints for BOLA/IDOR testing.

Integrates with API Sentinel's hardened HTTP transport for safe remote URL imports.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse
import yaml

from app.security_engine.integration import (
    validate_target_safety,
    create_safe_http_client,
    execute_safe_request,
    TargetSafetyError,
)

logger = logging.getLogger("api_sentinel.openapi_parser")

MAX_SPEC_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_ENDPOINTS_LIMIT = 1000

HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD")
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SENSITIVE_RESOURCE_PATTERN = re.compile(
    r"/(?:users|patients|records|orders|accounts|payments|profiles|customers|invoices|documents|clients|members)",
    re.IGNORECASE,
)
OBJECT_ID_PARAM_PATTERN = re.compile(
    r"\{[^}]*(?:id|uuid|key|number|code|ref)[^}]*\}",
    re.IGNORECASE,
)


class OpenApiParserError(ValueError):
    """Raised when an OpenAPI/Swagger specification is invalid, unsupported, or exceeds limits."""
    pass


class OpenApiParser:
    """Production parser for OpenAPI 3.x and Swagger 2.0 specifications."""

    @classmethod
    def parse_from_content(cls, content: str, file_type: str = "auto") -> Dict[str, Any]:
        """Parse raw JSON or YAML string into normalized OpenAPI specification structure."""
        if not content:
            raise OpenApiParserError("Specification content is empty.")

        # Check raw size limit (5 MB) before parsing
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > MAX_SPEC_SIZE_BYTES:
            raise OpenApiParserError(
                f"Specification size ({len(content_bytes)} bytes) exceeds the maximum allowed limit of {MAX_SPEC_SIZE_BYTES} bytes (5 MB)."
            )

        if not content.strip():
            raise OpenApiParserError("Specification content is empty.")

        spec = cls._parse_raw_content(content, file_type)
        return cls._normalize_specification(spec)

    @classmethod
    def parse_from_url(cls, url: str, allow_lab: bool = False) -> Dict[str, Any]:
        """Fetch remote OpenAPI specification over hardened HTTPX transport and parse it.

        Strict security enforcement:
        - SSRF validation via validate_target_safety()
        - Destination-IP pinning to prevent DNS rebinding
        - Rejection of cloud metadata, private IPs, and link-local targets
        - 5 MB stream size limit
        """
        if not url or not url.strip():
            raise OpenApiParserError("Specification URL is empty.")

        url = url.strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise OpenApiParserError(f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

        # 1. Pre-flight SSRF Validation
        try:
            validate_target_safety(url, allow_lab=allow_lab)
        except TargetSafetyError as tse:
            raise OpenApiParserError(f"Security Policy Rejection for URL: {str(tse)}")

        # 2. Fetch using hardened HTTP transport
        try:
            with create_safe_http_client(allow_lab=allow_lab, timeout=10.0, target_url=url) as client:
                resp = execute_safe_request(
                    client,
                    method="GET",
                    url=url,
                    allow_lab=allow_lab,
                    max_redirects=3,
                    headers={"Accept": "application/json, application/yaml, text/yaml, */*"},
                )

                if resp.status_code != 200:
                    raise OpenApiParserError(f"Remote specification server responded with HTTP {resp.status_code}")

                body_bytes = resp.content
                if len(body_bytes) > MAX_SPEC_SIZE_BYTES:
                    raise OpenApiParserError(
                        f"Remote specification response ({len(body_bytes)} bytes) exceeds 5 MB limit."
                    )

                content_str = resp.text
                return cls.parse_from_content(content_str, file_type="auto")
        except TargetSafetyError as tse:
            raise OpenApiParserError(f"SSRF Safety Rejection: {str(tse)}")
        except OpenApiParserError:
            raise
        except Exception as err:
            logger.error("Failed to fetch remote OpenAPI spec: %s", err)
            raise OpenApiParserError(f"Failed to fetch remote OpenAPI specification: {str(err)}")

    # -------------------------------------------------------------------------
    # Internal Parsing & Normalization
    # -------------------------------------------------------------------------

    @classmethod
    def _parse_raw_content(cls, content: str, file_type: str = "auto") -> Dict[str, Any]:
        """Convert content string to Python dictionary using JSON or safe YAML."""
        spec = None
        clean_content = content.strip()

        # If forced json or looks like json
        if file_type == "json" or (file_type == "auto" and clean_content.startswith("{")):
            try:
                spec = json.loads(content)
            except Exception as j_err:
                if file_type == "json":
                    raise OpenApiParserError(f"Invalid JSON specification: {str(j_err)}")
                # Fall back to YAML attempt

        if spec is None:
            try:
                spec = yaml.safe_load(content)
            except Exception as y_err:
                raise OpenApiParserError(f"Failed to parse specification as JSON or YAML: {str(y_err)}")

        if not isinstance(spec, dict):
            raise OpenApiParserError("Parsed specification must be a top-level dictionary/object.")

        return spec

    @classmethod
    def _normalize_specification(cls, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spec version, extract metadata, normalize endpoints and auth schemes."""
        spec_version, version_type = cls._detect_spec_version(spec)

        info = spec.get("info") or {}
        title = str(info.get("title") or "Untitled API").strip()
        description = str(info.get("description") or "").strip()
        api_version = str(info.get("version") or "1.0.0").strip()

        # Extract Server / Base URLs
        server_urls = cls._extract_server_urls(spec, version_type)
        base_url = server_urls[0] if server_urls else ""

        # Extract Security Schemes
        security_schemes = cls._extract_security_schemes(spec, version_type)

        # Extract Endpoints
        raw_paths = spec.get("paths")
        if raw_paths is None:
            raw_paths = {}

        if not isinstance(raw_paths, dict):
            raise OpenApiParserError("The 'paths' field in specification must be a dictionary.")

        endpoints: List[Dict[str, Any]] = []
        seen_endpoints: Set[Tuple[str, str]] = set()
        warnings: List[str] = []
        external_refs: List[str] = []

        # Parse endpoints across paths
        for path_str, path_item in raw_paths.items():
            if not isinstance(path_str, str) or not path_str.startswith("/"):
                warnings.append(f"Skipping malformed path '{path_str}' (must begin with a forward slash).")
                continue

            if not isinstance(path_item, dict):
                continue

            # Path-level parameters
            path_level_params = cls._extract_parameters(path_item.get("parameters", []), external_refs)

            for method_key, operation in path_item.items():
                method_upper = method_key.upper()
                if method_upper not in HTTP_METHODS:
                    continue  # Skip $ref, summary, description, or custom extensions at path level

                if not isinstance(operation, dict):
                    continue

                endpoint_key = (path_str, method_upper)
                if endpoint_key in seen_endpoints:
                    warnings.append(f"Duplicate operation '{method_upper} {path_str}' encountered; skipped.")
                    continue
                seen_endpoints.add(endpoint_key)

                # Operation metadata
                op_id = str(operation.get("operationId") or "").strip() or None
                summary = str(operation.get("summary") or "").strip() or None
                op_desc = str(operation.get("description") or "").strip() or None
                tags = [str(t).strip() for t in operation.get("tags", []) if str(t).strip()]

                # Combined parameters (path-level + operation-level)
                op_params = cls._extract_parameters(operation.get("parameters", []), external_refs)
                all_params = cls._merge_parameters(path_level_params, op_params)

                # Request body schema
                request_schema = cls._extract_request_body(operation, version_type, external_refs)

                # Responses
                responses_info = cls._extract_responses(operation.get("responses", {}), external_refs)

                # Security requirements for this endpoint
                sec_reqs = operation.get("security")
                if sec_reqs is None:
                    sec_reqs = spec.get("security", [])

                # Sensitive endpoint identification
                has_resource = bool(SENSITIVE_RESOURCE_PATTERN.search(path_str))
                has_id_param = bool(OBJECT_ID_PARAM_PATTERN.search(path_str))
                is_sensitive = has_resource or has_id_param

                # State-changing method identification
                is_state_changing = method_upper in STATE_CHANGING_METHODS

                endpoints.append({
                    "path": path_str,
                    "method": method_upper,
                    "operation_id": op_id,
                    "summary": summary,
                    "description": op_desc,
                    "tags": tags,
                    "parameters": all_params,
                    "request_schema": request_schema,
                    "responses": responses_info,
                    "security_requirements": sec_reqs,
                    "is_sensitive_candidate": is_sensitive,
                    "is_state_changing": is_state_changing,
                    "is_selected": True,
                })

                if len(endpoints) > MAX_ENDPOINTS_LIMIT:
                    raise OpenApiParserError(
                        f"Specification contains more than {MAX_ENDPOINTS_LIMIT} endpoints, which exceeds the supported limit."
                    )

        sensitive_count = sum(1 for e in endpoints if e["is_sensitive_candidate"])
        state_changing_count = sum(1 for e in endpoints if e["is_state_changing"])

        return {
            "title": title,
            "description": description,
            "version": api_version,
            "spec_version": spec_version,
            "base_url": base_url,
            "server_urls": server_urls,
            "endpoints": endpoints,
            "security_schemes": security_schemes,
            "total_endpoints": len(endpoints),
            "sensitive_endpoints_count": sensitive_count,
            "state_changing_count": state_changing_count,
            "external_refs_detected": list(set(external_refs)),
            "warnings": warnings,
        }

    # -------------------------------------------------------------------------
    # Helper Extractors
    # -------------------------------------------------------------------------

    @classmethod
    def _detect_spec_version(cls, spec: Dict[str, Any]) -> Tuple[str, str]:
        """Identify if spec is OpenAPI 3.0.x, 3.1.x, or Swagger 2.0."""
        if "openapi" in spec:
            openapi_ver = str(spec["openapi"]).strip()
            if openapi_ver.startswith("3.0"):
                return f"OpenAPI {openapi_ver}", "openapi_3"
            elif openapi_ver.startswith("3.1"):
                return f"OpenAPI {openapi_ver}", "openapi_3"
            elif openapi_ver.startswith("3."):
                return f"OpenAPI {openapi_ver}", "openapi_3"
            else:
                raise OpenApiParserError(
                    f"Unsupported OpenAPI specification version: '{openapi_ver}'. Only OpenAPI 3.x and Swagger 2.0 are supported."
                )

        if "swagger" in spec:
            swagger_ver = str(spec["swagger"]).strip()
            if swagger_ver.startswith("2."):
                return f"Swagger {swagger_ver}", "swagger_2"
            else:
                raise OpenApiParserError(
                    f"Unsupported Swagger version: '{swagger_ver}'. Only Swagger 2.0 is supported."
                )

        raise OpenApiParserError(
            "Unrecognized API specification format. Document must contain 'openapi' or 'swagger' top-level declaration."
        )

    @classmethod
    def _extract_server_urls(cls, spec: Dict[str, Any], version_type: str) -> List[str]:
        """Extract server/base URLs from OpenAPI 3.x 'servers' or Swagger 2.0 'host'/'basePath'."""
        urls: List[str] = []

        if version_type == "openapi_3":
            servers = spec.get("servers") or []
            if isinstance(servers, list):
                for s in servers:
                    if isinstance(s, dict) and "url" in s:
                        raw_url = str(s["url"]).strip()
                        # Resolve variables if present
                        if "variables" in s and isinstance(s["variables"], dict):
                            for var_name, var_info in s["variables"].items():
                                default_val = str(var_info.get("default", ""))
                                raw_url = raw_url.replace(f"{{{var_name}}}", default_val)
                        if raw_url:
                            urls.append(raw_url)

        elif version_type == "swagger_2":
            host = spec.get("host", "").strip()
            base_path = spec.get("basePath", "").strip()
            schemes = spec.get("schemes", ["https"])
            scheme = schemes[0] if schemes else "https"

            if host:
                full_url = f"{scheme}://{host}"
                if base_path and base_path != "/":
                    full_url = f"{full_url}/{base_path.lstrip('/')}"
                urls.append(full_url)
            elif base_path:
                urls.append(base_path)

        # Default fallback
        if not urls:
            urls.append("")

        return urls

    @classmethod
    def _extract_security_schemes(cls, spec: Dict[str, Any], version_type: str) -> List[Dict[str, Any]]:
        """Extract declared authentication schemes."""
        schemes_list: List[Dict[str, Any]] = []

        if version_type == "openapi_3":
            components = spec.get("components") or {}
            raw_schemes = components.get("securitySchemes") or {}
        else:
            raw_schemes = spec.get("securityDefinitions") or {}

        if isinstance(raw_schemes, dict):
            for scheme_name, scheme_obj in raw_schemes.items():
                if not isinstance(scheme_obj, dict):
                    continue
                s_type = str(scheme_obj.get("type") or "unknown").strip()
                s_scheme = str(scheme_obj.get("scheme") or "").strip() or None
                s_in = str(scheme_obj.get("in") or "").strip() or None
                desc = str(scheme_obj.get("description") or "").strip() or None

                schemes_list.append({
                    "name": scheme_name,
                    "type": s_type,
                    "scheme": s_scheme,
                    "in": s_in,
                    "description": desc,
                })

        return schemes_list

    @classmethod
    def _extract_parameters(cls, params_raw: Any, external_refs: List[str]) -> List[Dict[str, Any]]:
        """Extract and normalize parameter objects."""
        params_out: List[Dict[str, Any]] = []
        if not isinstance(params_raw, list):
            return params_out

        for p in params_raw:
            if not isinstance(p, dict):
                continue

            ref = p.get("$ref")
            if ref:
                if ref.startswith("http://") or ref.startswith("https://"):
                    external_refs.append(ref)
                continue

            p_name = str(p.get("name") or "").strip()
            p_in = str(p.get("in") or "query").strip().lower()
            p_req = bool(p.get("required", False))
            p_desc = str(p.get("description") or "").strip()

            # Type resolution (OpenAPI 3 schema vs Swagger 2 type)
            schema = p.get("schema") or {}
            p_type = schema.get("type") or p.get("type") or "string"

            if p_name:
                params_out.append({
                    "name": p_name,
                    "in": p_in,
                    "required": p_req,
                    "type": str(p_type),
                    "description": p_desc,
                })

        return params_out

    @classmethod
    def _merge_parameters(cls, path_params: List[Dict[str, Any]], op_params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge path-level and operation-level parameters, with operation-level overriding path-level on name+in conflict."""
        merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for p in path_params:
            key = (p["name"], p["in"])
            merged[key] = p
        for p in op_params:
            key = (p["name"], p["in"])
            merged[key] = p
        return list(merged.values())

    @classmethod
    def _extract_request_body(cls, operation: Dict[str, Any], version_type: str, external_refs: List[str]) -> Optional[Dict[str, Any]]:
        """Extract request body schema definition."""
        if version_type == "openapi_3":
            req_body = operation.get("requestBody")
            if isinstance(req_body, dict):
                content = req_body.get("content") or {}
                if isinstance(content, dict):
                    # Check JSON schema first
                    json_content = content.get("application/json") or content.get("*/*") or {}
                    schema = json_content.get("schema") or {}
                    ref = schema.get("$ref")
                    if ref and (ref.startswith("http://") or ref.startswith("https://")):
                        external_refs.append(ref)
                    return {
                        "content_type": "application/json" if "application/json" in content else list(content.keys())[0] if content else "none",
                        "required": bool(req_body.get("required", False)),
                        "schema": schema,
                    }

        elif version_type == "swagger_2":
            # In Swagger 2.0, body parameters are in parameters with in: "body"
            params = operation.get("parameters") or []
            if isinstance(params, list):
                for p in params:
                    if isinstance(p, dict) and p.get("in") == "body":
                        schema = p.get("schema") or {}
                        ref = schema.get("$ref")
                        if ref and (ref.startswith("http://") or ref.startswith("https://")):
                            external_refs.append(ref)
                        return {
                            "content_type": "application/json",
                            "required": bool(p.get("required", False)),
                            "schema": schema,
                        }

        return None

    @classmethod
    def _extract_responses(cls, responses_dict: Any, external_refs: List[str]) -> Dict[str, Any]:
        """Extract response status codes and summaries."""
        resps: Dict[str, Any] = {}
        if not isinstance(responses_dict, dict):
            return resps

        for code, resp_obj in responses_dict.items():
            code_str = str(code).strip()
            if isinstance(resp_obj, dict):
                desc = str(resp_obj.get("description") or "").strip()
                resps[code_str] = {"description": desc}
            else:
                resps[code_str] = {"description": str(resp_obj)}

        return resps
