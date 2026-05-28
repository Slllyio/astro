"""Tier-1 foundation: functional nature of each graha per Lagna (D-7 locked).

Doctrine lock - D-7 (``docs/doctrine-decisions.md``)
====================================================

PVR Narasimha Rao / Sanjay Rath synthesis of the full 12-lagna x 9-planet
functional benefic/malefic matrix. Each cell takes one of four labels:

- ``yogakaraka``         -- the planet owns BOTH a kendra (1/4/7/10) AND
                            a kona (5/9) from the lagna. The strongest
                            single-planet benefic indicator in the chart.
- ``functional_benefic`` -- the planet owns 1 (Lagna), 5, or 9 (Trikona),
                            OR a kendra where the natural-malefic status
                            of the planet absorbs the kendradhipati
                            tendency.
- ``functional_neutral`` -- the planet owns 2 (Maraka with caveats) or a
                            kendra + upachaya mix where Trikona ownership
                            does not dominate. Returned for nodes (Rahu,
                            Ketu) for every lagna since classical doctrine
                            does not grant the shadow planets a lordship-
                            based nature.
- ``functional_malefic`` -- the planet owns 3, 6, 8, 11, or 12 with no
                            compensating Trikona ownership; or a kendra
                            where the kendradhipati dosha (natural benefic
                            owning a kendra) dominates.

The matrix is hardcoded as ``FUNCTIONAL_NATURE_TABLE`` (a
``Final[dict[int, dict[str, str]]]``) and the public
``compute_functional_nature(asc_sign)`` function wraps each lookup in a
``Finding`` envelope.

Known interpretive deviations from K.N. Rao school
---------------------------------------------------

D-7 commits to the PVR / Sanjay Rath synthesis. Four cells admit
legitimate alternative readings in K.N. Rao's school. We name them
explicitly so downstream consumers (e.g. ``dispute_surfacing.py``,
Tier-3) can surface the alternative without secretly mutating the
deterministic D-7 lookup:

+--------------+---------+----------------------+--------------------+--------------------------------------------------------------+
| Lagna        | Planet  | This impl (PVR/Rath) | Rao school         | Rationale                                                    |
+==============+=========+======================+====================+==============================================================+
| Cancer (4)   | Jupiter | functional_malefic   | functional_benefic | 6L+9L; 6th dusthana dominates for natural benefic per PVR.   |
|              |         |                      |                    | Rao reads 9L Trikona as dominant for a natural benefic and   |
|              |         |                      |                    | calls Jupiter functionally benefic for Cancer lagna.         |
+--------------+---------+----------------------+--------------------+--------------------------------------------------------------+
| Sagittarius  | Saturn  | functional_malefic   | functional_neutral | 2L Maraka + 3L upachaya = combined malefic per PVR. Rao      |
| (9)          |         |                      |                    | treats the 2L+3L mix as neutral because neither pure         |
|              |         |                      |                    | Trikona nor pure dusthana dominates.                         |
+--------------+---------+----------------------+--------------------+--------------------------------------------------------------+
| Capricorn    | Mars    | functional_malefic   | functional_neutral | 4L kendra + 11L upachaya; debilitation + 11L upachaya        |
| (10)         |         |                      |                    | dominate per PVR. Rao treats 4L kendra (Mars debilitated     |
|              |         |                      |                    | in Cancer notwithstanding) as compensating the 11L           |
|              |         |                      |                    | upachaya, yielding neutral.                                  |
+--------------+---------+----------------------+--------------------+--------------------------------------------------------------+
| Aquarius     | Mars    | functional_malefic   | functional_neutral | 3L upachaya + 10L kendradhipati dosha per PVR. Rao treats    |
| (11)         |         |                      |                    | the 3L+10L mix as neutral on the grounds that kendradhipati  |
|              |         |                      |                    | dosha applies primarily to natural benefics, not Mars.       |
+--------------+---------+----------------------+--------------------+--------------------------------------------------------------+

These four cells can be exposed via ``dispute_surfacing.py`` (Tier-3) for
downstream consumers who prefer the Rao reading. The D-7 lookup itself
always returns the PVR/Rath value; the Rao alternative is metadata, not
a mode switch.

The shadow-planet invariant
---------------------------
Rahu and Ketu have **no lordship** in classical Parashari doctrine, so
they cannot derive a functional benefic/malefic status from house
ownership. We return ``functional_neutral`` for both on every lagna; the
evidence line ``nature=functional_neutral`` is paired with
``shadow_planet=true`` so downstream consumers (e.g. dispute_surfacing)
can distinguish "neutral because no lordship" from "neutral because
mixed-ownership cancelled out."

The 12-lagna sign-to-house map (used to derive the canonical table)
-------------------------------------------------------------------

For each ascendant sign A, the N-th house is sign ``((A + N - 2) % 12) + 1``.
Combined with ``app.core.dignity.SIGN_RULERS``, this produces the planet
that owns the N-th house from that lagna. Each cell below was derived
by enumerating the houses each planet owns from that lagna and applying
the doctrine-priority order: 1L > yogakaraka > pure Trikona >
mixed-Trikona-dominated > pure-malefic.

Public API
==========

    compute_functional_nature(asc_sign) -> dict[str, Finding]
    FUNCTIONAL_NATURE_TABLE: Final[dict[int, dict[str, str]]]

Usage
=====

    >>> from app.reading.computations.functional_nature import (
    ...     compute_functional_nature,
    ... )
    >>> natures = compute_functional_nature(asc_sign=4)  # Cancer
    >>> natures["Mars"].verdict
    'Mars is yogakaraka for Cancer lagna (owns kendra+kona)'
"""
from __future__ import annotations

