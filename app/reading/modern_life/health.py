"""Modern-health signal detection (V1.5).

Detects contemporary health indicators with **mandatory psychological
discipline**: this module never reduces mental-health states to a
"graha-peeda" verdict. Instead it surfaces classical *contextual*
markers (Moon-Mercury, Moon-Saturn, Moon-Rahu, 4H, Moon's
nakshatra-lord) as advisory context for downstream LLM narration.

Signals detected
================

Mental-health context (advisory, NOT outcome predictions)
---------------------------------------------------------

- ``anxiety_context``       Moon-Mercury affliction (conjunction or
                            tight angle) — classically read as a "racing
                            mind" marker; surfaces context only.
- ``depression_context``    Moon-Saturn affliction — classical "heavy
                            mind" marker.
- ``dissociation_context``  Moon-Rahu affliction — classical "scattered
                            attention" marker; explicit reminder NOT to
                            equate with clinical diagnosis.
- ``emotional_foundation``  4H planets + 4L placement read together with
                            Moon. Advisory context for emotional
                            stability discussion.
- ``moon_nakshatra_lord``   Identification of the lord of the
                            nakshatra of the Moon (additional context
                            pillar — classical "Bha-grishita" reading).

Physical-health markers
-----------------------

- ``digestive_focus``       Sun/Mars in 6H, Mars-Saturn in 6H.
- ``chronic_focus``         Saturn in 6H, 8H or 12H.
- ``accident_prone``        Mars in 8H, or Mars-Rahu/Ketu axis in
                            6/8/12H.

Public API
==========

    detect_modern_health(chart, asc_sign) -> list[Finding]
"""
from __future__ import annotations

from typing import Final

from app.core.dignity import SIGN_RULERS
from app.reading.modern_life._helpers import (
    house_sign_from_asc,
    planet_house,
    planet_nakshatra_lord,
    planet_sign,
    planets_in_house,
    planets_in_sign,
)
from app.reading.schema import ConfidenceScore, Finding

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=modern_life.health (V1.5 advisory; classification=primitive); "
    "mental_health=context_only_not_diagnosis"
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
        id=f"modern_life.health.{rule_slug}",
        rule=f"modern_life.health.{rule_slug}",
        source_sequence=None,
        classification="primitive",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=evidence + [_DOCTRINE_SENTINEL],
        confidence=_ADVISORY_CONFIDENCE,
    )


def _co_located(d1: dict, p1: str, p2: str) -> bool:
    s1 = planet_sign(d1, p1)
    s2 = planet_sign(d1, p2)
    return s1 is not None and s2 is not None and s1 == s2


def _anxiety_context(chart: dict, asc_sign: int) -> Finding | None:
    """Moon-Mercury affliction context."""
    d1 = chart.get("d1", {})
    if _co_located(d1, "Moon", "Mercury"):
        return _finding(
            "anxiety_context",
            "neutral",
            "Modern mental-health context: Moon-Mercury (racing-mind classical marker)",
            [
                "moon_mercury_co_located=True",
                "note=psychological_context_not_clinical_diagnosis",
                "note=Moon_at_4H_lord_and_Moon_nakshatra_lord_should_also_be_inspected",
            ],
        )
    return None


def _depression_context(chart: dict, asc_sign: int) -> Finding | None:
    """Moon-Saturn affliction context."""
    d1 = chart.get("d1", {})
    if _co_located(d1, "Moon", "Saturn"):
        return _finding(
            "depression_context",
            "neutral",
            "Modern mental-health context: Moon-Saturn (heavy-mind classical marker)",
            [
                "moon_saturn_co_located=True",
                "note=psychological_context_not_clinical_diagnosis",
                "note=requires_4H_plus_moon_nakshatra_lord_corroboration",
            ],
        )
    return None


def _dissociation_context(chart: dict, asc_sign: int) -> Finding | None:
    """Moon-Rahu affliction context."""
    d1 = chart.get("d1", {})
    if _co_located(d1, "Moon", "Rahu") or _co_located(d1, "Moon", "Ketu"):
        return _finding(
            "dissociation_context",
            "neutral",
            "Modern mental-health context: Moon-Rahu/Ketu (scattered-attention classical marker)",
            [
                f"moon_rahu={_co_located(d1, 'Moon', 'Rahu')}",
                f"moon_ketu={_co_located(d1, 'Moon', 'Ketu')}",
                "note=psychological_context_not_clinical_diagnosis",
                "note=never_equate_with_dissociative_disorder",
            ],
        )
    return None


