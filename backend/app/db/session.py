"""Database session and engine init with Postgres and SQLite support (Phase 7)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import Settings
from backend.app.models.base import Base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

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

    pg_url = db_url or settings.database_url
    async_engine = create_async_engine(pg_url, echo=False, future=True)
    async_session_factory = async_sessionmaker(
        bind=async_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def init_db() -> None:
        import backend.app.models  # noqa: F401

        async with async_engine.begin() as conn:
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
    # Standard SQLite via sync session with async adapter interface
    sqlite_url = "sqlite:///./pravahx_dev.db"
    sync_engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})
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
