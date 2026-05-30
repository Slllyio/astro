"""Practitioner extended yoga: Chamara Yoga (Phaladeepika).

Doctrine source: Phaladeepika (Mantreshwara) — Chamara Yoga.

Classical rule
==============

Chamara Yoga (literally "the fly-whisk yoga", a royal regalia)
confers regal status, authoritative power, and lasting eminence. It
forms when:

    The **lagna lord** (1L) is in **exaltation** AND placed in a
    **kendra** (1/4/7/10) from lagna, AND **Jupiter** either
    **conjoins** the 1L (same sign) OR fully **aspects** the 1L by
    classical drishti.

Jupiter's full drishti per BPHS Ch.26:

    The 5th, 7th, and 9th whole-sign houses from Jupiter's own
    position. So Jupiter at sign S aspects signs at offsets +4, +6,
    +8 (1-indexed: ((S - 1 + N - 1) mod 12) + 1 for N in {5, 7, 9}).

Public API
==========

    detect_chamara(d1_chart, asc_sign) -> list[Finding]

ID pattern: ``practitioner.yogas_extended.chamara.detected``.
classification="yoga", direction="positive".
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Sign rulers (BPHS Vol.I Ch.3).
_SIGN_RULERS: Final[dict[int, str]] = {
    1: "Mars",     2: "Venus",   3: "Mercury", 4: "Moon",
    5: "Sun",      6: "Mercury", 7: "Venus",   8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# Exaltation signs (BPHS Ch.3 v.40).
_EXALTATION: Final[dict[str, int]] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7,
}

_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})

# Jupiter's full-aspect house-offsets (BPHS Ch.26): 5th, 7th, 9th from
# Jupiter's position.
_JUPITER_ASPECT_OFFSETS: Final[tuple[int, ...]] = (5, 7, 9)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Phaladeepika Chamara Yoga (1L exalted in kendra + Jup conj/aspect)"
)


def _house_lord(asc_sign: int, house: int) -> str:
    sign = ((asc_sign - 1 + house - 1) % 12) + 1
    return _SIGN_RULERS[sign]


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


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


def _jupiter_aspects_sign(jupiter_sign: int, target_sign: int) -> bool:
    """True if Jupiter at jupiter_sign fully aspects target_sign
    (whole-sign drishti, 5/7/9 from Jupiter). Conjunction (same sign)
    is treated as a separate interaction by the caller; this returns
    False for same-sign.
    """
    if jupiter_sign == target_sign:
        return False
    for offset in _JUPITER_ASPECT_OFFSETS:
        aspected = ((jupiter_sign - 1 + offset - 1) % 12) + 1
        if aspected == target_sign:
            return True
    return False


def _build_finding(
    lagna_lord: str, ll_sign: int, ll_house: int,
    jupiter_sign: int, interaction: str,
) -> Finding:
    verdict = (
        f"Chamara Yoga — 1L {lagna_lord} exalted in {ll_house}H, "
        f"Jupiter {interaction} (regal eminence)"
    )[:140]
    evidence = [
        f"1L={lagna_lord}",
        f"1L_sign={ll_sign}",
        f"1L_house={ll_house}",
        "1L_dignity=exalted",
        f"Jupiter_sign={jupiter_sign}",
        f"jupiter_interaction={interaction}",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id="practitioner.yogas_extended.chamara.detected",
        rule="chamara_yoga",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_chamara(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Chamara Yoga per Phaladeepika.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int, ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        A list with at most ONE Finding. Empty when 1L is not exalted,
        when 1L is not in a kendra, or when Jupiter neither conjoins
        nor fully aspects the 1L.

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    lagna_lord = _house_lord(asc_sign, 1)
    ll_sign = _planet_sign(d1_chart, lagna_lord)
    if ll_sign is None:
        return []

    # 1L must be exalted.
    if _EXALTATION.get(lagna_lord) != ll_sign:
        return []

    # 1L must be in a kendra from lagna.
    ll_house = _whole_sign_house(ll_sign, asc_sign)
    if ll_house not in _KENDRAS:
        return []

    # Jupiter conjunction or aspect on 1L.
    jupiter_sign = _planet_sign(d1_chart, "Jupiter")
    if jupiter_sign is None:
        return []

    if jupiter_sign == ll_sign:
        interaction = "conjunction with 1L"
    elif _jupiter_aspects_sign(jupiter_sign, ll_sign):
        interaction = "aspect on 1L"
    else:
        return []

    return [_build_finding(
        lagna_lord, ll_sign, ll_house, jupiter_sign, interaction,
    )]


__all__ = ["detect_chamara"]
