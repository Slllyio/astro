"""Qualitative longevity combinations — Alpayu / Madhyayu / Purnayu (How to Judge a Horoscope Vol II,
HTJAH-II:3251-3474). Raman's COMBINATION-based longevity judgment, complementing the mathematical
ayurdaya span the engine already computes. Reports which cited combinations fire and the longevity
class each indicates. ADDITIVE / reported — verdict-invariant.

Only the cleanly-evaluable combinations (placements, dignities and whole-sign graha aspects) are
encoded; the navamsa-based and strength-gated (weak/strong "in vargas") death-age combos in the same
lists remain a documented backlog.

Usage:
    from app.raman_saab.primitives import longevity_combos as lc
    lc.fired(chart)   # -> [(class, span, description), ...]
"""
from __future__ import annotations

from typing import Callable, Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.drishti import aspects_planet
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.sign_attributes import is_keeta

_MALEFICS: Final[tuple[str, ...]] = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury", "Moon")
_NAT_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury")
_SEVEN: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_PANAPHARAS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_APOKLIMAS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})
_TRIKONAS: Final[frozenset[int]] = frozenset({1, 5, 9})


def _rh(chart: RamanChart, p: str) -> int | None:
    pp = chart.planets.get(p)
    return pp.rasi_house if pp else None


def _all_in(chart: RamanChart, planets: tuple[str, ...], house: int) -> bool:
    return all(_rh(chart, p) == house for p in planets)


def _occupants(chart: RamanChart, house: int) -> list[str]:
    return [n for n, p in chart.planets.items() if p.rasi_house == house]


def _house_has_malefic(chart: RamanChart, house: int) -> bool:
    return any(_rh(chart, m) == house for m in _MALEFICS)


def _lord_of(chart: RamanChart, house: int) -> str:
    """Sign-lord of the whole-sign `house` reckoned from the Lagna."""
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _sign_of(chart: RamanChart, planet: str) -> int | None:
    pp = chart.planets.get(planet)
    return pp.sign if pp else None


def _dignity_is(chart: RamanChart, planet: str, *names: str) -> bool:
    """`planet` is present AND its compound dignity is one of `names` (safe for an absent lord)."""
    return planet in chart.planets and dignity(planet, chart) in names


def _present(chart: RamanChart, planets: tuple[str, ...]) -> list[str]:
    return [p for p in planets if p in chart.planets]


def _conj_or_aspected(chart: RamanChart, by: str, lord: str) -> bool:
    """`lord` is conjoined with, or aspected by, `by` — or the lord itself IS `by`."""
    if by not in chart.planets or lord not in chart.planets:
        return False
    if by == lord:
        return True
    return _rh(chart, by) == _rh(chart, lord) or aspects_planet(by, lord, chart)


def _group_all_in(chart: RamanChart, group: tuple[str, ...], houses: frozenset[int]) -> bool:
    """Every present member of `group` occupies one of `houses` (group must be non-empty)."""
    members = [g for g in group if g in chart.planets]
    return bool(members) and all(_rh(chart, g) in houses for g in members)


# Alpayu (8-32) -------------------------------------------------------------------------------------
def _alpayu_sun_moon_mars_5th(c: RamanChart) -> bool:
    return _all_in(c, ("Sun", "Moon", "Mars"), 5)


def _alpayu_moon_leo_sunsat_8th_venus_2nd(c: RamanChart) -> bool:
    return (_sign_of(c, "Moon") == 5 and _rh(c, "Sun") == 8
            and _rh(c, "Saturn") == 8 and _rh(c, "Venus") == 2)


def _alpayu_mars_jup_lagna_moon_7th_8th_tenanted(c: RamanChart) -> bool:
    return (_rh(c, "Mars") == 1 and _rh(c, "Jupiter") == 1
            and _rh(c, "Moon") == 7 and bool(_occupants(c, 8)))


def _alpayu_lord1_lord8_9th_planet8_afflicted(c: RamanChart) -> bool:
    if _rh(c, _lord_of(c, 1)) != 1 or _rh(c, _lord_of(c, 8)) != 9:
        return False
    return any(aspects_planet(m, occ, c) for occ in _occupants(c, 8)
               for m in _MALEFICS if m in c.planets)


