"""Tier-1 foundation: Jaimini Rashi-drishti per Sutras Adhyaya 1, Pada 4.

Doctrine source: Jaimini Sutras Adhyaya 1, Pada 4 (Rashi-drishti sutras).

Jaimini's rashi-drishti is fundamentally different from the Parashari
graha-drishti: it operates on SIGNS, not planets, and the aspect set is
fully determined by the three sign-categories
(Chara / Sthira / Dwiswabhava).

Sign categories
===============

  - **Movable** (Chara)      : Aries (1), Cancer (4), Libra (7),
                               Capricorn (10).
  - **Fixed** (Sthira)       : Taurus (2), Leo (5), Scorpio (8),
                               Aquarius (11).
  - **Dual** (Dwiswabhava)   : Gemini (3), Virgo (6), Sagittarius (9),
                               Pisces (12).

Sutras (Jaimini 1.4)
====================

  - **Movable -> Fixed**: Each movable sign aspects all four fixed signs
    EXCEPT the immediately-following sign (the fixed sign at +1 from the
    movable). So Aries (1) aspects Leo, Scorpio, Aquarius -- but not
    Taurus.
  - **Fixed -> Movable**: Each fixed sign aspects all four movable signs
    EXCEPT the immediately-preceding sign. So Taurus (2) aspects Cancer,
    Libra, Capricorn -- but not Aries.
  - **Dual -> Dual**: Each dual sign aspects all three OTHER dual signs.

A movable sign never aspects another movable sign; a fixed never another
fixed; and dual signs only aspect duals. Self-aspect is excluded.

Symmetry invariant
==================

The rashi-drishti graph is symmetric (mutual aspect for every pair):
movable M aspects fixed F iff fixed F aspects movable M (the
``immediately-following`` and ``immediately-preceding`` conditions are
mirror images), and dual aspects are symmetric by construction.

Public API
==========

  compute_jaimini_drishti(d1_chart, asc_sign) -> dict[str, Finding]

Returns 12 Findings, one per sign, each describing the set of signs it
aspects under Jaimini rashi-drishti. Output keys: ``sign_1`` .. ``sign_12``.

  _signs_aspected_by(sign) -> tuple[int, ...]
  _sign_category(sign) -> {"movable", "fixed", "dual"}

Are internal helpers exposed for testing and downstream reuse (e.g. by
Sequence 5's Karakamsha-Lagna repeat checks).

Usage
=====

    >>> from app.reading.computations.jaimini_drishti import (
    ...     compute_jaimini_drishti,
    ... )
    >>> result = compute_jaimini_drishti({}, asc_sign=1)
    >>> "sign_1" in result
    True
    >>> result["sign_1"].verdict        # doctest: +SKIP
    'Aries (movable) aspects Leo, Scorpio, Aquarius'
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sign-category tables
# ---------------------------------------------------------------------------

_MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED_SIGNS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})


# Sign names (1-indexed; index 0 is unused).
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _sign_category(sign: int) -> str:
    """Return ``"movable"`` / ``"fixed"`` / ``"dual"`` for a 1..12 sign."""
    if not 1 <= sign <= 12:
        raise ValueError(f"sign must be in [1, 12], got {sign!r}")
    if sign in _MOVABLE_SIGNS:
        return "movable"
    if sign in _FIXED_SIGNS:
        return "fixed"
    return "dual"


def _signs_aspected_by(sign: int) -> tuple[int, ...]:
    """Return the sorted-by-doctrine signs aspected by ``sign``.

    For movable signs: all fixed signs except the immediately-following.
    For fixed signs:   all movable signs except the immediately-preceding.
    For dual signs:    all other dual signs.

    The order returned mirrors the natural traversal in the sutras (the
    aspected category, starting from the sign just past the excluded
    one). Stable across calls.
    """
    if not 1 <= sign <= 12:
        raise ValueError(f"sign must be in [1, 12], got {sign!r}")
    category = _sign_category(sign)
    if category == "movable":
        # Exclude the next sign (sign + 1).
        excluded = (sign % 12) + 1
        return tuple(s for s in (2, 5, 8, 11) if s != excluded)
    if category == "fixed":
        # Exclude the previous sign (sign - 1).
        excluded = ((sign - 2) % 12) + 1
        return tuple(s for s in (1, 4, 7, 10) if s != excluded)
    # dual: all other duals
    return tuple(s for s in (3, 6, 9, 12) if s != sign)


# ---------------------------------------------------------------------------
# Finding builder
# ---------------------------------------------------------------------------


def _verdict_for(sign: int, category: str, aspected: tuple[int, ...]) -> str:
    """Build the human-readable verdict for one sign."""
    name = _SIGN_NAMES[sign]
    aspected_names = ", ".join(_SIGN_NAMES[a] for a in aspected)
    return f"{name} ({category}) aspects {aspected_names}"


def _sign_finding(sign: int) -> Finding:
    """Build the Finding for one sign's Jaimini rashi-drishti row."""
    category = _sign_category(sign)
    aspected = _signs_aspected_by(sign)
    key = f"sign_{sign}"
    return Finding(
        id=f"foundation.jaimini_drishti.{key}",
        rule="jaimini_drishti",
        source_sequence=None,
        classification="primitive",
        direction="neutral",  # aspect existence; charged direction is consumer's job
        verdict=_verdict_for(sign, category, aspected),
        evidence=[
            f"sign={sign}",
            f"sign_name={_SIGN_NAMES[sign]}",
            f"category={category}",
            f"aspects={list(aspected)}",
            "doctrine=Jaimini Sutras 1.4 (Rashi-drishti)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_jaimini_drishti(
    d1_chart: dict, asc_sign: int,
) -> dict[str, Finding]:
    """Emit per-sign Jaimini rashi-drishti relationships.

    Args:
        d1_chart: Currently ignored -- Jaimini rashi-drishti is purely a
            sign-category property, independent of which planets sit
            where. The arg is preserved for API consistency with the
            other Tier-1 modules and so future extensions (e.g. emitting
            planet-on-sign annotations) are non-breaking.
        asc_sign: Ascendant rashi (1..12). Validated for range; not used
            in the rashi-drishti calculation itself, but kept for the
            same API-consistency reason.

    Returns:
        Dict keyed by ``sign_<N>`` (N=1..12), each value a Finding with
        ``id="foundation.jaimini_drishti.sign_<N>"`` describing the
        signs aspected by sign N.

    Raises:
        ValueError: if ``asc_sign`` is not in ``1..12``.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )
    # d1_chart is intentionally accepted but unused; touching it avoids
    # "argument never used" lint warnings.
    _ = d1_chart

    return {f"sign_{sign}": _sign_finding(sign) for sign in range(1, 13)}


__all__ = [
    "compute_jaimini_drishti",
]
