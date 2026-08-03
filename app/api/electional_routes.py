"""HTTP surface over the WALLED electional (Muhurtha) subsystem — `app.raman_saab.electional`.

One endpoint answers "what does Raman's *Muhurtha* say about this day for this native": the
day's Tarabala and Chandrabala measured from the native's own janma star/rasi, the five
panchanga limbs, Panchaka, the ASP ch.XV transit-band elections read against the native's
Bhinnashtakavarga, and the day's negative windows (Rahu Kalam + Durmuhurtha) as local ISO
times. The judgment itself is `electional.window_scorer.evaluate_moment` — this module adds
no doctrine, only the ephemeris plumbing and the JSON shape.

DOCTRINE NOTE (surfaced to callers): output is a statement of Raman's electional METHOD —
never a validated prediction. See the package docstring and CLAUDE.md "Measured Truth".

Endpoints:
    GET /electional/today   native birth params (+ optional date/hour/act) -> the day's
                            electional reading.

Usage:
    curl "http://127.0.0.1:8000/electional/today?year=1990&month=7&day=15&hour=12\
&latitude=12.97&longitude=77.59&tz_offset=5.5&date=2026-08-03&act=marriage"
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date as date_cls, datetime, timedelta, timezone
from typing import Annotated, Literal, Optional

import swisseph as swe
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.panchanga import compute_panchanga
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.electional.asp_transit_elections import transit_election
from app.raman_saab.electional.negative_windows import (
    Window,
    durmuhurtha_windows,
    rahu_kalam,
)
from app.raman_saab.electional.window_scorer import evaluate_moment

logger = logging.getLogger(__name__)

electional_router = APIRouter(prefix="/electional", tags=["Electional (Muhurtha)"])

#: The seven grahas ASP ch.XV states transit-band rules for (Rahu/Ketu carry none).
_TRANSIT_GRAHAS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

_DISCLAIMER = ("What B. V. Raman's *Muhurtha* says of this day for this native — a statement "
               "of the electional method, never a validated prediction.")


class ElectionalQuery(BaseModel):
    """The NATIVE's birth (same params the /report surface takes) plus the day to elect."""

    model_config = ConfigDict(extra="forbid")

    year: int = Field(..., ge=1800, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-12.0, le=14.0)
    name: str = Field("api", max_length=120)
    ayanamsa: Literal["raman", "lahiri"] = "lahiri"
    # The day being elected; defaults to today. The election is judged at `election_hour`
    # local time (noon by default) — the moment decides which negative window it falls in.
    date: Optional[date_cls] = None
    election_hour: int = Field(12, ge=0, le=23)
    election_minute: int = Field(0, ge=0, le=59)
    # Raman's per-activity Panchaka exception (MUHURTHA-3:157-168) and the Janma-star
    # activity split; unknown/absent acts simply skip the exception.
    act: Optional[str] = Field(None, max_length=40)


def sun_events(birth: BirthData) -> tuple[float, float, float]:
    """(sunrise, sunset, next sunrise) Julian Days for `birth`'s local civil date and place.

    Mirrors the verified-live ``swe.rise_trans`` pattern in ``chart/kala_context.py`` (rsmi
    flags BEFORE geopos, all positional). The following sunrise is included because Raman's
    NOCTURNAL durmuhurthas partition sunset -> next sunrise (MUHURTHA-4:276-320).

    Raises:
        ValueError: at extreme latitudes where no ordinary sunrise/sunset exists.
    """
    geopos: tuple[float, float, float] = (birth.longitude, birth.latitude, 0.0)
    jd_midnight = swe.julday(birth.year, birth.month, birth.day,
                             0.0 - birth.tz_offset, swe.GREG_CAL)
    rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    sett = swe.CALC_SET | swe.BIT_DISC_CENTER
    try:
        _r, tret = swe.rise_trans(jd_midnight, swe.SUN, rise, geopos, 0.0, 0.0, swe.FLG_SWIEPH)
        sunrise = float(tret[0])
        _r, tret = swe.rise_trans(sunrise, swe.SUN, sett, geopos, 0.0, 0.0, swe.FLG_SWIEPH)
        sunset = float(tret[0])
        _r, tret = swe.rise_trans(sunset, swe.SUN, rise, geopos, 0.0, 0.0, swe.FLG_SWIEPH)
        next_sunrise = float(tret[0])
    except swe.Error as exc:
        raise ValueError(
            f"sunrise/sunset undefined at latitude {birth.latitude} on "
            f"{birth.year:04d}-{birth.month:02d}-{birth.day:02d}: the day's negative windows "
            f"are partitions of a real day/night span, so polar day/night is out of scope "
            f"({exc})") from exc
    return sunrise, sunset, next_sunrise


def _jd_to_local_iso(jd: float, tz_offset: float) -> str:
    """A UT Julian Day as a local ISO-8601 timestamp at `tz_offset` hours."""
    year, month, day, hour = swe.revjul(jd + tz_offset / 24.0, swe.GREG_CAL)
    tz = timezone(timedelta(hours=tz_offset))
    stamp = datetime(int(year), int(month), int(day), tzinfo=tz) + timedelta(hours=float(hour))
    return stamp.isoformat(timespec="seconds")


def _cite(c: Citation) -> str:
    return f"{c.work}:{c.line}"


def _window_json(w: Window, tz_offset: float) -> dict:
    return {"label": w.label, "start": _jd_to_local_iso(w.start_jd, tz_offset),
            "end": _jd_to_local_iso(w.end_jd, tz_offset), "source": _cite(w.source)}


