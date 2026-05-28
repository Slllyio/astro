"""Unified yoga-strength scoring for the Phase-3B Tier-1 catalog.

Every detected yoga produces a continuous strength score in [0, 1] via
this module. The formula is:

    raw_strength = geometric_mean(
        shadbala_total(p) / shadbala_ceiling(p)
        for p in yoga.participants
    )

    drishti_modulator = 1.0 + (drik_bala(participant) / 240.0)  # ≈ ±0.25

    yoga_strength = clamp(raw_strength × drishti_modulator, 0, 1)

    if vipareeta:
        yoga_strength = 1.0 - yoga_strength   # classical inversion

The drishti_modulator is folded in implicitly because Drik-bala is
already a Shadbala component. We surface it here separately so that
future yoga-specific modulators (e.g., "Kemadruma cancellation if
benefic in 2nd/12th from Moon") can also live in this module.

References:
    BPHS 27 (Shadbala)
    BPHS 36 + Phaladeepika 6.39 (Vipareeta inversion principle)
    See docs/bphs_reference.md §3-4 for sloka anchors.
"""
from __future__ import annotations

from app.core.ephemeris_engine import whole_sign_house
from app.core.shadbala import _max_shadbala_ceiling, shadbala_total
from app.core.yoga_types import YogaInstance


def _participant_shadbala_fraction(
    planet: str, chart: dict, asc_sign: int
) -> float:
    """Return ``shadbala_total / max_ceiling`` for one participant.

    Returns 0.0 when the planet is missing from the chart or the entry
    lacks the needed fields. Phase-3B keeps this fault-tolerant so a
    partial chart doesn't crash the catalog scoring.
    """
    entry = chart.get(planet)
    if not entry:
        return 0.0
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return 0.0
    longitude = entry.get("longitude")
    if not isinstance(longitude, (int, float)):
        longitude = (sign - 1) * 30.0 + 15.0
    d9_sign = entry.get("d9_sign", sign)
    house = whole_sign_house(asc_sign, sign)

    breakdown = shadbala_total(
        planet,
        longitude=float(longitude),
        d1_sign=sign,
        d9_sign=d9_sign,
        house=house,
        chart=chart,
    )
    ceiling = _max_shadbala_ceiling(planet)
    if ceiling <= 0:
        return 0.0
    raw = breakdown["total"] / ceiling
    # Shadbala can dip below 0 (Drik-bala negative); clamp to [0, 1] for
    # the geometric-mean step which requires non-negative inputs.
    return max(0.0, min(1.0, raw))


def _geometric_mean(values: list[float]) -> float:
    """Geometric mean for [0, 1] values; defined as 0 if any value is 0."""
    if not values:
        return 0.0
    if any(v <= 0.0 for v in values):
        return 0.0
    product = 1.0
    for v in values:
        product *= v
    return product ** (1.0 / len(values))


def score_yoga_strength(
    participants: tuple[str, ...],
    chart: dict,
    asc_sign: int,
    *,
    invert_for_vipareeta: bool = False,
) -> float:
    """Compute yoga strength in [0, 1] from participant Shadbalas.

    Used by every detector in ``app/core/yogas/`` so the formula stays
    consistent across the catalog. Inversion (per BPHS 36 / Phaladeepika
    6.39) is applied at the end for Vipareeta-class yogas: a weak
    participant → strong Vipareeta outcome.
    """
    if not participants:
        return 0.0
    fractions = [
        _participant_shadbala_fraction(p, chart, asc_sign)
        for p in participants
    ]
    raw_strength = _geometric_mean(fractions)
    if invert_for_vipareeta:
        raw_strength = 1.0 - raw_strength
    return max(0.0, min(1.0, raw_strength))


def build_yoga_instance(
    *,
    name: str,
    category: str,
    participants: tuple[str, ...],
    houses_activated: tuple[int, ...],
    promise_axis: str,
    lords_involved: tuple[str, ...],
    chart: dict,
    asc_sign: int,
    invert_for_vipareeta: bool = False,
) -> YogaInstance:
    """Construct a fully-scored YogaInstance with strength baked in.

    The single entry point Phase-3B detectors use to emit results.
    Each detector defines the structural metadata; this helper handles
    the strength scoring uniformly.
    """
    strength = score_yoga_strength(
        participants, chart, asc_sign,
        invert_for_vipareeta=invert_for_vipareeta,
    )
    return YogaInstance(
        name=name,
        category=category,  # type: ignore[arg-type]
        participants=participants,
        houses_activated=tuple(sorted(set(houses_activated))),
        promise_axis=promise_axis,
        lords_involved=lords_involved,
        strength=strength,
    )


__all__ = [
    "score_yoga_strength",
    "build_yoga_instance",
]
