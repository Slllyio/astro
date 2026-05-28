"""Tier-1 utility: the practitioner 3-vote rule for confidence calibration.

Doctrine source: practitioner 3-vote rule (house + lord + karaka), the
cross-cutting confidence-calibration mechanism used by every downstream
practitioner / domain module.

Three pillars of evidence are checked for any signification:

  1. **House**  -- does the relevant bhava itself bear favourable
                   indicators (occupant, aspects, ashtakavarga score)?
  2. **Lord**   -- does the lord of that bhava exhibit favourable
                   placement (dignity, strength, conjunctions)?
  3. **Karaka** -- does the natural karaka for the theme exhibit
                   favourable state (dignity, freedom from affliction)?

Each pillar contributes a boolean vote. The aggregate score is the
exact fraction ``votes_for / 3``.

Schema-aware band mapping
=========================

The schema's ``ConfidenceScore.band`` literal set is
``{"indicative_only", "low", "medium", "high", "very_strong"}``;
"moderate" and "absent" are not members. The classical-spec 4-band
scheme maps as follows:

  - 3/3 (score 1.000) -> ``"very_strong"``
  - 2/3 (score 0.667) -> ``"medium"``   (== "moderate" in spec wording)
  - 1/3 (score 0.333) -> ``"indicative_only"``
  - 0/3 (score 0.000) -> ``"indicative_only"`` (== "absent" in spec wording)

The collapse of 0/3 and 1/3 into a shared band is acceptable: the
``score`` field still distinguishes them precisely for downstream
consumers that need fine-grained ranking.

Public API
==========

  cast_confidence_vote(house_indicator, lord_indicator, karaka_indicator)
      -> ConfidenceScore

This is a *utility* function, not a Finding emitter. Practitioner /
domain modules collect their votes, call this helper, and embed the
resulting ConfidenceScore in their Finding.

Usage
=====

    >>> from app.reading.computations.confidence_voting import (
    ...     cast_confidence_vote,
    ... )
    >>> score = cast_confidence_vote(True, True, False)
    >>> score.score        # 2/3
    0.6666666666666666
    >>> score.band         # the schema 'medium' bucket (== 'moderate')
    'medium'
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Band thresholds
# ---------------------------------------------------------------------------


# Mapping from the integer vote count {0,1,2,3} to the schema band
# literal. See module docstring for the doctrinal justification.
_BAND_BY_COUNT: Final[dict[int, str]] = {
    3: "very_strong",
    2: "medium",
    1: "indicative_only",
    0: "indicative_only",
}


def _ensure_bool(value: object, name: str) -> bool:
    """Reject truthy ints / strings / None loudly.

    The 3-vote rule is a strict three-bool function; accidentally
    passing an integer (e.g. ``1`` or ``0``) would silently work via
    Python's bool subtyping and corrupt downstream aggregations. We
    refuse anything that is not exactly a ``bool``.
    """
    if not isinstance(value, bool):
        raise TypeError(
            f"{name} must be bool, got {type(value).__name__} "
            f"({value!r})"
        )
    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def cast_confidence_vote(
    house_indicator: bool,
    lord_indicator: bool,
    karaka_indicator: bool,
) -> ConfidenceScore:
    """Aggregate the 3-vote rule into a ``ConfidenceScore``.

    Args:
        house_indicator: True if the relevant bhava's own indicators are
            favourable.
        lord_indicator: True if the bhava's lord's placement is
            favourable.
        karaka_indicator: True if the signification's natural karaka is
            favourably placed.

    Returns:
        A ``ConfidenceScore`` whose:

          - ``score`` = ``votes_for / 3`` (exact fraction in
            ``{0.0, 1/3, 2/3, 1.0}``);
          - ``votes`` is a fixed 3-key dict
            ``{"house", "lord", "karaka"}`` -> bool;
          - ``band`` follows the schema-aware mapping in the module
            docstring (3/3 -> very_strong, 2/3 -> medium, 1/3 and
            0/3 -> indicative_only).

    Raises:
        TypeError: if any of the three indicators is not exactly a
            ``bool`` instance.

    Example:
        >>> score = cast_confidence_vote(True, True, True)
        >>> score.band
        'very_strong'
        >>> score.score
        1.0
    """
    house = _ensure_bool(house_indicator, "house_indicator")
    lord = _ensure_bool(lord_indicator, "lord_indicator")
    karaka = _ensure_bool(karaka_indicator, "karaka_indicator")

    count = int(house) + int(lord) + int(karaka)
    score = count / 3.0
    band = _BAND_BY_COUNT[count]

    return ConfidenceScore(
        score=score,
        votes={"house": house, "lord": lord, "karaka": karaka},
        band=band,  # type: ignore[arg-type]
    )


__all__ = ["cast_confidence_vote"]
