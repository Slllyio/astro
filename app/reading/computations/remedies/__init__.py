"""Practitioner remedies package - Beej mantras, daan, gemstones, yantras.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs) + classical Vedic remedies tradition. This package
decomposes the remedies recommender into four category sub-modules, each
emitting Findings with a stable id pattern
``practitioner.remedies.<category>.<key>``.

The orchestrator :func:`generate_remedies` aggregates all four
sub-modules into a single dict envelope keyed by category.

Sub-modules:
    - :mod:`mantras`   - Beej mantras per afflicted planet
    - :mod:`daan`      - Daan (charity) items per planet
    - :mod:`gemstones` - Gemstones with lagna-suitability gating
    - :mod:`yantras`   - Yantras (geometric diagrams) per planet

Public re-exports below are the canonical entry points for downstream
consumers (``domains/*``); sub-modules are also independently importable.

Discipline
==========

The three "per-planet" categories (mantras, daan, yantras) are returned
for EVERY afflicted planet -- they are universally applicable, karmically
safe, and required by the practitioner-locked rule that charity and
mantra remedies must precede gem strengthening (daan-before-gem).

The gemstones category is conditional:

    - POSITIVE Findings only for planets in {1L, 5L, 9L, AK} whose
      functional nature is benefic or yogakaraka.
    - NEGATIVE (BLOCKED) Findings for any functional_malefic planet
      -- this surfaces the non-negotiable practitioner rule (e.g. Blue
      Sapphire BLOCKED for Aries lagna).
    - No Finding at all for neutral / non-eligible benefic planets.
"""
from __future__ import annotations

import logging

from app.reading.schema import Finding

from app.reading.computations.remedies.daan import (
    DAAN_TABLE,
    recommend_daan,
)
from app.reading.computations.remedies.gemstones import (
    GEMSTONE_PLANET_TABLE,
    recommend_gemstones,
)
from app.reading.computations.remedies.mantras import (
    BEEJ_MANTRA_TABLE,
    recommend_mantras,
)
from app.reading.computations.remedies.yantras import (
    YANTRA_TABLE,
    recommend_yantras,
)

logger = logging.getLogger(__name__)


def generate_remedies(
    afflicted_planets: list[str],
    lagna_lord: str,
    fifth_lord: str,
    ninth_lord: str,
    atmakaraka: str,
    asc_sign: int,
    functional_natures: dict[str, str],
) -> dict[str, list[Finding]]:
    """Master entry: build all 4 remedy categories at once.

    Args:
        afflicted_planets: Ordered list of canonical planet names whose
            afflictions should be remedied. Duplicates are dropped by
            the per-planet sub-modules.
        lagna_lord: Planet ruling the 1st house (for gem gating).
        fifth_lord: Planet ruling the 5th house (Trikona, for gem gating).
        ninth_lord: Planet ruling the 9th house (Trikona, for gem gating).
        atmakaraka: Highest-degree planet (for gem gating).
        asc_sign: Ascendant rashi 1..12.
        functional_natures: Mapping from planet name to functional nature
            string. Source: :mod:`app.reading.computations.functional_nature`.

    Returns:
        dict with four keys:

            - ``mantras``   - list[Finding], one per afflicted planet
            - ``daan``      - list[Finding], one per afflicted planet
            - ``yantras``   - list[Finding], one per afflicted planet
            - ``gemstones`` - list[Finding], filtered by eligibility gate

        Each list preserves the input ordering (modulo deduplication for
        per-planet categories and the canonical planet ordering for
        gemstones). Empty input produces empty per-planet lists; the
        gemstones list may still emit BLOCKED Findings for any
        functional_malefic planet.

    Raises:
        ValueError: bubbled up from sub-modules on invalid asc_sign,
            unknown planet names, or unrecognised functional natures.
    """
    return {
        "mantras":   recommend_mantras(afflicted_planets),
        "daan":      recommend_daan(afflicted_planets),
        "yantras":   recommend_yantras(afflicted_planets),
        "gemstones": recommend_gemstones(
            lagna_lord=lagna_lord,
            fifth_lord=fifth_lord,
            ninth_lord=ninth_lord,
            atmakaraka=atmakaraka,
            asc_sign=asc_sign,
            functional_natures=functional_natures,
        ),
    }


__all__ = [
    "generate_remedies",
    "recommend_mantras",
    "recommend_gemstones",
    "recommend_daan",
    "recommend_yantras",
    "BEEJ_MANTRA_TABLE",
    "GEMSTONE_PLANET_TABLE",
    "DAAN_TABLE",
    "YANTRA_TABLE",
]
