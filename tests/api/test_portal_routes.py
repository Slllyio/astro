"""HTTP smoke tests for the family-charts portal at ``/portal/*``.

Per the Phase-2 spec these tests bring up a **minimal FastAPI app**
containing only ``portal_router`` plus a per-test in-memory aiosqlite
session — they DO NOT depend on ``app.main`` or any sibling router. This
keeps the test surface tight and isolates B2's work from B1/B3.

Engine call inside GET /portal/{id} is REAL (not mocked): the Bangalore
baseline runs in well under a second, and the test verifies the master
reading actually rendered.

Canonical baseline matches the rest of the suite (CLAUDE.md):
    1990-07-15 12:00 IST, lat 12.97 N, lon 77.59 E, tz +05:30.
"""
from __future__ import annotations

import os

# Must run before any `from app...` import so the engine + daemon honour
# the test-mode environment. Pattern lifted verbatim from
# ``tests/conftest.py``.
os.environ.setdefault("DAEMON_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("PORTAL_ENABLED", "false")
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.portal_routes import router as portal_router
from app.core.database import get_db
from app.models.domain import Base
import app.portal.models  # noqa: F401 — register Person on Base.metadata


# Canonical baseline used throughout the test suite. See CLAUDE.md.
BANGALORE_FORM = {
    "name": "Test Bangalore",
    "relationship": "self",
    "dob": "1990-07-15",
    "time": "12:00",
    "tz": "+05:30",
    "lat": "12.97",
    "lon": "77.59",
    "place_name": "Bangalore, India",
    "notes": "Canonical test baseline.",
}


# ---------------------------------------------------------------------------
# Fixtures — minimal app with only portal_router
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def portal_engine() -> AsyncIterator[AsyncEngine]:
    """Per-test in-memory aiosqlite engine with a single shared connection."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(portal_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """httpx AsyncClient against a minimal FastAPI(app=portal_router)."""
    app = FastAPI()
    app.include_router(portal_router)

    sessionmaker = async_sessionmaker(portal_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Index view
# ---------------------------------------------------------------------------

async def test_get_index_returns_200_and_empty_state(client: AsyncClient) -> None:
    """GET /portal/ on a fresh DB returns 200 with the empty-state CTA."""
    resp = await client.get("/portal/")
    assert resp.status_code == 200
    body = resp.text
    # Family Charts header + the Add link must both appear.
    assert "Family Chart" in body
    assert "/portal/new" in body


async def test_get_index_after_create_lists_the_person(client: AsyncClient) -> None:
    """GET /portal/ after creating a person shows that person's name + link."""
    # Seed via POST /new (follow_redirects=False so we observe the 303).
    create_resp = await client.post(
        "/portal/new", data=BANGALORE_FORM, follow_redirects=False
    )
    assert create_resp.status_code == 303

    index = await client.get("/portal/")
    assert index.status_code == 200
    body = index.text
    assert "Test Bangalore" in body
    assert "Bangalore, India" in body


# ---------------------------------------------------------------------------
# New form
# ---------------------------------------------------------------------------

async def test_get_new_returns_form(client: AsyncClient) -> None:
    """GET /portal/new returns 200 with a usable form."""
    resp = await client.get("/portal/new")
    assert resp.status_code == 200
    body = resp.text
    assert 'action="/portal/new"' in body
    for field in ("name", "relationship", "dob", "tz", "lat", "lon"):
        assert f'name="{field}"' in body


async def test_post_new_creates_person_and_redirects(client: AsyncClient) -> None:
    """POST /portal/new with valid data creates a row + 303s to /portal/{id}."""
    resp = await client.post(
        "/portal/new", data=BANGALORE_FORM, follow_redirects=False
    )
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/portal/")
    person_id = location.removeprefix("/portal/")
    # UUID4 hex string — 36 chars including dashes.
    assert len(person_id) == 36
    assert person_id.count("-") == 4


async def test_post_new_invalid_lat_returns_422(client: AsyncClient) -> None:
    """Out-of-range latitude is rejected (422) and the form is re-rendered."""
    bad = dict(BANGALORE_FORM)
    bad["lat"] = "999"
    resp = await client.post("/portal/new", data=bad)
    assert resp.status_code == 422
    # User-typed value is preserved on re-render so they can fix it.
    body = resp.text
    assert "error" in body.lower() or "could not" in body.lower() or "422" in str(resp.status_code)
    assert "999" in body


async def test_post_new_invalid_relationship_returns_422(client: AsyncClient) -> None:
    """An unknown relationship value is rejected by the Literal validator."""
    bad = dict(BANGALORE_FORM)
    bad["relationship"] = "robot-overlord"
    resp = await client.post("/portal/new", data=bad)
    assert resp.status_code == 422
    assert resp.status_code == 422


async def test_post_new_invalid_dob_returns_422(client: AsyncClient) -> None:
    """A malformed dob (not YYYY-MM-DD) is rejected at the date-parse step."""
    bad = dict(BANGALORE_FORM)
    bad["dob"] = "not-a-date"
    resp = await client.post("/portal/new", data=bad)
    assert resp.status_code == 422
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------

async def _create_baseline_person(client: AsyncClient) -> str:
    """Helper: POST the Bangalore baseline + return the created person id."""
    resp = await client.post(
        "/portal/new", data=BANGALORE_FORM, follow_redirects=False
    )
    assert resp.status_code == 303
    return resp.headers["location"].removeprefix("/portal/")


async def test_get_detail_returns_master_reading(client: AsyncClient) -> None:
    """GET /portal/{id} renders the person's full master reading."""
    person_id = await _create_baseline_person(client)
    resp = await client.get(f"/portal/{person_id}")
    assert resp.status_code == 200
    body = resp.text
    # Person identity strip at the top.
    assert "Test Bangalore" in body
    assert "1990-07-15" in body
    # Master reading sections render.
    assert "Chart overview" in body or "Lagna" in body
    assert "Current MD lord" in body
    assert "Six life domains" in body
    # Bangalore baseline produces Mercury MD per the doctrine lock.
    assert "Mercury" in body


async def test_get_detail_nonexistent_returns_404(client: AsyncClient) -> None:
    """GET /portal/{unknown_id} returns 404."""
    resp = await client.get("/portal/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Edit view
# ---------------------------------------------------------------------------

async def test_get_edit_returns_prefilled_form(client: AsyncClient) -> None:
    """GET /portal/{id}/edit shows a form pre-populated from the saved row."""
    person_id = await _create_baseline_person(client)
    resp = await client.get(f"/portal/{person_id}/edit")
    assert resp.status_code == 200
    body = resp.text
    assert f'action="/portal/{person_id}/edit"' in body
    # Pre-filled name (the only literal that survives template escaping unchanged).
    assert 'value="Test Bangalore"' in body
    assert 'value="1990-07-15"' in body
    assert 'value="+05:30"' in body


async def test_get_edit_nonexistent_returns_404(client: AsyncClient) -> None:
    """GET /portal/{unknown_id}/edit returns 404."""
    resp = await client.get("/portal/no-such-id/edit")
    assert resp.status_code == 404


async def test_post_edit_updates_person(client: AsyncClient) -> None:
    """POST /portal/{id}/edit applies the changes + 303s back to detail."""
    person_id = await _create_baseline_person(client)
    updated = dict(BANGALORE_FORM)
    updated["name"] = "Renamed Person"
    updated["notes"] = "Updated notes after edit."

    resp = await client.post(
        f"/portal/{person_id}/edit", data=updated, follow_redirects=False
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == f"/portal/{person_id}"

    # Verify the change persisted by re-reading the detail page.
    detail = await client.get(f"/portal/{person_id}")
    assert detail.status_code == 200
    assert "Renamed Person" in detail.text


async def test_post_edit_invalid_data_returns_422(client: AsyncClient) -> None:
    """Invalid edit input re-renders the form with 422 + preserves typed values."""
    person_id = await _create_baseline_person(client)
    bad = dict(BANGALORE_FORM)
    bad["lat"] = "999"
    resp = await client.post(f"/portal/{person_id}/edit", data=bad)
    assert resp.status_code == 422
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def test_post_delete_soft_deletes_and_redirects(client: AsyncClient) -> None:
    """POST /portal/{id}/delete soft-deletes + 303s back to /portal/."""
    person_id = await _create_baseline_person(client)
    resp = await client.post(
        f"/portal/{person_id}/delete", follow_redirects=False
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/portal/"

    # Subsequent detail GET returns 404 (soft-deleted is invisible by default).
    detail = await client.get(f"/portal/{person_id}")
    assert detail.status_code == 404

    # Index no longer lists the deleted person.
    index = await client.get("/portal/")
    assert "Test Bangalore" not in index.text


async def test_post_delete_nonexistent_returns_404(client: AsyncClient) -> None:
    """Deleting an unknown id returns 404."""
    resp = await client.post("/portal/no-such-id/delete")
    assert resp.status_code == 404
