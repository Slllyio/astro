"""End-to-end daemon tick tests with synthetic transits."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.daemon.transit_worker import NadiTransitDaemon
from app.models.domain import Account, NatalChart, TransitAlert, UserProfile


# Build a synthetic transit chart that ONLY Saturn-sign-1 makes aspects.
# Other transit planets parked at sign=2, lon=30 (i.e. start of Taurus).
# Natal noise planets placed at sign=12 -> all noise interactions land on
# house_distance in {2, 6, 11, 12}, which are NOT in any VEDIC_ASPECTS row.
def _synthetic_transit_chart() -> dict[str, Any]:
    def pos(sign: int, lon: float) -> dict[str, Any]:
        return {
            "name": "X", "longitude": lon, "sign": sign,
            "sign_name": "X", "degree_in_sign": lon - (sign - 1) * 30,
            "is_retrograde": False,
        }
    return {
        "d1": {
            "Sun":     pos(2, 30.0),   # noise
            "Moon":    pos(2, 30.0),   # noise
            "Mercury": pos(2, 30.0),   # noise
            "Venus":   pos(2, 30.0),   # noise
            "Mars":    pos(2, 30.0),   # noise
            "Jupiter": pos(2, 30.0),   # noise
            "Rahu":    pos(2, 30.0),   # noise
            "Ketu":    pos(2, 30.0),   # noise
            "Saturn":  pos(1, 0.0),    # the test signal
        }
    }


def _seed_natal(user_id: int) -> NatalChart:
    """Natal positions chosen so Saturn-at-sign-1 fires exactly 3 aspects:
        - CONJUNCTION with Sun (sign=1, lon=2.0  -> within 3deg orb -> is_exact)
        - OPPOSITION  with Moon (sign=7, lon=180.0)
        - SATURN_3RD with Mars (sign=3, lon=60.0)
    All other natal planets parked at sign=12, lon=330 (no aspect from anything)."""
    return NatalChart(
        user_id=user_id,
        birth_jd=2451545.0, birth_moon_longitude=180.0,
        ascendant_lon=0.0, ascendant_sign=1,  # synthetic; daemon doesn't read these
        sun_lon=2.0,        sun_sign=1,
        moon_lon=180.0,     moon_sign=7,
        mars_lon=60.0,      mars_sign=3,
        mercury_lon=330.0,  mercury_sign=12,
        jupiter_lon=330.0,  jupiter_sign=12,
        venus_lon=330.0,    venus_sign=12,
        saturn_lon=330.0,   saturn_sign=12,
        rahu_lon=330.0,     rahu_sign=12,
        ketu_lon=330.0,     ketu_sign=12,
        full_chart_json={"synthetic": True},
    )


async def _seed_user_with_natal(db: AsyncSession) -> int:
    """Seed an Account + UserProfile + NatalChart and return the user id.

    Account is required because UserProfile.account_id is a FK; we use a
    deterministic google_sub per test via the session's identity map so
    repeated calls in the same test don't collide.
    """
    account = Account(
        google_sub="daemon-test-sub",
        email="daemon-test@example.com",
        name="Daemon Test",
    )
    db.add(account)
    await db.flush()
    user = UserProfile(
        account_id=account.id,
        name="DaemonTest",
        birth_year=2000, birth_month=1, birth_day=1,
        birth_hour=0, birth_minute=0,
        latitude=0.0, longitude=0.0, tz_offset=0.0,
    )
    db.add(user)
    await db.flush()
    db.add(_seed_natal(user.id))
    await db.commit()
    return user.id


# ---------- single-tick generation ----------

async def test_single_tick_generates_expected_alerts(db_session: AsyncSession) -> None:
    user_id = await _seed_user_with_natal(db_session)

    daemon = NadiTransitDaemon(check_interval_seconds=3600)
    daemon._last_transits = _synthetic_transit_chart()  # bypass network/ephemeris
    await daemon.process_natal_charts(db_session)

    alerts = (await db_session.execute(
        select(TransitAlert)
        .where(TransitAlert.user_id == user_id, TransitAlert.is_active.is_(True))
        .order_by(TransitAlert.alert_type)
    )).scalars().all()

    keys = {(a.transit_planet, a.natal_planet, a.alert_type) for a in alerts}
    assert keys == {
        ("Saturn", "Sun", "CONJUNCTION"),
        ("Saturn", "Moon", "OPPOSITION"),
        ("Saturn", "Mars", "SATURN_3RD"),
    }


async def test_conjunction_within_orb_is_exact(db_session: AsyncSession) -> None:
    user_id = await _seed_user_with_natal(db_session)

    daemon = NadiTransitDaemon()
    daemon._last_transits = _synthetic_transit_chart()
    await daemon.process_natal_charts(db_session)

    conj = (await db_session.execute(
        select(TransitAlert).where(
            TransitAlert.user_id == user_id,
            TransitAlert.alert_type == "CONJUNCTION",
        )
    )).scalar_one()
    # Saturn lon=0, natal Sun lon=2 -> circular_distance=2.0 <= 3.0 default orb -> True
    assert conj.is_exact is True
    # Drishti aspects ignore orb, never is_exact.
    saturn_3rd = (await db_session.execute(
        select(TransitAlert).where(
            TransitAlert.user_id == user_id,
            TransitAlert.alert_type == "SATURN_3RD",
        )
    )).scalar_one()
    assert saturn_3rd.is_exact is False


# ---------- idempotency ----------

async def test_second_tick_no_duplicate_inserts(db_session: AsyncSession) -> None:
    user_id = await _seed_user_with_natal(db_session)

    daemon = NadiTransitDaemon()
    daemon._last_transits = _synthetic_transit_chart()
    await daemon.process_natal_charts(db_session)
    await daemon.process_natal_charts(db_session)  # same transits, second tick

    count = (await db_session.execute(
        select(TransitAlert).where(TransitAlert.user_id == user_id)
    )).scalars().all()
    # Exactly 3 active alerts from the first tick; the second tick is a no-op.
    assert len(count) == 3
    assert all(a.is_active for a in count)


# ---------- stale alert deactivation ----------

async def test_is_exact_flips_on_subsequent_tick(db_session: AsyncSession) -> None:
    """Regression guard: when an alert is already active and the orb status
    changes (transit moves into/out of exact range while still in the same
    sign), the existing TransitAlert row's is_exact must update in place.

    Architectural concern raised in code review: SQLAlchemy 2.0 typed
    Mapped[bool] columns are instrumented descriptors, so attribute
    assignment dirty-tracks the instance and the change persists on commit.
    This test proves it - if dirty tracking ever fails, the assertion
    below catches the silent regression.
    """
    user_id = await _seed_user_with_natal(db_session)
    daemon = NadiTransitDaemon()

    # Cycle 1: Saturn at sign=1, lon=0 -> CONJUNCTION with Sun (lon=2), is_exact=True.
    daemon._last_transits = _synthetic_transit_chart()
    await daemon.process_natal_charts(db_session)
    db_session.expire_all()  # drop any cached instances

    alert = (await db_session.execute(
        select(TransitAlert).where(
            TransitAlert.user_id == user_id,
            TransitAlert.alert_type == "CONJUNCTION",
        )
    )).scalar_one()
    assert alert.is_exact is True

    # Cycle 2: Move Saturn to lon=29 (still sign=1, so CONJUNCTION still fires
    # via whole-sign drishti) but circular_distance(29, 2) = 27 > 3.0 orb,
    # so is_exact must flip to False on the SAME alert row.
    new_chart = _synthetic_transit_chart()
    new_chart["d1"]["Saturn"] = {
        "name": "Saturn", "longitude": 29.0, "sign": 1,
        "sign_name": "Aries", "degree_in_sign": 29.0, "is_retrograde": False,
    }
    daemon._last_transits = new_chart
    await daemon.process_natal_charts(db_session)
    db_session.expire_all()

    alert_after = (await db_session.execute(
        select(TransitAlert).where(
            TransitAlert.user_id == user_id,
            TransitAlert.alert_type == "CONJUNCTION",
        )
    )).scalar_one()
    # Same row, mutated in place: same id, is_exact flipped.
    assert alert_after.id == alert.id, "expected same row, not a duplicate insert"
    assert alert_after.is_exact is False, "is_exact mutation did not persist"


async def test_stale_alerts_deactivated_when_aspect_no_longer_holds(
    db_session: AsyncSession,
) -> None:
    user_id = await _seed_user_with_natal(db_session)

    daemon = NadiTransitDaemon()
    daemon._last_transits = _synthetic_transit_chart()
    await daemon.process_natal_charts(db_session)

    # Move Saturn out of sign=1 into sign=2 (no aspects to anything in our seed).
    new_chart = _synthetic_transit_chart()
    new_chart["d1"]["Saturn"] = {
        "name": "Saturn", "longitude": 30.0, "sign": 2,
        "sign_name": "Taurus", "degree_in_sign": 0.0, "is_retrograde": False,
    }
    daemon._last_transits = new_chart
    await daemon.process_natal_charts(db_session)

    alerts = (await db_session.execute(
        select(TransitAlert).where(TransitAlert.user_id == user_id)
    )).scalars().all()
    # Three rows still exist (current-state table, not append-only), but all
    # should now be inactive since none of the aspects hold any more.
    assert len(alerts) == 3
    assert all(a.is_active is False for a in alerts)


# ---------- run_once integration (uses AsyncSessionLocal under the hood) ----------

async def test_run_once_uses_async_session_local(monkeypatch, db_engine) -> None:
    """run_once() opens its own session via AsyncSessionLocal (not via Depends).
    Patch the module-level session-maker to point at the test engine and stub
    out fetch_realtime_transits so the test is offline and deterministic."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    test_sm = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr("app.daemon.transit_worker.AsyncSessionLocal", test_sm)

    async with test_sm() as s:
        await _seed_user_with_natal(s)

    daemon = NadiTransitDaemon()

    async def fake_fetch() -> dict:
        chart = _synthetic_transit_chart()
        daemon._last_transits = chart
        return chart

    monkeypatch.setattr(daemon, "fetch_realtime_transits", fake_fetch)
    await daemon.run_once()

    async with test_sm() as s:
        rows = (await s.execute(
            select(TransitAlert).where(TransitAlert.is_active.is_(True))
        )).scalars().all()
        assert len(rows) == 3
