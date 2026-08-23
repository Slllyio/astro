"""Gulika (Mandi) — the chief non-luminous point, and its house effects (BPHS ch.25, ch.3).

Gulika deserves "special consideration in natal horoscopy" (BPHS-25:566). Its longitude is the
ascendant rising at the start of Saturn's eighth of the day (computed in `chart.ephemeris.
gulika_longitude`, BPHS-3:1303); its effect follows the house it occupies (BPHS-25:560, sl.62-73 —
Gulika in the ascendant..12th).

Effect text is read from the corpus in place, cited to its sloka line. Two of the twelve slokas had
their number destroyed by OCR (sl.68 house-7 as "6,8.", sl.72 house-11 with a junk prefix) and are
recovered by a hand-verified line repair. The Dhuma-family upagraha longitudes (ch.3 worked example
internally inconsistent) stay deferred — Gulika does not depend on that arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Final

from app.parashara.doctrine.corpus_index import slokas_of
from app.parashara.doctrine.sources import Citation, passage

_WORK: Final[str] = "BPHS-25"
#: house -> sloka number (62 = ascendant .. 73 = 12th house).
_SLOKA_FOR_HOUSE = {h: 61 + h for h in range(1, 13)}
#: OCR-number-dropped slokas, hand-verified to the real line (house -> 1-indexed line).
_REPAIR: Final[dict[int, int]] = {7: 652, 11: 711}


@dataclass(frozen=True)
class GulikaEffect:
    house: int
    text: str
    source: Citation


@lru_cache(maxsize=1)
def _by_house() -> dict[int, GulikaEffect]:
    by_num = {s.number: s for s in slokas_of(_WORK)}
    out: dict[int, GulikaEffect] = {}
    for house, num in _SLOKA_FOR_HOUSE.items():
        if house in _REPAIR:
            line = _REPAIR[house]
            p = passage(f"{_WORK}:{line}")
            text = (p or {}).get("text", "").strip()
            out[house] = GulikaEffect(house, text, Citation(_WORK, line))
        elif num in by_num:
            s = by_num[num]
            out[house] = GulikaEffect(house, s.text, s.source)
    return out


def effect_in_house(house: int) -> GulikaEffect | None:
    """Parashara's effect for Gulika occupying `house` (1..12), or None if unrecoverable (BPHS-25)."""
    if not 1 <= house <= 12:
        raise ValueError("house must be 1..12")
    return _by_house().get(house)
