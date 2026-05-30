"""Tier-2 doctrine: refuse-to-output invariants ("rookie guards").

Doctrine source
===============

Practitioner craft, not chart doctrine. These guards catch four classes
of mistake that the engine could otherwise emit silently:

1. **Marriage timing without D9 dispositor agreement** — Sanjay Rath's
   formulation requires D9-dispositor concurrence before any marriage
   *timing* (vs natal *promise*) is asserted. A predicted marriage
   window without the D9 evidence is a rookie pattern; surface it.

2. **Raja Yoga with weak participants** — a Raja Yoga whose
   participating planets are combust, in a dusthana (6/8/12 trika),
   or otherwise debilitated cannot deliver its named result. BPHS
   Vol.II Ch.34 v.2 ("Lagna and house lords must be strong for the yoga
   to fructify"). The guard fires when ANY participant is weak.

3. **Health prediction without lagna-lord context** — classical
   diagnostics anchor health on the 1H (body) and 1L. A health verdict
   that does not reference the lagna lord is incomplete by construction.

4. **Career thin evidence** — practitioner schools converge on five
   pillars: D1-10H state, D10 lagna, Amatya Karaka, Sun placement,
   Saturn's role. A direction asserted with only 1 of these pillars
   confirming is rookie overreach.

Each guard emits a Finding with id ``practitioner.rookie_guards.<rule>``,
``classification="affliction"`` and ``direction="negative"`` (a guard
is a *problem detection*).

Public API
==========

    check_rookie_invariants(reading_output: dict) -> list[Finding]

The reading dict is the partially-built pre-seal envelope; only the
sections used by each guard are read. Missing sections are tolerated.
"""
from __future__ import annotations

import logging
from typing import Any, Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# Minimum pillar count below which a career direction is "thin evidence".
_CAREER_PILLAR_THRESHOLD: Final[int] = 2


def _make_finding(rule_name: str, verdict: str, evidence: list[str]) -> Finding:
    """Build a guard Finding with the locked classification/direction."""
    return Finding(
        id=f"practitioner.rookie_guards.{rule_name}",
        rule="rookie_guards",
        source_sequence=None,
        classification="affliction",
        direction="negative",
        verdict=verdict[:140],
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _check_marriage_d9_dispositor(reading: dict) -> Finding | None:
    """Guard 1: marriage timing predicted without D9 dispositor agreement."""
    marriage = reading.get("marriage")
    if not isinstance(marriage, dict):
        return None
    predicted_window = marriage.get("predicted_window")
    if not predicted_window:
        return None
    d9_ok = bool(marriage.get("d9_dispositor_confirmation"))
    if d9_ok:
        return None
    return _make_finding(
        "marriage_no_d9_dispositor",
        "WARNING: Marriage timing emitted without D9 dispositor confirmation",
        evidence=[
            f"predicted_window={predicted_window}",
            "d9_dispositor_confirmation=False",
            "doctrine=Sanjay Rath UL+7L+D9 dispositor formulation",
        ],
    )


def _is_raja_yoga(name: str) -> bool:
    """Match yoga names that claim 'Raja' status."""
    return "raja" in name.lower()


def _participant_weak(state: dict) -> bool:
    """A participant is weak if combust OR in trika OR flagged weak."""
    if not isinstance(state, dict):
        return False
    return bool(state.get("combust") or state.get("in_trika") or state.get("weak"))


def _check_raja_yoga_weak_participants(reading: dict) -> Finding | None:
    """Guard 2: Raja yoga claimed but participants weak."""
    yogas = reading.get("yogas")
    if not isinstance(yogas, list):
        return None
    for yoga in yogas:
        if not isinstance(yoga, dict):
            continue
        name = str(yoga.get("name", ""))
        if not _is_raja_yoga(name):
            continue
        states = yoga.get("participating_planet_states") or {}
        if not isinstance(states, dict):
            continue
        weak_planets = [p for p, s in states.items() if _participant_weak(s)]
        if weak_planets:
            return _make_finding(
                "raja_yoga_weak_participants",
                f"WARNING: Raja Yoga '{name}' weak participants: "
                f"{', '.join(weak_planets)}",
                evidence=[
                    f"yoga_name={name}",
                    f"weak_planets={weak_planets}",
                    "doctrine=BPHS Vol.II Ch.34 v.2 (lords must be strong)",
                ],
            )
    return None


def _check_health_lagna_lord_context(reading: dict) -> Finding | None:
    """Guard 3: health prediction missing lagna-lord context."""
    health = reading.get("health")
    if not isinstance(health, dict):
        return None
    verdict = health.get("verdict")
    if not verdict:
        return None
    if health.get("lagna_lord_context"):
        return None
    return _make_finding(
        "health_no_lagna_lord_context",
        "WARNING: Health prediction emitted without lagna-lord context",
        evidence=[
            f"verdict={verdict}",
            "lagna_lord_context_missing=True",
            "doctrine=Classical 1H/1L health anchoring",
        ],
    )


def _check_career_thin_evidence(reading: dict) -> Finding | None:
    """Guard 4: career direction with insufficient pillar confirmation."""
    career = reading.get("career")
    if not isinstance(career, dict):
        return None
    direction_str = career.get("direction")
    if not direction_str:
        return None
    pillars = career.get("pillar_confirmations") or {}
    if not isinstance(pillars, dict):
        return None
    confirmed = sum(1 for v in pillars.values() if bool(v))
    total = len(pillars)
    if total == 0:
        return None
    if confirmed >= _CAREER_PILLAR_THRESHOLD:
        return None
    return _make_finding(
        "career_thin_evidence",
        f"WARNING: Career direction '{direction_str}' confirmed by only "
        f"{confirmed}/{total} pillars",
        evidence=[
            f"direction={direction_str}",
            f"pillars_confirmed={confirmed}",
            f"pillars_total={total}",
            f"threshold={_CAREER_PILLAR_THRESHOLD}",
            "doctrine=5-pillar career synthesis (D1-10H/D10/AmK/Sun/Saturn)",
        ],
    )


_GUARDS: Final[tuple[Any, ...]] = (
    _check_marriage_d9_dispositor,
    _check_raja_yoga_weak_participants,
    _check_health_lagna_lord_context,
    _check_career_thin_evidence,
)


def check_rookie_invariants(reading_output: dict) -> list[Finding]:
    """Inspect a reading dict for known rookie-mistake patterns.

    Args:
        reading_output: Partially-built reading envelope. Only the
            sections referenced by each guard are read; missing sections
            are tolerated silently.

    Returns:
        List of Findings (one per fired guard). Empty list if no
        violations were detected. Each Finding has:
            - ``id`` = ``practitioner.rookie_guards.<rule_name>``
            - ``classification`` = ``"affliction"``
            - ``direction`` = ``"negative"``
            - ``verdict`` begins with ``"WARNING: "``
    """
    if not isinstance(reading_output, dict):
        return []

    findings: list[Finding] = []
    for guard in _GUARDS:
        try:
            result = guard(reading_output)
        except Exception as exc:  # noqa: BLE001
            logger.debug("rookie guard %s raised: %s", guard.__name__, exc)
            continue
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["check_rookie_invariants"]
