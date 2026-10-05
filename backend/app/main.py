"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This is the factory function used by Uvicorn.
    Routes, middleware and event handlers are added in later phases.
    """
    app = FastAPI(
        title="PravahX API",
        description="Dam break and river blockage inundation modelling",
        version="0.1.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )

    @app.get("/api/v1/health/live", tags=["system"])
    async def health_live() -> dict[str, str]:
        """Liveness probe — the process is up."""
        return {"status": "ok"}

    return app
