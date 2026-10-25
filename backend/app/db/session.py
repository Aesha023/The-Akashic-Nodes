"""Database session and engine init with Postgres and SQLite support (Phase 7)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import Settings
from backend.app.models.base import Base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Patch GeoAlchemy2 sqlite dialect to gracefully ignore SpatiaLite DDL functions
# when running on SQLite without SpatiaLite (e.g. offline unit testing)
try:
    from geoalchemy2.admin.dialects import sqlite as geo_sqlite

    orig_after_create = geo_sqlite.after_create

    def safe_geo_after_create(table: Any, bind: Any, **kw: Any) -> None:
        try:
            orig_after_create(table, bind, **kw)  # type: ignore[no-untyped-call]
        except Exception as e:
            if "no such function" in str(e) or "RecoverGeometryColumn" in str(e):
                pass
            else:
                raise

    geo_sqlite.after_create = safe_geo_after_create
except Exception:
    pass

settings = Settings()

# Check if postgres credentials are provided or database URL is set
db_url = os.environ.get("DATABASE_URL", "")
use_postgres = bool(db_url.startswith("postgresql") or settings.postgres_user)

if use_postgres:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.pool import NullPool

    pg_url = db_url or settings.database_url
    async_engine = create_async_engine(pg_url, poolclass=NullPool, echo=False, future=True)
    async_session_factory = async_sessionmaker(
        bind=async_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    sync_pg_url = pg_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    if not sync_pg_url.startswith("postgresql+psycopg://") and sync_pg_url.startswith(
        "postgresql://"
    ):
        sync_pg_url = sync_pg_url.replace("postgresql://", "postgresql+psycopg://")
    sync_engine = create_engine(sync_pg_url, poolclass=NullPool, echo=False)
    sync_session_factory = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

    async def init_db() -> None:
        import backend.app.models  # noqa: F401

        async with async_engine.begin() as conn:
            # Enable PostGIS extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            await conn.run_sync(Base.metadata.create_all)

    async def get_db() -> AsyncGenerator[Any, None]:
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
else:
    import sqlite3

    from sqlalchemy import event

    sqlite_url = "sqlite:///./pravahx_dev.db"
    sync_engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})

    @event.listens_for(sync_engine, "connect")
    def _setup_sqlite_spatial_functions(dbapi_connection: Any, connection_record: Any) -> None:
        if isinstance(dbapi_connection, sqlite3.Connection):
            dummy_ewkb = (
                b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00"
            )
            dbapi_connection.create_function("AsEWKB", -1, lambda *args: dummy_ewkb)
            dbapi_connection.create_function(
                "GeomFromWKB", -1, lambda *args: args[0] if args else None
            )
            dbapi_connection.create_function("GeomFromEWKT", -1, lambda *args: dummy_ewkb)
            dbapi_connection.create_function("GeomFromText", -1, lambda *args: dummy_ewkb)
            dbapi_connection.create_function("RecoverGeometryColumn", -1, lambda *args: 1)
            dbapi_connection.create_function("CreateSpatialIndex", -1, lambda *args: 1)

    sync_session_factory = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

    class DatabaseSessionAdapter:
        """Async-compatible wrapper around synchronous SQLAlchemy session for SQLite."""

        def __init__(self, session: Session) -> None:
            self._session = session

        async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
            return self._session.execute(statement, *args, **kwargs)

        def add(self, instance: Any) -> None:
            self._session.add(instance)

        async def flush(self) -> None:
            self._session.flush()

        async def commit(self) -> None:
            self._session.commit()

        async def rollback(self) -> None:
            self._session.rollback()

        async def delete(self, instance: Any) -> None:
            self._session.delete(instance)

        async def close(self) -> None:
            self._session.close()

    async def init_db() -> None:

        Base.metadata.create_all(sync_engine)

    # Automatically create tables for SQLite on import
    import backend.app.models  # noqa: F401

    Base.metadata.create_all(sync_engine)
    with sync_engine.begin() as conn:
        import contextlib

        for col_sql in [
            "ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64)",
            "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0",
        ]:
            with contextlib.suppress(Exception):
                conn.execute(text(col_sql))

    async def get_db() -> AsyncGenerator[Any, None]:
        session = sync_session_factory()
        adapter = DatabaseSessionAdapter(session)
        try:
            yield adapter
            await adapter.commit()
        except Exception:
            await adapter.rollback()
            raise
        finally:
            await adapter.close()
