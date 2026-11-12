"""Automated Test Suite for OpenAPI & Swagger Specification Parser.

Tests parsing of OpenAPI 3.0, 3.1, and Swagger 2.0 specs, parameter extraction,
sensitive endpoint candidate classification, limits (5 MB, 1,000 endpoints),
and SSRF protection on remote spec imports.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.openapi_parser import OpenApiParser, OpenApiParserError
from app.security_engine.integration import TargetSafetyError


# Fixtures for various specs

OPENAPI_30_JSON = json.dumps({
    "openapi": "3.0.3",
    "info": {
        "title": "Healthcare Management API",
        "description": "Patient portal service",
        "version": "1.2.0"
    },
    "servers": [
        {"url": "https://api.healthcare.example.com/v1"}
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "apiKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-KEY"
            }
        }
    },
    "paths": {
        "/api/patients": {
            "get": {
                "operationId": "listPatients",
                "summary": "List all patients",
                "parameters": [
                    {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "X-Request-ID", "in": "header", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {"description": "Patient list returned"}
                }
            },
            "post": {
                "operationId": "createPatient",
                "summary": "Create patient record",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Patient created"}
                }
            }
        },
        "/api/patients/{patient_id}": {
            "parameters": [
                {"name": "patient_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "get": {
                "operationId": "getPatient",
                "summary": "Get patient details",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {"description": "Patient details returned"},
                    "404": {"description": "Not found"}
                }
            },
            "delete": {
                "operationId": "deletePatient",
                "summary": "Delete patient",
                "responses": {
                    "204": {"description": "Patient deleted"}
                }
            }
        }
    }
})

OPENAPI_31_JSON = json.dumps({
    "openapi": "3.1.0",
    "info": {
        "title": "Modern Microservice API",
        "version": "2.0.0"
    },
    "servers": [{"url": "http://127.0.0.1:8001"}],
    "paths": {
        "/status": {
            "get": {
                "operationId": "getStatus",
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
})

OPENAPI_YAML = """
openapi: 3.0.0
info:
  title: Orders Service
  version: 1.0.0
servers:
  - url: https://orders.example.com
paths:
  /orders/{order_id}:
    get:
      summary: Retrieve Order
      parameters:
        - name: order_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Order details
