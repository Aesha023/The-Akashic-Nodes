"""Sliding-window in-memory and Redis rate limiting dependency (B3 Security)."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import ClassVar

from fastapi import HTTPException, Request, status

from backend.app.core.config import Settings

_settings = Settings()


class SlidingWindowRateLimiter:
    """Sliding-window request rate limiter."""

    _requests: ClassVar[dict[str, list[float]]] = defaultdict(list)

    def __init__(self, max_requests: int = 120, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        # Check if rate limiting is disabled in development / test
        if not _settings.is_secure and request.headers.get("X-Test-No-Rate-Limit") == "1":
            return

        now = time.time()
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key")
        key = f"{client_ip}:{api_key}" if api_key else client_ip

        # Clean timestamps older than window
        timestamps = self._requests[key]
        cutoff = now - self.window_seconds
        valid_timestamps = [t for t in timestamps if t > cutoff]

        if len(valid_timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - valid_timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per minute.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        valid_timestamps.append(now)
        self._requests[key] = valid_timestamps

    @classmethod
    def reset(cls) -> None:
        """Clear recorded requests (for testing)."""
        cls._requests.clear()


# Default standard and strict rate limiters
standard_rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)
strict_rate_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)
