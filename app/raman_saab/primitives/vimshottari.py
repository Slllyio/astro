"""Vimshottari Dasha — the event-timing layer.

The 120-year Vimshottari cycle is the spine of Vedic event prediction: it sequences
the planetary Mahadasha (major period) and Bhukti (sub-period) lords across a life, so
a NATAL verdict ("the 8th is afflicted") can be projected onto TIME ("the maraka period
runs 1962-1966"). This is what lets the engine reason about *when* a significator's
results manifest — the layer the placement-only judges deliberately lacked.

Sequence + weights (the canonical Vimshottari order, 120 years total):
    Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17.

The birth Mahadasha lord + elapsed fraction come from the Moon's nakshatra (reusing the
main engine's ``calculate_vimshottari_mahadasha``). The full timeline is then unrolled
forward in **Julian-Day space** (``birth_jd ± years * 365.2425``; never
``datetime.timedelta`` — see CLAUDE.md), and a Bhukti subdivides its Mahadasha
proportionally (``Bhukti_years = MD_years * bhukti_lord_years / 120``), ordered from the
MD lord onward.

Validated against Raman's dated deaths (``tests/raman_saab/test_vimshottari.py``): the
running Mahadasha at the death date reproduces Raman's stated period for every dated
death golden (Lincoln Saturn/Mercury, Hitler Rahu/Moon match to the Bhukti).

Usage:
    from app.raman_saab.primitives.vimshottari import dasha_on, date_to_jd
    period = dasha_on(chart, date_to_jd(1966, 2, 7))   # -> DashaPeriod(maha='Rahu', antar=...)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final, Optional

import swisseph as swe

from app.core.ephemeris_engine import (
    DASHA_LORDS, DAYS_PER_VEDIC_YEAR, calculate_vimshottari_mahadasha)
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives import dignity as _dignity
from app.raman_saab.primitives.shadbala import total as _shadbala_total

_LORD_YEARS: Final[dict[str, int]] = dict(DASHA_LORDS)
_SEQUENCE: Final[tuple[str, ...]] = tuple(name for name, _ in DASHA_LORDS)
_TOTAL_YEARS: Final[int] = 120


@dataclass(frozen=True)
class DashaPeriod:
    """A running period: its Mahadasha lord, its Bhukti (antar) lord (None for an
    MD-level span), its [start, end) bounds in Julian Days, and — when the span is a
    Pratyantardasha (sub-sub-period) — its Pratyantar lord (None for MD/Bhukti-level
    spans, so every existing 4-argument construction is unchanged)."""
    maha: str
    antar: Optional[str]
    start_jd: float
    end_jd: float
    pratyantar: Optional[str] = None

    def contains(self, jd: float) -> bool:
        return self.start_jd <= jd < self.end_jd


def date_to_jd(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """Gregorian calendar date -> Julian Day (Swiss Ephemeris, GREG_CAL)."""
    return swe.julday(year, month, day, hour, swe.GREG_CAL)


def _sequence_from(lord: str) -> list[str]:
    """The 9-lord Vimshottari cycle rotated to begin with `lord`."""
    i = _SEQUENCE.index(lord)
    return [_SEQUENCE[(i + offset) % 9] for offset in range(9)]


def mahadasha_timeline(chart: RamanChart, span_years: float = 140.0) -> list[DashaPeriod]:
    """The Mahadasha sequence from the birth MD's true start, unrolled `span_years`
    forward (>= a full 120-year cycle, so it covers any realistic lifespan). The first
    MD began BEFORE birth; ``time_elapsed_years`` of it had already run at birth."""
    md = calculate_vimshottari_mahadasha(chart.planets["Moon"].lon, chart.jd_ut)
    lord = md["mahadasha_lord"]
    md_start = chart.jd_ut - md["time_elapsed_years"] * DAYS_PER_VEDIC_YEAR
    periods: list[DashaPeriod] = []
    cursor, accrued, idx = md_start, 0.0, 0
    sequence = _sequence_from(lord)
    while accrued < span_years:
        lord_i = sequence[idx % 9]
        years = _LORD_YEARS[lord_i]
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        periods.append(DashaPeriod(lord_i, None, cursor, end))
        cursor, accrued, idx = end, accrued + years, idx + 1
    return periods


def bhuktis(md: DashaPeriod) -> list[DashaPeriod]:
    """The 9 Bhuktis (antardashas) of a Mahadasha, proportional and ordered from the MD
    lord onward."""
    total_years = (md.end_jd - md.start_jd) / DAYS_PER_VEDIC_YEAR
    out: list[DashaPeriod] = []
    cursor = md.start_jd
    for antar in _sequence_from(md.maha):
        years = total_years * _LORD_YEARS[antar] / _TOTAL_YEARS
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        out.append(DashaPeriod(md.maha, antar, cursor, end))
        cursor = end
    return out


def dasha_on(chart: RamanChart, jd: float) -> Optional[DashaPeriod]:
    """The (Mahadasha, Bhukti) period running on Julian Day `jd`, or None if `jd` falls
    outside the unrolled timeline."""
    for md in mahadasha_timeline(chart):
        if md.contains(jd):
            for bh in bhuktis(md):
                if bh.contains(jd):
                    return bh
            return md
    return None


def pratyantars(bh: DashaPeriod) -> list[DashaPeriod]:
    """The 9 Pratyantardashas (sub-sub-periods) of a Bhukti, proportional and ordered
    from the Bhukti lord onward — the SAME ``lord_years / 120`` split ``bhuktis()``
    applies one level up, in JD space (HPA ch.24 treats Dasa/Bhukti/Antara as one
    self-similar proportional hierarchy; HTJAH-II:668-702 names all three levels —
    "as lords of the Dasas (main-periods), as lords of Bhuktis (Sub-periods) or as
    lords of the Antaras" — as carriers of a house's results).

    ``bh`` must be a Bhukti-level span (``antar`` set); raises ValueError otherwise.
    """
    if bh.antar is None:
        raise ValueError("pratyantars() needs a Bhukti-level DashaPeriod (antar set), "
                         "got an MD-level span")
    total_years = (bh.end_jd - bh.start_jd) / DAYS_PER_VEDIC_YEAR
    out: list[DashaPeriod] = []
    cursor = bh.start_jd
    for pd_lord in _sequence_from(bh.antar):
        years = total_years * _LORD_YEARS[pd_lord] / _TOTAL_YEARS
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        out.append(DashaPeriod(bh.maha, bh.antar, cursor, end, pd_lord))
        cursor = end
    return out


def pratyantar_on(chart: RamanChart, jd: float) -> Optional[DashaPeriod]:
    """The (Mahadasha, Bhukti, Pratyantar) period running on Julian Day `jd`, or None
    outside the timeline. A NEW resolver — ``dasha_on`` is deliberately untouched so
    every existing caller keeps its exact Bhukti-level behaviour."""
    bh = dasha_on(chart, jd)
    if bh is None or bh.antar is None:
        return bh
    for pd in pratyantars(bh):
        if pd.contains(jd):
            return pd
    return bh


@dataclass(frozen=True)
class MarakaSet:
    """The death-inflicting grahas, tiered by Raman's doctrine (HTJAH-I:770-795). A maraka's
    Dasha is when a fatal 8th/longevity affliction is most apt to mature; the tier weights how
    strong a death-signal the period carries (it does NOT narrow the set — the doctrine is
    deliberately broad, so the death-WINDOW ranking, not set membership, discriminates).

    ``primary_rank`` orders the primary tier as Raman does (USER DECISION 2026-10-24, timing
    gap check fix 7): "Of these several determinants above mentioned, planets in conjunction
    with lords of 2nd and 7th are the most powerful in causing death, while the lords
    themselves are least powerful" (HTJAH-I:783-784). 3 = conjunct a 2nd/7th lord, 2 = a
    (malefic) occupant of the 2nd/7th or a planet aspecting a 2nd/7th lord, 1 = the lord
    alone. VARIANT on record, not applied: HPA-15:41-46 also ranks the 2nd over the 7th ("The
    2nd house is always stronger in inflicting death than the 7th")."""
    primary: frozenset[str]
    secondary: frozenset[str]
    tertiary: frozenset[str]
    primary_rank: tuple[tuple[str, int], ...] = ()

    def all(self) -> frozenset[str]:
        return self.primary | self.secondary | self.tertiary

    def rank(self, graha: str) -> int:
        """Primary sub-rank (3 conjunct > 2 occupant/aspecting > 1 lord); 0 outside primary."""
        if graha not in self.primary:
            return 0
        return dict(self.primary_rank).get(graha, 1)

    def weight(self, graha: str) -> int:
        """Death-signal weight: primary 3 (lord) / 4 (occupant or aspecting a lord) / 5
        (conjunct a 2nd/7th lord), secondary 2, tertiary 1, non-maraka 0 (HTJAH-I:783-784)."""
        if graha in self.primary:
            return 2 + self.rank(graha)
        if graha in self.secondary:
            return 2
        if graha in self.tertiary:
            return 1
        return 0


def _node_is_maraka(chart: RamanChart, node: str) -> bool:
    """A node (Rahu/Ketu) becomes a maraka by OCCUPYING the 2nd/7th/8th from the Moon, OR by
    conjoining/aspecting a 2nd/7th lord (HTJAH-II:4806-4814, Chart 35: Rahu in the 8th-from-Moon
    AND associated with the 7th lord). Nodes carry no lordship, so only occupation/association."""
    p = chart.planets.get(node)
    moon = chart.planets.get("Moon")
    if p is None or moon is None:
        return False
    if ((p.rasi_house - moon.rasi_house) % 12) + 1 in (2, 7, 8):
        return True
    l2 = SIGN_LORDS[((chart.asc_sign - 1) + 1) % 12 + 1]
    l7 = SIGN_LORDS[((chart.asc_sign - 1) + 6) % 12 + 1]
    for lord in (l2, l7):
        lp = chart.planets.get(lord)
        if lp is not None and (lp.rasi_house == p.rasi_house
                               or drishti.aspects_planet(node, lord, chart)):
            return True
    return False


def _lord_of_house(chart: RamanChart, house: int) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


#: The karaka Raman PRINTS in each house's "Time of Fructification" factor list. A house he
#: prints no karaka for gets none (USER DECISION 2026-10-24, timing gap check fix 1 — this
#: replaces the old rule of adding `BHAVA_KARAKA` for every house, with "Sun" as a default):
#:   H3  "(d) the Karaka, and the planets in association with or aspecting Karaka"
#:       (HTJAH-I:3526); Mars is "the Karaka for brothers (Kuja or Mars)" (HTJAH-I:3428)
#:   H4  "(g) the Karaka of the fourth Bhava" (HTJAH-I:4309-4310); Moon, "MatruKaraka" (HTJAH-I:4421)
#:   H5  "(f) the lord of the 5th from the Moon and the Karaka of the 5th Bhava"
#:       (HTJAH-I:5322-5323); "Jupiter, the Karaka for children" (HTJAH-I:5619)
#:   H6  "(f) the lord of the 6th from the Moon and the Karaka of the 6th" (HTJAH-I:6275);
#:       "Mars, Karaka of the 6th Bhava" (HTJAH-I:6621)
#:   H7  "(g) the Karaka of the 7th Bhava" (HTJAH-I:8272); "KalatraKaraka: Venus" (HTJAH-I:8504)
#:   H9  "(g) the Sun who is the Karaka for father" (HTJAH-I:12737-12738) — the Sun, NOT Jupiter
#:   H12 "The position of Saturn is also of significance as he is the Karaka of loss"
#:       (HTJAH-I:17733-17734)
#: H1, H2, H10 and H11 print no karaka (HTJAH-I:1586-1588, 2584-2586, 14071-14075,
#: 16390-16395); H8's section prints no factor list at all (HTJAH-I:10316), so it takes the
#: general (a)-(f) factors only ("The same consideration holds good with reference to the
#: other houses", HTJAH-I:1588-1589).
TIMER_KARAKA: Final[dict[int, str]] = {
    3: "Mars", 4: "Moon", 5: "Jupiter", 6: "Mars", 7: "Venus", 9: "Sun", 12: "Saturn"}

#: The planet each node acts like (USER DECISION 2026-10-24, fix 2): "Rahu gives the results
#: of Venus (the planet with whom he associates), Jupiter (his sign- dispositor) and Saturn
#: (Sanivad Rahu)" (HTJAH-I:11740-11741); "Ketu being in a martian sign and aiso according to
#: the dictum Kujavad Ketu can also influence the 9th house" (HTJAH-I:12762-12763).
NODE_DICTUM: Final[dict[str, str]] = {"Rahu": "Saturn", "Ketu": "Mars"}

_NAK_LORDS: Final[tuple[str, ...]] = _SEQUENCE   # Ashwini=Ketu ... Revati=Mercury


def nakshatra_lord_of(chart: RamanChart, planet: str) -> Optional[str]:
    """The Vimshottari lord of the nakshatra ``planet`` occupies (None if absent). Raman:
    "the fact of a planet being situated in a particular constellation is of paramount
    importance especially in the matter of predicting significant events" (HTJAH-I:4518-4520)."""
    p = chart.planets.get(planet)
    if p is None:
        return None
    nak = getattr(p, "nakshatra", None) or int((p.lon % 360.0) // (360.0 / 27)) + 1
    return _NAK_LORDS[(int(nak) - 1) % 9]


def timer_set(chart: RamanChart, house: int) -> frozenset[str]:
    """Raman's 'Time of Fructification' significator set for a bhava — the planets that bring
    that house's results in their Dasha or Bhukti. It is the flattening of ``timer_roles``,
    which carries the factor-by-factor derivation and every citation; the two can never drift
    because this function is defined from that one.

    Corrected 2026-10-24 (USER DECISION, timing gap check fix 1 + fix 2): the set follows
    Raman's PRINTED per-house lists (no karaka where he prints none, the Sun for the 9th, the
    lord counted from the Moon only from the 2nd house on, the karaka's associates for the
    3rd) and gives the nodes all four of Raman's result channels (sign lord, conjoined planet,
    nakshatra lord, Sanivad Rahu / Kujavad Ketu)."""
    return frozenset(timer_roles(chart, house))


#: The role tags `timer_roles` can emit, in the order Raman lists the factors
#: (HTJAH-I:1586-1588): the house's own lord, its karaka, occupants, aspecters, planets
#: conjoining/aspecting the lord, the lord-from-the-Moon, the 3rd house's karaka associates,
#: and the four node channels.
TIMER_ROLE_TAGS: Final[tuple[str, ...]] = (
    "owns", "karaka", "occupies", "aspects house", "conjoins lord", "aspects lord",
    "lord from Moon", "conjoins karaka", "aspects karaka",
    "node of a timer's sign", "node joins a timer", "node in a timer's star",
    "Sanivad Rahu", "Kujavad Ketu")


def timer_roles(chart: RamanChart, house: int) -> dict[str, tuple[str, ...]]:
    """Role-preserving timer set — BY WHICH of Raman's printed factors each planet influences
    ``house`` ("owns", "aspects lord", ...). Raman himself always names the factor ("Saturn,
    as lord of the 2nd, aspecting its lord ..."), and the narration restores that.

    The factors (USER DECISION 2026-10-24, timing gap check fixes 1-2):

    * (a) the lord, (b) planets aspecting the house, (c) planets posited in it, (d) planets
      aspecting the lord, (e) planets in association with the lord — "The same consideration
      holds good with reference to the other houses" (HTJAH-I:1586-1589).
    * (f) the lord of the house counted from the Moon, FROM THE 2ND HOUSE ON: the 1st-house
      list stops at (e) (HTJAH-I:1586-1588); the 2nd adds "(f) lord of the 2nd from the Moon"
      (HTJAH-I:2586) and every later printed list repeats it (4309, 5322, 6275, 8271, 12737,
      14075, 16395, 17733). The 3rd-house paragraph prints no (f) but says "The general
      principles ... in reference to the 1st and 2nd houses also hold good with reference to
      the 3rd" (HTJAH-I:3521-3522), so it carries the 2nd-house factor.
    * the karaka only where printed (``TIMER_KARAKA``); for the 3rd, also "the planets in
      association with or aspecting Karaka" (HTJAH-I:3526).
    * a node, when any of its four channels is itself a timer: its sign lord ("Ketu should
      give the results of sign dispositor Saturn", HTJAH-I:8566-8567), the planet it joins
      ("Venus (the planet with whom he associates)", HTJAH-I:11740), its nakshatra lord
      ("Rahu being a shadowy planet should give the results of Mars whose star he occupies",
      HTJAH-I:4478-4479), and the planet it acts like ("Saturn (Sanivad Rahu)",
      HTJAH-I:11741; "the dictum Kujavad Ketu", HTJAH-I:12762-12763). Channels are tested
      against the non-node set, so the result does not depend on which node is read first.

    Returns {planet: (role tag, ...)} with tags in TIMER_ROLE_TAGS order of first hit."""
    roles: dict[str, list[str]] = {}

    def _add(name: str, tag: str) -> None:
        tags = roles.setdefault(name, [])
        if tag not in tags:
            tags.append(tag)

    lord = _lord_of_house(chart, house)
    _add(lord, "owns")                                            # (a) the H-lord
    karaka = TIMER_KARAKA.get(house)
    if karaka is not None:                                        # printed karaka only
        _add(karaka, "karaka")
    for name, p in chart.planets.items():                         # (b)/(c)
        if p.rasi_house == house:
            _add(name, "occupies")
        if drishti.aspects_house(name, house, chart):
            _add(name, "aspects house")
    lp = chart.planets.get(lord)
    if lp is not None:                                            # (d)/(e)
        for name, p in chart.planets.items():
            if name != lord:
                if p.rasi_house == lp.rasi_house:
                    _add(name, "conjoins lord")
                if drishti.aspects_planet(name, lord, chart):
                    _add(name, "aspects lord")
    moon = chart.planets.get("Moon")
    if moon is not None and house >= 2:                           # (f) from the 2nd house on
        _add(SIGN_LORDS[(moon.sign - 1 + (house - 1)) % 12 + 1], "lord from Moon")
    if house == 3 and karaka is not None:                         # 3rd: the karaka's associates
        kp = chart.planets.get(karaka)
        if kp is not None:
            for name, p in chart.planets.items():
                if name != karaka:
                    if p.rasi_house == kp.rasi_house:
                        _add(name, "conjoins karaka")
                    if drishti.aspects_planet(name, karaka, chart):
                        _add(name, "aspects karaka")
    base = set(roles)                     # the set BEFORE any node channel is applied
    for node in ("Rahu", "Ketu"):                                 # the four node channels
        np_ = chart.planets.get(node)
        if np_ is None:
            continue
        if SIGN_LORDS[np_.sign] in base:
            _add(node, "node of a timer's sign")
        if any(n in base for n, p in chart.planets.items()
               if n not in NODE_DICTUM and p.rasi_house == np_.rasi_house):
            _add(node, "node joins a timer")
        if nakshatra_lord_of(chart, node) in base:
            _add(node, "node in a timer's star")
        if NODE_DICTUM[node] in base:
            _add(node, "Sanivad Rahu" if node == "Rahu" else "Kujavad Ketu")
    return {name: tuple(tags) for name, tags in roles.items()}


# Allied event houses (gains 2/11, travel 9/12). NO Raman citation stands behind grading one
# house on the other's set, so since 2026-10-24 (USER DECISION, timing gap check fix 3) they
# never enter a house's grade: `active_houses` reports them only as a separately labelled
# `allied_via` note. The matter-level significator windows in the judge's timing overlay
# still read the pair, as a disclosed engine convenience.
_EVENT_AUX_HOUSES: Final[dict[int, tuple[int, ...]]] = {2: (11,), 11: (2,), 9: (12,), 12: (9,)}


def maraka_set(chart: RamanChart) -> MarakaSet:
    """Raman's full tiered maraka set. REUSES the existing `chart.maraka_points` doctrine
    (primitives/maraka.py: 2nd/7th lords + occupants/associates, 3rd/8th lords, Saturn/weakest)
    for the LAGNA tiers, and adds the FROM-MOON marakas (2nd/7th-from-Moon -> secondary,
    8th-from-Moon -> tertiary), node marakas, and the Saturn-in-10th Mrityu Yoga (-> tertiary).
    Validated: every dated death golden's Mahadasha lord lands in the set (incl. the functional
    Rahu/Jupiter marakas)."""
    primary: set[str] = set()
    secondary: set[str] = set()
    tertiary: set[str] = set()
    # 1. Lagna tiers — reuse the existing maraka_points doctrine.
    mp = getattr(chart, "maraka_points", None)
    if mp is not None:
        bucket = {"primary": primary, "secondary": secondary, "tertiary": tertiary}
        for u in mp.units:
            bucket[u.tier].add(u.graha)
    else:  # Track-B fallback: the two maraka-house lords only
        primary.add(SIGN_LORDS[((chart.asc_sign - 1) + 1) % 12 + 1])
        primary.add(SIGN_LORDS[((chart.asc_sign - 1) + 6) % 12 + 1])
    moon = chart.planets.get("Moon")
    if moon is not None:
        # 2. From-Moon house lords (Raman reads the 2nd/7th/8th from the Moon as well as Lagna).
        secondary.add(SIGN_LORDS[(moon.sign - 1 + 1) % 12 + 1])   # 2nd from Moon
        secondary.add(SIGN_LORDS[(moon.sign - 1 + 6) % 12 + 1])   # 7th from Moon
        tertiary.add(SIGN_LORDS[(moon.sign - 1 + 7) % 12 + 1])    # 8th from Moon
        # 3. Node marakas.
        for node in ("Rahu", "Ketu"):
            if _node_is_maraka(chart, node):
                secondary.add(node)
    # 4. Saturn-in-10th Mrityu Yoga. (No Raman citation located; kept as the engine's
    #    earlier reading and disclosed by the timing gap check, 2026-10-24.)
    sat = chart.planets.get("Saturn")
    if sat is not None and sat.rasi_house == 10:
        tertiary.add("Saturn")
    # 5. Tertiary Saturn, the full printed breadth (fix 7, USER DECISION 2026-10-24):
    #    "(c) Tertiary Determinants of Death .—(i) Saturn in conjunction, association or aspect
    #    with the Maraka (determinants of death) mentioned above" (HTJAH-I:793-794) — any
    #    primary or secondary maraka, not only a 2nd/7th lord.
    if sat is not None and "Saturn" not in primary | secondary:
        for m in sorted((primary | secondary) - {"Saturn"}):
            if lords_associated(chart, "Saturn", m):
                tertiary.add("Saturn")
                break
    # Keep each graha in its strongest tier only.
    secondary -= primary
    tertiary -= primary | secondary
    return MarakaSet(frozenset(primary), frozenset(secondary), frozenset(tertiary),
                     _primary_ranks(chart, frozenset(primary)))


def _primary_ranks(chart: RamanChart, primary: frozenset[str]) -> tuple[tuple[str, int], ...]:
    """Raman's order inside the primary tier (HTJAH-I:783-784): 3 for a planet conjunct a
    2nd/7th lord, 2 for an occupant of the 2nd/7th or a planet aspecting a 2nd/7th lord, 1 for
    the lord alone."""
    lords = {_lord_of_house(chart, 2), _lord_of_house(chart, 7)}
    out: list[tuple[str, int]] = []
    for g in sorted(primary):
        p = chart.planets.get(g)
        rank = 1
        if p is not None:
            conj = any((lp := chart.planets.get(lord)) is not None and lord != g
                       and lp.rasi_house == p.rasi_house for lord in lords)
            occ = p.rasi_house in (2, 7) or any(
                lord != g and lord in chart.planets and drishti.aspects_planet(g, lord, chart)
                for lord in lords)
            rank = 3 if conj else (2 if occ else 1)
        out.append((g, rank))
    return tuple(out)


def lifespan_gate(chart: RamanChart, span_years: Optional[float] = None) -> dict[str, bool]:
    """{planet: does its Mahadasha BEGIN inside the native's span?} (USER DECISION 2026-10-24,
    timing gap check fix 5). Raman: "Whether the native of the horoscope is likely to enjoy the
    Dasha of the ascendant lord or for that matter, the Dasha of the lord of any house in
    consideration. For knowing this, the longevity should be previously ascertained"
    (HTJAH-I:1578-1580); "Venus can give the effects of first house only as minor lord"
    (HTJAH-I:1622-1623); HPA-15:21-37 applies the same to marakas. A planet whose Mahadasha
    starts after the span acts only through its bhuktis. ``span_years`` defaults to the
    ayurdaya span; {} on a Track-B chart."""
    if getattr(chart, "jd_ut", None) is None:
        return {}
    if span_years is None:
        from app.raman_saab.primitives import ayurdaya
        span_years = ayurdaya.longevity(chart).total_years
    end = chart.jd_ut + span_years * DAYS_PER_VEDIC_YEAR
    out: dict[str, bool] = {}
    for md in mahadasha_timeline(chart, 120.0):
        if md.maha not in out:
            out[md.maha] = md.start_jd < end
    return out


def death_weight_fn(chart: RamanChart, ms: Optional[MarakaSet] = None,
                    span_years: Optional[float] = None) -> Callable[[str], int]:
    """The per-lord death-signal weight ``death_window`` sums (fix 7, USER DECISION
    2026-10-24): ``MarakaSet.weight`` (primary ordered by HTJAH-I:783-784), and for a node that
    carries a late maraka's delegated power, that maraka's weight (HTJAH-I:11194-11203)."""
    ms = ms or maraka_set(chart)
    delegated = dict(delegated_marakas(chart, ms, lifespan_gate(chart, span_years)))

    def _weight(g: str) -> int:
        return max(ms.weight(g), ms.weight(delegated[g]) if g in delegated else 0)
    return _weight


def delegated_marakas(chart: RamanChart, ms: Optional[MarakaSet] = None,
                      gate: Optional[dict[str, bool]] = None) -> tuple[tuple[str, str], ...]:
    """(node, delegating maraka) pairs: a maraka whose Mahadasha falls outside the span hands its
    killing power to a node occupying its sign (USER DECISION 2026-10-24, fix 7). Raman:
    "Saturn Dasha will come in the native's 90th year, which is far too late. Saturn by virtue
    of his inherent affinity with Rahu (Sanivad Rahu) delegates his Maraka or killing power to
    Rahu" and "as Saturn himself cannot cause death, he must naturally delegate his power on
    the planet occupying his sign. Such a planet would be Rahu" (HTJAH-I:11194-11203)."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    ms = ms or maraka_set(chart)
    gate = gate if gate is not None else lifespan_gate(chart)
    out: list[tuple[str, str]] = []
    for m in sorted(ms.all()):
        if m in ("Rahu", "Ketu") or gate.get(m, True):
            continue
        for node in ("Rahu", "Ketu"):
            np_ = chart.planets.get(node)
            if np_ is not None and SIGN_LORDS[np_.sign] == m:
                out.append((node, m))
    return tuple(out)


def maraka_lords(chart: RamanChart) -> frozenset[str]:
    """The full maraka graha set (all tiers). Back-compat shim over `maraka_set`."""
    return maraka_set(chart).all()


def maraka_running_phrase(flag: bool | None) -> str:
    """How every report surface states whether the running period is maraka-tier.

    ``None`` means the check could not be made for this chart, and is said so — never folded
    into "no maraka-tier lord", which would be a confident statement the engine did not make
    (audit 2026-10-23: the report's fallback used to set the flag to False on an exception)."""
    if flag is None:
        return "could not be determined for this chart"
    return "carries a maraka-tier lord" if flag else "carries no maraka-tier lord"


def is_maraka_period(chart: RamanChart, jd: float, *, strength: str = "any") -> bool:
    """True when the period running on `jd` carries a maraka. ``strength="any"`` (default): the
    Mahadasha OR Bhukti lord is a maraka. ``strength="strong"``: BOTH are marakas (the sharper
    death-timing signature). NOTE: ``any`` is broad/low-discrimination -- the maraka set spans most
    grahas, so the majority of periods qualify; use ``strong`` (or death_window ranking) for a
    discriminating death-timing claim, not ``any``."""
    period = dasha_on(chart, jd)
    if period is None:
        return False
    marakas = maraka_set(chart).all()
    md_maraka = period.maha in marakas
    antar_maraka = period.antar is not None and period.antar in marakas
    if strength == "strong":
        return md_maraka and antar_maraka
    return md_maraka or antar_maraka


# ---------------------------------------------------------------------------
# Death window (Phase 2) — maraka Dasha periods x the ayurdaya span
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeathWindow:
    """A death-prone period: a maraka Bhukti overlapping the alloted-span region, with its
    maraka tier-score (MD-weight + Bhukti-weight)."""
    maha: str
    antar: str
    start_jd: float
    end_jd: float
    score: int

    def label(self) -> str:
        y0, m0, _d0, _ = swe.revjul(self.start_jd, swe.GREG_CAL)
        y1, m1, _d1, _ = swe.revjul(self.end_jd, swe.GREG_CAL)
        return f"{self.maha}/{self.antar} {int(y0)}-{int(m0):02d}..{int(y1)}-{int(m1):02d}"


_SPAN_BAND_YEARS: Final[dict[str, float]] = {"alpa": 5.0, "madhya": 8.0, "purna": 10.0}


def death_window(chart: RamanChart) -> tuple[DeathWindow, ...]:
    """The alloted-span death window: the maraka Bhukti periods overlapping the ayurdaya span
    ± its class band, in chronological order. This is when the alloted lifespan expires UNDER a
    maraka — the natural-death region.

    HONEST LIMIT: a strong EARLIER maraka can cut life short well before the span (premature /
    violent death — Lincoln 56, JFK 46), and isolating WHICH maraka strikes then is the
    chart-specific 'strongest-maraka + transit' judgement the engine deliberately does NOT make.
    So this predicts the natural-death region, not a premature death; the validated, robust claim
    is the weaker `is_maraka_period(death_date)` (the death always falls in *some* maraka period)
    plus the Mahadasha match. None on a Track-B chart (no birth_jd)."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    from app.raman_saab.primitives import ayurdaya
    ms = maraka_set(chart)
    span = ayurdaya.longevity(chart)
    death_jd = chart.jd_ut + span.total_years * DAYS_PER_VEDIC_YEAR
    _death_weight = death_weight_fn(chart, ms, span.total_years)
    band = _SPAN_BAND_YEARS.get(span.longevity_class, 8.0) * DAYS_PER_VEDIC_YEAR
    lo, hi = death_jd - band, death_jd + band
    out: list[DeathWindow] = []
    for md in mahadasha_timeline(chart):
        if md.start_jd > hi:
            break
        for bh in bhuktis(md):
            if bh.end_jd < lo or bh.start_jd > hi:
                continue
            score = _death_weight(bh.maha) + _death_weight(bh.antar)
            if score > 0:
                out.append(DeathWindow(bh.maha, bh.antar, bh.start_jd, bh.end_jd, score))
    return tuple(out)


# ---------------------------------------------------------------------------
# General event-timing (Phase 3) — a matter's significators x their Dasha
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EventWindow:
    """A Mahadasha window of one of a matter's significators, tagged with the role by which it
    signifies (lord / karaka / afflictor / reliever / maraka). These are the periods when the
    matter's results are 'active' — the soft, validatable claim ("the event fell in a
    significator's Dasha"), not a single-date prediction."""
    graha: str
    role: str
    start_jd: float
    end_jd: float

    def label(self) -> str:
        y0, m0, _d, _ = swe.revjul(self.start_jd, swe.GREG_CAL)
        y1, m1, _e, _ = swe.revjul(self.end_jd, swe.GREG_CAL)
        return f"{self.graha}({self.role}) {int(y0)}-{int(y1)}"


# Role priority when one graha signifies a matter several ways: iterated in order, the LAST
# match wins, so the more event-salient roles (maraka/afflictor) override the generic timer/
# lord/karaka tags.
_ROLE_ORDER: Final[tuple[str, ...]] = (
    "timer", "lord", "karaka", "reliever", "maraka", "afflictor")


def significator_dasha_windows(
    chart: RamanChart, grahas_by_role: dict[str, frozenset[str]], *, span_years: float = 120.0,
) -> tuple[EventWindow, ...]:
    """The Mahadasha windows of a matter's significators, given a {role: {graha,...}} map (the
    caller assembles it from lead.lord, sig.primary_karaka, the fired-rule subjects, and — for
    death/relative-death matters — `maraka_set`; kept decoupled from the judge to avoid an import
    cycle). One window per (graha, strongest-role) within `span_years` from birth, chronological.
    Empty on a Track-B chart (no birth_jd)."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    role_of: dict[str, str] = {}
    for role in _ROLE_ORDER:                       # weakest first so stronger roles overwrite
        for g in grahas_by_role.get(role, ()):  # type: ignore[arg-type]
            role_of[g] = role
    horizon = chart.jd_ut + span_years * DAYS_PER_VEDIC_YEAR
    out: list[EventWindow] = []
    for md in mahadasha_timeline(chart, span_years):
        if md.start_jd >= horizon:
            break
        if md.maha in role_of:
            # Clip the start to birth. The FIRST Mahadasha's nominal start precedes birth by
            # the elapsed balance (a native born partway through Mercury's 17 years gets a
            # window nominally opening in 1978 for a 1990 birth) — astronomically right, but
            # "the matter is active in 1978" is false for a person who did not exist then.
            # Clipped here at the source rather than in a renderer: the same window is now
            # read by four surfaces, and the un-clipped value escaped through the newest one.
            out.append(EventWindow(md.maha, role_of[md.maha],
                                   max(md.start_jd, chart.jd_ut), md.end_jd))
    out.sort(key=lambda w: w.start_jd)
    return tuple(out)


# ---------------------------------------------------------------------------
# Dasha-driven house activation (inverse timer-set) — which houses a running
# period lights up, the basis of Raman's temporally-prioritized reading.
# ---------------------------------------------------------------------------

#: Raman's fructification tiers, strongest first. "same lord" is the Mahadasha lord's OWN
#: bhukti: Raman's par-excellence/ordinary test is about "the sub-period of ANOTHER
#: influencing the 1st house, who is associated with the main lord" (HTJAH-I:1635-1637), so
#: it does not apply when the two lords are one planet (USER DECISION 2026-10-24, timing gap
#: check fix 3; the engine used to count a lord as "associated" with itself and print par
#: excellence). It sits inside the both-lords band, below "ordinary", because the association
#: that lifts a bhukti to par excellence is not there to be found.
TIER_ORDER: Final[tuple[str, ...]] = (
    "par excellence", "ordinary", "same lord", "limited", "feeble")
SAME_LORD_TIER: Final[str] = "same lord"


@dataclass(frozen=True)
class ActiveHouse:
    """A house lit up by the running Dasha. Raman reads the chart through the period: the running
    Mahadasha/Bhukti lord ACTIVATES the houses it signifies (the inverse of `timer_set`), and the
    matter fructifies there.

    ``grade`` is Raman's tier for the house, in key form: ``par_excellence`` / ``ordinary`` /
    ``same_lord`` / ``limited`` / ``feeble`` (``tier`` gives the spoken form). Corrected
    2026-10-24 (USER DECISION, timing gap check fix 3): the old two-grade label printed
    "par_excellence" whenever both lords influenced the house, with no association test, so a
    bhukti Raman calls "ordinary" was shown as par excellence; and each house is now graded on
    ITS OWN printed factor list. ``allied_via`` names the allied event house (2<->11, 9<->12)
    through which a period lord ALSO reaches the house — a separately labelled note with no
    Raman citation behind it, never part of the grade."""
    house: int
    grade: str
    md_activates: bool
    antar_activates: bool
    md_lord: str
    antar_lord: Optional[str]
    allied_via: tuple[int, ...] = ()

    @property
    def tier(self) -> str:
        return self.grade.replace("_", " ")


def period_tier(chart: RamanChart, md: str, antar: Optional[str],
                md_influences: bool, antar_influences: bool) -> Optional[str]:
    """Raman's tier for one house in the period ``md``/``antar``, given whether each lord is in
    the house's own timer set. The MD lord's own bhukti returns ``SAME_LORD_TIER`` when it
    influences the house (HTJAH-I:1635, "the sub-period of another"); otherwise this is
    ``bhukti_tier`` with the association read by ``lords_associated``."""
    if antar is not None and antar == md:
        return SAME_LORD_TIER if md_influences else None
    associated = (antar is not None and md_influences and antar_influences
                  and lords_associated(chart, md, antar))
    return bhukti_tier(md_influences, antar is not None and antar_influences, associated)


def running_top_tier(md: str, antar: Optional[str], associated: bool) -> str:
    """The best tier the running bhukti can give a house both lords influence: par excellence
    when the AD lord is associated with the MD lord, ordinary when not, and "same lord" for the
    MD lord's own bhukti (HTJAH-I:1635-1640)."""
    if antar is None or antar == md:
        return SAME_LORD_TIER
    return "par excellence" if associated else "ordinary"


def active_houses(chart: RamanChart, jd: float) -> tuple[ActiveHouse, ...]:
    """The houses the running period lights up on ``jd`` (HTJAH-I:1586-1596: a Dasha lord gives the
    results of the houses it owns/occupies/aspects/associates-with — exactly `timer_set` membership,
    read in reverse), each graded with Raman's tier on the house's OWN timer set (fix 3, USER
    DECISION 2026-10-24: no 2/11 or 9/12 union inside the grade). Strongest tier first. Empty
    on a Track-B chart (no jd_ut). NOTE: broad-recall by design — a slow lord (Saturn/Rahu)
    times most houses."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    period = dasha_on(chart, jd)
    if period is None:
        return ()
    md, antar = period.maha, period.antar
    out: list[ActiveHouse] = []
    for house in range(1, 13):
        timers = timer_set(chart, house)
        md_hit = md in timers
        antar_hit = antar is not None and antar in timers
        tier = period_tier(chart, md, antar, md_hit, antar_hit)
        if tier is None:
            continue
        allied = tuple(aux for aux in _EVENT_AUX_HOUSES.get(house, ())
                       if (md in (aux_set := timer_set(chart, aux)) and not md_hit)
                       or (antar is not None and antar in aux_set and not antar_hit))
        out.append(ActiveHouse(house, tier.replace(" ", "_"), md_hit, antar_hit, md, antar,
                               allied))
    out.sort(key=lambda a: (TIER_ORDER.index(a.tier), a.house))
    return tuple(out)


@dataclass(frozen=True)
class LordQuality:
    """How WELL a Dasha lord delivers the houses it activates — a strength/dignity DESCRIPTOR, not
    a verdict (HTJAH-II:10004-10008: the activated house's result is good/bad per the lord's
    strength). ``tag`` summarises: well / poorly / mixed / unknown."""
    lord: str
    strong: Optional[bool]          # is_powerful; None on Track-B / node (no Shadbala)
    dignity: str
    combust: bool
    vargottama: bool
    tag: str


_GOOD_DIGNITIES: Final[frozenset[str]] = frozenset({"exalt", "moolatrikona", "own"})


def _delivery_tag(strong: Optional[bool], dignity: str, combust: bool, vargottama: bool) -> str:
    if combust or dignity == "debil" or (strong is False and dignity == "enemy"):
        return "poorly"
    if (strong is True or dignity in _GOOD_DIGNITIES or vargottama) and not combust:
        return "well"
    if strong is None and dignity == "neutral":
        return "unknown"
    return "mixed"


def lord_quality(chart: RamanChart, lord: str) -> LordQuality:
    """The activating lord's delivery quality (reuses `is_powerful`, `dignity`, combustion). Nodes
    have no Shadbala/lordship -> strong None, dignity 'neutral'."""
    p = chart.planets.get(lord)
    if p is None:
        return LordQuality(lord, None, "neutral", False, False, "unknown")
    strong: Optional[bool] = None
    if p.shadbala_rupas is not None:
        strong = _shadbala_total.is_powerful(lord, p.shadbala_rupas.total / 60.0)
    dig = _dignity.dignity(lord, chart)
    combust = p.combust_fraction >= 0.5
    return LordQuality(lord, strong, dig, combust, p.vargottama,
                       _delivery_tag(strong, dig, combust, p.vargottama))


def lords_associated(chart: RamanChart, a: str, b: str) -> bool:
    """Two planets are 'associated' in Raman's sense — CONJOINED (same rasi) or in mutual aspect.

    This drives the bhukti grading of HTJAH-I:1635-1640: during the Mahadasha of a planet
    influencing a house, the sub-period of ANOTHER planet that also influences that house gives its
    results *par excellence* **when that Bhukti lord is associated with the Mahadasha lord**; if it
    influences the house but is NOT associated with the MD lord, only ORDINARY results follow."""
    pa, pb = chart.planets.get(a), chart.planets.get(b)
    if pa is None or pb is None:
        return False
    if pa.rasi_house == pb.rasi_house:                      # conjunction
        return True
    return drishti.aspects_planet(a, b, chart) or drishti.aspects_planet(b, a, chart)


def bhukti_tier(md_influences: bool, antar_influences: bool, associated: bool) -> Optional[str]:
    """Raman's fructification tier for ONE house in a given Mahadasha/bhukti. UNIFORM across all
    twelve houses — Raman states this explicitly (HTJAH-I:1588-1589 and repeats it for every house:
    "the general principles enunciated in regard to the 1st house lord hold equally good", 2617,
    3522, 4333, 8294, 16435) — applied to each house with ITS OWN significators.

    The four grades (HTJAH-I:1592-1596, 1635-1640 [1st]; 2588-2599 [2nd, incl. 'feeble']; the
    'feeble' grade recurs at 16404 [11th] / 17746 [12th]). Record of what is PRINTED: the
    par-excellence/ordinary split by association is printed only for the 1st house
    (HTJAH-I:1635-1640); the MD-only grade reads "feeble" for the 2nd, 11th and 12th, "limited"
    for the 3rd and 7th, "limited or even nominal" for the 4th, "limited or nominal" for the
    5th, "limited or small" for the 6th and "a very small extent" for the 9th. The uniform
    scheme is the CLAUDE.md lock, applied by Raman's own "hold equally good" statement:
      both lords influence the house + AD lord ASSOCIATED with the MD lord -> 'par excellence'
      both lords influence the house + AD lord NOT associated with MD lord  -> 'ordinary'
      only the AD (bhukti) lord influences the house (MD does not)          -> 'limited'
      only the MD lord influences the house (the current bhukti does not)   -> 'feeble'
    Returns None if neither period-lord influences the house."""
    if md_influences and antar_influences:
        return "par excellence" if associated else "ordinary"
    if antar_influences:
        return "limited"
    if md_influences:
        return "feeble"
    return None