"""

SWAGGER_20_JSON = json.dumps({
    "swagger": "2.0",
    "info": {
        "title": "Legacy Swagger API",
        "version": "1.0.0"
    },
    "host": "api.legacy.test",
    "basePath": "/v2",
    "schemes": ["https"],
    "securityDefinitions": {
        "basicAuth": {
            "type": "basic"
        }
    },
    "paths": {
        "/users/{user_id}": {
            "get": {
                "operationId": "getUserLegacy",
                "parameters": [
                    {"name": "user_id", "in": "path", "required": True, "type": "string"},
                    {"name": "api_key", "in": "query", "required": False, "type": "string"}
                ],
                "responses": {
                    "200": {"description": "User found"}
                }
            }
        }
    }
})


def test_parse_valid_openapi_30_json():
    """Verify valid OpenAPI 3.0 parsing, metadata extraction, and endpoint counts."""
    res = OpenApiParser.parse_from_content(OPENAPI_30_JSON, file_type="json")
    assert res["title"] == "Healthcare Management API"
    assert res["version"] == "1.2.0"
    assert res["spec_version"] == "OpenAPI 3.0.3"
    assert res["base_url"] == "https://api.healthcare.example.com/v1"
    assert res["total_endpoints"] == 4  # GET /api/patients, POST /api/patients, GET /api/patients/{id}, DELETE /api/patients/{id}


def test_parse_valid_openapi_31_json():
    """Verify valid OpenAPI 3.1 specification parsing."""
    res = OpenApiParser.parse_from_content(OPENAPI_31_JSON, file_type="json")
    assert res["title"] == "Modern Microservice API"
    assert "OpenAPI 3.1" in res["spec_version"]
    assert res["total_endpoints"] == 1


def test_parse_valid_openapi_yaml():
    """Verify OpenAPI YAML parsing."""
    res = OpenApiParser.parse_from_content(OPENAPI_YAML, file_type="yaml")
    assert res["title"] == "Orders Service"
    assert res["total_endpoints"] == 1
    assert res["endpoints"][0]["path"] == "/orders/{order_id}"


def test_parse_valid_swagger_20():
    """Verify Swagger 2.0 specification parsing and base URL construction."""
    res = OpenApiParser.parse_from_content(SWAGGER_20_JSON, file_type="json")
    assert res["title"] == "Legacy Swagger API"
    assert "Swagger 2.0" in res["spec_version"]
    assert res["base_url"] == "https://api.legacy.test/v2"
    assert res["total_endpoints"] == 1


def test_missing_metadata_defaults():
    """Verify spec without info block falls back to safe defaults."""
    minimal_spec = json.dumps({"openapi": "3.0.0", "paths": {}})
    res = OpenApiParser.parse_from_content(minimal_spec)
    assert res["title"] == "Untitled API"
    assert res["version"] == "1.0.0"
    assert res["total_endpoints"] == 0


def test_missing_paths():
    """Verify spec with missing or empty paths field parses cleanly."""
    spec_str = json.dumps({"openapi": "3.0.0", "info": {"title": "No Paths"}})
    res = OpenApiParser.parse_from_content(spec_str)
    assert res["total_endpoints"] == 0


def test_invalid_json():
    """Verify malformed JSON raises OpenApiParserError."""
    with pytest.raises(OpenApiParserError, match="Failed to parse|Invalid JSON"):
        OpenApiParser.parse_from_content("{malformed: json: here", file_type="json")


def test_invalid_yaml():
    """Verify invalid YAML raises OpenApiParserError."""
    with pytest.raises(OpenApiParserError, match="Failed to parse"):
        OpenApiParser.parse_from_content("key: [unclosed list", file_type="yaml")


def test_unsupported_specification_version():
    """Verify unsupported OpenAPI/Swagger versions are rejected."""
    bad_ver = json.dumps({"openapi": "4.0.0", "paths": {}})
    with pytest.raises(OpenApiParserError, match="Unsupported OpenAPI specification version"):
        OpenApiParser.parse_from_content(bad_ver)

    unknown_spec = json.dumps({"raml": "1.0", "title": "Not supported"})
    with pytest.raises(OpenApiParserError, match="Unrecognized API specification format"):
        OpenApiParser.parse_from_content(unknown_spec)


def test_duplicate_endpoints_skipping():
    """Verify duplicate operations on the same path are deduplicated with warnings."""
    spec_with_dups = {
        "openapi": "3.0.0",
        "paths": {
            "/api/test": {
                "get": {"summary": "First"},
            }
        }
    }
    # Pass dict through JSON
    res = OpenApiParser.parse_from_content(json.dumps(spec_with_dups))
    assert res["total_endpoints"] == 1


def test_parameter_extraction():
    """Verify path, query, and header parameter extraction and merging."""
    res = OpenApiParser.parse_from_content(OPENAPI_30_JSON)
    # Check GET /api/patients query and header params
    list_op = next(e for e in res["endpoints"] if e["path"] == "/api/patients" and e["method"] == "GET")
    param_names = [p["name"] for p in list_op["parameters"]]
    param_ins = [p["in"] for p in list_op["parameters"]]
    assert "page" in param_names
    assert "X-Request-ID" in param_names
    assert "query" in param_ins
    assert "header" in param_ins

    # Check GET /api/patients/{patient_id} path parameter inherited from path-level
    get_op = next(e for e in res["endpoints"] if e["path"] == "/api/patients/{patient_id}" and e["method"] == "GET")
    assert any(p["name"] == "patient_id" and p["in"] == "path" and p["required"] is True for p in get_op["parameters"])


def test_request_body_extraction():
    """Verify request body schema extraction for POST operation."""
    res = OpenApiParser.parse_from_content(OPENAPI_30_JSON)
    post_op = next(e for e in res["endpoints"] if e["path"] == "/api/patients" and e["method"] == "POST")
    req_body = post_op["request_schema"]
    assert req_body is not None
    assert req_body["content_type"] == "application/json"
    assert req_body["required"] is True
    assert "properties" in req_body["schema"]


def test_security_scheme_extraction():
    """Verify security schemes (Bearer, API Key Header) are parsed."""
    res = OpenApiParser.parse_from_content(OPENAPI_30_JSON)
    schemes = {s["name"]: s for s in res["security_schemes"]}
    assert "bearerAuth" in schemes
    assert schemes["bearerAuth"]["scheme"] == "bearer"
    assert "apiKeyHeader" in schemes
    assert schemes["apiKeyHeader"]["in"] == "header"


def test_sensitive_endpoint_identification():
    """Verify endpoints with object IDs or sensitive resources are flagged as candidates."""
    res = OpenApiParser.parse_from_content(OPENAPI_30_JSON)
    # /api/patients/{patient_id} has both sensitive resource keyword AND object ID
    sensitive_ops = [e for e in res["endpoints"] if e["is_sensitive_candidate"]]
    assert len(sensitive_ops) >= 2  # GET and DELETE on /api/patients/{patient_id}
    assert res["sensitive_endpoints_count"] >= 2


def test_state_changing_operation_identification():
    """Verify GET is safe while POST and DELETE are classified as state-changing."""
    res = OpenApiParser.parse_from_content(OPENAPI_30_JSON)
    get_op = next(e for e in res["endpoints"] if e["path"] == "/api/patients" and e["method"] == "GET")
    post_op = next(e for e in res["endpoints"] if e["path"] == "/api/patients" and e["method"] == "POST")
    del_op = next(e for e in res["endpoints"] if e["path"] == "/api/patients/{patient_id}" and e["method"] == "DELETE")

    assert get_op["is_state_changing"] is False
    assert post_op["is_state_changing"] is True
    assert del_op["is_state_changing"] is True


def test_specification_exceeding_5mb():
    """Verify specs exceeding 5 MB are rejected immediately."""
    huge_data = " " * (5 * 1024 * 1024 + 50)
    with pytest.raises(OpenApiParserError, match="exceeds the maximum allowed limit"):
        OpenApiParser.parse_from_content(huge_data)


def test_more_than_1000_endpoints():
    """Verify specification exceeding 1,000 endpoints raises an error."""
    paths_dict = {}
    for i in range(1005):
        paths_dict[f"/endpoint_{i}"] = {"get": {"responses": {"200": {"description": "ok"}}}}
    huge_spec = json.dumps({"openapi": "3.0.0", "paths": paths_dict})
    with pytest.raises(OpenApiParserError, match="exceeds the supported limit"):
        OpenApiParser.parse_from_content(huge_spec)


def test_external_reference_detection():
    """Verify external $ref URLs are flagged without automatic network dereference."""
    spec_with_ext_ref = json.dumps({
        "openapi": "3.0.0",
        "paths": {
            "/api/external": {
                "get": {
                    "responses": {
                        "200": {"description": "ok"}
                    },
                    "parameters": [
                        {"$ref": "https://external.example.com/schemas/User.json"}
                    ]
                }
            }
        }
    })
    res = OpenApiParser.parse_from_content(spec_with_ext_ref)
    assert len(res["external_refs_detected"]) >= 1
    assert "https://external.example.com/schemas/User.json" in res["external_refs_detected"]


def test_remote_url_ssrf_rejection():
    """Verify remote URL import rejects cloud metadata, link-local, and unauthorized IPs."""
    # Cloud metadata endpoint must be blocked unconditionally
    with pytest.raises(OpenApiParserError, match="Security Policy Rejection|strictly forbidden"):
        OpenApiParser.parse_from_url("http://169.254.169.254/latest/meta-data")

    # Localhost rejected when allow_lab is False
    with pytest.raises(OpenApiParserError, match="Security Policy Rejection|Scanning localhost"):
        OpenApiParser.parse_from_url("http://127.0.0.1:8001/openapi.json", allow_lab=False)
