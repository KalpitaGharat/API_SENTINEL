"""In-memory synchronous HTTPX transport for Healthcare Demo API.

Provides seamless, high-speed, direct execution of Demo API endpoints for testing
without requiring background network daemons, open sockets, or inter-thread IPC.
"""

import json
from typing import Optional
import httpx
from fastapi import HTTPException

from demo_api.config import settings
from demo_api.main import (
    health_check,
    login,
    LoginRequest,
    get_current_user,
    get_my_profile,
    get_patient_record,
    get_admin_metrics,
    toggle_demo_mode,
    ModeToggleRequest,
)


class DemoApiTransport(httpx.BaseTransport):
    """Synchronous in-process transport executing Demo API routes."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        auth_hdr = request.headers.get("Authorization")

        # Build response headers matching security headers middleware
        resp_headers = {
            "Content-Type": "application/json",
            "Server": "uvicorn",
        }
        if settings.ENABLE_SECURITY_HEADERS or not settings.DEMO_VULNERABLE_MODE:
            resp_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            resp_headers["X-Content-Type-Options"] = "nosniff"
            resp_headers["X-Frame-Options"] = "DENY"
            resp_headers["Content-Security-Policy"] = "default-src 'self'"
            resp_headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        try:
            # 1. Health check
            if path == "/health":
                return httpx.Response(200, json=health_check(), headers=resp_headers, request=request)

            # 2. Authentication Login
            elif path == "/api/auth/login" and request.method == "POST":
                body = json.loads(request.content.decode("utf-8")) if request.content else {}
                res = login(LoginRequest(**body))
                return httpx.Response(200, json=res.model_dump(), headers=resp_headers, request=request)

            # 3. Patient Self Profile
            elif path == "/api/patients/me":
                user = get_current_user(auth_hdr)
                return httpx.Response(200, json=get_my_profile(user), headers=resp_headers, request=request)

            # 4. Patient Medical Record (BOLA target)
            elif path.startswith("/api/patients/") and request.method == "GET":
                user = get_current_user(auth_hdr)
                parts = path.rstrip("/").split("/")
                pid = int(parts[-1])
                rec = get_patient_record(pid, user)
                return httpx.Response(200, json=rec, headers=resp_headers, request=request)

            # 5. Admin Metrics
            elif path == "/api/admin/metrics":
                res = get_admin_metrics(auth_hdr)
                return httpx.Response(200, json=res, headers=resp_headers, request=request)

            # 6. Mode toggle
            elif path == "/api/demo/mode" and request.method == "POST":
                body = json.loads(request.content.decode("utf-8")) if request.content else {}
                admin_hdr = request.headers.get("X-Demo-Admin-Token")
                res = toggle_demo_mode(
                    ModeToggleRequest(**body),
                    x_demo_admin_token=admin_hdr,
                    authorization=auth_hdr,
                )
                return httpx.Response(200, json=res, headers=resp_headers, request=request)

            # Route not found
            else:
                return httpx.Response(404, json={"detail": f"Route {path} not found."}, headers=resp_headers, request=request)

        except HTTPException as exc:
            return httpx.Response(exc.status_code, json={"detail": exc.detail}, headers=resp_headers, request=request)
        except Exception as err:
            return httpx.Response(500, json={"detail": f"Internal server error: {str(err)}"}, headers=resp_headers, request=request)
