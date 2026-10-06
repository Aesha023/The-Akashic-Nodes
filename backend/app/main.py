"""FastAPI application factory and middleware configuration (Phase 7)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1 import api_v1_router
from backend.app.core.config import Settings
from backend.app.db.session import init_db
from pravahx.errors import PravahXError

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Lifespan context manager initializing DB tables on startup."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PravahX API",
        description="Dam break and river blockage inundation modelling platform",
        version="0.1.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global PravahXError RFC 9457 problem details handler
    @app.exception_handler(PravahXError)
    async def pravahx_error_handler(request: Request, exc: PravahXError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "type": f"https://pravahx.internal/errors/{exc.code.lower()}",
                "title": exc.code,
                "detail": exc.message,
                "instance": str(request.url),
                "context": exc.detail,
            },
        )

    # Include API routers
    app.include_router(api_v1_router)

    return app
