"""Practitioner extended yoga: Lakshmi Yoga (BPHS Ch.40).

Doctrine source: BPHS Ch.40 — Lakshmi Yoga.

Classical rule
==============

Lakshmi Yoga is a fortune yoga indicating wealth, prosperity, and the
blessings of Lakshmi (the goddess of fortune). The yoga forms when:

    The **9th-house lord** (Bhagyesh / 9L) is in **exaltation, own
    sign, or moolatrikona sign**, AND **Venus** (the karaka of Lakshmi)
    is in **exaltation, own sign, or moolatrikona sign**.

Stricter sub-variant (locked as ``lakshmi.strict``):

    Primary conditions hold, AND
    - The 9L is also placed in the 9th house itself (the 9L "returns
      home"), AND
    - Venus is in a kendra (1/4/7/10) or kona (5/9) from lagna.

At most one variant per chart is emitted (strict suppresses primary).

Dignity at the sign-level
=========================

Moolatrikona is properly a degree-restricted dignity (BPHS Ch.3 v.31).
For sign-level fixtures that may not carry precise longitude, we treat
the entire moolatrikona sign as MT-eligible — a conservative
practitioner deviation that matches how most fixture-based readers
detect Lakshmi. When longitude IS supplied, the same sign-only check
still applies (we deliberately avoid a hidden longitude-dependent
filter to keep results sign-deterministic).

The MT signs (one per non-nodal planet):
    Sun=Leo (5), Moon=Taurus (2), Mars=Aries (1), Mercury=Virgo (6),
    Jupiter=Sagittarius (9), Venus=Libra (7), Saturn=Aquarius (11).

Public API
==========

    detect_lakshmi(d1_chart, asc_sign) -> list[Finding]

ID pattern: ``practitioner.yogas_extended.lakshmi.<variant>``
where variant is ``"detected"`` (primary) or ``"strict"``.
classification="yoga", direction="positive".
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Sign rulers (BPHS Vol.I Ch.3) — 1-indexed.
_SIGN_RULERS: Final[dict[int, str]] = {
    1: "Mars",     2: "Venus",   3: "Mercury", 4: "Moon",
    5: "Sun",      6: "Mercury", 7: "Venus",   8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# Exaltation signs per BPHS Ch.3 v.40.
_EXALTATION: Final[dict[str, int]] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7,
}

# Own signs per BPHS Ch.3.
_OWN_SIGNS: Final[dict[str, frozenset[int]]] = {
    "Sun":     frozenset({5}),
    "Moon":    frozenset({4}),
    "Mars":    frozenset({1, 8}),
    "Mercury": frozenset({3, 6}),
    "Jupiter": frozenset({9, 12}),
    "Venus":   frozenset({2, 7}),
    "Saturn":  frozenset({10, 11}),
}

# Moolatrikona signs (sign-level, BPHS Ch.3 v.31). Degree-restricted in
# strict BPHS; sign-level here for fixture compatibility.
_MOOLATRIKONA_SIGNS: Final[dict[str, int]] = {
    "Sun": 5, "Moon": 2, "Mars": 1, "Mercury": 6,
    "Jupiter": 9, "Venus": 7, "Saturn": 11,
}

_KENDRA_KONA: Final[frozenset[int]] = frozenset({1, 4, 5, 7, 9, 10})


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Ch.40 Lakshmi Yoga (9L dignified + Venus dignified)"
)


def _dignified_signs(planet: str) -> frozenset[int]:
    """Return the union of own + exaltation + MT signs for the planet."""
    signs: set[int] = set(_OWN_SIGNS.get(planet, frozenset()))
    exalt = _EXALTATION.get(planet)
    if exalt:
        signs.add(exalt)
    mt = _MOOLATRIKONA_SIGNS.get(planet)
    if mt:
        signs.add(mt)
    return frozenset(signs)


def _house_lord(asc_sign: int, house: int) -> str:
    sign = ((asc_sign - 1 + house - 1) % 12) + 1
    return _SIGN_RULERS[sign]


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


def _planet_sign(d1_chart: Mapping[str, Mapping[str, object]], planet: str) -> int | None:
    entry = d1_chart.get(planet)
    if not entry:
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not 1 <= sign <= 12:
        return None
    return sign


def _dignity_label(planet: str, sign: int) -> str:
    if sign == _EXALTATION.get(planet):
        return "exalted"
    if sign == _MOOLATRIKONA_SIGNS.get(planet):
        return "moolatrikona"
    if sign in _OWN_SIGNS.get(planet, frozenset()):
        return "own"
    return "neutral"


def _build_finding(
    variant: str,
    ninth_lord: str, ninth_lord_sign: int, ninth_lord_house: int,
    venus_sign: int, venus_house: int,
) -> Finding:
    label = {
        "detected": "Lakshmi Yoga",
        "strict":   "Lakshmi Yoga (strict)",
    }[variant]
    nl_dignity = _dignity_label(ninth_lord, ninth_lord_sign)
    ven_dignity = _dignity_label("Venus", venus_sign)
    verdict = (
        f"{label} — 9L {ninth_lord} {nl_dignity} ({ninth_lord_house}H) "
        f"+ Venus {ven_dignity} ({venus_house}H) — wealth, fortune"
    )[:140]
    evidence = [
        f"variant={variant}",
        f"9L={ninth_lord}",
        f"9L_sign={ninth_lord_sign}",
        f"9L_dignity={nl_dignity}",
        f"9L_house={ninth_lord_house}",
        f"Venus_sign={venus_sign}",
        f"Venus_dignity={ven_dignity}",
        f"Venus_house={venus_house}",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.yogas_extended.lakshmi.{variant}",
        rule="lakshmi_yoga",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_lakshmi(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Lakshmi Yoga (BPHS Ch.40).

    Args:
        d1_chart: Mapping {planet_name: {"sign": int, ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        A list with at most ONE Finding (strict variant suppresses
        primary). Empty when either 9L is not dignified or Venus is
        not dignified, or when either planet's sign is missing.

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    ninth_lord = _house_lord(asc_sign, 9)
    nl_sign = _planet_sign(d1_chart, ninth_lord)
    venus_sign = _planet_sign(d1_chart, "Venus")
    if nl_sign is None or venus_sign is None:
        return []

    nl_dignified = nl_sign in _dignified_signs(ninth_lord)
    venus_dignified = venus_sign in _dignified_signs("Venus")
    if not (nl_dignified and venus_dignified):
        return []

    nl_house = _whole_sign_house(nl_sign, asc_sign)
    venus_house = _whole_sign_house(venus_sign, asc_sign)

    # Strict check: 9L in 9H AND Venus in kendra/kona.
    if nl_house == 9 and venus_house in _KENDRA_KONA:
        return [_build_finding(
            "strict", ninth_lord, nl_sign, nl_house, venus_sign, venus_house,
        )]
    return [_build_finding(
        "detected", ninth_lord, nl_sign, nl_house, venus_sign, venus_house,
    )]


__all__ = ["detect_lakshmi"]
