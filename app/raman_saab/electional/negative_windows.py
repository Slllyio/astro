"""Negative time windows — Rahu Kalam, Durmuhurtha, thyajya, Panchaka (MUHURTHA).

Everything here is computed exactly as Raman's *Muhurtha* states it, cited per rule.
Deliberate omissions, per doctrine-first: **Yamagandam and Gulika Kalam are NOT encoded** —
neither appears anywhere in Raman's Muhurtha text (grep-verified over the full ingested
book, 2026-08-03); their definitions exist only in non-citable corpus works
(Kala Prakasika). If Raman didn't state it, this engine doesn't compute it.

All window functions are PURE — they take sunrise/sunset Julian days (or ghati offsets) and
return JD windows, so tests need no ephemeris. `app/raman_saab/chart/kala_context.py`
already computes sunrise/sunset via swe.rise_trans for callers that need them live.

Usage:
    from app.raman_saab.electional.negative_windows import (
        rahu_kalam, durmuhurtha_windows, lagna_thyajya, nakshatra_thyajya, panchaka)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.doctrine.sources import Citation

#: MUHURTHA-18:767-786 — Raman's printed Rahu Kalam table (sunrise 6 a.m. frame):
#: Sunday 4:30-6 p.m., Monday 7:30-9 a.m., Tuesday 3-4:30 p.m., Wednesday 12-1:30 p.m.,
#: Thursday 1:30-3 p.m., Friday 10:30 a.m.-12, Saturday 9-10:30 a.m. Expressed as the
#: 1-based EIGHTH of daylight each window occupies (weekday 0=Sunday .. 6=Saturday).
RAHU_KALAM_EIGHTH: Final[dict[int, int]] = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}

#: MUHURTHA-4:290-293 — diurnal muhurthas (of 15) inauspicious for all days.
DIURNAL_DURMUHURTHAS: Final[frozenset[int]] = frozenset({1, 2, 4, 10, 11, 12, 15})
#: MUHURTHA-4:292-293 — nocturnal muhurthas (of 15) inauspicious for all nights.
NOCTURNAL_DURMUHURTHAS: Final[frozenset[int]] = frozenset({1, 2, 6, 7})
#: MUHURTHA-4:312-320 — extra weekday-specific inauspicious DIURNAL muhurthas
#: (weekday 0=Sunday). "Wednesday, abhijit" = the 8th diurnal muhurtha (midday).
WEEKDAY_DURMUHURTHAS: Final[dict[int, frozenset[int]]] = {
    0: frozenset({14}), 1: frozenset({8, 12}), 2: frozenset({4, 11}), 3: frozenset({8}),
    4: frozenset({12, 13}), 5: frozenset({4, 8}), 6: frozenset({1, 2})}

#: MUHURTHA-2:170-193 — Lagna thyajya: the rejected half-ghati (12 min) per rising sign.
#: "first" / "middle" / "last" half-ghati of the sign's rise.
LAGNA_THYAJYA_PART: Final[dict[int, str]] = {
    1: "first", 2: "first", 9: "first", 6: "first",          # bhujanga (serpent)
    12: "last", 10: "last", 4: "last", 8: "last",            # Rahu
    3: "middle", 7: "middle", 5: "middle", 11: "middle"}     # Gridhra

#: MUHURTHA-2:205-215 — per-nakshatra thyajya kala: start ghati (from the constellation's
#: commencement), lasting 4 ghatis. AS PRINTED in the ingested text; the Bharani (4) and
#: Purvabhadra (10) cells are OCR-fragile in this scan and were encoded verbatim, not
#: "corrected" against any other authority.
NAKSHATRA_THYAJYA_START_GHATI: Final[tuple[int, ...]] = (
    50, 4, 30, 40, 14, 21, 30, 20, 32,      # Aswini..Aslesha
    30, 20, 1, 21, 20, 14, 14, 10, 14,      # Makha..Jyeshta
    20, 20, 20, 10, 10, 18, 10, 30, 30)     # Moola..Revati
THYAJYA_SPAN_GHATIS: Final[int] = 4

#: MUHURTHA-3:104-117 — Panchaka remainders and their names.
_PANCHAKA_NAMES: Final[dict[int, str]] = {
    1: "mrityu", 2: "agni", 4: "raja", 6: "chora", 8: "roga"}
#: MUHURTHA-3:157-168 — which panchaka each election type must avoid.
PANCHAKA_AVOID_BY_ACT: Final[dict[str, frozenset[str]]] = {
    "occupation": frozenset({"raja"}),
    "housebuilding": frozenset({"raja", "agni"}),
    "travel": frozenset({"chora"}),
    "marriage": frozenset({"roga", "mrityu"}),
    "upanayanam": frozenset({"roga", "mrityu"}),
}

_GHATI_DAYS: Final[float] = 1.0 / 60.0     # one ghati = 24 minutes = 1/60 day


@dataclass(frozen=True)
class Window:
    start_jd: float
    end_jd: float
    label: str
    source: Citation


@dataclass(frozen=True)
class PanchakaResult:
    remainder: int
    name: Optional[str]        # None when favourable (remainder 0, 3, 5, 7)
    favourable: bool
    source: Citation


def rahu_kalam(weekday: int, sunrise_jd: float, sunset_jd: float) -> Window:
    """The day's Rahu Kalam window — the printed eighth of daylight (MUHURTHA-18:767-786).
    `weekday`: 0=Sunday .. 6=Saturday."""
    eighth = RAHU_KALAM_EIGHTH[weekday % 7]
    span = (sunset_jd - sunrise_jd) / 8.0
    start = sunrise_jd + (eighth - 1) * span
    return Window(start, start + span, "Rahu Kalam", Citation("MUHURTHA-18", 767))


def durmuhurtha_windows(weekday: int, sunrise_jd: float, sunset_jd: float,
                        next_sunrise_jd: float) -> tuple[Window, ...]:
    """All inauspicious muhurthas of one day+night (MUHURTHA-4:276-320): the sidereal day
    holds 30 muhurthas — 15 diurnal, 15 nocturnal — each 1/15 of the actual day (or night)
    length; the general bad sets plus the weekday's own rejected diurnal muhurthas."""
    out: list[Window] = []
    day_span = (sunset_jd - sunrise_jd) / 15.0
    bad_day = DIURNAL_DURMUHURTHAS | WEEKDAY_DURMUHURTHAS[weekday % 7]
    for m in sorted(bad_day):
        start = sunrise_jd + (m - 1) * day_span
        out.append(Window(start, start + day_span, f"Durmuhurtha (diurnal {m})",
                          Citation("MUHURTHA-4", 290)))
    night_span = (next_sunrise_jd - sunset_jd) / 15.0
    for m in sorted(NOCTURNAL_DURMUHURTHAS):
        start = sunset_jd + (m - 1) * night_span
        out.append(Window(start, start + night_span, f"Durmuhurtha (nocturnal {m})",
                          Citation("MUHURTHA-4", 292)))
    return tuple(out)