import logging
from typing import Final, Literal

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Sign names (1-indexed: index 0 unused).
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


FunctionalNature = Literal[
    "yogakaraka",
    "functional_benefic",
    "functional_neutral",
    "functional_malefic",
]


# 3-vote envelope -- functional nature is a single deterministic lookup,
# not a 3-pillar judgment.
_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# The canonical 12-lagna x 9-planet functional matrix (D-7).
#
# Per-cell derivation (PVR / Sanjay Rath):
#
# - Lagna lord (1L) is ALWAYS benefic (even if it owns a trika house too).
# - Yogakaraka requires BOTH a kendra (1/4/7/10) AND a kona (5/9). Since
#   1L is handled separately, the YK label is applied when the planet
#   owns one of 4/7/10 AND one of 5/9 (i.e. excluding the 1L case).
# - Pure trikona (5L or 9L alone or paired with another trikona or 1) =
#   benefic.
# - Pure malefic ownership (3/6/8/11/12 with no trikona) = malefic.
# - Mixed-trikona-dominant (e.g. 5L+11L, 9L+12L) where one house is
#   trikona and the other is upachaya/dusthana: trikona wins -> benefic.
#   Exception: 9L+8L for Saturn / Sagittarius -> ben (8 is dusthana but
#   9 dominates). 9L+6L for Jupiter / Cancer -> mal (kendradhipati on a
#   natural benefic, plus 6 is a dusthana that dominates here per PVR).
# - Mixed kendra+upachaya (e.g. 4L+11L) for a natural benefic = neutral.
# - Kendradhipati dosha (natural benefic owning ONLY kendra houses, no
#   trikona, no 1L) = malefic (Jupiter/Venus/Mercury cases).
# - Maraka (2L, 7L) for non-benefic-significator planets = neutral; 7L
#   is also kendra, but Maraka cancels the benefic kendra tendency.
# - Rahu/Ketu = neutral, ALWAYS (shadow planets have no lordship).
# ---------------------------------------------------------------------------