def _alpayu_mars_lagna_sun_saturn_kendras(c: RamanChart) -> bool:
    return (_rh(c, "Mars") == 1 and _rh(c, "Sun") in _KENDRAS
            and _rh(c, "Saturn") in _KENDRAS)


def _alpayu_saturn_lagna_enemy_benefics_apoklima(c: RamanChart) -> bool:
    bens = _present(c, _BENEFICS)
    return (_rh(c, "Saturn") == 1 and _dignity_is(c, "Saturn", "enemy")
            and bool(bens) and all(_rh(c, b) in _APOKLIMAS for b in bens))


def _alpayu_sun_lagna_hemmed_by_malefics(c: RamanChart) -> bool:
    return _rh(c, "Sun") == 1 and _house_has_malefic(c, 2) and _house_has_malefic(c, 12)


def _alpayu_no_benefic_kendra_8th_tenanted(c: RamanChart) -> bool:
    return (not any(_rh(c, b) in _KENDRAS for b in _BENEFICS if b in c.planets)
            and bool(_occupants(c, 8)))


def _alpayu_sun_moon_saturn_8th(c: RamanChart) -> bool:
    return _all_in(c, ("Sun", "Moon", "Saturn"), 8)


def _alpayu_malefic_lagna_moon_with_malefic_no_benefic_aspect(c: RamanChart) -> bool:
    moon = c.planets.get("Moon")
    if moon is None or not _house_has_malefic(c, 1):
        return False
    moon_with_malefic = any(_rh(c, m) == moon.rasi_house for m in _MALEFICS)
    no_benefic_aspect = not any(b in c.planets and aspects_planet(b, "Moon", c)
                                for b in _NAT_BENEFICS)
    return moon_with_malefic and no_benefic_aspect


# Madhyayu (32-75) ----------------------------------------------------------------------------------
def _madhya_malefics_spread(c: RamanChart) -> bool:
    return all(_house_has_malefic(c, h) for h in (2, 3, 4, 5, 8, 11))


def _madhya_malefic_8th_saturn_6th_benefic_trine_kendra(c: RamanChart) -> bool:
    good = _KENDRAS | _TRIKONAS
    return (_house_has_malefic(c, 8) and _rh(c, "Saturn") == 6
            and any(_rh(c, b) in good for b in _BENEFICS if b in c.planets))


def _madhya_benefic_7th_moon_lagna_or_cancer(c: RamanChart) -> bool:
    moon = c.planets.get("Moon")
    benefic_7th = any(_rh(c, b) == 7 for b in _BENEFICS if b in c.planets)
    return benefic_7th and moon is not None and (moon.rasi_house == 1 or moon.sign == 4)


def _madhya_lord8_lagna_8th_no_benefic(c: RamanChart) -> bool:
    return (_rh(c, _lord_of(c, 8)) == 1
            and not any(_rh(c, b) == 8 for b in _BENEFICS if b in c.planets))


def _madhya_moon_dusthana_mercury_kendra_venus_jupiter(c: RamanChart) -> bool:
    moon = c.planets.get("Moon")
    venus, jupiter = _rh(c, "Venus"), _rh(c, "Jupiter")
    return (moon is not None and moon.rasi_house in {1, 8, 12}
            and _rh(c, "Mercury") in {4, 10}
            and venus is not None and jupiter is not None and venus == jupiter)


def _madhya_all_seven_in_5th(c: RamanChart) -> bool:
    present = [p for p in _SEVEN if p in c.planets]
    return len(present) == 7 and all(_rh(c, p) == 5 for p in present)


def _madhya_benefics_own_moon_exalt_lagna(c: RamanChart) -> bool:
    if not all(b in c.planets for b in _NAT_BENEFICS):
        return False
    benefics_own = all(dignity(b, c) in ("own", "moolatrikona") for b in _NAT_BENEFICS)
    moon = c.planets.get("Moon")
    return benefics_own and moon is not None and moon.rasi_house == 1 and dignity("Moon", c) == "exalt"