def _emotional_foundation(chart: dict, asc_sign: int) -> Finding | None:
    """4H planets + 4L placement as emotional-foundation context."""
    d1 = chart.get("d1", {})
    fourth_sign = house_sign_from_asc(asc_sign, 4)
    fourth_lord = SIGN_RULERS[fourth_sign]
    fourth_lord_sign = planet_sign(d1, fourth_lord)
    fourth_lord_house = (
        planet_house(asc_sign, fourth_lord_sign)
        if fourth_lord_sign is not None
        else None
    )
    fourth_h_planets = planets_in_house(asc_sign, d1, 4)

    return _finding(
        "emotional_foundation",
        "neutral",
        "Modern mental-health context: 4H + 4L emotional-foundation snapshot",
        [
            f"4h_planets={sorted(fourth_h_planets)}",
            f"4l={fourth_lord}",
            f"4l_house={fourth_lord_house}",
            "note=emotional_foundation_pillar_per_v1.5_spec",
            "note=context_only_not_diagnosis",
        ],
    )


def _moon_nakshatra_lord_context(chart: dict, asc_sign: int) -> Finding | None:
    """Surface the lord of Moon's nakshatra as a mental-context pillar."""
    d1 = chart.get("d1", {})
    lord = planet_nakshatra_lord(d1, "Moon")
    if lord is None:
        return None
    lord_sign = planet_sign(d1, lord)
    lord_house = planet_house(asc_sign, lord_sign) if lord_sign is not None else None
    return _finding(
        "moon_nakshatra_lord",
        "neutral",
        f"Modern mental-health context: Moon's nakshatra-lord = {lord}",
        [
            f"moon_nakshatra_lord={lord}",
            f"lord_sign={lord_sign}",
            f"lord_house={lord_house}",
            "note=Bha_grishita_pillar_for_mental_context",
        ],
    )


def _digestive_focus(chart: dict, asc_sign: int) -> Finding | None:
    """Sun/Mars in 6H — practitioners' digestive/inflammation marker."""
    d1 = chart.get("d1", {})
    sixth = set(planets_in_house(asc_sign, d1, 6))
    inflame = sixth & {"Sun", "Mars"}
    if inflame:
        return _finding(
            "digestive_focus",
            "negative",
            f"Modern health: digestive/inflammation focus ({sorted(inflame)} in 6H)",
            [
                f"6h_planets={sorted(sixth)}",
                "note=advisory_lifestyle_context",
            ],
        )
    return None


def _chronic_focus(chart: dict, asc_sign: int) -> Finding | None:
    """Saturn in 6/8/12H — classical chronic-condition emphasis."""
    d1 = chart.get("d1", {})
    sat_sign = planet_sign(d1, "Saturn")
    if sat_sign is None:
        return None
    sat_house = planet_house(asc_sign, sat_sign)
    if sat_house in (6, 8, 12):
        return _finding(
            "chronic_focus",
            "negative",
            f"Modern health: chronic-condition emphasis (Saturn in {sat_house}H)",
            [
                f"saturn_house={sat_house}",
                "note=advisory_long_arc_health_planning",
            ],
        )
    return None


def _accident_prone(chart: dict, asc_sign: int) -> Finding | None:
    """Mars in 8H, or Mars-Rahu/Ketu in 6/8/12H."""
    d1 = chart.get("d1", {})
    mars_sign = planet_sign(d1, "Mars")
    if mars_sign is None:
        return None
    mars_house = planet_house(asc_sign, mars_sign)

    if mars_house == 8:
        return _finding(
            "accident_prone",
            "negative",
            "Modern health: accident/injury context (Mars in 8H)",
            [
                f"mars_house={mars_house}",
                "note=advisory_caution_marker_not_certainty",
            ],
        )
    # Mars-Rahu/Ketu axis in dusthana.
    same_sign = set()
    for node in ("Rahu", "Ketu"):
        if _co_located(d1, "Mars", node):
            same_sign.add(node)
    if same_sign and mars_house in (6, 8, 12):
        return _finding(
            "accident_prone",
            "negative",
            f"Modern health: accident/injury context (Mars+{sorted(same_sign)} in {mars_house}H)",
            [
                f"mars_house={mars_house}",
                f"shared_with={sorted(same_sign)}",
                "note=advisory_caution_marker_not_certainty",
            ],
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_modern_health(chart: dict, asc_sign: int) -> list[Finding]:
    """Run all modern-health detectors and return non-null Findings.

    Mental-health findings are CONTEXT only. The verdict text contains
    no outcome predictions ("will get", "guaranteed", etc.) — those
    phrases are explicitly blocked in tests.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    detectors = (
        _anxiety_context,
        _depression_context,
        _dissociation_context,
        _emotional_foundation,
        _moon_nakshatra_lord_context,
        _digestive_focus,
        _chronic_focus,
        _accident_prone,
    )
    findings: list[Finding] = []
    for fn in detectors:
        result = fn(chart, asc_sign)
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["detect_modern_health"]
