"""The four Ayurdaya reductions (haranas) — BPHS ch.43, applied to the Nisargayu span.

BPHS-43:567 — "the four kinds of reductions suggested for Pindayu be performed for Nisargayu as
well." Each planet's natural allotment (scaled by exaltation, `longevity.py`) is cut by whichever
ONE reduction is largest (BPHS-43:392, "the highest reduction is only to be done ignoring the
others"). The four, verbatim from the chapter:

  1. Astangata (BPHS-43:268) — a COMBUST planet loses half; Venus and Saturn are exempt.
  2. Satru Kshetra (BPHS-43:272) — a planet in an ENEMY'S sign loses one third; a RETROGRADE planet
     ("Vakrachara") is exempt.
  3. Vyayadi (BPHS-43:281) — a planet in the 12th/11th/10th/9th/8th/7th loses full/1-2/1-3/1-4/1-5/
     1-6 respectively; a BENEFIC loses half of that. For longevity the Moon and Mercury are always
     benefic. When several planets share one bhava only the STRONGEST loses (BPHS-43:429).
  4. Kroorodaya (BPHS-43:369) — a MALEFIC (Sun, Mars, Saturn) in the ascendant loses (asc-cusp-in-
     minutes x its years) / 21600, i.e. the fraction asc_longitude/360; halved if a benefic aspects it.

The ascendant's OWN contribution to Nisargayu (BPHS-43:569) forks on whether the lagna lord or the
navamsa-lagna lord is stronger — DEFERRED here (not faked), so `nisargayu_after_haranas` returns the
harana-reduced PLANETARY span and says the ascendant contribution is not yet added.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation

#: The order 12th..7th -> full, 1/2, 1/3, 1/4, 1/5, 1/6 (BPHS-43:281), for a malefic.
_VYAYADI: Final[Mapping[int, float]] = {12: 1.0, 11: 1 / 2, 10: 1 / 3, 9: 1 / 4, 8: 1 / 5, 7: 1 / 6}
#: For longevity: Moon and Mercury are ALWAYS benefic (BPHS-43:291); with Jupiter and Venus.
_LONGEVITY_BENEFICS: Final[frozenset[str]] = frozenset({"Moon", "Mercury", "Jupiter", "Venus"})
#: Kroorodaya applies only to these malefics in the lagna (BPHS-43:369).
_KROORODAYA_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})

APPLIES_TO_NISARGAYU: Final[Citation] = Citation("BPHS-43", 567)
ASTANGATA_SOURCE: Final[Citation] = Citation("BPHS-43", 268)
SATRU_SOURCE: Final[Citation] = Citation("BPHS-43", 272)
VYAYADI_SOURCE: Final[Citation] = Citation("BPHS-43", 281)
KROORODAYA_SOURCE: Final[Citation] = Citation("BPHS-43", 369)
HIGHEST_ONLY_SOURCE: Final[Citation] = Citation("BPHS-43", 392)


def astangata_fraction(planet: str, *, combust: bool) -> float:
    """Combust -> lose half; Venus and Saturn exempt (BPHS-43:268)."""
    return 0.5 if (combust and planet not in ("Venus", "Saturn")) else 0.0


def satru_kshetra_fraction(*, in_enemy_sign: bool, retrograde: bool) -> float:
    """Enemy's sign -> lose one third; retrograde exempt (BPHS-43:272)."""
    return 1 / 3 if (in_enemy_sign and not retrograde) else 0.0


def vyayadi_fraction(house: int, *, is_benefic: bool) -> float:
    """House 12..7 -> full..1/6; a benefic loses half of the malefic figure (BPHS-43:281)."""
    base = _VYAYADI.get(house, 0.0)
    return base * 0.5 if is_benefic else base


def kroorodaya_fraction(planet: str, *, in_lagna: bool, asc_longitude: float,
                        benefic_aspect: bool) -> float:
    """Malefic (Sun/Mars/Saturn) in the ascendant -> asc-cusp-minutes / 21600 = asc_longitude/360;
    halved if a benefic aspects it (BPHS-43:369). asc_longitude is the ABSOLUTE cusp (the /21600
    divisor is the whole zodiac's minutes); the within-sign reading is the documented alternative."""
    if planet not in _KROORODAYA_MALEFICS or not in_lagna:
        return 0.0
    frac = (asc_longitude % 360.0) / 360.0
    return frac * 0.5 if benefic_aspect else frac


def is_longevity_benefic(planet: str) -> bool:
    """Moon, Mercury, Jupiter, Venus — Mercury always, even joined to a malefic (BPHS-43:291)."""
    return planet in _LONGEVITY_BENEFICS


def net_fraction(*fractions: float) -> float:
    """When several reductions apply to one planet, only the highest is taken (BPHS-43:392)."""
    return max((f for f in fractions if f > 0.0), default=0.0)


@dataclass(frozen=True)
class HaranaResult:
    planet: str
    astangata: float
    satru_kshetra: float
    vyayadi: float
    kroorodaya: float
    net: float               # the highest applicable — the one actually deducted
    reason: str              # which reduction won (for the reading's working)
