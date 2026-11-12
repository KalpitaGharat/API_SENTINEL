"""API Sentinel - Main FastAPI Application.

Central backend for explainable API security testing and remediation.
Connects the security testing engine, SQLite persistence, NVIDIA Nemotron,
and the Streamlit frontend.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, get_db
from app.schemas import HealthResponse
from app.routes import scans, findings, retesting, reports, events, dataset, targets

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api_sentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: Initialize database tables on startup."""
    logger.info("Initializing API Sentinel database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down API Sentinel Backend.")


app = FastAPI(
    title="API Sentinel Backend",
    description=(
        "Explainable API Security Testing and Remediation Platform for Student Developers and Small Businesses.\n\n"
        "**Core Capabilities:**\n"
        "- Automated testing for BOLA/IDOR, Authentication Weaknesses, and Missing Headers.\n"
        "- AI-assisted explanations and remediation via NVIDIA Nemotron.\n"
        "- Verification and retesting workflow to confirm vulnerability fixes."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (Configurable for local Streamlit frontend development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root health probe",
)
def root_health():
    """Return backend operational status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        database="connected",
    )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="API and Database health check",
)
def api_health(db: Session = Depends(get_db)):
    """Verify backend and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as db_err:
        logger.error("Database health check failed: %s", db_err)
        db_status = f"unhealthy: {str(db_err)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        database=db_status,
    )


# Register Routers
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(retesting.router)
app.include_router(reports.router)
app.include_router(events.router)
app.include_router(dataset.router)
app.include_router(targets.router)

# Mount compiled production React dashboard at root if built
import os
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
