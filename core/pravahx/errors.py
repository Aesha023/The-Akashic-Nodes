"""Typed error hierarchy for PravahX.

Every error is typed and carries structured context. Errors surface to the
user through the API as problem-details JSON (RFC 9457) with a stable ``code``,
a human message and a ``trace_id``.

This module is used by both the core science package and the backend.
"""

from __future__ import annotations

from typing import Any


class PravahXError(Exception):
    """Base error for the entire PravahX system.

    All errors carry:
    - code: stable machine-readable error code (e.g. "CONFIG_INVALID")
    - message: human-readable description
    - detail: optional structured context
    """

    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


# ── Configuration ────────────────────────────────────────────────────────────


class ConfigError(PravahXError):
    """Scenario configuration is invalid."""

    code = "CONFIG_INVALID"


class ConfigFieldError(ConfigError):
    """A specific config field failed validation."""

    code = "CONFIG_FIELD_INVALID"

    def __init__(
        self,
        message: str,
        *,
        field: str,
        value: Any = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = detail or {}
        detail["field"] = field
        if value is not None:
            detail["value"] = str(value)
        super().__init__(message, detail=detail)
        self.field = field


# ── Data ─────────────────────────────────────────────────────────────────────


class DataError(PravahXError):
    """Error accessing, downloading or processing input data."""

    code = "DATA_ERROR"


class DataNotFoundError(DataError):
    """Required data was not found."""

    code = "DATA_NOT_FOUND"


class DataCorruptError(DataError):
    """Data failed integrity check (hash mismatch)."""

    code = "DATA_CORRUPT"


class DataAccessDeniedError(DataError):
    """Credentials missing or insufficient for a data source."""

    code = "DATA_ACCESS_DENIED"


# ── Engine ───────────────────────────────────────────────────────────────────


class EngineError(PravahXError):
    """Error from a hydrodynamic engine."""

    code = "ENGINE_ERROR"

    def __init__(
        self,
        message: str,
        *,
        engine: str,
        log_path: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = detail or {}
        detail["engine"] = engine
        if log_path is not None:
            detail["log_path"] = log_path
        super().__init__(message, detail=detail)
        self.engine = engine
        self.log_path = log_path


class EngineNotInstalledError(EngineError):
    """The engine binary or container is not available."""

    code = "ENGINE_NOT_INSTALLED"


class EngineTimeoutError(EngineError):
    """The engine exceeded its time limit."""

    code = "ENGINE_TIMEOUT"


class EngineDivergenceError(EngineError):
    """The solver diverged (permanent failure, do not retry)."""

    code = "ENGINE_DIVERGED"


class EnginePrecomputedError(EngineError):
    """Error importing or verifying precomputed engine results."""

    code = "ENGINE_PRECOMPUTED_ERROR"


# ── Pipeline ─────────────────────────────────────────────────────────────────


class PipelineError(PravahXError):
    """Error in the pipeline orchestrator."""

    code = "PIPELINE_ERROR"


class StageError(PipelineError):
    """A pipeline stage failed."""

    code = "STAGE_ERROR"

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        attempt: int = 1,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = detail or {}
        detail["stage"] = stage
        detail["attempt"] = attempt
        super().__init__(message, detail=detail)
        self.stage = stage
        self.attempt = attempt


class CheckpointError(PipelineError):
    """Checkpoint save, load or verification failed."""

    code = "CHECKPOINT_ERROR"


# ── Provenance ───────────────────────────────────────────────────────────────


class ProvenanceError(PravahXError):
    """Integrity check on a run artefact failed."""

    code = "PROVENANCE_ERROR"


class HashMismatchError(ProvenanceError):
    """A file hash does not match its recorded value."""

    code = "HASH_MISMATCH"

    def __init__(
        self,
        message: str,
        *,
        path: str,
        expected: str,
        actual: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = detail or {}
        detail.update({"path": path, "expected": expected, "actual": actual})
        super().__init__(message, detail=detail)


# ── Coupling ─────────────────────────────────────────────────────────────────


class CouplingError(PravahXError):
    """Error in SPH-to-FM coupling."""

    code = "COUPLING_ERROR"


class VolumeConservationError(CouplingError):
    """Volume conservation check failed at the coupling hand-off."""

    code = "VOLUME_CONSERVATION_ERROR"

    def __init__(
        self,
        message: str,
        *,
        expected_m3: float,
        actual_m3: float,
        tolerance: float,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = detail or {}
        detail.update(
            {
                "expected_m3": expected_m3,
                "actual_m3": actual_m3,
                "tolerance": tolerance,
                "error_fraction": abs(actual_m3 - expected_m3) / expected_m3
                if expected_m3 > 0
                else float("inf"),
            }
        )
        super().__init__(message, detail=detail)


# ── Egress / secure mode ────────────────────────────────────────────────────


class EgressBlockedError(PravahXError):
    """An outbound network call was blocked by secure mode or the allow-list."""

    code = "EGRESS_BLOCKED"


# ── Auth (backend) ───────────────────────────────────────────────────────────


class AuthError(PravahXError):
    """Authentication or authorisation error."""

    code = "AUTH_ERROR"


class CredentialsError(AuthError):
    """Invalid credentials."""

    code = "CREDENTIALS_INVALID"


class TokenExpiredError(AuthError):
    """Access or refresh token has expired."""

    code = "TOKEN_EXPIRED"


class PermissionDeniedError(AuthError):
    """The user does not have the required permission."""

    code = "PERMISSION_DENIED"

    def __init__(
        self,
        message: str,
        *,
        required_permission: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = detail or {}
        detail["required_permission"] = required_permission
        super().__init__(message, detail=detail)


class RateLimitedError(AuthError):
    """Too many requests."""

    code = "RATE_LIMITED"


# ── Not found / conflict ────────────────────────────────────────────────────


class NotFoundError(PravahXError):
    """Resource not found."""

    code = "NOT_FOUND"


class ConflictError(PravahXError):
    """Optimistic locking conflict (stale version)."""

    code = "CONFLICT"


class IdempotencyConflictError(ConflictError):
    """Idempotency key already used with a different request."""

    code = "IDEMPOTENCY_CONFLICT"