def _karana_number(panchanga_index: int) -> int:
    """core.panchanga's 0..59 karana index -> the MUHURTHA-2:151-160 movable number 1..7.

    Only the seven movable karanas carry a number in Raman's enumeration (Vishti is 7, the
    one MUHURTHA-8:1171 discards). The four FIXED karanas — Kimstughna 0, Shakuni 57,
    Chatushpada 58, Naga 59 — are not in that cycle and map to 0, which no rule names.
    """
    return ((panchanga_index - 1) % 7) + 1 if 1 <= panchanga_index <= 56 else 0


@electional_router.get("/today")
async def electional_today(q: Annotated[ElectionalQuery, Query()]) -> dict:
    """The day's electional reading for one native, per Raman's *Muhurtha*.

    Casts the nativity (for the janma nakshatra/rasi and the Bhinnashtakavarga the ASP-15
    transit bands are read against) and the elected moment (for the day's Moon, lagna and
    panchanga), then judges via `window_scorer.evaluate_moment`. All ephemeris work is
    offloaded to a worker thread.
    """

    def _build() -> dict:
        natal = cast_chart(
            BirthData(name=q.name, year=q.year, month=q.month, day=q.day, hour=q.hour,
                      minute=q.minute, tz_offset=q.tz_offset, latitude=q.latitude,
                      longitude=q.longitude),
            ayanamsa=q.ayanamsa)
        janma_nakshatra = natal.planets["Moon"].nakshatra
        janma_rasi = natal.planets["Moon"].sign

        elect_on = q.date or date_cls.today()
        moment_birth = BirthData(name="election", year=elect_on.year, month=elect_on.month,
                                 day=elect_on.day, hour=q.election_hour,
                                 minute=q.election_minute, tz_offset=q.tz_offset,
                                 latitude=q.latitude, longitude=q.longitude)
        day_chart = cast_chart(moment_birth, ayanamsa=q.ayanamsa)
        jd = day_chart.jd_ut
        assert jd is not None  # cast_chart from BirthData always sets jd_ut

        p = compute_panchanga(jd)
        weekday = p["vara"]["index"]                    # 0=Sunday .. 6=Saturday
        tithi_in_paksha = p["tithi"]["index"] % 15 + 1  # 1..15 within the paksha
        day_nakshatra = int(p["nakshatra"]["index"]) + 1
        yoga = p["yoga"]["index"] + 1
        karana = _karana_number(p["karana"]["index"])

        sunrise, sunset, next_sunrise = sun_events(moment_birth)
        windows = (rahu_kalam(weekday, sunrise, sunset),
                   *durmuhurtha_windows(weekday, sunrise, sunset, next_sunrise))

        ev = evaluate_moment(
            jd=jd, janma_nakshatra=janma_nakshatra, janma_rasi=janma_rasi,
            tithi_in_paksha=tithi_in_paksha, weekday=weekday, day_nakshatra=day_nakshatra,
            yoga=yoga, karana=karana, election_moon_rasi=day_chart.planets["Moon"].sign,
            lagna_sign=day_chart.asc_sign, act=q.act, negative_windows=windows)

        transits = []
        for graha in _TRANSIT_GRAHAS:
            te = transit_election(natal, graha, day_chart.planets[graha].sign)
            if te is not None:
                transits.append({"graha": te.graha, "transit_sign": te.transit_sign,
                                 "bindus": te.bindus, "verdict": te.verdict,
                                 "activities": list(te.activities),
                                 "source": _cite(te.source)})

        return {
            "date": elect_on.isoformat(),
            "act": q.act,
            "ayanamsa": q.ayanamsa,
            "moment": {"jd": jd, "local_iso": _jd_to_local_iso(jd, q.tz_offset),
                       "sunrise": _jd_to_local_iso(sunrise, q.tz_offset),
                       "sunset": _jd_to_local_iso(sunset, q.tz_offset)},
            "native": {"janma_nakshatra": janma_nakshatra, "janma_rasi": janma_rasi},
            "day": {"moon_rasi": day_chart.planets["Moon"].sign,
                    "moon_nakshatra": day_nakshatra, "lagna_sign": day_chart.asc_sign,
                    "weekday": weekday, "vara": p["vara"]["name"],
                    "tithi": p["tithi"]["name"], "paksha": p["tithi"]["paksha"],
                    "tithi_in_paksha": tithi_in_paksha,
                    "yoga": p["yoga"]["name"], "karana": p["karana"]["name"]},
            "ok": ev.ok,
            "hard_failures": list(ev.hard_failures),
            "score": ev.score,
            "tarabala": {"tara": ev.tarabala.tara, "name": ev.tarabala.name,
                         "favourable": ev.tarabala.favourable,
                         "negative_opening_ghatis": ev.tarabala.negative_opening_ghatis,
                         "source": _cite(ev.tarabala.source)},
            "chandrabala": ev.chandrabala_ok,
            "limbs": [{"limb": lv.limb, "value": lv.value, "suitable": lv.suitable,
                       "source": _cite(lv.source)} for lv in ev.limbs],
            "panchaka": {"remainder": ev.panchaka.remainder, "name": ev.panchaka.name,
                         "favourable": ev.panchaka.favourable,
                         "source": _cite(ev.panchaka.source)},
            "transit_elections": transits,
            "negative_windows": [_window_json(w, q.tz_offset) for w in windows],
            "disclaimer": _DISCLAIMER,
        }

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("electional reading failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"electional reading failed: {exc}") from exc
