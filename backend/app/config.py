"""Configuration management for API Sentinel Backend.

Loads environment variables, validates settings, and provides
centralized access to application configuration.
"""

from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings with environment variable fallback."""

    # Server configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    # Database configuration
    DATABASE_URL: str = "sqlite:///./api_sentinel.db"

    # Safety Controls
    # In production, default to False to strictly block localhost/private IP scanning (SSRF protection).
    # In controlled educational lab environments, set ALLOW_LOCAL_LAB_SCANNING=True in .env.
    ALLOW_LOCAL_LAB_SCANNING: bool = False

    # Target Credential Authenticated Encryption (Fernet)
    TARGET_CREDENTIAL_ENCRYPTION_KEY: str = ""

    # NVIDIA Nemotron AI Configuration
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    AI_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins into a list of strings."""
        if not self.CORS_ORIGINS or not self.CORS_ORIGINS.strip():
            return ["http://localhost:8501", "http://127.0.0.1:8501"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
