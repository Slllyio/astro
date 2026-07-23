"""HTTP endpoints for the soul-destiny reading (REPORT-ONLY). EXPERIMENT BRANCH.

Wraps ``judges/soul_reading.py`` + ``judges/family_soul_group.py``. Stateless single-shot: POST a
birth and receive the soul-destiny reading (Parashari mokṣa core + Jaimini soul-script + nakṣatra
signature + soul-purpose narrative), or POST several members for the soul-group interlock.

DOCTRINE NOTE (surfaced to callers): report-only — imported by nothing in the D1 verdict path, so
the golden ratchet is untouched. On the ``soul-destiny-experiment`` branch the Jaimini citation
firewall is deliberately lifted (see ``doctrine/book_registry.py``) so the Jaimini soul-script
carries citations; DO NOT deploy from ``main`` without re-review. A scripted destiny is a promise
and a tendency, not a fixed fate.

Endpoints:
    POST /soul         JSON birth -> the soul-destiny reading.
    POST /soul/group   {"members":[{role, birth...}]} -> the soul-group interlock (nets nothing).
    GET  /soul/about   the provenance note + the EXPERIMENT firewall caveat.
"""
from __future__ import annotations

import asyncio
import dataclasses
import logging
from typing import Callable, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.family_soul_group import build_family_soul_group
from app.raman_saab.judges.soul_reading import build_soul_reading

logger = logging.getLogger(__name__)

soul_router = APIRouter(prefix="/soul", tags=["Soul-Destiny (Jaimini + Parashari moksha)"])


class SoulRequest(BaseModel):
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


class SoulMember(SoulRequest):
    role: str = Field(..., min_length=1, max_length=40)


class SoulGroupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    members: list[SoulMember] = Field(..., min_length=2, max_length=8)


def _birth(req: SoulRequest, name: str) -> BirthData:
    return BirthData(name=name, year=req.year, month=req.month, day=req.day, hour=req.hour,
                     minute=req.minute, tz_offset=req.tz_offset, latitude=req.latitude,
                     longitude=req.longitude)


async def _run(fn: Callable[[], dict]) -> dict:
    try:
        return await asyncio.to_thread(fn)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("soul reading failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"soul reading failed: {exc}") from exc


@soul_router.get("/about")
async def about() -> dict:
    """The soul layer's provenance stance + the EXPERIMENT firewall caveat."""
    return {
        "layer": "soul-destiny (Jaimini soul-script + Parashari moksha core)",
        "report_only": True,
        "verdict_authority": "Parashari 5th/9th/12th (the core decides); the Jaimini and "
                             "nakshatra layers corroborate, netting no verdict",
        "experiment": "the Jaimini citation firewall is deliberately lifted on the "
                      "soul-destiny-experiment branch; do NOT deploy from main without re-review",
        "not_fatalism": "a scripted destiny is a promise and a tendency, not a fixed fate",
    }


@soul_router.post("")
async def post_soul(req: SoulRequest) -> dict:
    """Cast the nativity and return its soul-destiny reading (the swisseph cast runs off-thread)."""
    def _build() -> dict:
        chart = cast_chart(_birth(req, "api"), ayanamsa=req.ayanamsa)
        return dataclasses.asdict(build_soul_reading(chart))
    return await _run(_build)


@soul_router.post("/group")
async def post_group(req: SoulGroupRequest) -> dict:
    """Cross-reference several members' souls -> the soul-group interlock (nets no verdict)."""
    def _build() -> dict:
        pairs = [(m.role, cast_chart(_birth(m, m.role), ayanamsa=m.ayanamsa)) for m in req.members]
        return dataclasses.asdict(build_family_soul_group(pairs))
    return await _run(_build)
