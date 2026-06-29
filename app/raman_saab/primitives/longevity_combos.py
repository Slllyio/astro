"""Qualitative longevity combinations — Alpayu / Madhyayu / Purnayu (How to Judge a Horoscope Vol II,
HTJAH-II:3251-3474). Raman's COMBINATION-based longevity judgment, complementing the mathematical
ayurdaya span the engine already computes. Reports which cited combinations fire and the longevity
class each indicates. ADDITIVE / reported — verdict-invariant.

Only the cleanly-evaluable combinations (simple placements/dignities) are encoded; the navamsa- and
aspect-chain death-age combos in the same lists remain a documented backlog.

Usage:
    from app.raman_saab.primitives import longevity_combos as lc
    lc.fired(chart)   # -> [(class, span, description), ...]
"""
from __future__ import annotations

from typing import Callable, Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.dignity import dignity

_MALEFICS: Final[tuple[str, ...]] = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury", "Moon")
_SEVEN: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})


def _rh(chart: RamanChart, p: str) -> int | None:
    pp = chart.planets.get(p)
    return pp.rasi_house if pp else None


def _all_in(chart: RamanChart, planets: tuple[str, ...], house: int) -> bool:
    return all(_rh(chart, p) == house for p in planets)


def _occupants(chart: RamanChart, house: int) -> list[str]:
    return [n for n, p in chart.planets.items() if p.rasi_house == house]


def _house_has_malefic(chart: RamanChart, house: int) -> bool:
    return any(_rh(chart, m) == house for m in _MALEFICS)


# Alpayu (8-32) -------------------------------------------------------------------------------------
def _alpayu_sun_moon_mars_5th(c: RamanChart) -> bool:
    return _all_in(c, ("Sun", "Moon", "Mars"), 5)


def _alpayu_sun_moon_saturn_8th(c: RamanChart) -> bool:
    return _all_in(c, ("Sun", "Moon", "Saturn"), 8)


# Madhyayu (32-75) ----------------------------------------------------------------------------------
def _madhya_malefics_spread(c: RamanChart) -> bool:
    return all(_house_has_malefic(c, h) for h in (2, 3, 4, 5, 8, 11))


def _madhya_all_seven_in_5th(c: RamanChart) -> bool:
    present = [p for p in _SEVEN if p in c.planets]
    return len(present) == 7 and all(_rh(c, p) == 5 for p in present)


# Purnayu (75-120) ----------------------------------------------------------------------------------
def _purna_three_in_8th_dignified(c: RamanChart) -> bool:
    digs = {dignity(p, c) for p in _occupants(c, 8) if p not in ("Rahu", "Ketu")}
    return len(_occupants(c, 8)) >= 3 and {"exalt", "own"} <= digs and (
        "friend" in digs or "moolatrikona" in digs)


def _purna_saturn_or_8thlord_with_exalt(c: RamanChart) -> bool:
    eighth_lord = SIGN_LORDS[((c.asc_sign - 1) + 7) % 12 + 1]
    for key in ("Saturn", eighth_lord):
        kp = c.planets.get(key)
        if kp is None:
            continue
        if any(n != key and p.rasi_house == kp.rasi_house and dignity(n, c) == "exalt"
               for n, p in c.planets.items()):
            return True
    return False


#: (class, span, citation-line, predicate, description)
_COMBOS: Final[tuple[tuple[str, str, int, Callable[[RamanChart], bool], str], ...]] = (
    ("Alpayu", "8-32y", 3257, _alpayu_sun_moon_mars_5th,
     "Sun, Moon and Mars together in the 5th"),
    ("Alpayu", "8-32y", 3309, _alpayu_sun_moon_saturn_8th,
     "Sun, Moon and Saturn conjoined in the 8th"),
    ("Madhyayu", "32-75y", 3350, _madhya_malefics_spread,
     "malefics occupy the 2nd, 3rd, 4th, 5th, 8th and 11th"),
    ("Madhyayu", "32-75y", 3394, _madhya_all_seven_in_5th,
     "all the planets in the 5th house"),
    ("Purnayu", "75-120y", 3406, _purna_three_in_8th_dignified,
     "three planets in the 8th in exaltation, own and friendly signs"),
    ("Purnayu", "75-120y", 3408, _purna_saturn_or_8thlord_with_exalt,
     "Saturn or the 8th lord conjoined with an exalted planet"),
)


def fired(chart: RamanChart) -> list[tuple[str, str, str]]:
    """(class, span, description) for each encoded longevity combination that holds."""
    return [(cls, span, desc) for cls, span, _line, pred, desc in _COMBOS if pred(chart)]
