"""HTTP endpoints for KP birth-time rectification with chart-chosen questions.

Stateless, like ``/rectify``: the browser keeps the answers and re-POSTs all of them each round.
Casting every candidate minute is the slow step, so the cast set is cached per
(birth, window, today, engines); a new answer only recomputes likelihoods.

Nothing a visitor sends is stored or logged beyond the in-memory cast cache, which holds
chart predictions only (never answers) and is bounded.

Endpoints:
    GET  /kp-rectify/page     the interactive page
    GET  /kp-rectify/facts    the question bank (text, kind, options, rules)
    POST /kp-rectify/round    birth + window + answers -> band, answer effects, next questions, hand-off
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import logging
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from app.kp.rect_questions import FACT_BY_KEY, FACTS, Built
from app.kp.rect_session import built_for, session_result

logger = logging.getLogger(__name__)

kp_rectify_router = APIRouter(prefix="/kp-rectify", tags=["KP Birth-Time Rectification"])

_MAX_HALF_WINDOW = 60
_MAX_ANSWERS = 80
_CACHE_SIZE = 16
_PAGE = Path(__file__).resolve().parent.parent / "templates" / "kp_rectify.html"

_cache: "OrderedDict[tuple, Built]" = OrderedDict()
_lock = Lock()

DateParts = list[int]


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fact: str
    answer: Union[bool, str, int, DateParts, list[DateParts], None] = None


class RoundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year: int = Field(..., ge=1900, le=2030)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    tz: float = Field(5.5, ge=-12, le=14)
    lat: float = Field(..., ge=-66, le=66)
    lon: float = Field(..., ge=-180, le=180)
    half_window: int = Field(30, ge=5, le=_MAX_HALF_WINDOW)
    engines: list[Literal["kp", "raman"]] = Field(default_factory=lambda: ["kp"])
    answers: list[Answer] = Field(default_factory=list, max_length=_MAX_ANSWERS)
    n_questions: int = Field(8, ge=1, le=15)


def _session(req: RoundRequest) -> dict[str, Any]:
    t = _dt.date.today()
    return {"date": [req.year, req.month, req.day], "time": [req.hour, req.minute], "tz": req.tz,
            "lat": req.lat, "lon": req.lon, "window": [-req.half_window, req.half_window],
            "today": [t.year, t.month, t.day], "engines": sorted(set(req.engines)),
            "answers": [a.model_dump() for a in req.answers]}


def _built(S: dict) -> Built:
    key = (tuple(S["date"]), tuple(S["time"]), S["tz"], S["lat"], S["lon"], tuple(S["window"]),
           tuple(S["today"]), tuple(S["engines"]))
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    b = built_for(S)
    with _lock:
        _cache[key] = b
        while len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return b


def _validate(req: RoundRequest) -> None:
    try:
        _dt.date(req.year, req.month, req.day)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"invalid date: {exc}") from exc
    for a in req.answers:
        f = FACT_BY_KEY.get(a.fact)
        if f is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"unknown question {a.fact!r}")
        v = a.answer
        if v is None:
            continue
        if f.kind == "yesno" and not isinstance(v, bool):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{a.fact}: answer true or false")
        if f.kind == "choice" and not ((isinstance(v, str) and v in f.options) or
                                       (isinstance(v, int) and not isinstance(v, bool) and 0 <= v < len(f.options))):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{a.fact}: pick one of {list(f.options)}")
        if f.kind == "date":
            dates = v if isinstance(v, list) and v and isinstance(v[0], list) else [v]
            for d in dates:
                if not isinstance(d, list) or not 1 <= len(d) <= 3 or not all(isinstance(x, int) for x in d):
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{a.fact}: dates are [year, month?, day?]")
                try:
                    _dt.date(d[0], d[1] if len(d) > 1 else 1, d[2] if len(d) > 2 else 1)
                except ValueError as exc:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{a.fact}: {exc}") from exc
                if d[0] < req.year:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{a.fact}: date before birth")


@kp_rectify_router.get("/page", response_class=HTMLResponse)
async def kp_rectify_page() -> HTMLResponse:
    """The interactive rectification page."""
    return HTMLResponse(content=_PAGE.read_text(encoding="utf-8"))


@kp_rectify_router.get("/facts")
async def kp_rectify_facts() -> dict[str, Any]:
    """The question bank: every askable fact with its kind, options and the rules behind it."""
    return {"facts": [{"key": f.key, "kind": f.kind, "text": f.text, "options": list(f.options),
                       "ask_if": f.ask_if, "note": f.note} for f in FACTS]}


@kp_rectify_router.post("/round")
async def kp_rectify_round(req: RoundRequest) -> dict[str, Any]:
    """One round: posterior over minutes, what each answer did, the next questions for this chart."""
    _validate(req)
    S = _session(req)

    def work() -> dict[str, Any]:
        return session_result(S, built=_built(S), n_questions=req.n_questions, sims=200)
    try:
        return await asyncio.to_thread(work)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
