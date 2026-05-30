"""Tier-1 foundation: Argala (intervention) + Virodhargala (blocking).

Doctrine source: BPHS Vol.I Ch.30 (Argala Adhyaya).

BPHS Ch.30 defines Argala as the *intervention* exerted on a bhava by
planets sitting in particular signs counted from it. Argala speaks to
"which other planets shape this bhava's results?". Virodhargala is the
counter-intervention -- planets that *block* an Argala's effect.

Rules
=====

For a target bhava (1..12), let ``target_sign`` be the rashi falling in
that bhava from the Lagna (whole-sign houses). Counting forward (1-based)
from ``target_sign``:

  - **Argala** is contributed by planets in the **2nd, 4th, and 11th**
    signs from the target.
  - **Visesha (special) Argala** is contributed by planets in the
    **10th** from the target. We include this slot per the
    common-commentary tradition (Sanjay Rath et al.); it is treated
    identically to the primary Argala set for the purposes of the
    "survives blocking?" check below.
  - **Virodhargala** (the blockers) come from the **3rd, 5th, and 9th**:
        - 3rd blocks 2nd
        - 5th blocks 4th
        - 9th blocks 11th
    The 10th (visesha) is unblockable in this Phase-2 implementation
    (BPHS Ch.30 does not specify a Virodhargala for the 10th; we keep
    the doctrine conservative).

Mapping back to bhavas (whole-sign houses)
------------------------------------------

With whole-sign houses, ``house_of(planet) = ((planet.sign - asc_sign) %
12) + 1``. For the target bhava ``H``, ``target_sign = ((asc_sign - 1 +
H - 1) % 12) + 1``. The Argala slots are then expressed as ``offset``
from the target sign:

    offset(planet, target) = ((planet.sign - target_sign) % 12) + 1

A planet contributes Argala when ``offset in {2, 4, 10, 11}``, and
Virodhargala when ``offset in {3, 5, 9}``.

Verdict / direction
===================

We compute the *surviving* Argala set (Argala-side minus blocked
contributions) and classify the bhava's net intervention:

  - ``positive`` -- surviving set is non-empty AND purely benefic.
  - ``negative`` -- surviving set is non-empty AND purely malefic.
  - ``mixed``    -- surviving set has both benefic and malefic planets.
  - ``neutral``  -- surviving set is empty.

Benefic / malefic classification follows the project's locked Drik-bala
convention (BPHS 27.38): {Jupiter, Venus, Moon, Mercury} are benefics;
{Sun, Mars, Saturn, Rahu, Ketu} are malefics.

Public API
==========

  compute_argala(d1_chart, asc_sign) -> dict[int, Finding]

Returns one Finding per bhava 1..12; ``id`` is
``foundation.argala.h<N>``; ``classification`` is ``"primitive"``.

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> charts = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.argala import compute_argala
    >>> findings = compute_argala(charts["d1"], asc_sign=charts["ascendant"]["sign"])
    >>> findings[7].id
    'foundation.argala.h7'
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------


# Argala-contributing offsets (1-based count from the target sign).
# 2, 4, 11 are the primary Argala slots per BPHS Ch.30; 10 is the
# visesha (special) Argala slot per common-commentary tradition.
_ARGALA_OFFSETS: Final[frozenset[int]] = frozenset({2, 4, 10, 11})

# Virodhargala-contributing offsets and their pairing back to the
# Argala slot they BLOCK.
_VIRODHARGALA_BLOCK_MAP: Final[dict[int, int]] = {
    3: 2,
    5: 4,
    9: 11,
}
# Convenience: the set of blocker offsets we look for in the chart.
_VIRODHARGALA_OFFSETS: Final[frozenset[int]] = frozenset(_VIRODHARGALA_BLOCK_MAP.keys())


# Benefic / malefic classification mirrors the Drik-bala convention in
# app/core/shadbala.py (BPHS 27.38) and the Phase-2 bhava_bala module.
_BENEFIC: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Moon", "Mercury"}
)
_MALEFIC: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)


# Recognised graha names we examine in the chart. Any other chart key
# (custom Upagrahas, the Lagna entry, etc.) is silently ignored so the
# function stays robust to chart-shape changes.
_KNOWN_PLANETS: Final[frozenset[str]] = _BENEFIC | _MALEFIC


# 3-vote envelope -- argala is a single deterministic intervention check,
# not a 3-pillar judgment.
_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _target_sign(house: int, asc_sign: int) -> int:
    """Whole-sign rashi in bhava ``house`` for a chart with ``asc_sign``."""
    return ((asc_sign - 1 + house - 1) % 12) + 1


def _offset_from(target_sign: int, planet_sign: int) -> int:
    """1-based count from ``target_sign`` to ``planet_sign`` (1..12).

    A planet *in* the target sign returns 1; +1 sign returns 2; and so
    on. This is the convention used by all classical argala enumerations.
    """
    return ((planet_sign - target_sign) % 12) + 1


def _argala_planets_for_bhava(
    target_sign: int, d1_chart: dict
) -> list[str]:
    """Planet names contributing Argala (offsets 2/4/10/11) on the bhava."""
    out: list[str] = []
    for planet, entry in d1_chart.items():
        if planet not in _KNOWN_PLANETS:
            continue
        planet_sign = entry.get("sign")
        if not isinstance(planet_sign, int):
            continue
        if _offset_from(target_sign, planet_sign) in _ARGALA_OFFSETS:
            out.append(planet)
    # Stable / deterministic ordering for downstream consumers.
    out.sort()
    return out


def _virodhargala_planets_for_bhava(
    target_sign: int, d1_chart: dict
) -> list[str]:
    """Planet names contributing Virodhargala (offsets 3/5/9) on the bhava."""
    out: list[str] = []
    for planet, entry in d1_chart.items():
        if planet not in _KNOWN_PLANETS:
            continue
        planet_sign = entry.get("sign")
        if not isinstance(planet_sign, int):
            continue
        if _offset_from(target_sign, planet_sign) in _VIRODHARGALA_OFFSETS:
            out.append(planet)
    out.sort()
    return out


def _surviving_argala(
    target_sign: int, d1_chart: dict
) -> list[str]:
    """Argala planets whose slot is NOT blocked by any Virodhargala planet.

    A planet in slot 2 survives iff no planet sits in slot 3 (regardless
    of which planet); similarly 4 by 5 and 11 by 9. Visesha argala
    (offset 10) is never blocked in this implementation.
    """
    # Identify which blocker slots have *any* planet (we don't care
    # about identity for the blocking decision -- the classical rule is
    # "is there a planet there?").
    blocker_slots_occupied: set[int] = set()
    argala_planets_by_slot: dict[int, list[str]] = {}

    for planet, entry in d1_chart.items():
        if planet not in _KNOWN_PLANETS:
            continue
        planet_sign = entry.get("sign")
        if not isinstance(planet_sign, int):
            continue
        offset = _offset_from(target_sign, planet_sign)
        if offset in _ARGALA_OFFSETS:
            argala_planets_by_slot.setdefault(offset, []).append(planet)
        elif offset in _VIRODHARGALA_OFFSETS:
            blocker_slots_occupied.add(offset)

    # Determine which argala slots survive after blocking.
    survivors: list[str] = []
    for blocker_offset, argala_offset in _VIRODHARGALA_BLOCK_MAP.items():
        if blocker_offset in blocker_slots_occupied:
            # This argala slot is blocked; do not propagate its planets.
            continue
        survivors.extend(argala_planets_by_slot.get(argala_offset, []))
    # The 10th (visesha) argala is unblockable in this implementation.
    survivors.extend(argala_planets_by_slot.get(10, []))

    # Deduplicate (a single planet could in principle sit in only one
    # slot, but normalise just in case downstream consumers expect a set
    # semantics) and sort for determinism.
    return sorted(set(survivors))


def _direction_for(surviving: list[str]) -> str:
    """Map the surviving argala set to a Finding.direction enum value."""
    if not surviving:
        return "neutral"
    has_benefic = any(p in _BENEFIC for p in surviving)
    has_malefic = any(p in _MALEFIC for p in surviving)
    if has_benefic and has_malefic:
        return "mixed"
    if has_benefic:
        return "positive"
    return "negative"


def _verdict_for(
    house: int,
    surviving: list[str],
    argala: list[str],
    virodhargala: list[str],
) -> str:
    """Human-readable one-line verdict for the Finding."""
    if not argala and not virodhargala:
        return f"House {house} argala: no intervention"
    if surviving:
        survivors_str = ", ".join(surviving)
        body = f"surviving argala from {survivors_str}"
    else:
        body = "all argala blocked"
    if virodhargala:
        body = f"{body}; blocker(s): {', '.join(virodhargala)}"
    verdict = f"House {house} argala: {body}"
    # Hard cap at the schema's 140-char limit; truncate gracefully.
    if len(verdict) > 140:
        verdict = verdict[:137] + "..."
    return verdict


def _bhava_finding(
    house: int,
    target_sign: int,
    argala: list[str],
    virodhargala: list[str],
    surviving: list[str],
) -> Finding:
    """Build the Finding for one bhava's argala/virodhargala summary."""
    direction = _direction_for(surviving)
    return Finding(
        id=f"foundation.argala.h{house}",
        rule="argala",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=_verdict_for(house, surviving, argala, virodhargala),
        evidence=[
            f"house={house}",
            f"target_sign={target_sign}",
            f"argala_planets={argala}",
            f"virodhargala_planets={virodhargala}",
            f"surviving_argala={surviving}",
            "doctrine=BPHS Vol.I Ch.30 (Argala + Virodhargala)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_argala(
    d1_chart: dict, asc_sign: int,
) -> dict[int, Finding]:
    """Compute Argala + Virodhargala for every bhava (1..12).

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each entry
            must carry at least ``sign`` (1..12) for the planet to be
            considered. Unknown keys (Lagna, custom Upagrahas, etc.) are
            silently ignored.
        asc_sign: Ascendant rashi (1=Aries .. 12=Pisces).

    Returns:
        Dict keyed by house number (1..12), each value a Finding with
        ``id="foundation.argala.h<N>"``. Direction is positive if the
        surviving (unblocked) argala set is purely benefic, negative if
        purely malefic, mixed if both, neutral if empty.

    Raises:
        ValueError: if ``asc_sign`` is not in ``1..12``.

    Example:
        >>> findings = compute_argala(d1, asc_sign=6)
        >>> findings[7].direction in {"positive", "negative", "neutral", "mixed"}
        True
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )

    out: dict[int, Finding] = {}
    for house in range(1, 13):
        target_sign = _target_sign(house, asc_sign)
        argala = _argala_planets_for_bhava(target_sign, d1_chart)
        virodhargala = _virodhargala_planets_for_bhava(
            target_sign, d1_chart,
        )
        surviving = _surviving_argala(target_sign, d1_chart)
        out[house] = _bhava_finding(
            house, target_sign, argala, virodhargala, surviving,
        )
    return out


__all__ = ["compute_argala"]
