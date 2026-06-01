"""Practitioner extended yoga: Adhi Yoga (BPHS Ch.40).

Doctrine source: BPHS Ch.40 — Adhi Yoga.

Classical rule
==============

Adhi Yoga is formed when the natural benefics — **Jupiter, Venus, and
Mercury** — occupy the 6th, 7th, and/or 8th houses **from the Moon**
(NOT from the lagna). The benefic must literally occupy one of those
three signs counted from the Moon's own sign.

Variants
========

Practitioner-locked count thresholds (the brief named these tiers but
left the cutoffs implicit; we lock the natural mapping):

- **Maha Adhi Yoga** (great) — ALL THREE benefics in 6/7/8 from Moon.
- **Madhya Adhi Yoga** (middle) — EXACTLY TWO of the three.
- **Alpa Adhi Yoga** (small) — EXACTLY ONE of the three.

At most one variant is emitted per chart (the highest-tier matched).
Zero participants yields NO Finding (silent).

Houses-from-Moon math
=====================

The N-th house from the Moon (1..12) sits in the sign at:

    target_sign = ((moon_sign - 1 + (N - 1)) % 12) + 1

So 6/7/8 from the Moon ⇒ N in {6, 7, 8}.

Public API
==========

    detect_adhi(d1_chart, asc_sign) -> list[Finding]

The Finding id pattern is ``practitioner.yogas_extended.adhi.<variant>``
where ``<variant>`` is one of ``maha``, ``madhya``, or ``alpa``.
classification="yoga", direction="positive".
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# The three natural benefics that participate in Adhi Yoga.
_ADHI_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury")

# Houses counted from Moon (1=conjunction, 2=2nd house, etc.).
_ADHI_HOUSES_FROM_MOON: Final[frozenset[int]] = frozenset({6, 7, 8})


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Ch.40 Adhi Yoga (Jup/Ven/Mer in 6-7-8 from Moon)"
)


def _house_from_moon(moon_sign: int, planet_sign: int) -> int:
    """Return the 1..12 house position of planet_sign as counted from
    moon_sign (1 = same sign as Moon, 6 = 6th house from Moon, etc.).
    """
    return ((planet_sign - moon_sign) % 12) + 1


def _build_finding(
    variant: str,
    participants_in_678: list[tuple[str, int]],
) -> Finding:
    """Construct the Finding for the detected variant.

    ``variant`` is ``"maha"``, ``"madhya"``, or ``"alpa"``.
    ``participants_in_678`` is the list of (planet, house_from_moon)
    pairs that satisfied the 6/7/8-from-Moon condition.
    """
    labels = {
        "maha":   "Maha Adhi Yoga",
        "madhya": "Madhya Adhi Yoga",
        "alpa":   "Alpa Adhi Yoga",
    }
    summaries = {
        "maha":   "Jup+Ven+Mer all in 6/7/8 from Moon (great power, prosperity)",
        "madhya": "two of Jup/Ven/Mer in 6/7/8 from Moon (solid prosperity)",
        "alpa":   "one of Jup/Ven/Mer in 6/7/8 from Moon (modest prosperity)",
    }
    label = labels[variant]
    summary = summaries[variant]
    parts_str = "+".join(
        f"{p}({h}H)" for p, h in participants_in_678
    )
    verdict = f"{label} — {parts_str}: {summary}"[:140]
    evidence = [
        f"variant={variant}",
        f"participants={[p for p, _ in participants_in_678]!r}",
        *[
            f"{p}_house_from_moon={h}"
            for p, h in participants_in_678
        ],
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.yogas_extended.adhi.{variant}",
        rule="adhi_yoga",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_adhi(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Adhi Yoga (BPHS Ch.40) — Jup/Ven/Mer in 6/7/8 from Moon.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int (1..12), ...}}.
        asc_sign: 1..12 ascendant sign (validated; carried in evidence
            via positional convention — the rule itself does NOT use
            asc_sign for the computation but downstream consumers may).

    Returns:
        A list containing at most ONE Finding (the highest-tier variant).
        Empty list when Moon is absent, or when zero benefics occupy
        6/7/8 from the Moon.

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    moon_entry = d1_chart.get("Moon")
    if not moon_entry:
        return []
    moon_sign = moon_entry.get("sign")
    if not isinstance(moon_sign, int) or not 1 <= moon_sign <= 12:
        return []

    participants: list[tuple[str, int]] = []
    for planet in _ADHI_BENEFICS:
        entry = d1_chart.get(planet)
        if not entry:
            continue
        p_sign = entry.get("sign")
        if not isinstance(p_sign, int) or not 1 <= p_sign <= 12:
            continue
        house = _house_from_moon(moon_sign, p_sign)
        if house in _ADHI_HOUSES_FROM_MOON:
            participants.append((planet, house))

    count = len(participants)
    if count == 0:
        return []
    if count == 3:
        variant = "maha"
    elif count == 2:
        variant = "madhya"
    else:  # count == 1
        variant = "alpa"
    return [_build_finding(variant, participants)]


__all__ = ["detect_adhi"]
