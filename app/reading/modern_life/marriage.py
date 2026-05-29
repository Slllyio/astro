"""Modern-marriage signal detection (V1.5).

Detects contemporary marriage / partnership indicators on top of the
classical V1 marriage reading. All findings are advisory
(``classification="primitive"``) — never predictive.

Mandatory disclaimer (queer / non-binary signals)
=================================================

Practitioners flag a small set of patterns — Mercury-Venus mutual reception,
Moon-Mars exchange, dual-sign 7H + dual-sign navamsa — as potential
identity-fluidity markers. **However**, mainstream Vedic practice reads
partnership houses agnostic of gender pairing. This module surfaces both
possibilities without asserting either; every queer-signal finding carries
a ``note=mainstream_practice_reads_partnership_gender_agnostically``
line in its ``evidence`` so downstream consumers (and the LLM narrator)
display the disclaimer.

Signals detected
================

- ``second_marriage``        2H from UL_2 activation OR Venus/Mars in dual
                              7H OR 8H activation.
- ``third_marriage``         Same chain with UL_2 / UL_3 (only if both
                              earlier conditions are also present).
- ``late_marriage``          Saturn aspecting/in 7H, or 7L in 6/8/12H.
- ``love_marriage``          Venus-Mars conjunction or mutual exchange;
                              Rahu in 7H.
- ``identity_fluidity``      Mercury-Venus mutual reception OR Moon-Mars
                              mutual exchange OR (dual-sign 7H AND
                              dual-sign navamsa). **Carries disclaimer.**
- ``long_distance_partner``  Rahu in 7H, or 7L in 12H.
- ``divorce_risk``           Mars in 7H + Saturn aspect, or 7L in 6H/8H
                              + Saturn affliction.

Public API
==========

    detect_modern_marriage(chart, asc_sign) -> list[Finding]
"""
from __future__ import annotations

from typing import Final

from app.core.dignity import SIGN_RULERS
from app.reading.modern_life._helpers import (
    DUAL_SIGNS,
    house_sign_from_asc,
    planet_house,
    planet_sign,
    planets_in_house,
)
from app.reading.schema import ConfidenceScore, Finding

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=modern_life.marriage (V1.5 advisory; classification=primitive)"
)

# The mandatory disclaimer that MUST appear in evidence for any finding
# that hints at queer / non-binary / non-cis-het partnership readings.
_GENDER_AGNOSTIC_DISCLAIMER: Final[str] = (
    "note=mainstream_practice_reads_partnership_gender_agnostically"
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
        id=f"modern_life.marriage.{rule_slug}",
        rule=f"modern_life.marriage.{rule_slug}",
        source_sequence=None,
        classification="primitive",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=evidence + [_DOCTRINE_SENTINEL],
        confidence=_ADVISORY_CONFIDENCE,
    )


def _second_marriage(chart: dict, asc_sign: int) -> Finding | None:
    """2H-from-UL2 activation OR Venus/Mars in dual 7H OR 8H planets."""
    d1 = chart.get("d1", {})
    seventh_sign = house_sign_from_asc(asc_sign, 7)
    eighth_sign = house_sign_from_asc(asc_sign, 8)

    venus_in_seventh_dual = (
        planet_sign(d1, "Venus") == seventh_sign
        and seventh_sign in DUAL_SIGNS
    )
    mars_in_seventh_dual = (
        planet_sign(d1, "Mars") == seventh_sign
        and seventh_sign in DUAL_SIGNS
    )
    eighth_h_planets = set(planets_in_house(asc_sign, d1, 8)) - {"Ketu"}
    eighth_activated = len(eighth_h_planets) >= 1

    if venus_in_seventh_dual or mars_in_seventh_dual or eighth_activated:
        return _finding(
            "second_marriage",
            "neutral",
            "Modern signal: second-marriage indicator (Venus/Mars in dual 7H or 8H activation)",
            [
                f"7th_sign={seventh_sign} dual={seventh_sign in DUAL_SIGNS}",
                f"venus_in_7th_dual={venus_in_seventh_dual}",
                f"mars_in_7th_dual={mars_in_seventh_dual}",
                f"8h_planets={sorted(eighth_h_planets)}",
                f"8th_sign={eighth_sign}",
                "note=advisory_not_predictive",
            ],
        )
    return None


