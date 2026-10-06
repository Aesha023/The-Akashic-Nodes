"""Google Earth Engine client initialization and authentication (Phase 6 / Section 6)."""

from __future__ import annotations

import os
from pathlib import Path

from pravahx.errors import CredentialsError


class GEEClient:
    """Manager for Google Earth Engine session and service account authentication."""

    def __init__(
        self,
        service_account: str | None = None,
        key_file: str | Path | None = None,
        project: str | None = None,
    ) -> None:
        self.service_account = service_account or os.environ.get("EE_SERVICE_ACCOUNT")
        self.key_file = key_file or os.environ.get("EE_KEY_FILE")
        self.project = project or os.environ.get("EE_PROJECT")
        self._is_initialized = False

    def initialize(self) -> bool:
        """Initialize GEE if credentials are valid and ee package is available.

        Returns True if live GEE is authenticated, False if offline/mock fallback.
        """
        try:
            import ee  # type: ignore

            if self.service_account and self.key_file:
                key_path = Path(self.key_file)
                if not key_path.exists():
                    raise CredentialsError(
                        f"GEE service account key file not found: {key_path}",
                        detail={"key_file": str(key_path)},
                    )
                credentials = ee.ServiceAccountCredentials(self.service_account, str(key_path))
                ee.Initialize(credentials, project=self.project)
                self._is_initialized = True
                return True
            else:
                # Attempt default auth
                try:
                    ee.Initialize(project=self.project)
                    self._is_initialized = True
                    return True
                except Exception:
                    self._is_initialized = False
                    return False
        except ImportError:
            self._is_initialized = False
            return False

    @property
    def is_connected(self) -> bool:
        """Return whether active connection to Earth Engine is established."""
        return self._is_initialized
