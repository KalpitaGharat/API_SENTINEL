"""Intentionally Vulnerable Healthcare Demo API for API Sentinel Testing.

Provides controlled endpoints with synthetic medical records to demonstrate:
1. Broken Object Level Authorization (BOLA/IDOR) on GET /api/patients/{patient_id}
2. Authentication weaknesses and token validation
3. HTTP security header evaluation
4. Mode toggle between Vulnerable (default) and Secure (remediated) behavior
"""

import os
import secrets
from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from demo_api.config import settings

app = FastAPI(
    title="Healthcare Demo API (Synthetic Lab)",
    description="Intentionally vulnerable test API for API Sentinel vulnerability detection.",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# Synthetic Data Stores (Zero Real Patient Data)
# -----------------------------------------------------------------------------

SYNTHETIC_USERS: Dict[str, Dict[str, Any]] = {
    "patient_a": {
        "id": 101,
        "username": "patient_a",
        "password": "demo_password_a",
        "name": "Synthetic Patient A (Alice)",
        "owned_record_id": 101,
    },
    "patient_b": {
        "id": 102,
        "username": "patient_b",
        "password": "demo_password_b",
        "name": "Synthetic Patient B (Bob)",
        "owned_record_id": 102,
    },
}

SYNTHETIC_RECORDS: Dict[int, Dict[str, Any]] = {
    101: {
        "patient_id": 101,
        "owner_id": 101,
        "owner_username": "patient_a",
        "full_name": "Synthetic Patient A",
        "diagnosis": "Type 1 Diabetes (Synthetic Record)",
        "prescription": "Insulin Glargine 20 units daily",
        "attending_physician": "Dr. Gregory House (Synthetic)",
        "ssn_last4": "0101",
    },
    102: {
        "patient_id": 102,
        "owner_id": 102,
        "owner_username": "patient_b",
        "full_name": "Synthetic Patient B",
        "diagnosis": "Cardiac Arrhythmia (Synthetic Record)",
        "prescription": "Metoprolol Succinate 50mg daily",
        "attending_physician": "Dr. James Wilson (Synthetic)",
        "ssn_last4": "0202",
    },
}

# Controlled active tokens
DEMO_TOKENS: Dict[str, str] = {
    "sentinel_token_patient_a_101": "patient_a",
    "sentinel_token_patient_b_102": "patient_b",
}


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class ModeToggleRequest(BaseModel):
    vulnerable: bool
    enable_security_headers: Optional[bool] = None
    admin_token: Optional[str] = None


# -----------------------------------------------------------------------------
# Authentication Helpers
# -----------------------------------------------------------------------------

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extract and validate bearer token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Bearer token required.",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected 'Bearer <token>'.",
        )

    token = parts[1]
    username = DEMO_TOKENS.get(token)
    if not username or username not in SYNTHETIC_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    return SYNTHETIC_USERS[username]


# -----------------------------------------------------------------------------
# Security Headers Middleware
# -----------------------------------------------------------------------------

@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    """Optionally apply standard HTTP security headers based on configuration."""
    response = await call_next(request)
    
    # In secure mode or if ENABLE_SECURITY_HEADERS is enabled, add headers
    if settings.ENABLE_SECURITY_HEADERS or not settings.DEMO_VULNERABLE_MODE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """Return operational status and active mode."""
    return {
        "status": "healthy",
        "service": "healthcare_demo_api",
        "vulnerable_mode": settings.DEMO_VULNERABLE_MODE,
        "security_headers": settings.ENABLE_SECURITY_HEADERS or not settings.DEMO_VULNERABLE_MODE,
        "admin_auth_configured": bool(settings.DEMO_ADMIN_TOKEN and settings.DEMO_ADMIN_TOKEN.strip()),
    }


