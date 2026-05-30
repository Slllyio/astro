"""Modern-education signal detection (V1.5).

Detects contemporary education-modality indicators on top of the V1
education reading. All findings are advisory (``classification="primitive"``).

Signals detected
================

- ``online_remote_learning``    Rahu+Mercury in 4H, or Rahu in D24 4H.
- ``self_directed``              Ketu in 5H, or Mars in 4H (independent
                                 learning style).
- ``stem_inclination``           Mercury+Saturn in 4H/5H, or Mars+Mercury
                                 in 5H.
- ``humanities_inclination``     Jupiter+Venus in 4H/5H/9H.
- ``higher_education``           Strong 9H + 9L; Jupiter in 9H.
- ``research_phd``               Saturn-Jupiter exchange, or Jupiter in
                                 9H + Saturn in 5H.
- ``non_traditional_path``       Rahu in 9H, or 9L in 12H.

Public API
==========

    detect_modern_education(chart, asc_sign) -> list[Finding]
"""
from __future__ import annotations

from typing import Final

from app.core.dignity import SIGN_RULERS
from app.reading.modern_life._helpers import (
    house_sign_from_asc,
    planet_house,
    planet_sign,
    planets_in_house,
)
from app.reading.schema import ConfidenceScore, Finding

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=modern_life.education (V1.5 advisory; classification=primitive)"
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
        id=f"modern_life.education.{rule_slug}",
        rule=f"modern_life.education.{rule_slug}",
        source_sequence=None,
        classification="primitive",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=evidence + [_DOCTRINE_SENTINEL],
        confidence=_ADVISORY_CONFIDENCE,
    )


