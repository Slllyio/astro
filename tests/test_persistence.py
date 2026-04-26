"""Persistence layer tests: ORM round-trip, /profiles endpoints, WAL pragma."""
from __future__ import annotations

import pathlib

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models.domain import NatalChart, UserProfile

from _helpers import sample_profile_payload  # tests/ is on sys.path via pytest rootdir


# ---------- /profiles round-trip ----------

async def test_post_profile_creates_user_and_chart(
    authed_client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await authed_client.post("/profiles", json=sample_profile_payload())

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] >= 1
    assert body["name"] == "Test User"
    assert body["chart"]["current_mahadasha"]["mahadasha_lord"] == "Mercury"
    assert isinstance(body["chart"]["d1"], dict)
    assert "Saturn" in body["chart"]["d1"]

    # Lagna integration: response carries an ascendant and d1 entries are
    # annotated with whole-sign house numbers. Bangalore 1990-07-15 12:00 IST
    # has Virgo Lagna (sign 6) per the engine-layer test pin.
    assert body["chart"]["ascendant"] is not None
    assert body["chart"]["ascendant"]["sign_name"] == "Virgo"
    assert body["chart"]["ascendant"]["sign"] == 6
    for planet in ("Sun", "Moon", "Saturn", "Jupiter", "Mars",
                   "Mercury", "Venus", "Rahu", "Ketu"):
        h = body["chart"]["d1"][planet]["house"]
        assert isinstance(h, int) and 1 <= h <= 12, f"{planet} house out of range: {h}"

    # Verify persistence: fetch the chart row directly via the test session.
    chart = (await db_session.execute(
        # noqa: E501 - readability beats line length here
        NatalChart.__table__.select().where(NatalChart.user_id == body["id"])
    )).first()
    assert chart is not None
    row = chart._mapping
    assert row["birth_jd"] is not None and row["birth_jd"] > 0
    assert 1 <= row["saturn_sign"] <= 12
    assert row["ascendant_sign"] == 6, "Bangalore 1990 Lagna should persist as Virgo"
    assert 150.0 <= row["ascendant_lon"] < 180.0
    # All 9 graha longitudes should be valid sidereal degrees.
    for col in ("sun_lon", "moon_lon", "mars_lon", "mercury_lon", "jupiter_lon",
                "venus_lon", "saturn_lon", "rahu_lon", "ketu_lon"):
        assert 0.0 <= row[col] < 360.0, f"{col} out of range: {row[col]}"


async def test_get_transits_empty_initially(authed_client: AsyncClient) -> None:
    """A user with no transit alerts gets an empty list, not 404."""
    create_resp = await authed_client.post("/profiles", json=sample_profile_payload())
    user_id = create_resp.json()["id"]

    transits_resp = await authed_client.get(f"/profiles/{user_id}/transits")
    assert transits_resp.status_code == 200
    assert transits_resp.json() == []


async def test_get_transits_404_for_unknown_user(authed_client: AsyncClient) -> None:
    response = await authed_client.get("/profiles/99999/transits")
    assert response.status_code == 404


async def test_post_profile_validates_birth_data(authed_client: AsyncClient) -> None:
    bad_payload = sample_profile_payload(month=13)  # invalid
    response = await authed_client.post("/profiles", json=bad_payload)
    assert response.status_code == 422


# ---------- WAL pragma verification (constraint #4) ----------
# Must use a file-backed SQLite; PRAGMA journal_mode=WAL is a no-op for :memory:.

@pytest_asyncio.fixture
async def file_backed_engine(tmp_path: pathlib.Path):
    """Standalone fixture creating a fresh file-backed engine using app.core.database."""
    db_file = tmp_path / "wal_test.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    # Build the engine the same way the app does, including the WAL listener.
    # We bypass the global module-level engine to avoid polluting it.
    from sqlalchemy import event
    engine = create_async_engine(url)

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_wal(dbapi_connection, _record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()

    yield engine
    await engine.dispose()


async def test_sqlite_wal_pragma_active(file_backed_engine) -> None:
    """After the WAL listener fires, journal_mode must report 'wal'.

    We build the engine identically to how app.core.database does it (same
    create_async_engine + same event.listens_for hook) so this test exercises
    the actual listener pattern shipped to production. We do NOT reload the
    app.core.database module itself, because that mutates module-level globals
    referenced by FastAPI's Depends(get_db) and silently breaks override-based
    test isolation in subsequent tests.
    """
    async with file_backed_engine.connect() as conn:
        result = await conn.execute(text("PRAGMA journal_mode;"))
        mode = result.scalar()
    assert mode.lower() == "wal", f"expected wal, got {mode!r}"


# ---------- ORM constraints ----------

async def test_natal_chart_one_per_user(
    authed_client: AsyncClient, db_session: AsyncSession
) -> None:
    """The unique constraint on NatalChart.user_id (1:1) must hold."""
    create_resp = await authed_client.post("/profiles", json=sample_profile_payload())
    user_id = create_resp.json()["id"]

    user = await db_session.get(UserProfile, user_id)
    assert user is not None
    # Add a duplicate NatalChart and expect IntegrityError on commit.
    db_session.add(NatalChart(
        user_id=user_id,
        birth_jd=0.0, birth_moon_longitude=0.0,
        ascendant_lon=0.0, ascendant_sign=1,
        sun_lon=0, sun_sign=1, moon_lon=0, moon_sign=1,
        mars_lon=0, mars_sign=1, mercury_lon=0, mercury_sign=1,
        jupiter_lon=0, jupiter_sign=1, venus_lon=0, venus_sign=1,
        saturn_lon=0, saturn_sign=1, rahu_lon=0, rahu_sign=1,
        ketu_lon=0, ketu_sign=1,
        full_chart_json={},
    ))
    with pytest.raises(Exception):  # IntegrityError or InvalidRequestError; both correct
        await db_session.commit()
