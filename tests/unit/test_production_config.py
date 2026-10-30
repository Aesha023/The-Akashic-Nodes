"""Unit tests verifying production refuses to start with default/insecure credentials (P2)."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from backend.app.core.config import Settings


def test_dev_mode_allows_empty_or_default_credentials() -> None:
    """Dev and test modes allow local development defaults without raising."""
    settings = Settings(app_env="dev")
    assert settings.app_env == "dev"

    settings_test = Settings(app_env="test")
    assert settings_test.app_env == "test"


def test_production_refuses_default_secret_key() -> None:
    """Production mode must refuse default or empty SECRET_KEY."""
    with pytest.raises(ValueError, match="SECRET_KEY must be a strong secret"):
        Settings(
            app_env="production",
            secret_key=SecretStr("changeme"),
            postgres_password=SecretStr("secure_prod_pg_password_123!"),
            s3_secret_key=SecretStr("secure_prod_s3_key_456!"),
        )


def test_production_refuses_default_postgres_password() -> None:
    """Production mode must refuse default or insecure POSTGRES_PASSWORD."""
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD cannot be default/empty"):
        Settings(
            app_env="production",
            secret_key=SecretStr("a" * 32),
            postgres_password=SecretStr("postgres"),
            s3_secret_key=SecretStr("secure_prod_s3_key_456!"),
        )


def test_production_refuses_default_s3_secret() -> None:
    """Production mode must refuse default minioadmin S3_SECRET_KEY."""
    with pytest.raises(ValueError, match="S3_SECRET_KEY cannot be default/empty"):
        Settings(
            app_env="production",
            secret_key=SecretStr("a" * 32),
            postgres_password=SecretStr("secure_prod_pg_password_123!"),
            s3_secret_key=SecretStr("minioadmin"),
        )


def test_production_starts_cleanly_with_secure_credentials() -> None:
    """Production mode starts cleanly when all credentials are secure and non-default."""
    settings = Settings(
        app_env="production",
        secret_key=SecretStr("super_secure_production_secret_key_32_chars_minimum!"),
        postgres_password=SecretStr("strong_production_postgres_password_987#"),
        s3_secret_key=SecretStr("strong_production_minio_s3_secret_key_654@"),
    )
    assert settings.app_env == "production"
