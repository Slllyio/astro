"""Practitioner remedies: gemstones with lagna-suitability gating.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs) + classical lagna-suitability gating. Gemstones
strengthen a planet; strengthening a functional malefic is karmically
DANGEROUS. So gem recommendations are STRICTLY gated.

Eligibility rule (positive recommendation)
==========================================

A gemstone is RECOMMENDED iff its assigned planet is BOTH:

    1. one of the "safe to strengthen" planets:
         planet in {lagna_lord, fifth_lord, ninth_lord, atmakaraka}
    2. functionally favourable for this lagna:
         functional_natures[planet] in {"yogakaraka", "functional_benefic"}

Blockage rule (negative recommendation)
=======================================

If a planet is ``functional_malefic`` for this lagna, the corresponding
gemstone MUST be surfaced as BLOCKED (direction=negative). The blockage
is non-negotiable practitioner doctrine: e.g. Blue Sapphire is blocked
for Aries (Saturn = 10L+11L malefic), Yellow Sapphire is blocked for
Taurus (Jupiter = 8L+11L malefic), etc. The blocking finding is the
DOCTRINE-FAITHFUL response — practitioners insist these gems must NOT be
worn for these lagnas regardless of dasha or transit.

No-op (silent)
==============

functional_neutral planets, or planets not in the {1L,5L,9L,AK} trio that
happen to be benefic, are SKIPPED. The gem-table is small, so we just
emit nothing for them rather than a "no recommendation" finding.

The two-tier (POSITIVE/BLOCKED) discipline preserves the practitioner
"daan-before-gem" rule consumed by the package orchestrator:
``daan + mantras + yantras`` are ALWAYS returned for all afflicted
planets; gems are only ever returned for the strict eligibility gate.

Public API
==========

    recommend_gemstones(
        lagna_lord, fifth_lord, ninth_lord, atmakaraka,
        asc_sign, functional_natures,
    ) -> list[Finding]
    GEMSTONE_PLANET_TABLE: Final[dict[str, dict[str, str]]]
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_PLANETS: Final[frozenset[str]] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
     "Venus", "Saturn", "Rahu", "Ketu"}
)

# Allowable functional natures (defensive — caller should pass from
# functional_nature module which uses these exact strings).
_VALID_NATURES: Final[frozenset[str]] = frozenset({
    "functional_benefic", "functional_malefic",
    "functional_neutral", "yogakaraka",
})

_BENEFIC_NATURES: Final[frozenset[str]] = frozenset({
    "functional_benefic", "yogakaraka",
})


# Canonical gemstone -> planet table (frozen at module load). One entry
# per graha. ``slug`` is the lowercased / underscored form used in
# the Finding id grammar.
GEMSTONE_PLANET_TABLE: Final[dict[str, dict[str, str]]] = {
    "Sun":     {"gem": "Ruby",            "slug": "ruby"},
    "Moon":    {"gem": "Pearl",           "slug": "pearl"},
    "Mars":    {"gem": "Red Coral",       "slug": "red_coral"},
    "Mercury": {"gem": "Emerald",         "slug": "emerald"},
    "Jupiter": {"gem": "Yellow Sapphire", "slug": "yellow_sapphire"},
    "Venus":   {"gem": "Diamond",         "slug": "diamond"},
    "Saturn":  {"gem": "Blue Sapphire",   "slug": "blue_sapphire"},
    "Rahu":    {"gem": "Hessonite",       "slug": "hessonite"},
    "Ketu":    {"gem": "Cat's Eye",       "slug": "cats_eye"},
}


assert set(GEMSTONE_PLANET_TABLE.keys()) == set(_PLANETS), (
    "GEMSTONE_PLANET_TABLE missing planets: "
    f"{set(_PLANETS) - set(GEMSTONE_PLANET_TABLE.keys())!r}"
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Practitioner field-wisdom (foresightbypriyanka, dkscore, "
    "traditional almanacs)"
)


# Recommendations are not 3-pillar judgments — use the indicative envelope.
_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _eligible_planets(
    lagna_lord: str, fifth_lord: str, ninth_lord: str, atmakaraka: str,
) -> set[str]:
    """The {1L, 5L, 9L, AK} safe-to-strengthen set."""
    return {lagna_lord, fifth_lord, ninth_lord, atmakaraka}


def _positive_finding(
    planet: str, asc_sign: int, nature: str, role: str,
) -> Finding:
    """Build a positive Finding recommending the gem for `planet`."""
    cell = GEMSTONE_PLANET_TABLE[planet]
    gem = cell["gem"]
    slug = cell["slug"]
    verdict = (
        f"{gem} ({planet}) - safe for asc_sign={asc_sign} ({role}, {nature})"
    )[:140]
    evidence = [
        f"planet={planet}",
        f"gem={gem}",
        f"asc_sign={asc_sign}",
        f"nature={nature}",
        f"role={role}",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.remedies.gemstone.{slug}",
        rule="gemstone_remedy",
        source_sequence=None,
        classification="primitive",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _blocking_finding(planet: str, asc_sign: int) -> Finding:
    """Build a BLOCKED (negative) Finding for a functional-malefic gem."""
    cell = GEMSTONE_PLANET_TABLE[planet]
    gem = cell["gem"]
    slug = cell["slug"]
    verdict = (
        f"{gem} ({planet}) BLOCKED for asc_sign={asc_sign} "
        f"({planet} is functional_malefic)"
    )[:140]
    evidence = [
        f"planet={planet}",
        f"gem={gem}",
        f"asc_sign={asc_sign}",
        "nature=functional_malefic",
        "rule=do_not_strengthen_functional_malefic",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.remedies.gemstone.{slug}",
        rule="gemstone_remedy",
        source_sequence=None,
        classification="primitive",
        direction="negative",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _planet_role(
    planet: str, lagna_lord: str, fifth_lord: str,
    ninth_lord: str, atmakaraka: str,
) -> str:
    """Pick the most-significant role label for this planet."""
    roles: list[str] = []
    if planet == lagna_lord:
        roles.append("Lagna lord")
    if planet == fifth_lord:
        roles.append("5L Trikona")
    if planet == ninth_lord:
        roles.append("9L Trikona")
    if planet == atmakaraka:
        roles.append("Atmakaraka")
    return "+".join(roles) if roles else "eligible"


def recommend_gemstones(
    lagna_lord: str,
    fifth_lord: str,
    ninth_lord: str,
    atmakaraka: str,
    asc_sign: int,
    functional_natures: dict[str, str],
) -> list[Finding]:
    """Return gemstone Findings: positives (safe) + blockings (BLOCKED).

    Args:
        lagna_lord: Planet ruling the 1st house for the lagna.
        fifth_lord: Planet ruling the 5th house (Trikona).
        ninth_lord: Planet ruling the 9th house (Trikona).
        atmakaraka: Charasignificator (highest-degree planet).
        asc_sign: Ascendant rashi 1..12 (1=Aries .. 12=Pisces).
        functional_natures: Mapping from planet name to functional nature
            string (``"functional_benefic"``, ``"functional_malefic"``,
            ``"functional_neutral"``, ``"yogakaraka"``).

    Returns:
        List of Findings. POSITIVE Findings are emitted for planets in
        the {1L, 5L, 9L, AK} set whose nature is benefic/yogakaraka.
        NEGATIVE (BLOCKED) Findings are emitted for any functional_malefic
        planet, regardless of {1L,5L,9L,AK} membership. Neutral and
        non-eligible-benefic planets yield no Finding.

    Raises:
        ValueError: if ``asc_sign`` is not in 1..12, or if any nature
            in ``functional_natures`` is unrecognised, or if any planet
            name is invalid.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )

    # Defensive parameter validation.
    for label, planet in (
        ("lagna_lord", lagna_lord),
        ("fifth_lord", fifth_lord),
        ("ninth_lord", ninth_lord),
        ("atmakaraka", atmakaraka),
    ):
        if planet not in _PLANETS:
            raise ValueError(
                f"{label}={planet!r} is not a canonical planet name"
            )

    for planet, nature in functional_natures.items():
        if planet not in _PLANETS:
            raise ValueError(
                f"functional_natures has unknown planet {planet!r}"
            )
        if nature not in _VALID_NATURES:
            raise ValueError(
                f"functional_natures[{planet!r}]={nature!r} unknown; "
                f"expected one of {sorted(_VALID_NATURES)!r}"
            )

    eligible = _eligible_planets(lagna_lord, fifth_lord, ninth_lord, atmakaraka)
    out: list[Finding] = []

    # Iterate planets in canonical (table) order so output is ID-stable.
    for planet in GEMSTONE_PLANET_TABLE:
        nature = functional_natures.get(planet, "functional_neutral")

        if nature == "functional_malefic":
            # Block — non-negotiable.
            out.append(_blocking_finding(planet, asc_sign))
            continue

        if planet in eligible and nature in _BENEFIC_NATURES:
            role = _planet_role(
                planet, lagna_lord, fifth_lord, ninth_lord, atmakaraka,
            )
            out.append(_positive_finding(planet, asc_sign, nature, role))
            continue

        # All other cases (neutral, non-eligible benefic, shadow planet
        # with no lordship) — silent.

    return out


__all__ = ["recommend_gemstones", "GEMSTONE_PLANET_TABLE"]
