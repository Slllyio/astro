"""Practitioner extended yoga: Neech Bhanga Raja Yoga (D-11 primary rule).

Doctrine source: D-11 lockfile — BPHS Vol.I Ch.39 v.10 primary rule
(cancellation of debilitation).

Primary rule (THE ONLY TRIGGER)
================================

A debilitated planet P (sitting in its debilitation sign S) has its
debilitation cancelled when:

    The **rashi-lord (dispositor) of sign S** sits in a kendra
    (1st / 4th / 7th / 10th) from either the Lagna OR the natal Moon.

This is the BPHS Vol.I Ch.39 v.10 reading consistent with the canonical
example: Saturn debilitated in Aries → Aries-lord is Mars → if Mars
sits in a kendra from Lagna or Moon → Neech Bhanga for Saturn.

Supplementary rules (CITED IN EVIDENCE, NEVER SOLELY TRIGGER)
=============================================================

Per D-11 lockfile: BPHS Ch.39 vv.11–13 describe three additional
configurations. Per the lockfile they are demoted to **supplementary
evidence** — they are flagged in the Finding's evidence list when also
true, but they NEVER independently trigger a Finding.

The three supplementaries:

1. The exaltation-lord of P (i.e. the planet whose exaltation is S)
   sits in a kendra from Lagna or Moon.
2. The lord of P's own exaltation sign (the planet ruling the sign
   where P exalts) sits in a kendra from the debilitation-sign's lord.
3. P aspects (or conjoins) its own debilitation-sign lord (the
   dispositor).

Public API
==========

    detect_neech_bhanga(d1_chart, asc_sign, moon_sign) -> list[Finding]

Returns one Finding per debilitated planet whose debilitation is
cancelled by the primary rule. ID pattern:
``practitioner.yogas_extended.neech_bhanga.<planet>``.
classification="yoga", direction="positive".
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.core.dignity import DEBILITATION, EXALTATION, SIGN_RULERS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_KENDRAS_1_INDEXED: Final[frozenset[int]] = frozenset({1, 4, 7, 10})

# Jupiter's full-aspect house-offsets (used by supplementary #3 — though
# the rule applies generically to "aspects": any planet's drishti to its
# own depositor counts. We use a conservative approximation here:
# conjunction (same sign) OR 7th-house opposition.)
_GENERIC_DRISHTI_OFFSETS: Final[tuple[int, ...]] = (7,)  # 7th = opposition


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=D-11 lockfile — BPHS Vol.I Ch.39 v.10 primary "
    "(dispositor of debilitation sign in kendra from Lagna or Moon)"
)


def _planet_sign(
    d1_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = d1_chart.get(planet)
    if not entry:
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not 1 <= sign <= 12:
        return None
    return sign


def _house_from(reference_sign: int, target_sign: int) -> int:
    """1..12 house position of target_sign as counted from reference_sign
    (1 = same sign, 7 = opposite, etc.)."""
    return ((target_sign - reference_sign) % 12) + 1


def _exaltation_lord_for_sign(sign: int) -> str | None:
    """Return the planet whose EXALTATION sign is ``sign``, or None.

    There is at most one such planet per sign (the 7 traditional planets
    have distinct exaltation signs).
    """
    for planet, exalt_sign in EXALTATION.items():
        if exalt_sign == sign:
            return planet
    return None


def _planet_aspects_sign(
    planet_sign: int, target_sign: int,
) -> bool:
    """Conservative drishti check: conjunction (same sign) OR 7th-house
    opposition. Used for supplementary rule #3 only.
    """
    if planet_sign == target_sign:
        return True
    for offset in _GENERIC_DRISHTI_OFFSETS:
        if _house_from(planet_sign, target_sign) == offset:
            return True
    return False


def _build_finding(
    deb_planet: str,
    deb_sign: int,
    dispositor: str,
    dispositor_sign: int,
    house_from_lagna: int,
    house_from_moon: int,
    supplementary_notes: list[str],
) -> Finding:
    # Choose the more informative kendra-from anchor for the verdict.
    if house_from_lagna in _KENDRAS_1_INDEXED:
        anchor = f"{house_from_lagna}H from Lagna"
    else:
        anchor = f"{house_from_moon}H from Moon"
    verdict = (
        f"Neech Bhanga for {deb_planet} (deb. in sign {deb_sign}) — "
        f"{dispositor} (dispositor) in {anchor} (kendra)"
    )[:140]
    evidence = [
        f"debilitated_planet={deb_planet}",
        f"debilitation_sign={deb_sign}",
        f"dispositor={dispositor}",
        f"dispositor_sign={dispositor_sign}",
        f"house_of_dispositor_from_lagna={house_from_lagna}",
        f"house_of_dispositor_from_moon={house_from_moon}",
        "primary_rule=BPHS Ch.39 v.10 (dispositor in kendra from Lagna or Moon)",
        *supplementary_notes,
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.yogas_extended.neech_bhanga.{deb_planet}",
        rule="neech_bhanga_raja_yoga",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _supplementary_evidence(
    deb_planet: str,
    deb_sign: int,
    dispositor: str,
    dispositor_sign: int,
    asc_sign: int,
    moon_sign: int,
    d1_chart: Mapping[str, Mapping[str, object]],
) -> list[str]:
    """Collect SUPPLEMENTARY evidence strings per D-11 (Ch.39 vv.11-13).

    Each is recorded only when its specific condition holds — these never
    independently trigger a Finding (the caller will only attach them if
    the primary rule already fired).
    """
    notes: list[str] = []

    # Supplementary #1: the exaltation-lord of the debilitation sign
    # (planet whose exaltation IS deb_sign) sits in a kendra from
    # Lagna or Moon.
    exalt_lord = _exaltation_lord_for_sign(deb_sign)
    if exalt_lord is not None:
        exalt_lord_sign = _planet_sign(d1_chart, exalt_lord)
        if exalt_lord_sign is not None:
            from_lagna = _house_from(asc_sign, exalt_lord_sign)
            from_moon = _house_from(moon_sign, exalt_lord_sign)
            if (
                from_lagna in _KENDRAS_1_INDEXED
                or from_moon in _KENDRAS_1_INDEXED
            ):
                notes.append(
                    f"supplementary_1=BPHS Ch.39 v.11 — "
                    f"{exalt_lord} (exalts in deb-sign {deb_sign}) "
                    f"in kendra from Lagna/Moon"
                )

    # Supplementary #2: the lord of P's exaltation sign is in a kendra
    # from the debilitation-sign's lord (the dispositor).
    p_exalt_sign = EXALTATION.get(deb_planet)
    if p_exalt_sign is not None:
        p_exalt_sign_lord = SIGN_RULERS[p_exalt_sign]
        p_exalt_sign_lord_sign = _planet_sign(d1_chart, p_exalt_sign_lord)
        if p_exalt_sign_lord_sign is not None:
            from_dispositor = _house_from(
                dispositor_sign, p_exalt_sign_lord_sign,
            )
            if from_dispositor in _KENDRAS_1_INDEXED:
                notes.append(
                    f"supplementary_2=BPHS Ch.39 v.12 — "
                    f"{p_exalt_sign_lord} (lord of {deb_planet}'s exalt-sign) "
                    f"in kendra from dispositor"
                )

    # Supplementary #3: P aspects (or conjoins) its own debilitation-sign
    # lord (the dispositor).
    p_sign = _planet_sign(d1_chart, deb_planet)
    if p_sign is not None and _planet_aspects_sign(p_sign, dispositor_sign):
        notes.append(
            f"supplementary_3=BPHS Ch.39 v.13 — "
            f"{deb_planet} aspects/conjoins its dispositor {dispositor}"
        )

    return notes


def detect_neech_bhanga(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    moon_sign: int,
) -> list[Finding]:
    """Detect Neech Bhanga Raja Yoga per D-11 primary rule.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int (1..12), ...}}.
        asc_sign: 1..12 ascendant sign.
        moon_sign: 1..12 natal Moon sign (kendra-from-Moon anchor).

    Returns:
        Findings list — one per debilitated planet whose debilitation is
        cancelled by the primary rule. Empty when no debilitated planet
        has its dispositor in a kendra from Lagna or Moon.

    Raises:
        ValueError: if asc_sign or moon_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")
    if not 1 <= moon_sign <= 12:
        raise ValueError(f"moon_sign must be in 1..12, got {moon_sign}")

    findings: list[Finding] = []
    for planet, deb_sign in DEBILITATION.items():
        # Find planet's current sign (skip if missing).
        p_sign = _planet_sign(d1_chart, planet)
        if p_sign is None:
            continue
        # Planet must actually be in its debilitation sign.
        if p_sign != deb_sign:
            continue
        # Dispositor = rashi-lord of the debilitation sign.
        dispositor = SIGN_RULERS[deb_sign]
        dispositor_sign = _planet_sign(d1_chart, dispositor)
        if dispositor_sign is None:
            continue
        # Primary trigger: dispositor in kendra from Lagna OR Moon.
        from_lagna = _house_from(asc_sign, dispositor_sign)
        from_moon = _house_from(moon_sign, dispositor_sign)
        if (
            from_lagna not in _KENDRAS_1_INDEXED
            and from_moon not in _KENDRAS_1_INDEXED
        ):
            continue

        supplementary_notes = _supplementary_evidence(
            deb_planet=planet,
            deb_sign=deb_sign,
            dispositor=dispositor,
            dispositor_sign=dispositor_sign,
            asc_sign=asc_sign,
            moon_sign=moon_sign,
            d1_chart=d1_chart,
        )

        findings.append(_build_finding(
            deb_planet=planet,
            deb_sign=deb_sign,
            dispositor=dispositor,
            dispositor_sign=dispositor_sign,
            house_from_lagna=from_lagna,
            house_from_moon=from_moon,
            supplementary_notes=supplementary_notes,
        ))

    return findings


__all__ = ["detect_neech_bhanga"]