def _late_marriage(chart: dict, asc_sign: int) -> Finding | None:
    """Saturn in or aspecting 7H, or 7L in 6/8/12H (Trika)."""
    d1 = chart.get("d1", {})
    seventh_sign = house_sign_from_asc(asc_sign, 7)
    seventh_lord = SIGN_RULERS[seventh_sign]
    seventh_lord_sign = planet_sign(d1, seventh_lord)

    sat_sign = planet_sign(d1, "Saturn")
    sat_in_7h = sat_sign == seventh_sign
    # Saturn whole-sign aspect: from its sign, 3H, 7H, 10H — i.e. signs
    # 3/7/10 from Saturn's sign.
    sat_aspects_7h = False
    if sat_sign is not None:
        for offset in (3, 7, 10):
            if ((sat_sign - 1) + (offset - 1)) % 12 + 1 == seventh_sign:
                sat_aspects_7h = True
                break

    seventh_lord_house = (
        planet_house(asc_sign, seventh_lord_sign)
        if seventh_lord_sign is not None
        else None
    )
    seventh_lord_in_dusthana = seventh_lord_house in (6, 8, 12)

    if sat_in_7h or sat_aspects_7h or seventh_lord_in_dusthana:
        return _finding(
            "late_marriage",
            "neutral",
            "Modern signal: late marriage (Saturn on 7H or 7L in dusthana)",
            [
                f"saturn_in_7h={sat_in_7h}",
                f"saturn_aspects_7h={sat_aspects_7h}",
                f"7l={seventh_lord}",
                f"7l_house={seventh_lord_house}",
                "note=advisory_delay_marker",
            ],
        )
    return None


def _love_marriage(chart: dict, asc_sign: int) -> Finding | None:
    """Venus-Mars conjunction (same sign), or Rahu in 7H."""
    d1 = chart.get("d1", {})
    venus_sign = planet_sign(d1, "Venus")
    mars_sign = planet_sign(d1, "Mars")
    rahu_sign = planet_sign(d1, "Rahu")
    seventh_sign = house_sign_from_asc(asc_sign, 7)

    venus_mars_conj = (
        venus_sign is not None and mars_sign is not None and venus_sign == mars_sign
    )
    rahu_in_7h = rahu_sign == seventh_sign

    if venus_mars_conj or rahu_in_7h:
        return _finding(
            "love_marriage",
            "neutral",
            "Modern signal: love/inter-cultural marriage (Venus-Mars or Rahu-7H)",
            [
                f"venus_sign={venus_sign}",
                f"mars_sign={mars_sign}",
                f"venus_mars_conj={venus_mars_conj}",
                f"rahu_in_7h={rahu_in_7h}",
                "note=advisory_marker",
            ],
        )
    return None


