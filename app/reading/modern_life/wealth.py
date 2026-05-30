"""Modern-wealth signal detection (V1.5).

Detects contemporary wealth indicators on top of the V1 wealth reading.
All findings are advisory (``classification="primitive"``).

Signals detected
================

- ``crypto_speculation``    Mercury+Rahu cluster, especially in 11H or 2H
                            (modern speculative-asset marker).
- ``online_business``       Mercury+Rahu in 7H or 10H (digital commerce).
- ``modern_adhi_yoga``      Benefics (Jupiter/Mercury/Venus) in 6/7/8 from
                            ASC **or** from Moon (the classical Adhi
                            Yoga adapted to modern occupations: the
                            6/8/12 set need not be all clean — at least
                            one of 6 or 8 may carry Mars/Rahu and still
                            indicate modern entrepreneurial wealth).
- ``passive_income``        Jupiter+Venus in 2H/11H, or Jupiter
                            aspecting 11L.
- ``stock_market``          Mercury+Mars in 5H/11H with Rahu involvement.
- ``debt_burden``           6L in 2H/8H/12H, or Saturn-Rahu in 2H.
- ``foreign_income``        Rahu in 11H, or 11L in 12H/9H.

Public API
==========

    detect_modern_wealth(chart, asc_sign) -> list[Finding]
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
    "doctrine=modern_life.wealth (V1.5 advisory; classification=primitive)"
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
        id=f"modern_life.wealth.{rule_slug}",
        rule=f"modern_life.wealth.{rule_slug}",
        source_sequence=None,
        classification="primitive",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=evidence + [_DOCTRINE_SENTINEL],
        confidence=_ADVISORY_CONFIDENCE,
    )


def _crypto_speculation(chart: dict, asc_sign: int) -> Finding | None:
    """Mercury+Rahu in 11H or 2H."""
    d1 = chart.get("d1", {})
    for house in (11, 2):
        occupants = set(planets_in_house(asc_sign, d1, house))
        if {"Mercury", "Rahu"}.issubset(occupants):
            return _finding(
                "crypto_speculation",
                "neutral",
                f"Modern wealth signal: crypto/speculative-asset context (Mercury+Rahu in {house}H)",
                [
                    f"house={house}",
                    f"occupants={sorted(occupants)}",
                    "note=advisory_speculation_marker_not_endorsement",
                ],
            )
    return None


def _online_business(chart: dict, asc_sign: int) -> Finding | None:
    """Mercury+Rahu in 7H or 10H."""
    d1 = chart.get("d1", {})
    for house in (7, 10):
        occupants = set(planets_in_house(asc_sign, d1, house))
        if {"Mercury", "Rahu"}.issubset(occupants):
            return _finding(
                "online_business",
                "positive",
                f"Modern wealth signal: online business (Mercury+Rahu in {house}H)",
                [
                    f"house={house}",
                    f"occupants={sorted(occupants)}",
                    "note=digital_commerce_marker",
                ],
            )
    return None


def _modern_adhi_yoga(chart: dict, asc_sign: int) -> Finding | None:
    """Benefics in 6/7/8 from Lagna or Moon — modern variant Adhi Yoga."""
    d1 = chart.get("d1", {})
    benefics = {"Jupiter", "Venus", "Mercury"}

    # From Lagna.
    for house in (6, 7, 8):
        occ = set(planets_in_house(asc_sign, d1, house))
        if occ & benefics:
            ben_in = occ & benefics
            return _finding(
                "modern_adhi_yoga",
                "positive",
                f"Modern wealth signal: Adhi-Yoga variant (benefics in {house}H from Lagna)",
                [
                    f"house={house}",
                    f"benefics_in_house={sorted(ben_in)}",
                    "note=modern_variant_Adhi_Yoga",
                ],
            )

    # From Moon.
    moon_sign = planet_sign(d1, "Moon")
    if moon_sign is not None:
        for house in (6, 7, 8):
            target_sign = ((moon_sign - 1) + (house - 1)) % 12 + 1
            occ = {
                p for p, e in d1.items()
                if isinstance(e, dict) and e.get("sign") == target_sign
            }
            if occ & benefics:
                return _finding(
                    "modern_adhi_yoga",
                    "positive",
                    f"Modern wealth signal: Adhi-Yoga variant (benefics in {house}H from Moon)",
                    [
                        f"from_moon_house={house}",
                        f"benefics_in_house={sorted(occ & benefics)}",
                        "note=modern_variant_Adhi_Yoga_from_Moon",
                    ],
                )
    return None


def _passive_income(chart: dict, asc_sign: int) -> Finding | None:
    """Jupiter+Venus in 2H/11H."""
    d1 = chart.get("d1", {})
    for house in (2, 11):
        occ = set(planets_in_house(asc_sign, d1, house))
        if {"Jupiter", "Venus"}.issubset(occ):
            return _finding(
                "passive_income",
                "positive",
                f"Modern wealth signal: passive income (Jupiter+Venus in {house}H)",
                [
                    f"house={house}",
                    f"occupants={sorted(occ)}",
                    "note=passive_income_marker",
                ],
            )
    return None


def _stock_market(chart: dict, asc_sign: int) -> Finding | None:
    """Mercury+Mars+Rahu in 5H or 11H."""
    d1 = chart.get("d1", {})
    for house in (5, 11):
        occ = set(planets_in_house(asc_sign, d1, house))
        if {"Mercury", "Mars"}.issubset(occ) and ("Rahu" in occ or "Ketu" in occ):
            return _finding(
                "stock_market",
                "neutral",
                f"Modern wealth signal: stock-market/trading context ({house}H)",
                [
                    f"house={house}",
                    f"occupants={sorted(occ)}",
                    "note=advisory_speculation_marker",
                ],
            )
    return None


def _debt_burden(chart: dict, asc_sign: int) -> Finding | None:
    """6L in 2H/8H/12H, or Saturn-Rahu in 2H."""
    d1 = chart.get("d1", {})
    sixth_lord = SIGN_RULERS[house_sign_from_asc(asc_sign, 6)]
    sixth_lord_sign = planet_sign(d1, sixth_lord)
    sixth_lord_house = (
        planet_house(asc_sign, sixth_lord_sign)
        if sixth_lord_sign is not None
        else None
    )

    second = set(planets_in_house(asc_sign, d1, 2))
    sat_rahu_in_2 = {"Saturn", "Rahu"}.issubset(second)

    if sixth_lord_house in (2, 8, 12) or sat_rahu_in_2:
        return _finding(
            "debt_burden",
            "negative",
            "Modern wealth signal: debt-burden context (6L in 2/8/12 or Saturn-Rahu in 2H)",
            [
                f"6l={sixth_lord} 6l_house={sixth_lord_house}",
                f"sat_rahu_in_2h={sat_rahu_in_2}",
                "note=advisory_debt_management_marker",
            ],
        )
    return None


def _foreign_income(chart: dict, asc_sign: int) -> Finding | None:
    """Rahu in 11H, or 11L in 9H/12H."""
    d1 = chart.get("d1", {})
    rahu_sign = planet_sign(d1, "Rahu")
    rahu_house = planet_house(asc_sign, rahu_sign) if rahu_sign is not None else None

    eleventh_lord = SIGN_RULERS[house_sign_from_asc(asc_sign, 11)]
    eleventh_lord_sign = planet_sign(d1, eleventh_lord)
    eleventh_lord_house = (
        planet_house(asc_sign, eleventh_lord_sign)
        if eleventh_lord_sign is not None
        else None
    )

    if rahu_house == 11 or eleventh_lord_house in (9, 12):
        return _finding(
            "foreign_income",
            "positive",
            "Modern wealth signal: foreign income (Rahu-11H or 11L in 9/12H)",
            [
                f"rahu_house={rahu_house}",
                f"11l={eleventh_lord} 11l_house={eleventh_lord_house}",
                "note=foreign_or_cross_border_income_marker",
            ],
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_modern_wealth(chart: dict, asc_sign: int) -> list[Finding]:
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    detectors = (
        _crypto_speculation,
        _online_business,
        _modern_adhi_yoga,
        _passive_income,
        _stock_market,
        _debt_burden,
        _foreign_income,
    )
    findings: list[Finding] = []
    for fn in detectors:
        result = fn(chart, asc_sign)
        if result is not None:
            findings.append(result)
    return findings


__all__ = ["detect_modern_wealth"]
