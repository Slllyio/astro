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
from typing import Final, Optional

import swisseph as swe

from app.core.ephemeris_engine import (
    DASHA_LORDS, DAYS_PER_VEDIC_YEAR, calculate_vimshottari_mahadasha)
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA

_LORD_YEARS: Final[dict[str, int]] = dict(DASHA_LORDS)
_SEQUENCE: Final[tuple[str, ...]] = tuple(name for name, _ in DASHA_LORDS)
_TOTAL_YEARS: Final[int] = 120


@dataclass(frozen=True)
class DashaPeriod:
    """A running period: its Mahadasha lord, its Bhukti (antar) lord (None for an
    MD-level span), and its [start, end) bounds in Julian Days."""
    maha: str
    antar: Optional[str]
    start_jd: float
    end_jd: float

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


@dataclass(frozen=True)
class MarakaSet:
    """The death-inflicting grahas, tiered by Raman's doctrine (HTJAH-I:770-795). A maraka's
    Dasha is when a fatal 8th/longevity affliction is most apt to mature; the tier weights how
    strong a death-signal the period carries (it does NOT narrow the set — the doctrine is
    deliberately broad, so the death-WINDOW ranking, not set membership, discriminates)."""
    primary: frozenset[str]
    secondary: frozenset[str]
    tertiary: frozenset[str]

    def all(self) -> frozenset[str]:
        return self.primary | self.secondary | self.tertiary

    def weight(self, graha: str) -> int:
        """Death-signal weight: primary 3, secondary 2, tertiary 1, non-maraka 0."""
        if graha in self.primary:
            return 3
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


def timer_set(chart: RamanChart, house: int) -> frozenset[str]:
    """Raman's 'Time of Fructification' significator set for a bhava — the planets that bring
    that house's results in their Dasha. The SAME rule is given for every house (HTJAH-I:4303-
    4322 [4th] / 5315-5333 [5th]; HTJAH-II:9910-9934 [10th] / 14496-14537 [11th]):

      the H-lord, the H-karaka, the house's OCCUPANTS and ASPECTERS, the planets conjoining or
      aspecting the H-LORD, the H-lord from the MOON, and a NODE whose dispositor is itself a
      timer (a node gives the results of its sign-dispositor, HTJAH-I:2764/8566).

    This generalizes event-timing BEYOND death/marakas — gains (11th/2nd), career (10th),
    acquisition (4th), travel (9th/12th), children (5th) — lifting the non-death event-MD hit
    rate from ~10% to ~92% on the dated goldens. A planet gives a house's results in its Dasha
    when (and only when) it is in this set; the MD sets the theme, the Bhukti triggers."""
    ts: set[str] = set()
    lord = _lord_of_house(chart, house)
    ts.add(lord)
    ts.add(BHAVA_KARAKA.get(house, "Sun"))
    for name, p in chart.planets.items():
        if p.rasi_house == house or drishti.aspects_house(name, house, chart):
            ts.add(name)
    lp = chart.planets.get(lord)
    if lp is not None:
        for name, p in chart.planets.items():
            if name != lord and (p.rasi_house == lp.rasi_house
                                 or drishti.aspects_planet(name, lord, chart)):
                ts.add(name)
    moon = chart.planets.get("Moon")
    if moon is not None:
        ts.add(SIGN_LORDS[(moon.sign - 1 + (house - 1)) % 12 + 1])  # H-lord from the Moon
    for node in ("Rahu", "Ketu"):                                    # node via its dispositor
        np = chart.planets.get(node)
        if np is not None and SIGN_LORDS[np.sign] in ts:
            ts.add(node)
    return frozenset(ts)


# Secondary event houses unioned into the timer-set for a few matters (Raman reads gains from
# the 2nd AND 11th; foreign travel from the 9th AND 12th).
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
    # 4. Saturn-in-10th Mrityu Yoga.
    sat = chart.planets.get("Saturn")
    if sat is not None and sat.rasi_house == 10:
        tertiary.add("Saturn")
    # Keep each graha in its strongest tier only.
    secondary -= primary
    tertiary -= primary | secondary
    return MarakaSet(frozenset(primary), frozenset(secondary), frozenset(tertiary))


def maraka_lords(chart: RamanChart) -> frozenset[str]:
    """The full maraka graha set (all tiers). Back-compat shim over `maraka_set`."""
    return maraka_set(chart).all()


def is_maraka_period(chart: RamanChart, jd: float, *, strength: str = "any") -> bool:
    """True when the period running on `jd` carries a maraka. ``strength="any"`` (default): the
    Mahadasha OR Bhukti lord is a maraka. ``strength="strong"``: BOTH are marakas (the sharper
    death-timing signature)."""
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
    band = _SPAN_BAND_YEARS.get(span.longevity_class, 8.0) * DAYS_PER_VEDIC_YEAR
    lo, hi = death_jd - band, death_jd + band
    out: list[DeathWindow] = []
    for md in mahadasha_timeline(chart):
        if md.start_jd > hi:
            break
        for bh in bhuktis(md):
            if bh.end_jd < lo or bh.start_jd > hi:
                continue
            score = ms.weight(bh.maha) + ms.weight(bh.antar)
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
            out.append(EventWindow(md.maha, role_of[md.maha], md.start_jd, md.end_jd))
    out.sort(key=lambda w: w.start_jd)
    return tuple(out)
