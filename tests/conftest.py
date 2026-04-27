"""Shared pytest fixtures for the Phase 2 test suite.

Disables the background daemon and points the engine at an in-memory SQLite
before any app module is imported. Each test gets a fresh DB via
StaticPool (single shared connection so :memory: state persists across the
session-maker's session boundaries).
"""
from __future__ import annotations

import os

# Must run before any `from app...` import in this package.
os.environ.setdefault("DAEMON_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
# Don't load the vendored Flask portal during tests — its skyfield ephemeris
# would trigger a 16MB JPL download on first run and slow CI substantially.
os.environ.setdefault("PORTAL_ENABLED", "false")
# Force-blank OAuth credentials in tests so `.env` (if present locally) doesn't
# leak real Google credentials into the test session. setdefault is wrong here
# because we WANT to override anything sourced from .env; use direct assignment.
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Imported lazily inside fixtures so app modules see the env-overridden settings.


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Per-test in-memory SQLite engine with a single shared connection."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app.models.domain import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Per-test AsyncSession bound to the test engine."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """httpx AsyncClient against the FastAPI app with get_db overridden.

    Anonymous client - no Authorization header. Use `authed_client` for
    auth-gated routes, or paste a Bearer header into individual requests.
    """
    from app.core.database import get_db
    from app.main import app

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_account(db_engine: AsyncEngine):
    """Insert a single Account row directly via the test engine and yield it.

    Bypasses the OAuth dance entirely; tests that need an authenticated
    identity create one this way and use the JWT below.
    """
    from app.models.domain import Account
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        account = Account(
            google_sub="test-sub-12345",
            email="test@example.com",
            name="Test User",
            picture=None,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        yield account


@pytest_asyncio.fixture
async def authed_client(
    db_engine: AsyncEngine,
    seeded_account,
) -> AsyncIterator[AsyncClient]:
    """AsyncClient pre-loaded with a valid JWT for `seeded_account`.

    Tests requesting this fixture get an httpx client whose default headers
    include `Authorization: Bearer <jwt>`. Use this for any test that hits
    an auth-gated route (POST /profiles, GET /profiles/{id}/transits, /auth/me).
    """
    from app.core.auth import issue_access_token
    from app.core.database import get_db
    from app.main import app

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    token = issue_access_token(seeded_account.id, seeded_account.email)
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
    app.dependency_overrides.clear()
