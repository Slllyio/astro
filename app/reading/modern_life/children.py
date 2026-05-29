"""Modern-children signal detection (V1.5).

Detects contemporary indicators relating to children — including the
modern distinction between biological conception, IVF/ART (assisted
reproduction) and adoption / reception. All findings are advisory
(``classification="primitive"``).

Signals detected
================

- ``biological_indicator``    Strong 5H + 5L + Jupiter without major
                              affliction.
- ``ivf_art_context``         Saturn afflicts 5L (delay + medical
                              intervention marker); Rahu in 5H; 5L in
                              dusthana while Jupiter is afflicted.
- ``adoption_context``        Ketu in 5H, OR 5L in 12H combined with
                              Jupiter in 11H (reception/non-biological
                              path classically read by Sanjay Rath).
- ``delay_context``           Saturn in/aspecting 5H, 5L combust, or 5L
                              in 6/8/12.
- ``conception_difficulty``   Mars-Saturn on the 5H or 5L (classical
                              "stress on progeny" marker).

Public API
==========

    detect_modern_children(chart, asc_sign) -> list[Finding]
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
    "doctrine=modern_life.children (V1.5 advisory; classification=primitive)"
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
        id=f"modern_life.children.{rule_slug}",
        rule=f"modern_life.children.{rule_slug}",
        source_sequence=None,
        classification="primitive",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=evidence + [_DOCTRINE_SENTINEL],
        confidence=_ADVISORY_CONFIDENCE,
    )


def _saturn_aspects_sign(d1: dict, target_sign: int) -> bool:
    """Whole-sign aspect: Saturn aspects 3rd, 7th and 10th from itself."""
    s = planet_sign(d1, "Saturn")
    if s is None:
        return False
    for offset in (3, 7, 10):
        if ((s - 1) + (offset - 1)) % 12 + 1 == target_sign:
            return True
    return False


def _biological_indicator(chart: dict, asc_sign: int) -> Finding | None:
    """Strong 5H/5L + Jupiter clean (no malefic conjunction in 5H)."""
    d1 = chart.get("d1", {})
    fifth_sign = house_sign_from_asc(asc_sign, 5)
    fifth_lord = SIGN_RULERS[fifth_sign]
    fifth_lord_sign = planet_sign(d1, fifth_lord)
    fifth_lord_house = (
        planet_house(asc_sign, fifth_lord_sign)
        if fifth_lord_sign is not None
        else None
    )

    fifth_h_planets = set(planets_in_house(asc_sign, d1, 5))
    malefics = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
    jupiter_sign = planet_sign(d1, "Jupiter")

    fifth_clean = not (fifth_h_planets & malefics)
    fifth_lord_strong = fifth_lord_house in (1, 4, 5, 7, 9, 10, 11)
    jupiter_visible = jupiter_sign is not None

    if fifth_clean and fifth_lord_strong and jupiter_visible:
        return _finding(
            "biological_indicator",
            "positive",
            "Modern children signal: biological-pathway indicator (clean 5H, strong 5L)",
            [
                f"5h_planets={sorted(fifth_h_planets)}",
                f"5l={fifth_lord} 5l_house={fifth_lord_house}",
                f"jupiter_sign={jupiter_sign}",
                "note=advisory_marker_not_guarantee",
            ],
        )
    return None


def _ivf_art_context(chart: dict, asc_sign: int) -> Finding | None:
    """Saturn afflicts 5L or 5H + Jupiter afflicted by Rahu/Saturn."""
    d1 = chart.get("d1", {})
    fifth_sign = house_sign_from_asc(asc_sign, 5)
    fifth_lord = SIGN_RULERS[fifth_sign]
    fifth_lord_sign = planet_sign(d1, fifth_lord)

    sat_aspects_5h = _saturn_aspects_sign(d1, fifth_sign)
    sat_aspects_5l = (
        fifth_lord_sign is not None and _saturn_aspects_sign(d1, fifth_lord_sign)
    )
    rahu_in_5h = "Rahu" in set(planets_in_house(asc_sign, d1, 5))

    jupiter_sign = planet_sign(d1, "Jupiter")
    jupiter_with_node = jupiter_sign is not None and jupiter_sign in {
        planet_sign(d1, "Rahu"),
        planet_sign(d1, "Ketu"),
    }

    if sat_aspects_5h or sat_aspects_5l or rahu_in_5h or jupiter_with_node:
        return _finding(
            "ivf_art_context",
            "neutral",
            "Modern children signal: IVF/ART context (Saturn or Rahu pressure on 5H/5L/Jupiter)",
            [
                f"saturn_aspects_5h={sat_aspects_5h}",
                f"saturn_aspects_5l={sat_aspects_5l}",
                f"rahu_in_5h={rahu_in_5h}",
                f"jupiter_with_node={jupiter_with_node}",
                "note=medical_intervention_path_advisory",
            ],
        )
    return None


def _adoption_context(chart: dict, asc_sign: int) -> Finding | None:
    """Ketu in 5H, or 5L in 12H with Jupiter in 11H (Sanjay Rath reading)."""
    d1 = chart.get("d1", {})
    fifth_h = set(planets_in_house(asc_sign, d1, 5))
    ketu_in_5h = "Ketu" in fifth_h

    fifth_sign = house_sign_from_asc(asc_sign, 5)
    fifth_lord = SIGN_RULERS[fifth_sign]
    fifth_lord_sign = planet_sign(d1, fifth_lord)
    fifth_lord_house = (
        planet_house(asc_sign, fifth_lord_sign)
        if fifth_lord_sign is not None
        else None
    )
    jupiter_sign = planet_sign(d1, "Jupiter")
    jupiter_house = planet_house(asc_sign, jupiter_sign) if jupiter_sign is not None else None
    adoption_path = fifth_lord_house == 12 and jupiter_house == 11

    if ketu_in_5h or adoption_path:
        return _finding(
            "adoption_context",
            "neutral",
            "Modern children signal: adoption/reception context (Ketu-5H or 5L-12H + Jup-11H)",
            [
                f"ketu_in_5h={ketu_in_5h}",
                f"adoption_path={adoption_path}",
                f"5l_house={fifth_lord_house}",
                f"jupiter_house={jupiter_house}",
                "note=non_biological_path_advisory",
            ],
        )
    return None


def _delay_context(chart: dict, asc_sign: int) -> Finding | None:
    """Saturn on 5H, 5L combust or in 6/8/12."""
    d1 = chart.get("d1", {})
    fifth_sign = house_sign_from_asc(asc_sign, 5)
    sat_sign = planet_sign(d1, "Saturn")
    sat_on_5h = sat_sign == fifth_sign or _saturn_aspects_sign(d1, fifth_sign)

    fifth_lord = SIGN_RULERS[fifth_sign]
    fifth_lord_sign = planet_sign(d1, fifth_lord)
    fifth_lord_house = (
        planet_house(asc_sign, fifth_lord_sign)
        if fifth_lord_sign is not None
        else None
    )
    fifth_lord_in_dusthana = fifth_lord_house in (6, 8, 12)

    if sat_on_5h or fifth_lord_in_dusthana:
        return _finding(
            "delay_context",
            "negative",
            "Modern children signal: delay context (Saturn on 5H or 5L in 6/8/12)",
            [
                f"sat_on_5h={sat_on_5h}",
                f"5l_house={fifth_lord_house}",
                "note=advisory_delay_marker",
            ],
        )
    return None


def _conception_difficulty(chart: dict, asc_sign: int) -> Finding | None:
    """Mars-Saturn on 5H/5L."""
    d1 = chart.get("d1", {})
    fifth_sign = house_sign_from_asc(asc_sign, 5)
    fifth_lord = SIGN_RULERS[fifth_sign]
    fifth_lord_sign = planet_sign(d1, fifth_lord)

    mars_sign = planet_sign(d1, "Mars")
    sat_sign = planet_sign(d1, "Saturn")

    mars_sat_conj = (
        mars_sign is not None and sat_sign is not None and mars_sign == sat_sign
    )
    pressure_on_5h_or_5l = (
        mars_sat_conj
        and (mars_sign == fifth_sign or mars_sign == fifth_lord_sign)
    )

    if pressure_on_5h_or_5l:
        return _finding(
            "conception_difficulty",
            "negative",
            "Modern children signal: conception-difficulty context (Mars-Saturn on 5H/5L)",
            [
                f"mars_saturn_shared_sign={mars_sign}",
                f"5h_sign={fifth_sign} 5l_sign={fifth_lord_sign}",
                "note=advisory_difficulty_marker_not_finality",
            ],
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_modern_children(chart: dict, asc_sign: int) -> list[Finding]:
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    detectors = (
        _biological_indicator,
        _ivf_art_context,
        _adoption_context,
        _delay_context,
        _conception_difficulty,
    )
    findings: list[Finding] = []
    for fn in detectors:
        result = fn(chart, asc_sign)
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["detect_modern_children"]