FUNCTIONAL_NATURE_TABLE: Final[dict[int, dict[str, str]]] = {
    # Aries (1): Mars=1L+8L (ben as 1L); Sun=5L (ben); Moon=4L (ben);
    # Mercury=3L+6L (mal); Jupiter=9L+12L (ben, 9 dominates);
    # Venus=2L+7L (mal); Saturn=10L+11L (mal, kendradhipati + upachaya).
    1: {
        "Sun":     "functional_benefic",   # 5L Trikona
        "Moon":    "functional_benefic",   # 4L kendra (Moon non-malefic)
        "Mars":    "functional_benefic",   # 1L (Lagna lord)
        "Mercury": "functional_malefic",   # 3L + 6L
        "Jupiter": "functional_benefic",   # 9L Trikona dominates 12L
        "Venus":   "functional_malefic",   # 2L Maraka + 7L Maraka
        "Saturn":  "functional_malefic",   # 10L kendradhipati + 11L upachaya
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Taurus (2): Saturn YK (9L+10L); Venus=1L+6L ben; Sun=4L ben;
    # Mercury=2L+5L ben (5 dominates); Mars=7L+12L mal; Jupiter=8L+11L mal;
    # Moon=3L mal.
    2: {
        "Sun":     "functional_benefic",   # 4L kendra
        "Moon":    "functional_malefic",   # 3L upachaya
        "Mars":    "functional_malefic",   # 7L Maraka + 12L dusthana
        "Mercury": "functional_benefic",   # 5L Trikona dominates 2L
        "Jupiter": "functional_malefic",   # 8L + 11L both bad
        "Venus":   "functional_benefic",   # 1L (Lagna lord)
        "Saturn":  "yogakaraka",           # 9L Trikona + 10L kendra
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Gemini (3): Mercury=1L+4L ben; Venus=5L+12L ben; Saturn=8L+9L ben
    # (9 dominates); Jupiter=7L+10L mal (kendradhipati natural benefic);
    # Mars=6L+11L mal; Sun=3L mal; Moon=2L neu.
    3: {
        "Sun":     "functional_malefic",   # 3L upachaya
        "Moon":    "functional_neutral",   # 2L Maraka
        "Mars":    "functional_malefic",   # 6L + 11L both bad
        "Mercury": "functional_benefic",   # 1L (Lagna lord)
        "Jupiter": "functional_malefic",   # 7L+10L kendradhipati dosha
        "Venus":   "functional_benefic",   # 5L Trikona dominates 12L
        "Saturn":  "functional_benefic",   # 9L Trikona dominates 8L
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Cancer (4): Mars YK (5L+10L); Moon=1L ben; Mercury=3L+12L mal;
    # Venus=4L+11L neu; Jupiter=6L+9L mal (6 dominates for nat. benefic);
    # Saturn=7L+8L mal; Sun=2L neu.
    4: {
        "Sun":     "functional_neutral",   # 2L Maraka
        "Moon":    "functional_benefic",   # 1L (Lagna lord)
        "Mars":    "yogakaraka",           # 5L Trikona + 10L kendra
        "Mercury": "functional_malefic",   # 3L + 12L
        "Jupiter": "functional_malefic",   # 6L+9L; 6 dusthana dominates
        "Venus":   "functional_neutral",   # 4L kendra + 11L upachaya = mixed
        "Saturn":  "functional_malefic",   # 7L Maraka + 8L dusthana
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Leo (5): Mars YK (4L+9L); Sun=1L ben; Jupiter=5L+8L ben (5 dominates);
    # Saturn=6L+7L mal; Venus=3L+10L mal (kendradhipati nat. benefic);
    # Mercury=2L+11L mal; Moon=12L neu.
    5: {
        "Sun":     "functional_benefic",   # 1L (Lagna lord)
        "Moon":    "functional_neutral",   # 12L (mixed/sentinel)
        "Mars":    "yogakaraka",           # 4L kendra + 9L Trikona
        "Mercury": "functional_malefic",   # 2L + 11L bad
        "Jupiter": "functional_benefic",   # 5L Trikona dominates 8L
        "Venus":   "functional_malefic",   # 3L upachaya + 10L kendradhipati
        "Saturn":  "functional_malefic",   # 6L + 7L Maraka
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Virgo (6): Mercury=1L+10L ben (1L dominates); Venus=2L+9L ben
    # (9 dominates); Saturn=5L+6L ben (5 Trikona dominates); Mars=3L+8L mal;
    # Jupiter=4L+7L mal (kendradhipati natural benefic); Moon=11L mal;
    # Sun=12L neu.
    6: {
        "Sun":     "functional_neutral",   # 12L
        "Moon":    "functional_malefic",   # 11L upachaya
        "Mars":    "functional_malefic",   # 3L + 8L bad
        "Mercury": "functional_benefic",   # 1L (Lagna lord)
        "Jupiter": "functional_malefic",   # 4L+7L kendradhipati dosha
        "Venus":   "functional_benefic",   # 9L Trikona dominates 2L
        "Saturn":  "functional_benefic",   # 5L Trikona dominates 6L
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Libra (7): Saturn YK (4L+5L); Venus=1L+8L ben (1L dominates);
    # Mercury=9L+12L ben (9 dominates); Mars=2L+7L mal (Maraka pair);
    # Jupiter=3L+6L mal; Sun=11L mal; Moon=10L neu.
    7: {
        "Sun":     "functional_malefic",   # 11L upachaya
        "Moon":    "functional_neutral",   # 10L kendra (Moon mixed)
        "Mars":    "functional_malefic",   # 2L + 7L Maraka pair
        "Mercury": "functional_benefic",   # 9L Trikona dominates 12L
        "Jupiter": "functional_malefic",   # 3L + 6L both bad
        "Venus":   "functional_benefic",   # 1L (Lagna lord)
        "Saturn":  "yogakaraka",           # 4L kendra + 5L Trikona
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Scorpio (8): Mars=1L+6L ben (1L dominates); Moon=9L ben; Jupiter=2L+5L
    # ben (5 dominates); Sun=10L ben (kendra for nat. malefic); Venus=7L+12L mal;
    # Mercury=8L+11L mal; Saturn=3L+4L mal (3 upachaya).
    8: {
        "Sun":     "functional_benefic",   # 10L kendra
        "Moon":    "functional_benefic",   # 9L Trikona
        "Mars":    "functional_benefic",   # 1L (Lagna lord)
        "Mercury": "functional_malefic",   # 8L + 11L bad
        "Jupiter": "functional_benefic",   # 5L Trikona dominates 2L
        "Venus":   "functional_malefic",   # 7L Maraka + 12L dusthana
        "Saturn":  "functional_malefic",   # 3L upachaya + 4L kendradhipati
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Sagittarius (9): Jupiter=1L+4L ben (1L dominates); Sun=9L ben;
    # Mars=5L+12L ben (5 dominates); Mercury=7L+10L mal (kendradhipati nat. ben);
    # Moon=8L mal; Venus=6L+11L mal; Saturn=2L+3L mal.
    9: {
        "Sun":     "functional_benefic",   # 9L Trikona
        "Moon":    "functional_malefic",   # 8L dusthana
        "Mars":    "functional_benefic",   # 5L Trikona dominates 12L
        "Mercury": "functional_malefic",   # 7L+10L kendradhipati dosha
        "Jupiter": "functional_benefic",   # 1L (Lagna lord)
        "Venus":   "functional_malefic",   # 6L + 11L both bad
        "Saturn":  "functional_malefic",   # 2L + 3L upachaya
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Capricorn (10): Venus YK (5L+10L); Saturn=1L+2L ben (1L dominates);
    # Mercury=6L+9L ben (9 dominates); Sun=8L mal; Mars=4L+11L mal;
    # Jupiter=3L+12L mal; Moon=7L neu.
    10: {
        "Sun":     "functional_malefic",   # 8L dusthana
        "Moon":    "functional_neutral",   # 7L Maraka kendra
        "Mars":    "functional_malefic",   # 4L kendra + 11L upachaya = mixed-mal
        "Mercury": "functional_benefic",   # 9L Trikona dominates 6L
        "Jupiter": "functional_malefic",   # 3L + 12L both bad
        "Venus":   "yogakaraka",           # 5L Trikona + 10L kendra
        "Saturn":  "functional_benefic",   # 1L (Lagna lord)
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Aquarius (11): Venus YK (4L+9L); Saturn=1L+12L ben (1L dominates);
    # Mercury=5L+8L ben (5 dominates); Sun=7L neu; Moon=6L mal;
    # Mars=3L+10L mal; Jupiter=2L+11L mal.
    11: {
        "Sun":     "functional_neutral",   # 7L Maraka
        "Moon":    "functional_malefic",   # 6L dusthana
        "Mars":    "functional_malefic",   # 3L upachaya + 10L kendradhipati
        "Mercury": "functional_benefic",   # 5L Trikona dominates 8L
        "Jupiter": "functional_malefic",   # 2L + 11L upachaya
        "Venus":   "yogakaraka",           # 4L kendra + 9L Trikona
        "Saturn":  "functional_benefic",   # 1L (Lagna lord)
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
    # Pisces (12): Jupiter=1L+10L ben (1L dominates); Moon=5L ben;
    # Mars=2L+9L ben (9 dominates); Sun=6L mal; Mercury=4L+7L mal
    # (kendradhipati nat. benefic); Venus=3L+8L mal; Saturn=11L+12L mal.
    12: {
        "Sun":     "functional_malefic",   # 6L dusthana
        "Moon":    "functional_benefic",   # 5L Trikona
        "Mars":    "functional_benefic",   # 9L Trikona dominates 2L
        "Mercury": "functional_malefic",   # 4L+7L kendradhipati dosha
        "Jupiter": "functional_benefic",   # 1L (Lagna lord)
        "Venus":   "functional_malefic",   # 3L + 8L bad
        "Saturn":  "functional_malefic",   # 11L + 12L both bad
        "Rahu":    "functional_neutral",
        "Ketu":    "functional_neutral",
    },
}


# Compile-time integrity assertion: table is 12 x 9 and every cell is
# a valid FunctionalNature literal.
assert set(FUNCTIONAL_NATURE_TABLE.keys()) == set(range(1, 13)), (
    "FUNCTIONAL_NATURE_TABLE must have exactly 12 lagnas"
)
_VALID_CELL_VALUES: Final[frozenset[str]] = frozenset(
    {"yogakaraka", "functional_benefic", "functional_neutral", "functional_malefic"}
)
for _asc, _row in FUNCTIONAL_NATURE_TABLE.items():
    assert set(_row.keys()) == set(_PLANETS), (
        f"lagna {_asc} row keys are {set(_row.keys())!r}"
    )
    for _planet, _nat in _row.items():
        assert _nat in _VALID_CELL_VALUES, (
            f"FUNCTIONAL_NATURE_TABLE[{_asc}][{_planet}] = "
            f"{_nat!r} is not a valid nature"
        )
    # D-7 critical invariant: Rahu and Ketu are ALWAYS neutral.
    assert _row["Rahu"] == "functional_neutral", (
        f"lagna {_asc} Rahu must be neutral by D-7 doctrine"
    )
    assert _row["Ketu"] == "functional_neutral", (
        f"lagna {_asc} Ketu must be neutral by D-7 doctrine"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _direction_for(nature: str) -> str:
    """Map FunctionalNature -> Finding.direction enum value."""
    if nature in ("yogakaraka", "functional_benefic"):
        return "positive"
    if nature == "functional_malefic":
        return "negative"
    return "neutral"


def _verdict_for(planet: str, nature: str, asc_sign: int) -> str:
    """Human-readable one-line verdict for the Finding."""
    lagna_name = _SIGN_NAMES[asc_sign]
    if nature == "yogakaraka":
        return (
            f"{planet} is yogakaraka for {lagna_name} lagna "
            "(owns kendra+kona)"
        )
    if nature == "functional_benefic":
        return f"{planet} is functional benefic for {lagna_name} lagna"
    if nature == "functional_malefic":
        return f"{planet} is functional malefic for {lagna_name} lagna"
    # functional_neutral
    if planet in ("Rahu", "Ketu"):
        return (
            f"{planet} is functional neutral for {lagna_name} lagna "
            "(shadow planet)"
        )
    return f"{planet} is functional neutral for {lagna_name} lagna"


def _nature_finding(
    planet: str, asc_sign: int, nature: str,
) -> Finding:
    """Build the Finding for one (lagna, planet) cell."""
    direction = _direction_for(nature)
    verdict = _verdict_for(planet, nature, asc_sign)
    evidence = [
        f"asc_sign={asc_sign}",
        f"asc_sign_name={_SIGN_NAMES[asc_sign]}",
        f"planet={planet}",
        f"nature={nature}",
        f"doctrine=D-7 (pvr_sanjay_rath_synthesis)",
    ]
    if planet in ("Rahu", "Ketu"):
        # Pair the neutral nature with a sentinel so downstream consumers
        # can distinguish "neutral because no lordship" from
        # "neutral because mixed-ownership cancelled out."
        evidence.append("shadow_planet=true")
    return Finding(
        id=f"foundation.functional_nature.{planet.lower()}",
        rule="functional_nature",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=verdict,
        evidence=evidence,
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_functional_nature(asc_sign: int) -> dict[str, Finding]:
    """Compute functional nature of each graha for the given Lagna.

    Args:
        asc_sign: Ascendant rashi (1=Aries .. 12=Pisces).

    Returns:
        Dict keyed by planet name (Sun..Ketu), each value a Finding with
        ``id="foundation.functional_nature.<planet>"`` and the planet's
        functional nature for this lagna encoded in the ``evidence``
        list as ``nature=<value>``.

    Raises:
        ValueError: if ``asc_sign`` is not in ``1..12``.

    Example:
        >>> natures = compute_functional_nature(asc_sign=4)  # Cancer
        >>> natures["Mars"].direction
        'positive'
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )

    row = FUNCTIONAL_NATURE_TABLE[asc_sign]
    return {
        planet: _nature_finding(planet, asc_sign, row[planet])
        for planet in _PLANETS
    }


__all__ = [
    "compute_functional_nature",
    "FUNCTIONAL_NATURE_TABLE",
    "FunctionalNature",
]
