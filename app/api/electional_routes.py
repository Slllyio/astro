"""HTTP surface over the WALLED electional (Muhurtha) subsystem — `app.raman_saab.electional`.

Two endpoints answer "what does Raman's *Muhurtha* say about this day for this native": the
day's Tarabala and Chandrabala measured from the native's own janma star/rasi, the five
panchanga limbs, Panchaka, the ASP ch.XV transit-band elections read against the native's
Bhinnashtakavarga, and the day's negative windows (Rahu Kalam + Durmuhurtha) as local ISO
times. The judgment itself is `electional.window_scorer.evaluate_moment` — this module adds
no doctrine, only the ephemeris plumbing and the JSON shape.

DOCTRINE NOTE (surfaced to callers): output is a statement of Raman's electional METHOD —
never a validated prediction. See the package docstring and CLAUDE.md "Measured Truth".

Endpoints:
    GET /electional/today   native birth params (+ optional date/hour/act) -> the day's
                            electional reading at ONE moment.
    GET /electional/scan    the same native/day -> WHEN the day is clean: the same judgment
                            re-applied at interval samples from sunrise to next sunrise, and
                            the contiguous clean spans that come out of it (day_scanner).

Usage:
    curl "http://127.0.0.1:8000/electional/today?year=1990&month=7&day=15&hour=12\
&latitude=12.97&longitude=77.59&tz_offset=5.5&date=2026-08-03&act=marriage"
    curl "http://127.0.0.1:8000/electional/scan?year=1990&month=7&day=15&hour=12\
&latitude=12.97&longitude=77.59&tz_offset=5.5&date=2026-08-03&act=marriage&interval_minutes=30"
"""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import date as date_cls, datetime, timedelta
from typing import Annotated, Literal, Optional

import swisseph as swe
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.panchanga import compute_panchanga
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.electional.asp_transit_elections import transit_election
from app.raman_saab.electional.day_scanner import (
    DEFAULT_SAMPLE_MINUTES,
    CleanSpan,
    MomentInputs,
    jd_to_local_iso as _jd_to_local_iso,
    rank_spans,
    scan_day,
)
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

_SCAN_NOTE = ("Each span is judged by the SAME essentials ordering as the single-moment "
              "reading (MUHURTHA-10:226-228), sample by sample: it is verified at its sample "
              "points and only as fine as the sample interval. Ranking by essentials score "
              "orders Raman's own method, and promises nothing about outcomes.")


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


class ElectionalScanQuery(ElectionalQuery):
    """`/electional/scan` — the same native and day, plus the sampling resolution.

    `election_hour` / `election_minute` are inherited but unused here: the scan judges the
    WHOLE day (sunrise to the following sunrise, the span Raman's durmuhurthas partition),
    not one chosen moment.
    """

    interval_minutes: int = Field(DEFAULT_SAMPLE_MINUTES, ge=5, le=120)


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


def _birth_at(jd: float, q: ElectionalScanQuery) -> BirthData:
    """The sample instant as `BirthData` (local wall clock, to the nearest minute).

    `cast_chart` takes a birth record, not a Julian Day, so the sample's JD is converted back
    through the same `jd_to_local_iso` the output uses — which normalises the 23:59:60 /
    midnight rollover — and rounded to the minute the sample grid is aligned to anyway.
    """
    stamp = datetime.fromisoformat(_jd_to_local_iso(jd, q.tz_offset)) + timedelta(seconds=30)
    return BirthData(name="scan", year=stamp.year, month=stamp.month, day=stamp.day,
                     hour=stamp.hour, minute=stamp.minute, tz_offset=q.tz_offset,
                     latitude=q.latitude, longitude=q.longitude)


def _span_json(span: CleanSpan, rank: int) -> dict:
    """One clean span, reader-facing. `passing`/`failing` are the factors that DEFINE it."""
    return {"rank": rank, "start": span.start_local, "end": span.end_local,
            "start_jd": span.start_jd, "end_jd": span.end_jd,
            "duration_minutes": span.duration_minutes, "samples": span.samples,
            "score": span.score, "score_max": span.score_max,
            "passing": list(span.passing), "failing": list(span.failing)}