@app.post("/api/auth/login", response_model=LoginResponse, tags=["Authentication"])
def login(payload: LoginRequest):
    """Authenticate synthetic test patient and return a bearer token."""
    user = SYNTHETIC_USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = f"sentinel_token_{user['username']}_{user['id']}"
    DEMO_TOKENS[token] = user["username"]

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["id"],
        username=user["username"],
    )


@app.get("/api/patients/me", tags=["Patients"])
def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve authenticated patient's own profile."""
    return {
        "user_id": current_user["id"],
        "username": current_user["username"],
        "name": current_user["name"],
        "owned_record_id": current_user["owned_record_id"],
    }


@app.get("/api/patients/{patient_id}", tags=["Patients"])
def get_patient_record(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Fetch patient medical record.

    SECURITY VULNERABILITY (BOLA/IDOR):
    - When DEMO_VULNERABLE_MODE=True: returns record without verifying ownership (BOLA!).
    - When DEMO_VULNERABLE_MODE=False: returns 403 Forbidden if current_user["id"] != record["owner_id"].
    """
    record = SYNTHETIC_RECORDS.get(patient_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient record {patient_id} not found.",
        )

    # SECURE MODE: Validate server-side record ownership
    if not settings.DEMO_VULNERABLE_MODE:
        if record["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You are not authorized to access record {patient_id}.",
            )

    # VULNERABLE MODE: Return record to any authenticated user
    return record


@app.get("/api/admin/metrics", tags=["Admin"])
def get_admin_metrics(authorization: Optional[str] = Header(None)):
    """Administrative metrics endpoint.

    When tested unauthenticated, demonstrates broken authentication if unprotected.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for administrative metrics.",
        )
    return {
        "cpu_utilization": "18%",
        "memory_used_mb": 420,
        "active_sessions": len(DEMO_TOKENS),
    }


def extract_and_verify_admin_token(
    payload: ModeToggleRequest,
    x_demo_admin_token: Optional[str] = None,
    authorization: Optional[str] = None,
) -> bool:
    """Validate admin token using constant-time comparison against DEMO_ADMIN_TOKEN."""
    expected = settings.DEMO_ADMIN_TOKEN
    if not expected or not expected.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Demo mode modification is disabled because DEMO_ADMIN_TOKEN is not configured on the server.",
        )

    # 1. Extract token from X-Demo-Admin-Token header
    token = x_demo_admin_token

    # 2. Extract token from Authorization: Bearer <token>
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    # 3. Extract token from JSON payload body
    if not token and payload.admin_token:
        token = payload.admin_token

    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing demo admin token. Provide 'X-Demo-Admin-Token', 'Authorization: Bearer <token>', or 'admin_token' in JSON body.",
        )

    # Constant-time comparison prevents timing analysis
    if not secrets.compare_digest(token.strip(), expected.strip()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid demo admin token.",
        )

    return True


@app.post("/api/demo/mode", tags=["Demo Controls"])
def toggle_demo_mode(
    payload: ModeToggleRequest,
    x_demo_admin_token: Optional[str] = Header(None, alias="X-Demo-Admin-Token"),
    authorization: Optional[str] = Header(None),
):
    """Dynamic toggle between vulnerable and secure mode for live testing.

    SECURITY PROTECTION:
    Requires valid DEMO_ADMIN_TOKEN authorization via:
    - 'X-Demo-Admin-Token' header
    - 'Authorization: Bearer <DEMO_ADMIN_TOKEN>' header
    - 'admin_token' field in JSON request body
    """
    extract_and_verify_admin_token(payload, x_demo_admin_token, authorization)

    settings.DEMO_VULNERABLE_MODE = payload.vulnerable
    if payload.enable_security_headers is not None:
        settings.ENABLE_SECURITY_HEADERS = payload.enable_security_headers
    return {
        "status": "updated",
        "vulnerable_mode": settings.DEMO_VULNERABLE_MODE,
        "security_headers": settings.ENABLE_SECURITY_HEADERS or not settings.DEMO_VULNERABLE_MODE,
    }
