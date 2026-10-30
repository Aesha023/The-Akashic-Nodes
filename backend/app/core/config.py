"""Backend application settings from environment variables.

Secrets live only in .env (git-ignored) and are read here.
Never print secrets in logs, test output or the context file (Section 0.2).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentMode(StrEnum):
    """Deployment mode (constraint C)."""

    FULL = "full"
    SHOWCASE = "showcase"


class SecureMode(StrEnum):
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

    # Environment
    app_env: str = "dev"
    env: str = "dev"

    # Deployment
    pravahx_repo_url: str = ""
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

    # Alerts & Notifications (F16/F17)
    alert_webhook_url: str = ""
    alert_email_to: str = ""
    alert_email_from: str = "alerts@pravahx.local"
    smtp_host: str = "localhost"
    smtp_port: int = 1025

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

    @model_validator(mode="after")
    def validate_production_credentials(self) -> Self:
        """Ensure no default/insecure credentials are used outside development mode."""
        env_val = (self.app_env or self.env or "").lower().strip()
        if env_val not in ("dev", "development", "test"):
            # Check secret_key
            sec = self.secret_key.get_secret_value() if self.secret_key else ""
            insecure_secret_defaults = {
                "",
                "changeme",
                "secret",
                "pravahx_super_secret_jwt_key_default_32_bytes_long",
                "default",
            }
            if not sec or sec in insecure_secret_defaults or len(sec) < 32:
                msg = (
                    "Production security violation: SECRET_KEY must be at least "
                    f"32 chars (got {len(sec)}) in '{env_val}'."
                )
                raise ValueError(msg)

            # Check postgres_password
            pg_pw = self.postgres_password.get_secret_value() if self.postgres_password else ""
            insecure_pg_defaults = {
                "",
                "postgres",
                "password",
                "pravahx_dev_secret",
                "test_password",
            }
            if not pg_pw or pg_pw in insecure_pg_defaults:
                msg = (
                    "Production security violation: POSTGRES_PASSWORD cannot be "
                    f"default/empty in '{env_val}'."
                )
                raise ValueError(msg)

            # Check s3_secret_key
            s3_pw = self.s3_secret_key.get_secret_value() if self.s3_secret_key else ""
            insecure_s3_defaults = {"", "minioadmin", "password"}
            if not s3_pw or s3_pw in insecure_s3_defaults:
                msg = (
                    "Production security violation: S3_SECRET_KEY cannot be "
                    f"default/empty in '{env_val}'."
                )
                raise ValueError(msg)

        return self
