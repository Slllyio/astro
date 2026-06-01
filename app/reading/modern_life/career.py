"""Modern-career signal detection (V1.5).

Detects contemporary career indicators on top of the V1 classical reading.
All findings emitted here use ``classification="primitive"`` to mark them
as **advisory context**, not predictive verdicts.

Signals detected
================

- ``software_it``       Rahu + Mercury + Saturn presence in 10H **or** D10
                        (the "tech triad" pattern read by Anil-Kumar-Jain
                        / Lakshmi-Narayana sampradaya).
- ``social_media``      Rahu in 3H or 11H of D1 (creator-economy /
                        virality marker).
- ``remote_freelance``  Rahu in 12H, or Mercury+Rahu/Ketu in 3H.
- ``entrepreneur``      Mars+Saturn conjunction or 1L strong in 10H.
- ``government``        Sun+Saturn together in 10H (bureaucratic /
                        public-sector marker).
- ``consulting``        Jupiter+Mercury together in 9H or 10H (advisory /
                        teaching).
- ``finance_trading``   Mars+Mercury in 11H **with** Rahu/Ketu involvement
                        (modern day-trading marker).

Public API
==========

    detect_modern_career(chart, asc_sign) -> list[Finding]

The function is *pure*: a chart dict + asc_sign in → a list[Finding] out.
No I/O, no global state.
"""
from __future__ import annotations

from typing import Final

from app.reading.modern_life._helpers import (
    planet_sign,
    planets_in_house,
)
from app.reading.schema import ConfidenceScore, Finding

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=modern_life.career (V1.5 advisory; classification=primitive)"
)

_ADVISORY_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _finding(
    rule_slug: str,
    direction: str,
    verdict: str,
    evidence: list[str],
) -> Finding:
    return Finding(
        id=f"modern_life.career.{rule_slug}",
        rule=f"modern_life.career.{rule_slug}",
        source_sequence=None,
        classification="primitive",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=evidence + [_DOCTRINE_SENTINEL],
        confidence=_ADVISORY_CONFIDENCE,
    )