# Purnayu (75-120) ----------------------------------------------------------------------------------
def _purna_benefics_kendra_lord_supported(c: RamanChart) -> bool:
    # "benefics occupy kendras" is plural — require >=2 benefics in kendras (a single benefic in an
    # angle over-fires: ~45% of charts; the plural reading is both faithful and discriminating).
    ben_kendra = sum(1 for b in _BENEFICS if b in c.planets and c.planets[b].rasi_house in _KENDRAS) >= 2
    lord = SIGN_LORDS[c.asc_sign]
    lp = c.planets.get(lord)
    if not (ben_kendra and lp is not None):
        return False
    lord_with_ben = any(n in _BENEFICS and n != lord and p.rasi_house == lp.rasi_house
                        for n, p in c.planets.items())
    return lord_with_ben or aspects_planet("Jupiter", lord, c)


def _purna_lord1_kendra_malefics_6_12(c: RamanChart) -> bool:
    return (_rh(c, _lord_of(c, 1)) in _KENDRAS
            and _house_has_malefic(c, 12) and _house_has_malefic(c, 6))


def _purna_lord10_exalt_malefic_8th(c: RamanChart) -> bool:
    return _dignity_is(c, _lord_of(c, 10), "exalt") and _house_has_malefic(c, 8)


def _purna_malefics_upachaya_benefics_678(c: RamanChart) -> bool:
    bens = _present(c, _BENEFICS)
    return (all(_house_has_malefic(c, h) for h in (3, 6, 11))
            and bool(bens) and all(_rh(c, b) in {6, 7, 8} for b in bens))


def _purna_lord1_kendra_supported_venus_jupiter(c: RamanChart) -> bool:
    lord = _lord_of(c, 1)
    if _rh(c, lord) not in _KENDRAS:
        return False
    return _conj_or_aspected(c, "Venus", lord) and _conj_or_aspected(c, "Jupiter", lord)


def _purna_lord1_lord8_in_8_or_11(c: RamanChart) -> bool:
    return _rh(c, _lord_of(c, 1)) in {8, 11} and _rh(c, _lord_of(c, 8)) in {8, 11}


def _purna_saturn_with_1_10_8_lords_kendra(c: RamanChart) -> bool:
    sat = _rh(c, "Saturn")
    if sat is None or sat not in _KENDRAS:
        return False
    return all(_rh(c, _lord_of(c, h)) == sat for h in (1, 10, 8))


def _purna_lord8_own_or_saturn_8th(c: RamanChart) -> bool:
    return _dignity_is(c, _lord_of(c, 8), "own") or _rh(c, "Saturn") == 8


def _purna_three_in_8th_dignified(c: RamanChart) -> bool:
    digs = {dignity(p, c) for p in _occupants(c, 8) if p not in ("Rahu", "Ketu")}
    return len(_occupants(c, 8)) >= 3 and {"exalt", "own"} <= digs and (
        "friend" in digs or "moolatrikona" in digs)


def _purna_benefics_5_9_keeta_lagna_jupiter(c: RamanChart) -> bool:
    return (any(_rh(c, b) == 5 for b in _BENEFICS if b in c.planets)
            and any(_rh(c, b) == 9 for b in _BENEFICS if b in c.planets)
            and is_keeta(c.asc_sign) and _rh(c, "Jupiter") == 1)


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


def _purna_all_seven_in_9th(c: RamanChart) -> bool:
    present = [p for p in _SEVEN if p in c.planets]
    return len(present) == 7 and all(_rh(c, p) == 9 for p in present)


def _purna_saturn_1_9_moon_12_9(c: RamanChart) -> bool:
    moon = c.planets.get("Moon")
    return _rh(c, "Saturn") in {1, 9} and moon is not None and moon.rasi_house in {12, 9}


