"""Configuration for Intentionally Vulnerable Healthcare Demo API."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class DemoSettings(BaseSettings):
    """Healthcare Demo API configuration."""

    HOST: str = "127.0.0.1"
    PORT: int = 8001
    
    # Toggle between vulnerable (BOLA present) and secure (ownership enforced) behavior
    DEMO_VULNERABLE_MODE: bool = True
    
    # Toggle security headers middleware
    ENABLE_SECURITY_HEADERS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = DemoSettings(
    DEMO_VULNERABLE_MODE=os.environ.get("DEMO_VULNERABLE_MODE", "true").lower() in ("true", "1", "yes"),
    ENABLE_SECURITY_HEADERS=os.environ.get("ENABLE_SECURITY_HEADERS", "false").lower() in ("true", "1", "yes"),
)
