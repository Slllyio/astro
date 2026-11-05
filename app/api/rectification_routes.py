"""/rectify — retired. The engine no longer fits a birth time to a person's life events.

Until 2026-11-05 this endpoint searched the window around a stated birth time for the
moment whose dasha periods best matched the user's dated life events (marriage, job,
childbirth, a parent's death) and natal facts ("mother afflicted"), then returned that
time. The rest of the app would then read the chart cast at that time, including the very
dasha periods the events had been fitted to. That is circular: with a window of an hour
or two there is always some time whose periods line up with a handful of events, so the
"fit" is guaranteed by construction and the later reading "confirms" what was put in.
Published blind tests of astrology (Carlson 1985; Dean & Kelly 2003; Narlikar 2009) and
this project's own null results give no reason to trust the fit as evidence either way.

What replaces it (see ``docs/raman_saab/BIRTH_TIME_POLICY.md``):

* the birth time is taken as RECORDED, with its source stated (hospital record, birth
  certificate, family recollection, estimate);
* the reading reports how sensitive it is to that time instead of "correcting" it — the
  detailed report's "Rectification confidence" chapter re-casts the chart minute by minute
  out to +-60 minutes and names which pillars flip where, and the cited reader re-judges
  each house at -20 .. +20 minutes;
* the feedback form may ask non-event physical questions (build, apparent age, the
  two-sign portrait when the ascendant sits near a cusp); those are recorded, never used
  to move the time automatically.

Every /rectify call now answers 410 Gone with this policy, so an old client fails
loudly instead of silently getting a fitted time.
"""
from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

rectification_router = APIRouter(prefix="/rectify", tags=["Birth-Time Rectification (retired)"])

POLICY: dict = {
    "status": "retired",
    "retired_on": "2026-11-05",
    "reason": (
        "Event-based rectification picked the birth time whose dasha periods best matched "
        "the user's own dated life events, and the reading then read those same periods "
        "back. The fit is guaranteed by construction, so it is not evidence, and the "
        "reading built on it would look right for the wrong reason."),
    "what_the_engine_does_instead": [
        "Uses the birth time as recorded and asks where it came from (hospital record, "
        "birth certificate, family recollection, estimate).",
        "Reports birth-time sensitivity: the detailed report re-casts the chart minute by "
        "minute to +-60 minutes and names which pillars (lagna, navamsa lagna, Moon "
        "nakshatra, planet houses) flip and where; the cited reader re-judges each house "
        "at -20 .. +20 minutes.",
        "May record non-event physical observations (build, apparent age, the two-sign "
        "portrait near a cusp). These are shown to the user and never move the time "
        "automatically.",
    ],
    "never_used_to_set_a_birth_time": [
        "dated life events (marriage, job, children, a parent's death, surgery)",
        "life facts judged by the same house rules the reading uses (e.g. 'mother afflicted')",
    ],
    "policy_doc": "docs/raman_saab/BIRTH_TIME_POLICY.md",
}


def _gone() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_410_GONE, content=POLICY)


@rectification_router.get("/policy")
async def policy() -> dict:
    """The birth-time policy that replaced event-based rectification."""
    return POLICY


@rectification_router.get("/event-types")
async def event_types() -> JSONResponse:
    """Retired: there is no event taxonomy for rectification any more."""
    return _gone()


@rectification_router.post("")
async def post_rectify() -> JSONResponse:
    """Retired: always 410 Gone with the policy, whatever the body."""
    return _gone()
