"""Nadi & Transit Daemon: in-process asyncio worker that compares real-time
planetary positions against stored natal charts and persists transit alerts.

Architecture: started by FastAPI lifespan in app/main.py. Runs forever (until
.stop()) in 1 task. One DB session per cycle (sessions are NOT held across
asyncio.sleep, which would starve the connection pool).

Retrograde whipsaw - design note for forward compat:
    Saturn and Jupiter retrograde back over the same natal degree typically 3
    times per transit (~9 months). Toggling is_active=True/False is correct for
    the current-state /transits API, but if/when push notifications ship in
    Phase 3+, they will fire 3 times for the same astrologically-singular event.
    The mitigation (out of scope here) is an append-only AlertHistory table
    alongside this current-state TransitAlert table - delivery dedup checks
    history; the API keeps reading TransitAlert. No v1 schema change required.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.ephemeris_engine import calculate_all_charts
from app.daemon.nadi_rules import (
    AspectResult,
    NATAL_PLANETS,
    TRANSIT_PLANETS,
    compute_vedic_aspect,
    describe_aspect,
)
from app.models.domain import NatalChart, TransitAlert

logger = logging.getLogger(__name__)

# Map natal planet name -> (lon column, sign column) on NatalChart for fast access.
_NATAL_COLUMNS: dict[str, tuple[str, str]] = {
    "Sun": ("sun_lon", "sun_sign"),
    "Moon": ("moon_lon", "moon_sign"),
    "Mars": ("mars_lon", "mars_sign"),
    "Mercury": ("mercury_lon", "mercury_sign"),
    "Jupiter": ("jupiter_lon", "jupiter_sign"),
    "Venus": ("venus_lon", "venus_sign"),
    "Saturn": ("saturn_lon", "saturn_sign"),
    "Rahu": ("rahu_lon", "rahu_sign"),
    "Ketu": ("ketu_lon", "ketu_sign"),
}

# Idempotency key shape: (transit_planet, natal_planet, alert_type).
AspectKey = tuple[str, str, str]


class NadiTransitDaemon:
    def __init__(self, check_interval_seconds: int | None = None) -> None:
        self.check_interval_seconds = (
            check_interval_seconds
            if check_interval_seconds is not None
            else settings.DAEMON_CHECK_INTERVAL_SECONDS
        )
        self.is_running = False
        self._last_transits: dict[str, Any] | None = None
        self._stop_event = asyncio.Event()

    async def fetch_realtime_transits(self) -> dict[str, Any]:
        """Compute the current transit chart for now (UTC). Cached on self for the cycle."""
        now = dt.datetime.now(dt.timezone.utc)
        # Lat/lon/tz_offset don't influence sidereal planetary longitudes (they
        # only matter for ascendant/houses, which Phase 2 doesn't implement).
        # Using (0,0,0) keeps the call signature satisfied without geocoding.
        transits = calculate_all_charts(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            tz_offset=0.0,
        )
        self._last_transits = transits
        return transits

    def _detect_aspects_for_chart(self, chart: NatalChart) -> list[AspectResult]:
        """Run all (transit_planet x natal_planet) combinations for one natal chart."""
        if self._last_transits is None:
            return []
        transit_d1 = self._last_transits["d1"]
        results: list[AspectResult] = []

        for tp in TRANSIT_PLANETS:
            tp_pos = transit_d1[tp]
            for np in NATAL_PLANETS:
                lon_attr, sign_attr = _NATAL_COLUMNS[np]
                aspect = compute_vedic_aspect(
                    transit_planet=tp,
                    transit_sign=tp_pos["sign"],
                    transit_lon=tp_pos["longitude"],
                    natal_planet=np,
                    natal_sign=getattr(chart, sign_attr),
                    natal_lon=getattr(chart, lon_attr),
                    orb_degrees=settings.TRANSIT_ORB_DEGREES,
                )
                if aspect is not None:
                    results.append(aspect)
        return results

    async def _reconcile_alerts(
        self,
        db: AsyncSession,
        user_id: int,
        current_aspects: list[AspectResult],
    ) -> None:
        """Insert new aspects, deactivate stale ones; idempotent on repeat runs."""
        existing_stmt = select(TransitAlert).where(
            TransitAlert.user_id == user_id,
            TransitAlert.is_active.is_(True),
        )
        existing_rows = (await db.execute(existing_stmt)).scalars().all()
        existing_by_key: dict[AspectKey, TransitAlert] = {
            (row.transit_planet, row.natal_planet, row.alert_type): row
            for row in existing_rows
        }
        current_by_key: dict[AspectKey, AspectResult] = {
            (a.transit_planet, a.natal_planet, a.alert_type): a
            for a in current_aspects
        }

        added = 0
        for key, aspect in current_by_key.items():
            if key in existing_by_key:
                # Already active: refresh is_exact in case orb status changed mid-transit.
                row = existing_by_key[key]
                if row.is_exact != aspect.is_exact:
                    row.is_exact = aspect.is_exact
                continue
            db.add(TransitAlert(
                user_id=user_id,
                alert_type=aspect.alert_type,
                description=describe_aspect(aspect),
                transit_planet=aspect.transit_planet,
                natal_planet=aspect.natal_planet,
                is_exact=aspect.is_exact,
                is_active=True,
            ))
            added += 1

        stale_keys = set(existing_by_key) - set(current_by_key)
        deactivated = 0
        for key in stale_keys:
            row = existing_by_key[key]
            row.is_active = False
            deactivated += 1

        if added or deactivated:
            logger.info(
                "user_id=%s: %d new alerts, %d deactivated", user_id, added, deactivated
            )

    async def process_natal_charts(self, db: AsyncSession) -> None:
        """Stream chart IDs, then reconcile each chart in its own transaction.

        Per-chart atomicity (review fix #8): a failure in one user's reconcile
        no longer rolls back the entire cycle. Earlier users keep their alert
        updates; the bad chart is logged and skipped.

        Memory bound (constraint #3): pass 1 streams chart IDs (8 bytes each)
        rather than full ORM rows. At 1M users that's ~8MB, well below any
        reasonable budget. Pass 2 loads one chart at a time via db.get().
        selectinload(NatalChart.user) was dropped because reconcile only
        needs user_id, which lives on NatalChart directly.
        """
        id_stmt = select(NatalChart.id).execution_options(yield_per=1000)
        id_result = await db.stream(id_stmt)
        chart_ids = [cid async for cid in id_result.scalars()]

        for chart_id in chart_ids:
            try:
                chart = await db.get(NatalChart, chart_id)
                if chart is None:
                    # Deleted between pass 1 and pass 2 - benign race, skip.
                    continue
                aspects = self._detect_aspects_for_chart(chart)
                await self._reconcile_alerts(db, chart.user_id, aspects)
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(
                    "chart_id=%s reconcile failed; skipping this user", chart_id
                )

    async def run_once(self) -> None:
        """One full cycle: fetch transits, then reconcile every chart. Public for tests."""
        await self.fetch_realtime_transits()
        async with AsyncSessionLocal() as db:
            await self.process_natal_charts(db)

    async def start(self) -> None:
        self.is_running = True
        self._stop_event.clear()
        logger.info("Nadi & Transit Daemon starting (interval=%ds)", self.check_interval_seconds)

        consecutive_errors = 0
        while self.is_running:
            try:
                logger.info("Cycle: fetching real-time transits...")
                await self.run_once()
                consecutive_errors = 0
                logger.info("Cycle complete; sleeping %ds", self.check_interval_seconds)
            except asyncio.CancelledError:
                raise
            except Exception:
                consecutive_errors += 1
                # Exponential backoff capped at the configured interval.
                backoff = min(2 ** consecutive_errors, self.check_interval_seconds)
                logger.exception("Daemon cycle failed (attempt %d); backing off %ds",
                                 consecutive_errors, backoff)
                await self._sleep(backoff)
                continue

            await self._sleep(self.check_interval_seconds)

    async def _sleep(self, seconds: float) -> None:
        """Interruptible sleep: returns immediately if stop() is called."""
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    def stop(self) -> None:
        self.is_running = False
        self._stop_event.set()
        logger.info("Nadi & Transit Daemon stopping...")