# Aggregate (3469-3474) — the section's closing classifier. The Lagna-lord-and-benefics group
# maps kendra/panaphara/apoklima -> long/medium/short; the 8th-lord-and-malefics group maps them
# REVERSED -> short/medium/long. Each variant is a strict all-aligned predicate (rarely fires).
def _agg_benefics_kendra(c: RamanChart) -> bool:
    return _group_all_in(c, (_lord_of(c, 1), *_BENEFICS), _KENDRAS)


def _agg_benefics_panaphara(c: RamanChart) -> bool:
    return _group_all_in(c, (_lord_of(c, 1), *_BENEFICS), _PANAPHARAS)


def _agg_benefics_apoklima(c: RamanChart) -> bool:
    return _group_all_in(c, (_lord_of(c, 1), *_BENEFICS), _APOKLIMAS)


def _agg_malefics_kendra(c: RamanChart) -> bool:
    return _group_all_in(c, (_lord_of(c, 8), *_MALEFICS), _KENDRAS)


def _agg_malefics_panaphara(c: RamanChart) -> bool:
    return _group_all_in(c, (_lord_of(c, 8), *_MALEFICS), _PANAPHARAS)


def _agg_malefics_apoklima(c: RamanChart) -> bool:
    return _group_all_in(c, (_lord_of(c, 8), *_MALEFICS), _APOKLIMAS)