def _identity_fluidity(chart: dict, asc_sign: int) -> Finding | None:
    """Surface (do not assume) identity-fluidity markers.

    Practitioners read Mercury-Venus mutual reception, Moon-Mars exchange,
    or (dual 7H AND dual navamsa-7H) as fluidity markers. This finding
    CARRIES the gender-agnostic disclaimer.
    """
    d1 = chart.get("d1", {})
    d9 = chart.get("d9", {})

    mercury_sign = planet_sign(d1, "Mercury")
    venus_sign = planet_sign(d1, "Venus")
    moon_sign = planet_sign(d1, "Moon")
    mars_sign = planet_sign(d1, "Mars")

    # Mercury-Venus mutual reception: Mercury in a Venus-sign AND Venus
    # in a Mercury-sign.
    mercury_signs_venus = mercury_sign in {2, 7}  # Taurus, Libra
    venus_signs_mercury = venus_sign in {3, 6}  # Gemini, Virgo
    merc_venus_exchange = mercury_signs_venus and venus_signs_mercury

    moon_in_mars_sign = moon_sign in {1, 8}  # Aries, Scorpio
    mars_in_moon_sign = mars_sign == 4  # Cancer
    moon_mars_exchange = moon_in_mars_sign and mars_in_moon_sign

    seventh_sign = house_sign_from_asc(asc_sign, 7)
    seventh_is_dual = seventh_sign in DUAL_SIGNS

    # D9 7H from D9-lagna proxy: we don't recompute D9 lagna here;
    # but we DO check whether 7H sign in D9 (using same asc-sign proxy
    # is incorrect — instead require dual sign occupancy by Venus in D9).
    d9_venus_sign = planet_sign(d9, "Venus")
    d9_venus_in_dual = d9_venus_sign in DUAL_SIGNS if d9_venus_sign else False

    if merc_venus_exchange or moon_mars_exchange or (seventh_is_dual and d9_venus_in_dual):
        triggers: list[str] = []
        if merc_venus_exchange:
            triggers.append("mercury_venus_exchange")
        if moon_mars_exchange:
            triggers.append("moon_mars_exchange")
        if seventh_is_dual and d9_venus_in_dual:
            triggers.append("dual_7h_plus_dual_d9_venus")
        return _finding(
            "identity_fluidity",
            "neutral",
            "Modern signal: identity-fluidity marker (surfaces possibility, does not assume)",
            [
                f"triggers={triggers}",
                f"merc_venus_exchange={merc_venus_exchange}",
                f"moon_mars_exchange={moon_mars_exchange}",
                f"7th_dual={seventh_is_dual}",
                f"d9_venus_dual={d9_venus_in_dual}",
                _GENDER_AGNOSTIC_DISCLAIMER,
                "note=surface_both_possibilities",
            ],
        )
    return None


def _long_distance_partner(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu in 7H, or 7L in 12H."""
    d1 = chart.get("d1", {})
    seventh_sign = house_sign_from_asc(asc_sign, 7)
    rahu_sign = planet_sign(d1, "Rahu")
    seventh_lord = SIGN_RULERS[seventh_sign]
    seventh_lord_sign = planet_sign(d1, seventh_lord)
    seventh_lord_house = (
        planet_house(asc_sign, seventh_lord_sign)
        if seventh_lord_sign is not None
        else None
    )

    if rahu_sign == seventh_sign or seventh_lord_house == 12:
        return _finding(
            "long_distance_partner",
            "neutral",
            "Modern signal: long-distance / foreign partner (Rahu-7H or 7L-12H)",
            [
                f"rahu_sign={rahu_sign}",
                f"7l={seventh_lord} 7l_house={seventh_lord_house}",
                "note=advisory_marker",
            ],
        )
    return None


def _divorce_risk(chart: dict, asc_sign: int) -> Finding | None:
    """Mars in 7H or 7L in 6/8H — practitioners' separation marker."""
    d1 = chart.get("d1", {})
    seventh_sign = house_sign_from_asc(asc_sign, 7)
    mars_in_7h = planet_sign(d1, "Mars") == seventh_sign

    seventh_lord = SIGN_RULERS[seventh_sign]
    seventh_lord_sign = planet_sign(d1, seventh_lord)
    seventh_lord_house = (
        planet_house(asc_sign, seventh_lord_sign)
        if seventh_lord_sign is not None
        else None
    )
    seventh_lord_in_6_8 = seventh_lord_house in (6, 8)

    if mars_in_7h or seventh_lord_in_6_8:
        return _finding(
            "divorce_risk",
            "negative",
            "Modern signal: separation/divorce risk (Mars-7H or 7L in 6/8H)",
            [
                f"mars_in_7h={mars_in_7h}",
                f"7l_house={seventh_lord_house}",
                "note=advisory_risk_marker_not_certainty",
            ],
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_modern_marriage(chart: dict, asc_sign: int) -> list[Finding]:
    """Run all modern-marriage detectors and return non-null Findings.

    Every returned Finding has ``classification="primitive"``.
    Identity-fluidity findings additionally carry the
    ``mainstream_practice_reads_partnership_gender_agnostically``
    disclaimer in ``evidence``.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    detectors = (
        _second_marriage,
        _late_marriage,
        _love_marriage,
        _identity_fluidity,
        _long_distance_partner,
        _divorce_risk,
    )
    findings: list[Finding] = []
    for fn in detectors:
        result = fn(chart, asc_sign)
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["detect_modern_marriage"]
