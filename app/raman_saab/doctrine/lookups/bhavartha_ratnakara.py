"""H12 — Bhavartha Ratnakara karaka-in-12th inversion list.

Raman (HTJAH-II:16543-16546): "There is a little known but practically
applicable dictum in Bhavartha Ratnakara bearing on the twelfth house.
According to it a person will be fortunate in respect of that house whose
karaka is situated in the 12th house from the Ascendant." The printed karaka
enumeration (HTJAH-II:16549-16564) is inverted here per planet: planet in the
12th -> fortunate re the bhava(s) it is karaka of.

Source fidelity notes (do NOT "fix" these):
  - The printed list assigns NO bhava to Mercury — ``Mercury -> None`` is
    faithful to the source, not an oversight.
  - The 4th-house row is OCR-truncated ("Matrubhava or 4th house — The",
    HTJAH-II:16552); the Moon is restored from the worked example at
    HTJAH-II:16566-16567 ("if the Moon is in the 12th house, in respect of
    the 4th house indications").
  - The Sun is printed as karaka of BOTH the 1st (16549) and the 9th (16561);
    the worked example reads the Sun-in-12th via the 9th (16564-16566).

Pure doctrine data returned as judge metadata — no scoring logic.

Data source: docs/raman_saab/methodology/house_12_vyaya.md (Main
Considerations, Bhavartha Ratnakara dictum), verified against the corpus.

Usage:
    from app.raman_saab.doctrine.lookups.bhavartha_ratnakara import (
        karaka_in_12_inversion
    )
    karaka_in_12_inversion("Sun")      # -> "fortunate in respect of the 9th ..."
    karaka_in_12_inversion("Mercury")  # -> None (no printed karaka role)
"""
from __future__ import annotations

from app.raman_saab.ordinals import ordinal

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class KarakaInversion:
    """One planet's karaka-in-12th inversion row.

    Fields
    ------
    planet : str
        One of the 7 visible planets (the dictum names no nodes).
    bhavas : tuple[int, ...]
        Houses this planet is printed karaka of (empty for Mercury).
    result : str | None
        Human-readable inversion ("fortunate in respect of ..."); None when
        the printed list assigns the planet no bhava.
    sources : tuple[Citation, ...]
        Corpus line(s) carrying the printed karaka assignment(s).
    note : str
        Source-fidelity caveat (OCR truncation / deliberate absence), if any.
    """
    planet: str
    bhavas: tuple[int, ...]
    result: str | None
    sources: tuple[Citation, ...]
    note: str = ""


def _ii(*lines: int) -> tuple[Citation, ...]:
    return tuple(Citation("HTJAH-II", ln) for ln in lines)


def _ordinal(house: int) -> str:
    return ordinal(house)


def _fortunate(*houses: int) -> str:
    joined = " and ".join(_ordinal(h) for h in houses)
    return f"fortunate in respect of the {joined} house indications"


# Planet in the 12th from Lagna -> fortunate re its own bhava(s)
# (HTJAH-II:16543-16569; printed karaka list at 16549-16564).
KARAKA_IN_12_INVERSIONS: Final[Mapping[str, KarakaInversion]] = MappingProxyType({
    "Sun": KarakaInversion(
        "Sun", (1, 9), _fortunate(1, 9), _ii(16549, 16561, 16566),
        note="Printed karaka of both Thanubhava (1st) and Pitrubhava (9th); "
             "the worked example reads Sun-in-12th via the 9th."),
    "Moon": KarakaInversion(
        "Moon", (4,), _fortunate(4), _ii(16552, 16566, 16567),
        note="Printed 4th-house row is OCR-truncated ('— The'); the Moon is "
             "restored from the worked example at 16566-16567."),
    "Mars": KarakaInversion(
        "Mars", (3,), _fortunate(3), _ii(16551)),
    "Mercury": KarakaInversion(
        "Mercury", (), None, _ii(16547, 16549),
        note="The printed list (16549-16564) assigns Mercury no bhava — "
             "None is faithful to the source, not an oversight."),
    "Jupiter": KarakaInversion(
        "Jupiter", (2, 5, 10, 11), _fortunate(2, 5, 10, 11),
        _ii(16550, 16553, 16562, 16563)),
    "Venus": KarakaInversion(
        "Venus", (7,), _fortunate(7), _ii(16555, 16568)),
    "Saturn": KarakaInversion(
        "Saturn", (6, 8, 12), _fortunate(6, 8, 12),
        _ii(16554, 16557, 16563, 16564)),
})


def karaka_in_12_inversion(planet: str) -> str | None:
    """Inversion result for a planet in the 12th from Lagna.

    Returns the "fortunate in respect of ..." reading, or None for Mercury
    (the printed list assigns it no bhava). The dictum covers only the 7
    visible planets; nodes or garbage raise ValueError.
    """
    record = KARAKA_IN_12_INVERSIONS.get(planet)
    if record is None:
        raise ValueError(
            f"Bhavartha Ratnakara dictum covers the 7 visible planets only, "
            f"got {planet!r}")
    return record.result