def _software_it(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu+Mercury+Saturn cluster in 10H of D1 or D10."""
    d1 = chart.get("d1", {})
    d10 = chart.get("d10", {})

    d1_10h = set(planets_in_house(asc_sign, d1, 10))
    triad = {"Rahu", "Mercury", "Saturn"}
    d1_hits = triad & d1_10h

    d10_signs = {p: planet_sign(d10, p) for p in triad}
    d10_signs = {p: s for p, s in d10_signs.items() if s is not None}
    same_d10_sign = (
        len(d10_signs) >= 2
        and len(set(d10_signs.values())) == 1
    )

    if len(d1_hits) >= 2 or same_d10_sign:
        evidence = [
            f"d1_10h_triad_hits={sorted(d1_hits)}",
            f"d10_triad_signs={d10_signs}",
            "note=tech_triad_pattern",
        ]
        return _finding(
            "software_it",
            "positive",
            "Modern signal: software/IT (Rahu+Mercury+Saturn cluster in 10H/D10)",
            evidence,
        )
    return None


def _social_media(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu in 3H (self-effort / micro-blogging) or 11H (gains / virality)."""
    d1 = chart.get("d1", {})
    rahu_sign = planet_sign(d1, "Rahu")
    if rahu_sign is None:
        return None
    from app.reading.modern_life._helpers import planet_house

    rahu_house = planet_house(asc_sign, rahu_sign)
    if rahu_house in (3, 11):
        return _finding(
            "social_media",
            "positive",
            f"Modern signal: social-media virality (Rahu in {rahu_house}H)",
            [
                f"rahu_house={rahu_house}",
                "note=creator_economy_marker",
            ],
        )
    return None


def _remote_freelance(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu in 12H (foreign/remote) or Mercury+Rahu/Ketu in 3H."""
    d1 = chart.get("d1", {})
    twelfth = set(planets_in_house(asc_sign, d1, 12))
    third = set(planets_in_house(asc_sign, d1, 3))

    if "Rahu" in twelfth:
        return _finding(
            "remote_freelance",
            "positive",
            "Modern signal: remote/foreign work (Rahu in 12H)",
            ["rahu_in_12h=True", "note=foreign_or_remote_employment"],
        )
    if "Mercury" in third and (third & {"Rahu", "Ketu"}):
        return _finding(
            "remote_freelance",
            "positive",
            "Modern signal: freelance/gig work (Mercury+Rahu/Ketu in 3H)",
            [
                f"3h_planets={sorted(third)}",
                "note=self_directed_3h_pattern",
            ],
        )
    return None


def _entrepreneur(chart: dict, asc_sign: int) -> Finding | None:
    """Mars+Saturn conjunction in any house (drive + structure)."""
    d1 = chart.get("d1", {})
    mars_sign = planet_sign(d1, "Mars")
    sat_sign = planet_sign(d1, "Saturn")
    if mars_sign is not None and sat_sign is not None and mars_sign == sat_sign:
        from app.reading.modern_life._helpers import planet_house

        house = planet_house(asc_sign, mars_sign)
        return _finding(
            "entrepreneur",
            "positive",
            f"Modern signal: entrepreneur (Mars-Saturn conjunction in {house}H)",
            [
                f"shared_sign={mars_sign}",
                f"house={house}",
                "note=drive_plus_structure",
            ],
        )
    return None


def _government(chart: dict, asc_sign: int) -> Finding | None:
    """Sun+Saturn together in 10H — bureaucratic / public sector."""
    d1 = chart.get("d1", {})
    tenth = set(planets_in_house(asc_sign, d1, 10))
    if {"Sun", "Saturn"}.issubset(tenth):
        return _finding(
            "government",
            "positive",
            "Modern signal: government / bureaucratic career (Sun+Saturn in 10H)",
            [
                f"10h_planets={sorted(tenth)}",
                "note=public_sector_marker",
            ],
        )
    return None


def _consulting(chart: dict, asc_sign: int) -> Finding | None:
    """Jupiter+Mercury in 9H or 10H — advisory/teaching."""
    d1 = chart.get("d1", {})
    for house in (9, 10):
        occupants = set(planets_in_house(asc_sign, d1, house))
        if {"Jupiter", "Mercury"}.issubset(occupants):
            return _finding(
                "consulting",
                "positive",
                (
                    f"Modern signal: consulting/teaching/advisory "
                    f"(Jupiter+Mercury in {house}H)"
                ),
                [
                    f"house={house}",
                    f"occupants={sorted(occupants)}",
                    "note=advisory_career_marker",
                ],
            )
    return None


def _finance_trading(chart: dict, asc_sign: int) -> Finding | None:
    """Mars+Mercury in 11H with Rahu/Ketu involvement — modern trading."""
    d1 = chart.get("d1", {})
    eleventh = set(planets_in_house(asc_sign, d1, 11))
    if {"Mars", "Mercury"}.issubset(eleventh) and (eleventh & {"Rahu", "Ketu"}):
        return _finding(
            "finance_trading",
            "positive",
            "Modern signal: finance/trading (Mars+Mercury+Rahu/Ketu in 11H)",
            [
                f"11h_planets={sorted(eleventh)}",
                "note=modern_trading_marker",
            ],
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_modern_career(chart: dict, asc_sign: int) -> list[Finding]:
    """Run all modern-career detectors and return non-null Findings.

    Args:
        chart: full natal chart dict (``calculate_all_charts`` output);
            uses ``chart["d1"]`` and ``chart["d10"]`` only.
        asc_sign: 1-indexed natal ascendant rashi.

    Returns:
        list of :class:`Finding` (possibly empty). Every emitted Finding
        carries ``classification="primitive"`` (advisory, not predictive).
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    detectors = (
        _software_it,
        _social_media,
        _remote_freelance,
        _entrepreneur,
        _government,
        _consulting,
        _finance_trading,
    )
    findings: list[Finding] = []
    for fn in detectors:
        result = fn(chart, asc_sign)
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["detect_modern_career"]
