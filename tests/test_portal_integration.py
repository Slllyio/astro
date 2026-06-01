"""End-to-end smoke test for the V1.3 Family Charts portal.

Verifies that:

1. ``app.main.app`` boots with the portal router wired in.
2. ``GET  /portal/`` returns 200 with the portal landing page HTML.
3. ``POST /portal/new`` accepts a valid relative payload and persists it
   (303 redirect to ``/portal/{id}`` on success, or 200 reading view).
4. ``GET  /portal/{id}`` renders the master reading and includes the
   computed lagna sign + dasha-triple paragraph from
   ``compose_master_reading`` (the read-only reading-layer API the
   portal is required to reuse — no astro logic duplicated in the
   portal package).

This is the integration verification that proves the portal is wired
into the FastAPI app, the database persistence works, and the master
reading composer actually runs on saved-relative data. If the portal
package (B1/B2/B3 deliverables) hasn't been merged yet the test
skips with a clear marker so CI surfaces the unwired state rather
than a noisy ImportError.
"""

from __future__ import annotations

import importlib
import os

# Set test env BEFORE any ``app.*`` import — mirrors tests/conftest.py so
# this test is runnable both standalone (py -3.12 -m pytest tests/test_portal_integration.py)
# and as part of the full suite (where conftest.py has already done this).
os.environ.setdefault("DAEMON_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("PORTAL_ENABLED", "false")
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient


def _portal_router_available() -> bool:
    """True iff app.api.portal_routes can be imported (B1/B2/B3 merged)."""
    try:
        importlib.import_module("app.api.portal_routes")
    except ImportError:
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _portal_router_available(),
    reason=(
        "portal_routes not yet merged from B1/B2/B3 worktrees — "
        "this integration smoke test runs once the portal package + "
        "templates + routes ship."
    ),
)


# Canonical Bangalore baseline locked in CLAUDE.md — produces Mercury MD,
# Virgo Lagna ~173.99°, Moon at Revati pada 3. Reusing it gives the
# downstream reading-layer assertions a known-good chart fixture.
_RELATIVE_PAYLOAD = {
    "name": "Test Mother",
    "relationship": "mother",
    "dob": "1990-07-15",
    "time": "12:00",
    "tz": "+05:30",
    "lat": "12.97",
    "lon": "77.59",
    "place_name": "Bangalore, Karnataka, India",
    "notes": "Smoke-test relative",
}


@pytest.fixture
def app_with_inmemory_db():
    """FastAPI app instance with get_db patched to an in-memory aiosqlite engine.

    StaticPool keeps the single shared connection alive across sessionmaker
    boundaries so the :memory: DB state survives between the POST that
    creates the relative and the GET that renders the reading.
    """
    from app.core.database import get_db
    from app.main import app
    from app.models.domain import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # init_db has already run on app boot via lifespan; we still need to
    # create_all on the test engine because we're swapping it in below.
    import asyncio

    async def _create_schema():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("loop closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(_create_schema())

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
        loop.run_until_complete(engine.dispose())


def test_portal_index_returns_200(app_with_inmemory_db) -> None:
    """GET /portal/ renders the family charts landing page."""
    with TestClient(app_with_inmemory_db) as client:
        resp = client.get("/portal/")
    assert resp.status_code == 200, resp.text[:500]
    assert "text/html" in resp.headers.get("content-type", "")
    # Portal landing page should announce itself. Accept several reasonable
    # phrasings so we don't lock the test to a single template wording.
    body = resp.text
    assert any(
        marker in body
        for marker in (
            "Family Chart Portal",
            "Family Charts",
            "Family Chart",
            "saved relatives",
        )
    ), f"Portal landing page missing identifier marker. Body[:500]={body[:500]}"


def test_portal_new_relative_persists_and_redirects(
    app_with_inmemory_db,
) -> None:
    """POST /portal/new persists a relative and redirects to its reading."""
    with TestClient(app_with_inmemory_db) as client:
        resp = client.post(
            "/portal/new", data=_RELATIVE_PAYLOAD, follow_redirects=False
        )

    # The portal's documented contract is 303 SEE OTHER -> /portal/{id} on
    # success; some implementations use 302. A 200 (form re-render) is
    # accepted ONLY if it's the reading view, not a validation error.
    assert resp.status_code in (200, 302, 303), (
        f"Unexpected status {resp.status_code} for POST /portal/new. "
        f"Body[:500]={resp.text[:500]}"
    )

    if resp.status_code in (302, 303):
        location = resp.headers.get("location", "")
        assert location.startswith("/portal/"), (
            f"Redirect Location must point at /portal/{{id}}, got {location!r}"
        )
        # Path must include an id segment after /portal/, not just /portal/.
        assert location.rstrip("/") != "/portal", (
            f"Redirect must include the new relative id, got {location!r}"
        )
    else:
        # 200 path: must be the reading view, NOT the form re-rendered with
        # a validation error. The error path renders a red bootstrap alert.
        assert "alert-danger" not in resp.text, (
            "POST /portal/new with valid payload re-rendered the form with "
            "an error banner — the form schema rejected the payload."
        )


def test_portal_view_renders_master_reading(app_with_inmemory_db) -> None:
    """GET /portal/{id} renders the master reading (lagna + dasha triple)."""
    with TestClient(app_with_inmemory_db) as client:
        # 1) Create the relative
        post_resp = client.post(
            "/portal/new", data=_RELATIVE_PAYLOAD, follow_redirects=False
        )
        assert post_resp.status_code in (200, 302, 303), post_resp.text[:500]

        # 2) Extract the new id from the redirect Location (or follow form
        #    -> reading view if the implementation chose the 200 path).
        if post_resp.status_code in (302, 303):
            person_path = post_resp.headers["location"]
            view_resp = client.get(person_path)
        else:
            # 200 path — POST already returned the rendered reading view.
            view_resp = post_resp

    assert view_resp.status_code == 200, view_resp.text[:500]
    body = view_resp.text

    # 3) The portal's read-only reuse of compose_master_reading must
    #    surface the canonical Bangalore-baseline Lagna (Virgo) somewhere
    #    in the rendered reading. Accept "Virgo" OR the longitude prefix
    #    "173" (Virgo ~173.99°) — different templates render different fields.
    assert "Virgo" in body or "173" in body, (
        "Master reading view should surface Virgo Lagna for the canonical "
        f"Bangalore-baseline chart. Body[:1000]={body[:1000]}"
    )

    # 4) Dasha triple paragraph: the Bangalore baseline is Mercury MD at the
    #    moment of birth; compose_master_reading() yields a dasha-triple
    #    section keyed on the current MD lord. Either marker is acceptable.
    assert "Mercury" in body or "Dasha" in body or "dasha" in body, (
        "Master reading view should surface the dasha-triple section "
        f"(Mercury MD for Bangalore baseline). Body[:1000]={body[:1000]}"
    )
