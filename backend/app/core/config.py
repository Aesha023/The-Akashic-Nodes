"""Backend application settings from environment variables.

Secrets live only in .env (git-ignored) and are read here.
Never print secrets in logs, test output or the context file (Section 0.2).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentMode(str, Enum):
    """Deployment mode (constraint C)."""

    FULL = "full"
    SHOWCASE = "showcase"


class SecureMode(str, Enum):
    """Secure mode setting (decision D001 — system-level only)."""

    ONLINE = "online"
    SECURE = "secure"


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Deployment
    pravahx_deployment_mode: DeploymentMode = DeploymentMode.FULL
    pravahx_secure_mode: SecureMode = SecureMode.ONLINE

    # Database
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "pravahx"
    postgres_user: str = ""
    postgres_password: SecretStr = SecretStr("")

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Object storage
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: SecretStr = SecretStr("")
    s3_secret_key: SecretStr = SecretStr("")
    s3_bucket_artifacts: str = "pravahx-artifacts"
    s3_bucket_exports: str = "pravahx-exports"
    s3_region: str = "us-east-1"

    # Security
    secret_key: SecretStr = SecretStr("")
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Earth Engine (Phase 6)
    gee_service_account_email: str = ""
    gee_service_account_key_file: str = ""
    gee_project_id: str = ""

    # DualSPHysics (constraint A)
    dualsphysics_mode: Literal["cpu", "remote_gpu", "precomputed"] = "cpu"

    # Frontend
    vite_api_url: str = "http://localhost:8000/api/v1"

    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_showcase(self) -> bool:
        """Whether in read-only showcase mode."""
        return self.pravahx_deployment_mode == DeploymentMode.SHOWCASE

    @property
    def is_secure(self) -> bool:
        """Whether outbound network calls are blocked."""
        return self.pravahx_secure_mode == SecureMode.SECURE
