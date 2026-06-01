"""Upapada Lagna (UPL) — Jaimini marriage indicator (round-8 helper).

The Upapada Lagna is the Arudha Pada of the 12th bhava. Per Jaimini
Sutras 1.4 and BPHS Ch.29:

  1. Find the 12H sign and its lord L12.
  2. Compute the distance D (inclusive forward) from the 12H sign to
     L12's natal sign.
  3. Step D signs forward from L12's natal sign — this is the candidate
     Upapada sign.
  4. Special substitution rules: if D == 1 OR D == 7 (i.e. the candidate
     lands on the 12H itself or the 6H from it), use the 10th-from-L12
     instead. (Jaimini's "10th rule" for degenerate Arudhas.)

The UPL is the primary marriage indicator in Sanjay Rath's school:
  - UPL sign = type of spouse
  - 2nd from UPL = duration/quality of first marriage
  - planets aspecting / occupying 2nd-from-UPL = events in marital years

This is a thin, dedicated wrapper around the same Jaimini formula
already implemented generically in ``karakamsa_arudha.arudha_pada(12,
chart)``; the wrapper exists so callers can ask for UPL and the 2nd
from UPL directly with a more compact, marriage-focused result type.

Usage:
    from app.core.upapada_lagna import compute_upapada
    result = compute_upapada(chart)
    # result.upapada_sign, result.second_from_upl_sign, ...

Reference: Jaimini Sutras 1.4; BPHS Ch.29; Sanjay Rath "Crux of Vedic
Astrology" Ch.11 (UPL marriage doctrine).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart

logger = logging.getLogger(__name__)


_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


@dataclass(frozen=True)
class UpapadaResult:
    """Compact UPL result optimised for marriage-axis interpretation.

    Attributes:
        upapada_sign: The Upapada Lagna in zodiac terms (1..12).
        upapada_house_from_lagna: Which natal house the UPL falls in
            (1..12) measured from the chart's Lagna.
        twelfth_lord: Name of the 12H lord (the planet whose placement
            drove the UPL computation).
        twelfth_lord_house: Natal house of the 12H lord (1..12).
        second_from_upl_sign: The sign 2nd-from-UPL (zodiac 1..12). This
            is the canonical marriage-duration indicator per Sanjay Rath.
        distance_used: The Jaimini step-distance D actually used (after
            substitution); useful for debugging/audit.
        substitution_applied: True iff the 10th-from-L12 substitution
            kicked in (D was 1 or 7).
    """
    upapada_sign: int
    upapada_house_from_lagna: int
    twelfth_lord: str
    twelfth_lord_house: int
    second_from_upl_sign: int
    distance_used: int
    substitution_applied: bool


def _step_signs(from_sign: int, distance: int) -> int:
    """Step ``distance`` signs forward (inclusive count, wraps at 12)."""
    return ((from_sign - 1 + distance - 1) % 12) + 1


def compute_upapada(chart: Chart) -> UpapadaResult:
    """Compute the Upapada Lagna (UPL) for a chart.

    Args:
        chart: A populated ``Chart`` with at least the 12H lord's sign
            and house. Raises ``ValueError`` if the 12H lord is absent
            from ``chart.planet_signs``.

    Returns:
        ``UpapadaResult`` carrying the UPL sign, 2nd-from-UPL sign, and
        debug fields (distance, substitution flag) for audit traces.
    """
    twelfth_sign = _step_signs(chart.asc_sign, 12)
    twelfth_lord = _SIGN_LORDS[twelfth_sign]
    lord_sign = chart.sign_of(twelfth_lord)
    lord_house = chart.house_of(twelfth_lord)
    if lord_sign is None or lord_house is None:
        raise ValueError(
            f"chart missing position for 12H lord {twelfth_lord} "
            f"(sign={lord_sign}, house={lord_house})"
        )
    # Inclusive forward distance from 12H sign to lord's sign.
    distance = ((lord_sign - twelfth_sign) % 12) + 1
    substitution_applied = distance in (1, 7)
    if substitution_applied:
        # Jaimini 10th-rule for degenerate Arudhas: take 10th-from-L12.
        upapada_sign = _step_signs(lord_sign, 10)
        effective_distance = 10
    else:
        upapada_sign = _step_signs(lord_sign, distance)
        effective_distance = distance
    upapada_house = ((upapada_sign - chart.asc_sign) % 12) + 1
    second_from_upl = _step_signs(upapada_sign, 2)
    logger.debug(
        "UPL: 12H=%d 12L=%s lord_sign=%d D=%d sub=%s UPL=%d 2ndUPL=%d",
        twelfth_sign, twelfth_lord, lord_sign, distance,
        substitution_applied, upapada_sign, second_from_upl,
    )
    return UpapadaResult(
        upapada_sign=upapada_sign,
        upapada_house_from_lagna=upapada_house,
        twelfth_lord=twelfth_lord,
        twelfth_lord_house=lord_house,
        second_from_upl_sign=second_from_upl,
        distance_used=effective_distance,
        substitution_applied=substitution_applied,
    )
