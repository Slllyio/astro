"""Read-only API for the empirical engine.

One surface, two representations of the same payload. It serves what survived the
protocol and nothing else — and when nothing survived, it serves that as a
result with its working shown rather than an empty list.

Read-only by construction: there is no write path, no model call, and no
free-text generation anywhere behind these endpoints. Everything returned is a
measurement or a fixed disclosure string.

Endpoints:
    GET /empirical/survivors    the payload as JSON
    GET /empirical/report       the same payload as markdown
    GET /empirical/health       whether a survivor set is present at all
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Final

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.empirical.engine.report import FRAMING, render, to_markdown
from app.empirical.engine.survivors import SurvivorSet, load_survivors

logger = logging.getLogger(__name__)

empirical_router = APIRouter(prefix="/empirical", tags=["empirical"])

#: Local-only artifact, like every other corpus output in this repo.
_SURVIVORS_PATH: Final[Path] = Path("data/empirical/survivors.json")


def _load() -> SurvivorSet:
    """Load the survivor set, or an explicitly-empty one if none has been built.

    A missing file is not an error: it means no tournament has been run here. The
    surface says exactly that instead of 500-ing or implying a null result was
    measured when none was.
    """
    if not _SURVIVORS_PATH.is_file():
        return SurvivorSet(
            corpus="(none)",
            stage="unbuilt",
            notes=(
                "No survivor set has been built in this deployment. This is not a "
                "measured null — nothing has been measured here at all."
            ),
        )
    try:
        return load_survivors(_SURVIVORS_PATH)
    except ValueError as exc:
        # A malformed claim must never be served. Failing loudly is correct: the
        # only claims that may reach a reader are ones that beat their twin.
        logger.error("survivor set rejected: %s", exc)
        raise HTTPException(status_code=500, detail=f"survivor set failed validation: {exc}")


@empirical_router.get("/survivors")
async def get_survivors() -> dict[str, Any]:
    """Validated claims, or the measured null, with full disclosure."""
    return render(_load())


@empirical_router.get("/report", response_class=PlainTextResponse)
async def get_report() -> str:
    """The same payload as markdown. Loses nothing the JSON carries."""
    return to_markdown(_load())


@empirical_router.get("/health")
async def get_health() -> dict[str, Any]:
    """Whether anything has been built here, without implying a result."""
    survivor_set = _load()
    return {
        "survivor_set_present": _SURVIVORS_PATH.is_file(),
        "stage": survivor_set.stage,
        "shippable": survivor_set.is_shippable,
        "n_claims": len(survivor_set.claims),
        "tests_recorded": len(survivor_set.tested),
        "framing": FRAMING,
    }
