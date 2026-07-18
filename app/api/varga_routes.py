"""HTTP endpoint for the Shodasavarga (16 divisional-chart) reading.

Wraps ``app.raman_saab.judges.varga_judge.build_shodasavarga_report`` (see
``docs/raman_saab/varga_validation_field_case_01.md``). Stateless single-shot: POST a
birth (date + time + place + ayanamsa) and receive the full 16-varga report — each
division's lagna, lagna lord, domain karakas, benefic/malefic occupancy, the
confirms/weakens ``status`` and the Parijatadi Vargavisesha standings, every row
carrying its Raman citation.

DOCTRINE NOTE (surfaced to callers): these readings are a report-only surface. Only the
D9 navamsa modulates the D1 house verdicts inside the engine; the other fifteen divisions
describe, they do not adjudicate. Domain strings for the divisions Raman does not detail
rest on his own Parashara pointer (HPA-11:195-201) — see the per-row citation and
``GET /vargas/divisions``.

Endpoints:
    POST /vargas             JSON birth -> the 16-division report (both/either ayanamsa).
    GET  /vargas/divisions   the domain table (each division, matter, karakas, citation).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.varga_domains import DOMAINS
from app.raman_saab.judges.varga_judge import build_shodasavarga_report
from app.raman_saab.render_varga import to_dict

logger = logging.getLogger(__name__)

varga_router = APIRouter(prefix="/vargas", tags=["Divisional Charts (Shodasavarga)"])

_SUPPORTED_AYANAMSAS: tuple[str, ...] = ("raman", "lahiri")


class VargaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year: int = Field(..., ge=1800, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-12.0, le=14.0)
    ayanamsa: Literal["raman", "lahiri"] = "raman"


@varga_router.get("/divisions")
async def divisions() -> dict:
    """The Shodasavarga domain table — each division, the life-matter it studies, its
    karakas, related D1 house(s) and the Raman citation grounding the domain."""
    return {
        "count": len(DOMAINS),
        "divisions": [
            {"n": d.n, "name": d.name, "domain": d.domain,
             "related_houses": list(d.related_houses), "karakas": list(d.karakas),
             "citation": f"{d.source.work}:{d.source.line}", "notes": d.notes}
            for d in DOMAINS
        ],
    }


@varga_router.post("")
async def post_vargas(req: VargaRequest) -> dict:
    """Cast the nativity and return its 16-division Shodasavarga reading. The swisseph
    cast is offloaded to a worker thread (CPU-bound ephemeris work)."""
    if req.ayanamsa not in _SUPPORTED_AYANAMSAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail=f"unsupported ayanamsa {req.ayanamsa!r}; "
                                   f"use one of {_SUPPORTED_AYANAMSAS}")

    def _build() -> dict:
        chart = cast_chart(
            BirthData(name="api", year=req.year, month=req.month, day=req.day,
                      hour=req.hour, minute=req.minute, tz_offset=req.tz_offset,
                      latitude=req.latitude, longitude=req.longitude),
            ayanamsa=req.ayanamsa)
        report = to_dict(build_shodasavarga_report(chart))
        report["ayanamsa"] = req.ayanamsa
        return report

    try:
        return await asyncio.to_thread(_build)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("shodasavarga reading failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"shodasavarga reading failed: {exc}") from exc
