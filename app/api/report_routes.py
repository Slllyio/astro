"""HTTP endpoint for the full detailed reading (`app.raman_saab.detailed_report`).

Wraps ``build_detailed_report`` — the whole engine's answer for one chart: every contracted
section (Chart signature, Ruler of the nativity, House-by-house with per-house Conclusions,
the strength cross-check, Preponderance of testimonies, Longevity, the Life-narrative and its
companions, the Life-chapters, Gochara, the divisional deep-reads, Soul & destiny, Pitru
dosha, Integrated insights and the Nichod capstone), rendered as Markdown or a standalone HTML
document, plus a compact structured ``summary`` of the highest-signal synthesis fields.

DOCTRINE NOTE (surfaced to callers): the reading answers "what would Raman say", faithfully to
his texts — it is NOT a validated predictor of a life. The population-calibration overlay
(EMPIRICAL_ASTRODATABANK) discloses each reading's information content, never a real-outcome
claim; see the report's own "Information content" and "Measured Truth" framing.

Endpoints:
    POST /report            JSON birth (+ format, window) -> the full reading + summary.
    GET  /report/sections   the section contract (id, heading, since-version) — what a report
                            contains, in document order.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (
    SECTION_CONTRACT,
    build_detailed_report,
    to_markdown,
)
from app.raman_saab.report_html import standalone_html

logger = logging.getLogger(__name__)

report_router = APIRouter(prefix="/report", tags=["Detailed Reading"])

_SUPPORTED_AYANAMSAS: tuple[str, ...] = ("raman", "lahiri")


class ReportRequest(BaseModel):
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
    fmt: Literal["markdown", "html"] = Field("markdown", alias="format")
    years_back: int = Field(10, ge=0, le=120)
    years_forward: int = Field(20, ge=0, le=120)


def _summary(r) -> dict:
    """The highest-signal synthesis fields, all JSON-primitive — structured hooks for callers
    who do not want to parse the rendered prose. Every value is read, never re-judged."""
    ru, pr = r.ruler, r.preponderance
    return {
        "lagna": r.synthesis.lagna,
        "ruler_of_nativity": {
            "lagna_lord": ru.lagna_lord,
            "strongest_planet": ru.strongest,
            "strongest_rupas": (round(ru.strongest_rupas, 2)
                                if ru.strongest_rupas is not None else None),
            "coincide": ru.coincide,
        },
        "longevity": {"class": r.longevity_class, "years": r.longevity_years},
        "running_period": {"md": r.synthesis.running_md, "ad": r.synthesis.running_ad},
        "preponderance": {
            "most_corroborated_favourable": pr.most_corroborated_favourable,
            "most_corroborated_afflicted": pr.most_corroborated_afflicted,
            "most_contested": pr.most_contested,
        },
        "plain_opening": r.plain_reading.opening,
        "essence": r.nichod.essence,
    }


@report_router.get("/sections")
async def sections() -> dict:
    """The report's section contract in document order — each section's id, its Markdown
    heading (None for HTML-only sections), and the version that introduced it. Mirrors
    ``detailed_report.SECTION_CONTRACT`` (the append-only template ratchet)."""
    return {
        "count": len(SECTION_CONTRACT),
        "sections": [
            {"id": s.section_id, "heading": s.md_marker, "since": s.since}
            for s in SECTION_CONTRACT
        ],
    }


@report_router.post("")
async def post_report(req: ReportRequest) -> dict:
    """Cast the nativity and return its full detailed reading in the requested format, plus a
    compact structured summary. The build (ephemeris + full composition) is offloaded to a
    worker thread."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"unsupported ayanamsa {req.ayanamsa!r}; "
                                   f"use one of {_SUPPORTED_AYANAMSAS}")

    def _build() -> dict:
        birth = BirthData(name=req.name, year=req.year, month=req.month, day=req.day,
                          hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                          latitude=req.latitude, longitude=req.longitude)
        r = build_detailed_report(birth, ayanamsa=req.ayanamsa,
                                  years_back=req.years_back, years_forward=req.years_forward)
        rendered = standalone_html(r) if req.fmt == "html" else to_markdown(r)
        return {
            "ayanamsa": req.ayanamsa,
            "format": req.fmt,
            "summary": _summary(r),
            "report": rendered,
        }

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("detailed reading failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"detailed reading failed: {exc}") from exc
