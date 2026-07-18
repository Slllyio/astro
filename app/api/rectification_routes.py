"""HTTP endpoint for birth-time rectification & time discovery.

Wraps the ``app.raman_saab.rectification`` engine (see
``docs/raman_saab/methodology/rectification.md``). Stateless by design: HTTP is
naturally single-shot, so the client holds the accumulating list of life events and
re-POSTs the full set each round (the CLI's stateful session is the local-file
equivalent). Both ayanamsas (raman + Lahiri) are always searched; the response ranks
birth-time equivalence CLASSES, never a single point time.

Endpoint:
    POST /rectify   JSON birth data + dated life events (+ optional natal facts) ->
                    ranked candidate classes, the ayanamsa verdict, and the next
                    most-discriminating questions to ask.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.raman_saab.rectification.events import EVENT_TAXONOMY, LifeEvent, resolve_fact
from app.raman_saab.rectification.report import to_dict
from app.raman_saab.rectification.session import RectificationSession

logger = logging.getLogger(__name__)

rectification_router = APIRouter(prefix="/rectify", tags=["Birth-Time Rectification"])

#: Bounds on the CPU an unauthenticated POST can trigger (each event/ayanamsa multiplies
#: the swisseph work; discover mode sweeps the whole day).
_MAX_EVENTS = 24
_MAX_FACTS = 12
_MAX_WINDOW_MIN = 240


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: str = Field(..., description="a key of the event taxonomy, e.g. 'marriage'")
    year: int = Field(..., ge=1800, le=2200)
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    weight: float = Field(1.0, gt=0.0, le=10.0)


class FactInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(..., description="a signification key, e.g. 'mother'")
    observed: Literal["favourable", "mixed", "afflicted"]
    weight: float = Field(1.0, gt=0.0, le=10.0)


class RectifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["rectify", "discover"] = "rectify"
    year: int = Field(..., ge=1800, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-12.0, le=14.0)
    stated_hour: Optional[int] = Field(None, ge=0, le=23,
                                       description="required for mode='rectify'")
    stated_minute: Optional[int] = Field(0, ge=0, le=59)
    window_minutes: int = Field(60, ge=1, le=_MAX_WINDOW_MIN)
    ayanamsas: tuple[str, ...] = ("raman", "lahiri")
    events: list[EventInput] = Field(default_factory=list)
    facts: list[FactInput] = Field(default_factory=list)
    top_k: int = Field(8, ge=1, le=20)


@rectification_router.get("/event-types")
async def event_types() -> dict:
    """The rectification event taxonomy — each typed event, its fructification house,
    the doctrine citation, and the human question the UI can present."""
    return {
        "count": len(EVENT_TAXONOMY),
        "event_types": [
            {"key": s.key, "house": s.house, "aux_houses": list(s.aux_houses),
             "question": s.question,
             "citation": f"{s.source.work}:{s.source.line}"}
            for s in EVENT_TAXONOMY.values()
        ],
    }


@rectification_router.post("")
async def post_rectify(req: RectifyRequest) -> dict:
    """Rectify (stated time ± window) or discover (unknown time) a birth time from dated
    life events, searching both ayanamsas. Returns ranked candidate CLASSES + the
    ayanamsa verdict + next questions. Compute is offloaded to a worker thread (a
    discover-mode search casts many charts)."""
    if req.mode == "rectify" and req.stated_hour is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="mode='rectify' requires stated_hour (and stated_minute)")
    if len(req.events) > _MAX_EVENTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"too many events (max {_MAX_EVENTS})")
    if len(req.facts) > _MAX_FACTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"too many facts (max {_MAX_FACTS})")
    if not req.events and not req.facts:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="rectification needs evidence: supply at least one life event or "
                   "natal fact (GET /rectify/event-types lists valid event keys)")
    bad_ay = [a for a in req.ayanamsas if a not in ("raman", "lahiri")]
    if bad_ay:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"unsupported ayanamsa(s) {bad_ay}; use raman / lahiri")

    def _build_and_run() -> dict:
        session = RectificationSession.new(
            mode=req.mode, date=(req.year, req.month, req.day),
            lat=req.latitude, lon=req.longitude, tz=req.tz_offset,
            time=((req.stated_hour, req.stated_minute or 0)
                  if req.stated_hour is not None else None),
            window_minutes=req.window_minutes, ayanamsas=tuple(req.ayanamsas))
        for ev in req.events:
            session.add_event(LifeEvent(ev.event_type, ev.year, ev.month, ev.day,
                                        weight=ev.weight))
        for f in req.facts:
            session.add_fact(resolve_fact(f.subject, f.observed, weight=f.weight))
        return to_dict(session.evaluate(top_k=req.top_k))

    try:
        return await asyncio.to_thread(_build_and_run)
    except ValueError as exc:                       # bad event_type / fact subject
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("rectification failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"rectification failed: {exc}") from exc