#: (class, span, citation-line, predicate, description)
_COMBOS: Final[tuple[tuple[str, str, int, Callable[[RamanChart], bool], str], ...]] = (
    # ----- Alpayu (8-32y) -----
    ("Alpayu", "8-32y", 3257, _alpayu_sun_moon_mars_5th,
     "Sun, Moon and Mars together in the 5th"),
    ("Alpayu", "8-32y", 3266, _alpayu_moon_leo_sunsat_8th_venus_2nd,
     "the Moon in Leo with the Sun and Saturn in the 8th and Venus in the 2nd"),
    ("Alpayu", "8-32y", 3285, _alpayu_mars_jup_lagna_moon_7th_8th_tenanted,
     "Mars and Jupiter in the Lagna, the Moon in the 7th and the 8th house tenanted"),
    ("Alpayu", "8-32y", 3289, _alpayu_lord1_lord8_9th_planet8_afflicted,
     "the Lagna lord in the Lagna, the 8th lord in the 9th and a planet in the 8th aspected by a malefic"),
    ("Alpayu", "8-32y", 3297, _alpayu_mars_lagna_sun_saturn_kendras,
     "Mars in the Lagna and the Sun and Saturn in quadrants"),
    ("Alpayu", "8-32y", 3303, _alpayu_saturn_lagna_enemy_benefics_apoklima,
     "Saturn in the Lagna in an inimical sign and the benefics in the 3rd, 6th, 9th or 12th"),
    ("Alpayu", "8-32y", 3309, _alpayu_sun_moon_saturn_8th,
     "Sun, Moon and Saturn conjoined in the 8th"),
    ("Alpayu", "8-32y", 3323, _alpayu_sun_lagna_hemmed_by_malefics,
     "the Sun in the Lagna hemmed in between malefics"),
    ("Alpayu", "8-32y", 3326, _alpayu_no_benefic_kendra_8th_tenanted,
     "no benefics in the kendras and the 8th house tenanted"),
    ("Alpayu", "8-32y", 3333, _alpayu_malefic_lagna_moon_with_malefic_no_benefic_aspect,
     "the Lagna held by malefics and the Moon with malefics, unaspected by benefics"),
    # ----- Madhyayu (32-75y) -----
    ("Madhyayu", "32-75y", 3347, _madhya_malefic_8th_saturn_6th_benefic_trine_kendra,
     "a malefic in the 8th, Saturn in the 6th and a benefic in a trine or quadrant"),
    ("Madhyayu", "32-75y", 3350, _madhya_malefics_spread,
     "malefics occupy the 2nd, 3rd, 4th, 5th, 8th and 11th"),
    ("Madhyayu", "32-75y", 3370, _madhya_benefic_7th_moon_lagna_or_cancer,
     "a benefic in the 7th and the Moon in the Lagna or in Cancer"),
    ("Madhyayu", "32-75y", 3382, _madhya_lord8_lagna_8th_no_benefic,
     "the 8th lord in the Lagna and no benefic in the 8th"),
    ("Madhyayu", "32-75y", 3385, _madhya_moon_dusthana_mercury_kendra_venus_jupiter,
     "the Moon in the 1st, 8th or 12th, Mercury in the 4th or 10th and Venus with Jupiter"),
    ("Madhyayu", "32-75y", 3394, _madhya_all_seven_in_5th,
     "all the planets in the 5th house"),
    ("Madhyayu", "32-75y", 3397, _madhya_benefics_own_moon_exalt_lagna,
     "benefics in their own signs and the Moon exalted in the Lagna"),
    # ----- Purnayu (75-120y) -----
    ("Purnayu", "75-120y", 3404, _purna_benefics_kendra_lord_supported,
     "benefics in kendras and the Lagna lord joined by, or aspected by, a benefic/Jupiter"),
    ("Purnayu", "75-120y", 3406, _purna_three_in_8th_dignified,
     "three planets in the 8th in exaltation, own and friendly signs"),
    ("Purnayu", "75-120y", 3408, _purna_saturn_or_8thlord_with_exalt,
     "Saturn or the 8th lord conjoined with an exalted planet"),
    ("Purnayu", "75-120y", 3418, _purna_lord1_kendra_malefics_6_12,
     "the Lagna lord in a quadrant and malefics in the 12th and the 6th"),
    ("Purnayu", "75-120y", 3422, _purna_lord10_exalt_malefic_8th,
     "the 10th lord exalted and malefics in the 8th"),
    ("Purnayu", "75-120y", 3425, _purna_malefics_upachaya_benefics_678,
     "malefics in the 3rd, 6th and 11th and benefics grouped in the 6th, 7th or 8th"),
    ("Purnayu", "75-120y", 3429, _purna_lord1_kendra_supported_venus_jupiter,
     "the Lagna lord in a kendra, joined or aspected by both Venus and Jupiter"),
    ("Purnayu", "75-120y", 3433, _purna_lord1_lord8_in_8_or_11,
     "the Lagna and 8th lords in the 8th or the 11th"),
    ("Purnayu", "75-120y", 3436, _purna_saturn_with_1_10_8_lords_kendra,
     "Saturn joined with the 1st, 10th and 8th lords in a kendra"),
    ("Purnayu", "75-120y", 3439, _purna_lord8_own_or_saturn_8th,
     "the 8th lord in its own sign, or Saturn in the 8th"),
    ("Purnayu", "75-120y", 3448, _purna_benefics_5_9_keeta_lagna_jupiter,
     "benefics in the 5th and 9th with a Keeta-rasi Lagna occupied by Jupiter"),
    ("Purnayu", "75-120y", 3452, _purna_all_seven_in_9th,
     "all the planets in the 9th house"),
    ("Purnayu", "75-120y", 3466, _purna_saturn_1_9_moon_12_9,
     "Saturn in the 1st or 9th and the Moon in the 12th or 9th"),
    # ----- Aggregate classifier (3469-3474) -----
    ("Purnayu", "75-120y", 3469, _agg_benefics_kendra,
     "the Lagna lord and all benefics in kendras"),
    ("Madhyayu", "32-75y", 3469, _agg_benefics_panaphara,
     "the Lagna lord and all benefics in panapharas"),
    ("Alpayu", "8-32y", 3469, _agg_benefics_apoklima,
     "the Lagna lord and all benefics in apoklimas"),
    ("Alpayu", "8-32y", 3472, _agg_malefics_kendra,
     "the 8th lord and all malefics in kendras"),
    ("Madhyayu", "32-75y", 3472, _agg_malefics_panaphara,
     "the 8th lord and all malefics in panapharas"),
    ("Purnayu", "75-120y", 3472, _agg_malefics_apoklima,
     "the 8th lord and all malefics in apoklimas"),
)


def fired(chart: RamanChart) -> list[tuple[str, str, str]]:
    """(class, span, description) for each encoded longevity combination that holds."""
    return [(cls, span, desc) for cls, span, _line, pred, desc in _COMBOS if pred(chart)]