@electional_router.get("/scan")
async def electional_scan(q: Annotated[ElectionalScanQuery, Query()]) -> dict:
    """WHEN this day is clean for this native — the same judgment, sampled across the day.

    Iterates `window_scorer.evaluate_moment` (via `day_scanner.scan_day`) every
    `interval_minutes` from the first aligned local time at or after sunrise to the following
    sunrise — the span Raman's durmuhurthas partition — and returns the contiguous spans in
    which every sample passed, ranked by essentials score. No new doctrine: a span is exactly
    "the single-moment reading passed here, and here, and here".
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
        day_birth = BirthData(name="scan", year=elect_on.year, month=elect_on.month,
                              day=elect_on.day, hour=12, minute=0, tz_offset=q.tz_offset,
                              latitude=q.latitude, longitude=q.longitude)
        sunrise, sunset, next_sunrise = sun_events(day_birth)
        weekday_of_day = compute_panchanga(sunrise)["vara"]["index"]
        windows = (rahu_kalam(weekday_of_day, sunrise, sunset),
                   *durmuhurtha_windows(weekday_of_day, sunrise, sunset, next_sunrise))

        # Sample grid aligned to the LOCAL clock (…07:00, 07:30…), starting at the first
        # aligned instant at or after sunrise: Raman's day begins at sunrise, and the
        # durmuhurtha partition below only covers sunrise -> next sunrise.
        step = q.interval_minutes / 1440.0
        midnight_jd = swe.julday(elect_on.year, elect_on.month, elect_on.day,
                                 0.0 - q.tz_offset, swe.GREG_CAL)
        start_jd = midnight_jd + math.ceil((sunrise - midnight_jd) / step) * step

        def sampler(jd: float) -> MomentInputs:
            chart = cast_chart(_birth_at(jd, q), ayanamsa=q.ayanamsa)
            p = compute_panchanga(jd)
            return MomentInputs(
                tithi_in_paksha=p["tithi"]["index"] % 15 + 1,
                weekday=p["vara"]["index"],
                day_nakshatra=int(p["nakshatra"]["index"]) + 1,
                yoga=p["yoga"]["index"] + 1,
                karana=_karana_number(p["karana"]["index"]),
                election_moon_rasi=chart.planets["Moon"].sign,
                lagna_sign=chart.asc_sign)

        scan = scan_day(day_start_jd=start_jd, day_end_jd=next_sunrise,
                        janma_nakshatra=janma_nakshatra, janma_rasi=janma_rasi,
                        sampler=sampler, sample_minutes=q.interval_minutes, act=q.act,
                        negative_windows=windows, tz_offset=q.tz_offset)

        ranked = rank_spans(scan.clean_spans)
        rank_of = {id(s): i + 1 for i, s in enumerate(ranked)}
        return {
            "date": elect_on.isoformat(),
            "act": q.act,
            "ayanamsa": q.ayanamsa,
            "interval_minutes": scan.sample_minutes,
            "scan_window": {"start": _jd_to_local_iso(scan.start_jd, q.tz_offset),
                            "end": _jd_to_local_iso(scan.end_jd, q.tz_offset),
                            "start_jd": scan.start_jd, "end_jd": scan.end_jd,
                            "sunrise": _jd_to_local_iso(sunrise, q.tz_offset),
                            "sunset": _jd_to_local_iso(sunset, q.tz_offset),
                            "next_sunrise": _jd_to_local_iso(next_sunrise, q.tz_offset)},
            "native": {"janma_nakshatra": janma_nakshatra, "janma_rasi": janma_rasi},
            "sample_count": len(scan.samples),
            "clean_sample_count": scan.clean_sample_count,
            # chronological (each row carries its own rank); `best` is the top-ranked span.
            "clean_spans": [_span_json(s, rank_of[id(s)]) for s in scan.clean_spans],
            "best": _span_json(ranked[0], 1) if ranked else None,
            "blocked_windows": [_window_json(w, q.tz_offset) for w in scan.blocked_windows],
            "samples": [{"local_iso": s.local_iso, "jd": s.jd, "ok": s.ok,
                         "score": s.score, "hard_failures": list(s.evaluation.hard_failures)}
                        for s in scan.samples],
            "disclaimer": _DISCLAIMER,
            "scan_note": _SCAN_NOTE,
        }

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("electional day scan failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"electional day scan failed: {exc}") from exc
