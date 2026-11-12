"""
API Sentinel - Mock Data Provider
Supplies rich, realistic cybersecurity enterprise data for the dashboard.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

# Top KPIs
KPI_METRICS = {
    "total_scans": {
        "value": 24,
        "delta": "+26%",
        "delta_type": "positive",
        "description": "vs previous 30 days"
    },
    "total_vulnerabilities": {
        "value": 37,
        "delta": "-18%",
        "delta_type": "positive",  # Decrease in vulnerabilities is positive for security
        "description": "vs previous 30 days"
    },
    "fixed_verified": {
        "value": 28,
        "delta": "+40%",
        "delta_type": "positive",
        "description": "remediation rate"
    },
    "security_health": {
        "value": "76%",
        "delta": "+12 points",
        "delta_type": "positive",
        "description": "overall posture"
    }
}

# Vulnerability Distribution (Donut Chart)
SEVERITY_DISTRIBUTION = [
    {"severity": "Critical", "count": 6, "percentage": 16, "color": "#FF4D4F"},
    {"severity": "High", "count": 10, "percentage": 27, "color": "#FA8C16"},
    {"severity": "Medium", "count": 14, "percentage": 38, "color": "#FADB14"},
    {"severity": "Low", "count": 7, "percentage": 19, "color": "#00D4E8"},
]

# 14-Day Scan Activity
def get_14_day_scan_activity() -> List[Dict[str, Any]]:
    # 14 days up to Nov 10, 2026
    base_date = datetime(2026, 11, 10)
    data = []
    # Scans over last 14 days adding up to 24 scans total
    daily_counts = [1, 2, 1, 0, 3, 2, 1, 2, 1, 3, 2, 4, 1, 1]
    for i, count in enumerate(daily_counts):
        day = base_date - timedelta(days=(13 - i))
        data.append({
            "date": day.strftime("%b %d"),
            "full_date": day.strftime("%Y-%m-%d"),
            "scans": count,
            "endpoints_tested": count * 18 + (i * 3 % 11),
        })
    return data

# Recent Vulnerability Findings (Exact 5 from user specification)
RECENT_FINDINGS: List[Dict[str, Any]] = [
    {
        "id": "SEC-1001",
        "vulnerability": "Broken Object Level Authorization (BOLA)",
        "endpoint": "GET /api/users/{id}",
        "severity": "Critical",
        "status": "Open",
        "detected_on": "Nov 09",
        "owasp_category": "API1:2023 - Broken Object Level Authorization",
        "cvss_score": 8.8,
        "description": "The endpoint allows authenticated users to access other user profiles simply by changing the ID parameter in the URL path.",
        "remediation": "Validate that the user object ID matches the authenticated session token (e.g. JWT claims) before querying database records.",
        "code_snippet": "# Python / FastAPI Fix:\n@router.get('/api/users/{user_id}')\nasync def get_user(user_id: str, current_user = Depends(get_current_user)):\n    if current_user.id != user_id and not current_user.is_admin:\n        raise HTTPException(status_code=403, detail='Forbidden access to requested user object')",
    },
    {
        "id": "SEC-1002",
        "vulnerability": "Missing Security Headers",
        "endpoint": "/ (global)",
        "severity": "High",
        "status": "In Progress",
        "detected_on": "Nov 09",
        "owasp_category": "API8:2023 - Security Misconfiguration",
        "cvss_score": 7.5,
        "description": "Essential HTTP security response headers (Content-Security-Policy, X-Frame-Options, Strict-Transport-Security) are missing.",
        "remediation": "Add security headers in reverse proxy (NGINX/Cloudflare) or FastAPI middleware.",
        "code_snippet": "# Middleware implementation:\nresponse.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'\nresponse.headers['X-Content-Type-Options'] = 'nosniff'\nresponse.headers['X-Frame-Options'] = 'DENY'",
    },
    {
        "id": "SEC-1003",
        "vulnerability": "Weak Authentication Configuration",
        "endpoint": "POST /api/login",
        "severity": "High",
        "status": "Open",
        "detected_on": "Nov 08",
        "owasp_category": "API2:2023 - Broken Authentication",
        "cvss_score": 7.8,
        "description": "JWT tokens are signed using weak HMAC keys and do not enforce token expiration expiry claims properly.",
        "remediation": "Utilize asymmetric RS256/EdDSA signing keys or 256-bit entropy secrets, and enforce strict token expiration.",
        "code_snippet": "# Enforce minimum key entropy & expiry:\npayload = {'sub': user_id, 'exp': datetime.utcnow() + timedelta(minutes=15)}\ntoken = jwt.encode(payload, RSA_PRIVATE_KEY, algorithm='RS256')",
    },
    {
        "id": "SEC-1004",
        "vulnerability": "Insecure API Configuration",
        "endpoint": "GET /api/config",
        "severity": "Medium",
        "status": "Fixed",
        "detected_on": "Nov 08",
        "owasp_category": "API7:2023 - Server-Side Request Forgery & Misconfig",
        "cvss_score": 5.4,
        "description": "Public configuration endpoint exposes internal service hostnames and staging cluster IP addresses.",
        "remediation": "Strip internal addresses and infrastructure metadata from client-facing configuration responses.",
        "code_snippet": "# Sanitize response payload:\nreturn {'client_env': 'production', 'feature_flags': active_flags}",
    },
    {
        "id": "SEC-1005",
        "vulnerability": "Missing Rate Limiting",
        "endpoint": "POST /api/register",
        "severity": "Low",
        "status": "Verified",
        "detected_on": "Nov 07",
        "owasp_category": "API4:2023 - Unrestricted Resource Consumption",
        "cvss_score": 3.7,
        "description": "No rate limiting on user registration allows automated account creation and resource starvation.",
        "remediation": "Apply sliding-window IP and fingerprint-based rate limiting (e.g. 5 requests per 10 minutes).",
        "code_snippet": "# Redis token bucket rate limiter:\n@limiter.limit('5/10minute')\n@router.post('/api/register')\nasync def register_account(...):",
    },
]

# Complete set of 37 Vulnerabilities for the full Findings page
ALL_VULNERABILITIES: List[Dict[str, Any]] = [
    *RECENT_FINDINGS,
    {
        "id": "SEC-1006",
        "vulnerability": "SQL Injection in Search Query Parameter",
        "endpoint": "GET /api/v1/search?q={query}",
        "severity": "Critical",
        "status": "Open",
        "detected_on": "Nov 06",
        "owasp_category": "API10:2023 - Unsafe Consumption of APIs",
        "cvss_score": 9.2,
        "description": "Raw SQL concatenation in full-text search endpoint allows unauthenticated database extraction.",
        "remediation": "Use parameterized queries or ORM query builders strictly.",
        "code_snippet": "query = select(Items).where(Items.title.ilike(f'%{query}%'))",
    },
    {
        "id": "SEC-1007",
        "vulnerability": "Mass Assignment on User Profile Update",
        "endpoint": "PUT /api/users/profile",
        "severity": "Critical",
        "status": "Open",
        "detected_on": "Nov 05",
        "owasp_category": "API3:2023 - Broken Object Property Level Authorization",
        "cvss_score": 8.5,
        "description": "Clients can inject 'role': 'admin' or 'is_verified': true during standard profile updates.",
        "remediation": "Use explicit Pydantic request schemas with forbidden fields ignored or rejected.",
        "code_snippet": "class UpdateProfileSchema(BaseModel):\n    name: str\n    bio: Optional[str]",
    },
    {
        "id": "SEC-1008",
        "vulnerability": "Server-Side Request Forgery (SSRF) via Webhook URL",
        "endpoint": "POST /api/webhooks/test",
        "severity": "Critical",
        "status": "Open",
        "detected_on": "Nov 04",
        "owasp_category": "API7:2023 - Server Side Request Forgery",
        "cvss_score": 8.9,
        "description": "Webhook tester allows requests to cloud metadata (169.254.169.254) and local loopback.",
        "remediation": "Filter and blacklist private RFC 1918 IPs and cloud metadata IP ranges before dispatching webhook calls.",
        "code_snippet": "if ipaddress.ip_address(resolved_ip).is_private: raise ValueError('Private IP rejected')",
    },
    {
        "id": "SEC-1009",
        "vulnerability": "Unauthenticated Administrative Metric Endpoint",
        "endpoint": "GET /metrics",
        "severity": "Critical",
        "status": "Open",
        "detected_on": "Nov 03",
        "owasp_category": "API5:2023 - Broken Function Level Authorization",
        "cvss_score": 8.1,
        "description": "Prometheus metrics endpoint without TLS authentication reveals internal microservice topology.",
        "remediation": "Bind metrics endpoint to private internal network or require mTLS/Bearer token.",
        "code_snippet": "# Require internal network or bearer token",
    },
    {
        "id": "SEC-1010",
        "vulnerability": "Hardcoded Cryptographic Salt in Microservice Config",
        "endpoint": "POST /api/auth/reset-password",
        "severity": "Critical",
        "status": "In Progress",
        "detected_on": "Nov 02",
        "owasp_category": "API2:2023 - Broken Authentication",
        "cvss_score": 8.4,
        "description": "Password reset token generation uses static shared salt stored in public repository.",
        "remediation": "Rotate salt secrets, generate cryptographically random salts per token, and store in Vault.",
        "code_snippet": "salt = secrets.token_bytes(32)",
    },
    # High Severities
    {
        "id": "SEC-1011",
        "vulnerability": "CORS Wildcard with Credentials Allowed",
        "endpoint": "OPTIONS /api/v2/*",
        "severity": "High",
        "status": "Open",
        "detected_on": "Nov 05",
        "owasp_category": "API8:2023 - Security Misconfiguration",
        "cvss_score": 7.4,
        "description": "Access-Control-Allow-Origin is dynamically reflected with Access-Control-Allow-Credentials: true.",
        "remediation": "Restrict allowed origins to an explicit trusted whitelist.",
        "code_snippet": "allow_origins=['https://app.apisentinel.dev', 'https://console.apisentinel.dev']",
    },
    {
        "id": "SEC-1012",
        "vulnerability": "Unrestricted File Upload in Avatar Endpoint",
        "endpoint": "POST /api/user/avatar",
        "severity": "High",
        "status": "In Progress",
        "detected_on": "Nov 04",
        "owasp_category": "API8:2023 - Security Misconfiguration",
        "cvss_score": 7.6,
        "description": "Accepts executable MIME types (SVG, HTML, PHP) allowing stored XSS and code execution.",
        "remediation": "Validate file magic bytes, rewrite file names, and serve user assets from isolated sandboxed CDN.",
        "code_snippet": "ALLOWED_MIME = {'image/png', 'image/jpeg', 'image/webp'}",
    },
    {
        "id": "SEC-1013",
        "vulnerability": "XML External Entity (XXE) in Invoice Processing",
        "endpoint": "POST /api/billing/invoice/import",
        "severity": "High",
        "status": "Open",
        "detected_on": "Nov 03",
        "owasp_category": "API8:2023 - Security Misconfiguration",
        "cvss_score": 7.9,
        "description": "XML parser evaluates external entity declarations, facilitating local file disclosure.",
        "remediation": "Disable DTDs (External Entity Resolution) in XML parser configuration.",
        "code_snippet": "parser = defusedxml.lxml.XMLParser(resolve_entities=False)",
    },
    {
        "id": "SEC-1014",
        "vulnerability": "Debug Mode Enabled in Staging Endpoint",
        "endpoint": "GET /api/debug/dump",
        "severity": "High",
        "status": "Fixed",
        "detected_on": "Nov 02",
        "owasp_category": "API8:2023 - Security Misconfiguration",
        "cvss_score": 7.1,
        "description": "Endpoint returns full stack traces, environment variables, and unmasked connection strings.",
        "remediation": "Disable DEBUG flag in production and teardown staging debug routes.",
        "code_snippet": "if not settings.IS_PRODUCTION: router.include_router(debug_router)",
    },
    {
        "id": "SEC-1015",
        "vulnerability": "JWT Algorithm Confusion (None / HS256)",
        "endpoint": "POST /api/v1/auth/verify",
        "severity": "High",
        "status": "Verified",
        "detected_on": "Nov 01",
        "owasp_category": "API2:2023 - Broken Authentication",
        "cvss_score": 7.8,
        "description": "Backend accepts JWT tokens with 'alg': 'none' allowing arbitrary signature bypass.",
        "remediation": "Explicitly whitelist allowed signature algorithms during verification.",
        "code_snippet": "jwt.decode(token, key, algorithms=['RS256'])",
    },
    {
        "id": "SEC-1016",
        "vulnerability": "Sensitive Data Exposure in Error Responses",
        "endpoint": "POST /api/orders/checkout",
        "severity": "High",
        "status": "Fixed",
        "detected_on": "Oct 31",
        "owasp_category": "API3:2023 - Broken Object Property Level Authorization",
        "cvss_score": 7.2,
        "description": "Payment failure returns unmasked credit card fragments and payment gateway credentials.",
        "remediation": "Sanitize API exception handlers to output generic user-friendly messages only.",
        "code_snippet": "return JSONResponse(status_code=400, content={'error': 'Payment failed. Please retry.'})",
    },
    {
        "id": "SEC-1017",
        "vulnerability": "IDOR in Organization Billing Invoice Download",
        "endpoint": "GET /api/invoices/{invoice_id}/pdf",
        "severity": "High",
        "status": "Verified",
        "detected_on": "Oct 30",
        "owasp_category": "API1:2023 - Broken Object Level Authorization",
        "cvss_score": 7.7,
        "description": "Sequential invoice ID parameters allows users to download third-party customer receipts.",
        "remediation": "Use random UUIDs and enforce tenant boundary ownership check.",
        "code_snippet": "where(Invoice.id == invoice_id, Invoice.org_id == current_user.org_id)",
    },
    {
        "id": "SEC-1018",
        "vulnerability": "Missing Content-Type Validation",
        "endpoint": "POST /api/integrations/slack",
        "severity": "High",
        "status": "Fixed",
        "detected_on": "Oct 29",
        "owasp_category": "API8:2023 - Security Misconfiguration",
        "cvss_score": 7.0,
        "description": "Accepts arbitrary non-JSON payloads without validation, causing unhandled worker exceptions.",
        "remediation": "Enforce Strict application/json header validation on incoming requests.",
        "code_snippet": "if request.headers.get('content-type') != 'application/json': raise 415",
    },
]

# Ensure we have 37 total items for the detailed findings view
def get_all_37_findings() -> List[Dict[str, Any]]:
    findings = list(ALL_VULNERABILITIES)
    # Generate remaining items to match exactly 37
    medium_count = 14 - sum(1 for f in findings if f["severity"] == "Medium")
    low_count = 7 - sum(1 for f in findings if f["severity"] == "Low")
    
    id_counter = 1019
    for i in range(medium_count):
        findings.append({
            "id": f"SEC-{id_counter}",
            "vulnerability": f"Medium Risk: Excessive Data Exposure in Record #{i+1}",
            "endpoint": f"GET /api/v2/items/{100+i}",
            "severity": "Medium",
            "status": "Fixed" if i % 2 == 0 else "In Progress",
            "detected_on": f"Oct {28 - (i % 5)}",
            "owasp_category": "API3:2023 - Broken Object Property Level Authorization",
            "cvss_score": 5.0 + (i * 0.1),
            "description": "API responses return internal metadata fields not required by consumer applications.",
            "remediation": "Filter fields using response serialization models.",
            "code_snippet": "class ItemPublic(BaseModel):\n    id: str\n    name: str",
        })
        id_counter += 1

    for j in range(low_count):
        findings.append({
            "id": f"SEC-{id_counter}",
            "vulnerability": f"Low Risk: Verbose Server Banner Information #{j+1}",
            "endpoint": f"HEAD /api/v1/ping",
            "severity": "Low",
            "status": "Verified" if j % 2 == 0 else "Fixed",
            "detected_on": f"Oct {25 - (j % 5)}",
            "owasp_category": "API8:2023 - Security Misconfiguration",
            "cvss_score": 3.2 + (j * 0.1),
            "description": "Server reveals exact web server and kernel version headers.",
            "remediation": "Strip 'Server' and 'X-Powered-By' response headers in gateway configuration.",
            "code_snippet": "server_tokens off;",
        })
        id_counter += 1

    return findings

# Last Scan Summary (Exact from user specification)
LAST_SCAN_SUMMARY = {
    "target_api": "https://demo-api.apisentinel.dev",
    "scan_type": "Full Security Scan",
    "findings_count": 7,
    "findings_breakdown": {
        "Critical": 2,
        "High": 2,
        "Medium": 2,
        "Low": 1
    },
    "completed_on": "Nov 09, 2026, 14:32",
    "duration": "3 min 26 sec",
    "endpoints_scanned": 42,
    "security_score": "76 / 100",
    "status": "Passed with Warnings"
}

# Scan History (24 Total Past Scans)
SCAN_HISTORY_LOG = [
    {
        "id": "SCAN-2026-1109-01",
        "target": "https://demo-api.apisentinel.dev",
        "scan_type": "Full Security Scan",
        "timestamp": "Nov 09, 2026, 14:32",
        "duration": "3m 26s",
        "endpoints": 42,
        "critical": 2,
        "high": 2,
        "medium": 2,
        "low": 1,
        "status": "Completed",
    },
    {
        "id": "SCAN-2026-1109-02",
        "target": "https://auth.apisentinel.dev",
        "scan_type": "Authentication & Token Audit",
        "timestamp": "Nov 09, 2026, 09:15",
        "duration": "1m 45s",
        "endpoints": 12,
        "critical": 1,
        "high": 1,
        "medium": 0,
        "low": 1,
        "status": "Completed",
    },
    {
        "id": "SCAN-2026-1108-01",
        "target": "https://payment.apisentinel.dev",
        "scan_type": "PCI-DSS Pre-Audit",
        "timestamp": "Nov 08, 2026, 16:50",
        "duration": "4m 10s",
        "endpoints": 28,
        "critical": 0,
        "high": 2,
        "medium": 3,
        "low": 2,
        "status": "Completed",
    },
    {
        "id": "SCAN-2026-1107-01",
        "target": "https://demo-api.apisentinel.dev",
        "scan_type": "OWASP API Top 10",
        "timestamp": "Nov 07, 2026, 11:20",
        "duration": "2m 58s",
        "endpoints": 42,
        "critical": 3,
        "high": 3,
        "medium": 4,
        "low": 3,
        "status": "Completed",
    },
    {
        "id": "SCAN-2026-1106-01",
        "target": "https://staging.apisentinel.dev",
        "scan_type": "Regression Test Scan",
        "timestamp": "Nov 06, 2026, 18:05",
        "duration": "2m 14s",
        "endpoints": 34,
        "critical": 1,
        "high": 1,
        "medium": 2,
        "low": 1,
        "status": "Completed",
    },
]