def _online_remote_learning(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu+Mercury in 4H of D1 (or D24 4H if available)."""
    d1 = chart.get("d1", {})
    d24 = chart.get("divisional_charts", {}).get("D24") or chart.get("d24") or {}

    fourth_d1 = set(planets_in_house(asc_sign, d1, 4))
    rahu_merc_d1 = {"Rahu", "Mercury"}.issubset(fourth_d1)

    rahu_merc_d24 = False
    if isinstance(d24, dict) and d24:
        d24_rahu = planet_sign(d24, "Rahu")
        d24_merc = planet_sign(d24, "Mercury")
        if d24_rahu is not None and d24_merc is not None and d24_rahu == d24_merc:
            rahu_merc_d24 = True

    if rahu_merc_d1 or rahu_merc_d24:
        return _finding(
            "online_remote_learning",
            "positive",
            "Modern education signal: online/remote learning (Rahu+Mercury in 4H)",
            [
                f"rahu_merc_d1_4h={rahu_merc_d1}",
                f"rahu_merc_d24={rahu_merc_d24}",
                "note=digital_learning_marker",
            ],
        )
    return None


def _self_directed(chart: dict, asc_sign: int) -> Finding | None:
    """Ketu in 5H, or Mars in 4H — non-conventional learning."""
    d1 = chart.get("d1", {})
    fifth = set(planets_in_house(asc_sign, d1, 5))
    fourth = set(planets_in_house(asc_sign, d1, 4))
    ketu_in_5h = "Ketu" in fifth
    mars_in_4h = "Mars" in fourth
    if ketu_in_5h or mars_in_4h:
        return _finding(
            "self_directed",
            "positive",
            "Modern education signal: self-directed / non-traditional learning",
            [
                f"ketu_in_5h={ketu_in_5h}",
                f"mars_in_4h={mars_in_4h}",
                "note=autodidact_marker",
            ],
        )
    return None


def _stem_inclination(chart: dict, asc_sign: int) -> Finding | None:
    """Mercury+Saturn in 4/5H, or Mars+Mercury in 5H."""
    d1 = chart.get("d1", {})
    for house in (4, 5):
        occ = set(planets_in_house(asc_sign, d1, house))
        if {"Mercury", "Saturn"}.issubset(occ):
            return _finding(
                "stem_inclination",
                "positive",
                f"Modern education signal: STEM inclination (Mercury+Saturn in {house}H)",
                [f"house={house}", f"occupants={sorted(occ)}", "note=STEM_marker"],
            )
    fifth = set(planets_in_house(asc_sign, d1, 5))
    if {"Mars", "Mercury"}.issubset(fifth):
        return _finding(
            "stem_inclination",
            "positive",
            "Modern education signal: applied-STEM/engineering (Mars+Mercury in 5H)",
            [f"5h_occupants={sorted(fifth)}", "note=engineering_inclination_marker"],
        )
    return None


def _humanities_inclination(chart: dict, asc_sign: int) -> Finding | None:
    """Jupiter+Venus together in 4/5/9H."""
    d1 = chart.get("d1", {})
    for house in (4, 5, 9):
        occ = set(planets_in_house(asc_sign, d1, house))
        if {"Jupiter", "Venus"}.issubset(occ):
            return _finding(
                "humanities_inclination",
                "positive",
                f"Modern education signal: humanities/arts inclination (Jup+Ven in {house}H)",
                [f"house={house}", f"occupants={sorted(occ)}", "note=humanities_marker"],
            )
    return None


def _higher_education(chart: dict, asc_sign: int) -> Finding | None:
    """Jupiter in 9H, or strong 9L."""
    d1 = chart.get("d1", {})
    ninth_sign = house_sign_from_asc(asc_sign, 9)
    jupiter_in_9h = planet_sign(d1, "Jupiter") == ninth_sign
    ninth_lord = SIGN_RULERS[ninth_sign]
    ninth_lord_sign = planet_sign(d1, ninth_lord)
    ninth_lord_house = (
        planet_house(asc_sign, ninth_lord_sign)
        if ninth_lord_sign is not None
        else None
    )
    ninth_lord_strong = ninth_lord_house in (1, 4, 5, 7, 9, 10, 11)

    if jupiter_in_9h or ninth_lord_strong:
        return _finding(
            "higher_education",
            "positive",
            "Modern education signal: higher education path (Jup in 9H or strong 9L)",
            [
                f"jupiter_in_9h={jupiter_in_9h}",
                f"9l={ninth_lord} 9l_house={ninth_lord_house}",
                "note=higher_ed_marker",
            ],
        )
    return None


def _research_phd(chart: dict, asc_sign: int) -> Finding | None:
    """Jupiter in 9H + Saturn in 5H; or Jupiter-Saturn exchange."""
    d1 = chart.get("d1", {})
    ninth_sign = house_sign_from_asc(asc_sign, 9)
    fifth_sign = house_sign_from_asc(asc_sign, 5)
    jupiter_in_9h = planet_sign(d1, "Jupiter") == ninth_sign
    saturn_in_5h = planet_sign(d1, "Saturn") == fifth_sign

    # Jupiter-Saturn exchange: Jupiter in Saturn's sign, Saturn in Jupiter's sign.
    jup_signs = {planet_sign(d1, "Jupiter")}
    sat_signs = {planet_sign(d1, "Saturn")}
    jup_in_sat_sign = jup_signs & {10, 11}  # Capricorn, Aquarius
    sat_in_jup_sign = sat_signs & {9, 12}   # Sagittarius, Pisces
    exchange = bool(jup_in_sat_sign and sat_in_jup_sign)

    if (jupiter_in_9h and saturn_in_5h) or exchange:
        return _finding(
            "research_phd",
            "positive",
            "Modern education signal: research/PhD context (Jup-9H + Sat-5H or J-S exchange)",
            [
                f"jupiter_in_9h={jupiter_in_9h}",
                f"saturn_in_5h={saturn_in_5h}",
                f"jupiter_saturn_exchange={exchange}",
                "note=deep_research_marker",
            ],
        )
    return None


def _non_traditional_path(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu in 9H, or 9L in 12H."""
    d1 = chart.get("d1", {})
    ninth_sign = house_sign_from_asc(asc_sign, 9)
    rahu_in_9h = planet_sign(d1, "Rahu") == ninth_sign

    ninth_lord = SIGN_RULERS[ninth_sign]
    ninth_lord_sign = planet_sign(d1, ninth_lord)
    ninth_lord_house = (
        planet_house(asc_sign, ninth_lord_sign)
        if ninth_lord_sign is not None
        else None
    )

    if rahu_in_9h or ninth_lord_house == 12:
        return _finding(
            "non_traditional_path",
            "neutral",
            "Modern education signal: non-traditional / foreign-study path (Rahu-9H or 9L-12H)",
            [
                f"rahu_in_9h={rahu_in_9h}",
                f"9l_house={ninth_lord_house}",
                "note=foreign_or_non_traditional_marker",
            ],
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_modern_education(chart: dict, asc_sign: int) -> list[Finding]:
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    detectors = (
        _online_remote_learning,
        _self_directed,
        _stem_inclination,
        _humanities_inclination,
        _higher_education,
        _research_phd,
        _non_traditional_path,
    )
    findings: list[Finding] = []
    for fn in detectors:
        result = fn(chart, asc_sign)
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["detect_modern_education"]
