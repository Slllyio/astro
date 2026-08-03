"""Panchanga limb suitability for elections — only what Raman's Muhurtha states.

The five limbs (MUHURTHA-2:77-89) with the book's own favourability rules:
- Tithi: "The 4th, 8th, 12th and 14th lunar days both in the bright and the dark half are
  unsuitable for undertaking any auspicious work" (MUHURTHA-2:202-204, AS PRINTED — the
  classical rikta triad elsewhere is 4/9/14; Raman's printed list here is 4/8/12/14 and is
  encoded verbatim, not "corrected").
- Vara: "Tuesday and Saturday should be invariably avoided for all good and auspicious
  work" (MUHURTHA-2:194-200).
- Nakshatra: per-person via Tarabala (electional.tarabala); inherently, "Bharani is
  condemned for all good work" (MUHURTHA-3:88-91).
- Yoga: the appendix's general bad list — Vyaghata, Parigha, Vajra, Vyatipata, Vydhruti,
  Ganda, Atiganda, Sula, Vishkambha (MUHURTHA-18:861-864).
- Karana: "Vishtikarana must invariably be discarded" (MUHURTHA-8:1171).

Limb values (tithi/vara/nakshatra/yoga/karana numbers) come from the existing
`app/core/panchanga.py` `compute_panchanga(jd)` — this module only CLASSIFIES them under
MUHURTHA citations (core's own S-2 doctrinal layer cites Phaladeepika/BPHS, which are not
citable in raman_saab; the classification tables here are Raman's, independent of it).

Usage:
    from app.raman_saab.electional.panchanga_suitability import limb_suitability
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.doctrine.sources import Citation

#: MUHURTHA-2:202-204 (verbatim; see module docstring). Applies within EACH paksha (1..15).
UNSUITABLE_TITHIS: Final[frozenset[int]] = frozenset({4, 8, 12, 14})

#: MUHURTHA-2:194-200 — weekday 0=Sunday .. 6=Saturday.
UNSUITABLE_VARAS: Final[frozenset[int]] = frozenset({2, 6})    # Tuesday, Saturday

#: MUHURTHA-3:88-91 — inherently condemned nakshatras (1-based; Bharani = 2).
CONDEMNED_NAKSHATRAS: Final[frozenset[int]] = frozenset({2})

#: MUHURTHA-18:861-864 — the nine generally-inauspicious nitya yogas, by their 1..27
#: numbers in the MUHURTHA-2:133-145 enumeration: Vishkambha 1, Atiganda 6, Sula 9,
#: Ganda 10, Vyaghata 13, Vajra 15, Vyatipata 17, Parigha 19, Vydhruti 27.
INAUSPICIOUS_YOGAS: Final[frozenset[int]] = frozenset({1, 6, 9, 10, 13, 15, 17, 19, 27})

#: MUHURTHA-8:1171 — Vishti is karana 7 in the MUHURTHA-2:151-160 enumeration.
DISCARDED_KARANAS: Final[frozenset[int]] = frozenset({7})


@dataclass(frozen=True)
class LimbVerdict:
    limb: str
    value: int
    suitable: bool
    source: Citation


def limb_suitability(*, tithi_in_paksha: int, weekday: int, nakshatra: int, yoga: int,
                     karana: int) -> tuple[LimbVerdict, ...]:
    """Classify the five limbs for an auspicious election, per Raman's stated rules only.
    `tithi_in_paksha` is 1..15; `weekday` 0=Sunday..6=Saturday; the rest 1-based."""
    return (
        LimbVerdict("tithi", tithi_in_paksha, tithi_in_paksha not in UNSUITABLE_TITHIS,
                    Citation("MUHURTHA-2", 202)),
        LimbVerdict("vara", weekday, weekday % 7 not in UNSUITABLE_VARAS,
                    Citation("MUHURTHA-2", 194)),
        LimbVerdict("nakshatra", nakshatra, nakshatra not in CONDEMNED_NAKSHATRAS,
                    Citation("MUHURTHA-3", 88)),
        LimbVerdict("yoga", yoga, yoga not in INAUSPICIOUS_YOGAS,
                    Citation("MUHURTHA-18", 861)),
        LimbVerdict("karana", karana, karana not in DISCARDED_KARANAS,
                    Citation("MUHURTHA-8", 1171)),
    )