def lagna_thyajya(sign: int, rise_start_jd: float, rise_end_jd: float) -> Window:
    """The rejected half-ghati of a rising sign (MUHURTHA-2:170-193): first (bhujanga) /
    middle (Gridhra) / last (Rahu) 12 minutes of the sign's own rise."""
    part = LAGNA_THYAJYA_PART[sign]
    half_ghati = _GHATI_DAYS / 2.0
    if part == "first":
        start = rise_start_jd
    elif part == "last":
        start = rise_end_jd - half_ghati
    else:
        mid = (rise_start_jd + rise_end_jd) / 2.0
        start = mid - half_ghati / 2.0
    return Window(start, start + half_ghati, f"Lagna thyajya ({part})",
                  Citation("MUHURTHA-2", 170))


def nakshatra_thyajya(nakshatra: int, nak_start_jd: float) -> Window:
    """The constellation's thyajya kala (MUHURTHA-2:205-215): starts at the printed ghati
    from the nakshatra's commencement, lasts 4 ghatis."""
    start = nak_start_jd + NAKSHATRA_THYAJYA_START_GHATI[nakshatra - 1] * _GHATI_DAYS
    return Window(start, start + THYAJYA_SPAN_GHATIS * _GHATI_DAYS,
                  "Nakshatra thyajya", Citation("MUHURTHA-2", 205))


def panchaka(tithi: int, weekday: int, nakshatra: int, lagna_sign: int,
             act: Optional[str] = None) -> PanchakaResult:
    """Raman's Panchaka (MUHURTHA-3:104-168): (tithi# + weekday# + nakshatra# + lagna#) / 9;
    remainder 1 mrityu, 2 agni, 4 raja, 6 chora, 8 roga; 0/3/5/7 favourable. Worked example:
    13th tithi + Sunday(1) + Aslesha(9) + Virgo(6) = 29 -> remainder 2 = agni
    (MUHURTHA-3:118-142). `weekday` here is Raman's 1-based count (Sunday=1).

    With `act` given, an unfavourable remainder counts favourable UNLESS it is in that
    election type's own avoid-set (MUHURTHA-3:157-168) — Raman's per-activity exception."""
    total = tithi + weekday + nakshatra + lagna_sign
    rem = total % 9
    name = _PANCHAKA_NAMES.get(rem)
    if name is None:
        fav = True
    elif act is not None and act in PANCHAKA_AVOID_BY_ACT:
        fav = name not in PANCHAKA_AVOID_BY_ACT[act]
    else:
        fav = False
    return PanchakaResult(rem, name, fav, Citation("MUHURTHA-3", 104))
