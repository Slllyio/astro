"""Async SQLAlchemy 2.0 engine, session factory, and FastAPI DB dependency."""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _resolve_url(url: str) -> str:
    """Rewrite plain postgres URLs to use asyncpg; pass aiosqlite URLs through."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite+aiosqlite:"):
        return url
    if url.startswith("sqlite:"):
        return url.replace("sqlite:", "sqlite+aiosqlite:", 1)
    return url


DB_URL = _resolve_url(settings.DATABASE_URL)

engine = create_async_engine(DB_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Concurrent reads + writes against SQLite require WAL journal mode; the default
# rollback journal serializes every reader against every writer and the daemon
# starts producing 'database is locked' errors within minutes. See plan
# constraint #4 for context. WAL is a no-op for :memory: and for Postgres URLs.
#
# Async-pool caveat: on aiosqlite the engine.sync_engine 'connect' event does
# fire because aiosqlite ultimately produces a real DBAPI connection in a thread
# pool. If WAL ever fails to take effect, rebind to engine.pool instead.
if "sqlite" in DB_URL:

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_wal(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a per-request async session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables. Prototype-only; real deployments use Alembic migrations."""
    from app.models.domain import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
