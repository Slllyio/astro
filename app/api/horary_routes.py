"""HTTP surface over the WALLED horary (Prasna) subsystem — `app.raman_saab.horary`.

One endpoint judges a question asked at a moment: Neelakantha's Karyasiddhi verdict as
Raman translates it (`horary.prasna_judge.judge_prasna`) plus the ten printed sahams for the
query moment (`horary.sahams.compute_sahams`). The route resolves a plain-English `topic` to
its karyesa house when the caller does not name one, and ALWAYS passes `topic` down so the
coded exclusions (death / lifespan / serious illness / self-harm) fire inside the judge — a
refused query returns HTTP 200 carrying `refusal`, never a 500 and never a verdict.

DOCTRINE NOTE (surfaced to callers): output is a statement of the Prasna Tantra METHOD —
never a validated prediction. See the package docstring and CLAUDE.md "Measured Truth".

Endpoints:
    POST /horary/ask    {question, query_house|topic, moment?, latitude, longitude,
                        tz_offset} -> Karyasiddhi verdict + evidence + sahams.

Usage:
    curl -X POST http://127.0.0.1:8000/horary/ask -H 'content-type: application/json' \
      -d '{"question":"will the alliance be settled?","topic":"marriage",
           "latitude":12.97,"longitude":77.59,"tz_offset":5.5}'
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.electional_routes import sun_events
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.constants import SWE_PLANETS
from app.raman_saab.chart.model import BirthData
from app.raman_saab.horary.prasna_judge import EXCLUDED_TOPICS, judge_prasna
from app.raman_saab.horary.sahams import compute_sahams

logger = logging.getLogger(__name__)

horary_router = APIRouter(prefix="/horary", tags=["Horary (Prasna)"])

#: Plain-English topic -> the house whose lord is the Karyesa. Mirrors the karyesa examples
#: Raman gives at PRASNA-49:119-126 ("wealth -> 2nd lord, marriage -> 7th lord") extended
#: over the standard bhava significations; a caller who disagrees passes `query_house`
#: explicitly and this table is bypassed entirely.
TOPIC_HOUSE: dict[str, int] = {
    "marriage": 7, "wealth": 2, "career": 10, "children": 5, "travel": 3,
    "property": 4, "litigation": 6, "education": 4,
}

_DISCLAIMER = ("What Neelakantha's Prasna Tantra (tr. B. V. Raman) says of this query "
               "moment — a statement of the method, never a validated prediction.")


class PrasnaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=500)
    # Either names the karyesa house directly, or a topic this module maps to one.
    query_house: Optional[int] = Field(None, ge=1, le=12)
    topic: Optional[str] = Field(None, max_length=40)
    # The moment the question was asked, as LOCAL civil time at `tz_offset` (any tzinfo on
    # the value is ignored). Defaults to now.
    moment: Optional[datetime] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-12.0, le=14.0)
    ayanamsa: Literal["raman", "lahiri"] = "lahiri"


def _resolve_house(req: PrasnaRequest) -> int:
    """The karyesa house for this query, or 400 when neither route to one is given.

    An excluded topic resolves to a placeholder so `judge_prasna` — the single coded gate —
    is what refuses, rather than this module duplicating the exclusion list.
    """
    if req.query_house is not None:
        return req.query_house
    topic = (req.topic or "").strip().lower()
    if topic in EXCLUDED_TOPICS:
        return 1
    house = TOPIC_HOUSE.get(topic)
    if house is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"give query_house (1..12) or a known topic {sorted(TOPIC_HOUSE)}; "
                   f"got topic={req.topic!r}")
    return house


@horary_router.post("/ask")
async def ask(req: PrasnaRequest) -> dict:
    """Judge one Prasna. Casts the query-moment chart, runs the Karyasiddhi judgment and the
    ten sahams; ephemeris work is offloaded to a worker thread. Excluded topics return 200
    with `refusal` set and no verdict."""
    house = _resolve_house(req)
    topic = (req.topic or "").strip().lower() or None

    def _build() -> dict:
        tz = timezone(timedelta(hours=req.tz_offset))
        when = req.moment.replace(tzinfo=None) if req.moment else datetime.now(tz).replace(tzinfo=None)
        moment_birth = BirthData(name="prasna", year=when.year, month=when.month,
                                 day=when.day, hour=when.hour, minute=when.minute,
                                 tz_offset=req.tz_offset, latitude=req.latitude,
                                 longitude=req.longitude)
        chart = cast_chart(moment_birth, ayanamsa=req.ayanamsa)
        # The seven visible grahas only — the judge's benefic/10th-house counts and the
        # saham formulas are defined over them (Rahu/Ketu are chayagrahas).
        positions = {name: chart.planets[name].lon for name in SWE_PLANETS}

        verdict = judge_prasna(positions=positions, lagna_lon=chart.asc_lon,
                               query_house=house, topic=topic)
        base = {"question": req.question, "topic": topic,
                "moment": {"local_iso": when.replace(tzinfo=tz).isoformat(timespec="seconds"),
                           "jd": chart.jd_ut},
                "disclaimer": verdict.disclaimer or _DISCLAIMER}
        if verdict.refusal is not None:
            return {**base, "query_house": None, "refusal": verdict.refusal}

        jd = chart.jd_ut
        assert jd is not None  # cast_chart from BirthData always sets jd_ut
        sunrise, sunset, _next_sunrise = sun_events(moment_birth)
        is_day = sunrise <= jd < sunset
        sahams = compute_sahams(positions, chart.asc_lon, is_day=is_day)

        return {
            **base,
            "query_house": house,
            "refusal": None,
            "ayanamsa": req.ayanamsa,
            "lagna": {"lon": chart.asc_lon, "sign": chart.asc_sign},
            "is_day": is_day,
            "verdict": {"fulfilled": verdict.fulfilled,
                        "success_quarters": verdict.success_quarters,
                        "success_percent": verdict.success_quarters * 25,
                        "karyesa": verdict.karyesa},
            "evidence": list(verdict.evidence),
            "sahams": [{"name": s.name, "lon": s.lon, "rasi": s.rasi, "lord": s.lord,
                        "source": f"{s.source.work}:{s.source.line}"} for s in sahams],
        }

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("prasna judgment failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"prasna judgment failed: {exc}") from exc
