"""Gochara (transits) — Raman's timing layer on top of the natal chart.

Raman judged a transit by THREE things together: (1) the transiting planet's house FROM THE NATAL
MOON (classical Gochara benefic/malefic houses), (2) the Ashtakavarga support — the bindus the
planet earns in the transited sign in its OWN Bhinnashtakavarga (4+ is supportive, fewer poor), and
(3) the slow planets (Saturn, Jupiter, Rahu/Ketu) for the major turns, including Saturn's Sade-Sati
(transit of the 12th/1st/2nd from the Moon).

Usage:
    from app.raman_saab.primitives import transits as tr
    rows = tr.gochara(natal_chart, 2026, 6, 28)        # current transits vs the nativity
    sade = tr.sade_sati(natal_chart, 2026, 6, 28)
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Final

import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.constants import SWE_PLANETS
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.primitives import ashtakavarga as av
from app.raman_saab.primitives import kakshya

#: Houses FROM THE MOON in which a transiting planet gives benefic results (classical Gochara).
_GOCHARA_GOOD: Final[dict[str, frozenset[int]]] = {
    "Sun": frozenset({3, 6, 10, 11}),
    "Moon": frozenset({1, 3, 6, 7, 10, 11}),
    "Mars": frozenset({3, 6, 11}),
    "Mercury": frozenset({2, 4, 6, 8, 10, 11}),
    "Jupiter": frozenset({2, 5, 7, 9, 11}),
    "Venus": frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12}),
    "Saturn": frozenset({3, 6, 11}),
    "Rahu": frozenset({3, 6, 11}),
    "Ketu": frozenset({3, 6, 11}),
}

#: The Vedha (obstruction) house paired with each benefic Gochara house, per planet. When another
#: transiting planet occupies the Vedha house (from the Moon), the auspicious transit result is
#: cancelled (classical Gochara Vedha, Raman's HPA/HTJAH transit chapter).
_VEDHA: Final[dict[str, dict[int, int]]] = {
    "Sun": {3: 9, 6: 12, 10: 4, 11: 5},
    "Moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Mars": {3: 12, 6: 9, 11: 5},
    "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    "Saturn": {3: 12, 6: 9, 11: 5},
    "Rahu": {3: 12, 6: 9, 11: 5},
    "Ketu": {3: 12, 6: 9, 11: 5},
}

#: Pairs that cause NO Vedha to each other (Raman's exception): Sun↔Saturn, Moon↔Mercury.
_VEDHA_EXEMPT: Final[frozenset[frozenset[str]]] = frozenset(
    {frozenset({"Sun", "Saturn"}), frozenset({"Moon", "Mercury"})})

_ALL_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

#: The slow/significant transit planets Raman watches for major events.
SIGNIFICANT: Final[tuple[str, ...]] = ("Jupiter", "Saturn", "Rahu", "Ketu", "Mars")


@dataclass(frozen=True)
class TransitRow:
    planet: str
    sign: int                 # transit sign (1..12)
    house_from_moon: int      # 1..12 from natal Moon (the Gochara frame)
    house_from_lagna: int     # 1..12 from natal Lagna
    gochara_good: bool        # benefic house from the Moon
    bav_bindus: int | None    # bindus in the transited sign in the planet's OWN ashtakavarga
    supported: bool | None    # bav_bindus >= 4 (Ashtakavarga support)
    vedha_house: int | None   # the Vedha (obstruction) house for this transit (None if not benefic)
    vedha_by: tuple[str, ...]  # transiting planets occupying the Vedha house (obstructing)
    net_good: bool            # gochara_good AND not obstructed by Vedha
    # ── Kakshya micro-transit (ASP-13; added 2026-08-03) ──────────────────────────────────
    #: the 3¾° Kakshya the planet currently occupies and its ruling reference (None for nodes —
    #: they have no Ashtakavarga to judge against, per the 7-graha lock).
    kakshya_lord: str | None = None
    #: the ASP-13 judgment: did the Kakshya lord CONTRIBUTE a bindu to this sign in the
    #: transiting planet's own Ashtakavarga? ("Good income can be predicted when Jupiter
    #: transits the 3rd Kakshya ruled by Mars ... Mars has also contributed a bindu",
    #: ASP-13:459-474.) None when unjudgeable (nodes).
    kakshya_favourable: bool | None = None
    #: Raman's transit proportion, bindus/8 — "good effects ... to the extent of 62%" (5/8,
    #: ASP-13:280-282), "neutralises the evil to the extent of 75%" (6/8, ASP-13:416).
    bav_proportion: float | None = None


def transit_chart(year: int, month: int, day: int, *, ayanamsa: str = "lahiri") -> RamanChart:
    """Sidereal planet positions at noon UT on the given date (location-independent for signs)."""
    return cast_chart(BirthData(name="transit", year=year, month=month, day=day, hour=12,
                                minute=0, tz_offset=0.0, latitude=0.0, longitude=0.0),
                      ayanamsa=ayanamsa)


def gochara(natal: RamanChart, year: int, month: int, day: int, *,
            ayanamsa: str | None = None, planets: tuple[str, ...] = SIGNIFICANT) -> tuple[TransitRow, ...]:
    """Transit rows for `planets` on the date, judged from the natal Moon + natal Lagna + each
    planet's own Ashtakavarga support. Default ayanamsa = the natal chart's (so a Raman-cast natal is
    not mixed with a Lahiri-cast transit)."""
    tc = transit_chart(year, month, day, ayanamsa=ayanamsa or getattr(natal, "ayanamsa", "lahiri"))
    moon = natal.planets.get("Moon")
    moon_sign = moon.sign if moon else natal.asc_sign
    # house-from-Moon of EVERY transiting graha — needed to detect Vedha obstruction.
    hfm_of: dict[str, int] = {
        g: ((tc.planets[g].sign - moon_sign) % 12) + 1
        for g in _ALL_GRAHAS if g in tc.planets}
    rows: list[TransitRow] = []
    for planet in planets:
        p = tc.planets.get(planet)
        if p is None:
            continue
        ts = p.sign
        hfm = ((ts - moon_sign) % 12) + 1
        hfl = ((ts - natal.asc_sign) % 12) + 1
        good = hfm in _GOCHARA_GOOD.get(planet, frozenset())
        bav = av.bhinnashtakavarga(natal, planet)[ts] if planet in av.PLANETS else None
        vedha_house, vedha_by = _vedha(planet, hfm, hfm_of) if good else (None, ())
        # Kakshya micro-transit (ASP-13): judged from the transiting LONGITUDE against the
        # NATAL Prasthara of the planet's own Ashtakavarga. Nodes carry None throughout.
        k_lord: str | None = None
        k_fav: bool | None = None
        if planet in av.PLANETS:
            kr = kakshya.transit_kakshya_reading(natal, planet, p.lon)
            k_lord, k_fav = kr.kakshya_lord, kr.favourable
        rows.append(TransitRow(
            planet=planet, sign=ts, house_from_moon=hfm, house_from_lagna=hfl,
            gochara_good=good, bav_bindus=bav, supported=None if bav is None else bav >= 4,
            vedha_house=vedha_house, vedha_by=vedha_by, net_good=good and not vedha_by,
            kakshya_lord=k_lord, kakshya_favourable=k_fav,
            bav_proportion=None if bav is None else round(bav / 8.0, 3)))
    return tuple(rows)


def _vedha(planet: str, hfm: int, hfm_of: dict[str, int]) -> tuple[int | None, tuple[str, ...]]:
    """The Vedha house for `planet`'s benefic transit at house `hfm`, and any transiting grahas
    obstructing it (occupying that house from the Moon), excluding the exempt pairs and itself."""
    vh = _VEDHA.get(planet, {}).get(hfm)
    if vh is None:
        return None, ()
    obstr = tuple(q for q in _ALL_GRAHAS
                  if hfm_of.get(q) == vh and q != planet
                  and frozenset({planet, q}) not in _VEDHA_EXEMPT)
    return vh, obstr


def sade_sati(natal: RamanChart, year: int, month: int, day: int, *,
              ayanamsa: str | None = None) -> str | None:
    """Saturn's Sade-Sati phase if active (transit of the 12th/1st/2nd from the natal Moon). Default
    ayanamsa = the natal chart's."""
    tc = transit_chart(year, month, day, ayanamsa=ayanamsa or getattr(natal, "ayanamsa", "lahiri"))
    moon = natal.planets.get("Moon")
    sat = tc.planets.get("Saturn")
    if moon is None or sat is None:
        return None
    h = ((sat.sign - moon.sign) % 12) + 1
    return {12: "Sade-Sati: rising (12th from Moon)", 1: "Sade-Sati: peak (over the Moon)",
            2: "Sade-Sati: setting (2nd from Moon)"}.get(h)


# ---------------------------------------------------------------------------
# Gochara outlook (multi-year) — the same Gochara/Vedha scheme, over a span of time
# ---------------------------------------------------------------------------

#: The four slow movers a multi-year outlook is judged from. Their Gochara good/bad status
#: changes only at each sign ingress (~1 year for Jupiter, ~2.5 years for Saturn/Rahu/Ketu) — the
#: natural resolution for a 25-year graph. Mars and the faster grahas already have a point-in-time
#: reading in `gochara()`; a 25-year table at their ~45-day-or-faster cadence would fragment into
#: hundreds of slivers and stop being readable.
_TIMELINE_PLANETS: Final[tuple[str, ...]] = ("Jupiter", "Saturn", "Rahu", "Ketu")

_FLAGS_LIGHT: Final[int] = swe.FLG_SWIEPH | swe.FLG_SIDEREAL


@dataclass(frozen=True)
class GocharaSegment:
    """One continuous span in which `planet` occupies a single transiting sign. `gochara_good`
    and `bav_bindus` are constant for the whole span (both are functions of the sign alone).
    `vedha_sample_fraction` is the share of SAMPLED dates within the span where a Vedha
    obstruction was active — an intentionally coarse estimate: a fast mover (Moon, Mercury...)
    can start and end a Vedha cancellation within days, faster than this multi-year view samples.
    Read it as "rare" / "frequent" / "sustained", not as exact obstructed dates — the day-exact
    check is the `gochara()` snapshot elsewhere in the report."""
    planet: str
    start_jd: float
    end_jd: float
    sign: int
    house_from_moon: int
    gochara_good: bool
    bav_bindus: int | None
    vedha_sample_fraction: float


#: MEASURED, and the measurement killed two plausible optimisations — recorded here so the
#: next reader does not re-try them.
#:
#: The three `gochara_timeline` sweeps a report runs share one `ref_jd` but start at three
#: different offsets, so their 5-day grids are misaligned and almost never land on the same
#: date: 10,119 calls over 10,119 DISTINCT dates. Memoising therefore buys NOTHING within a
#: report. The cache is kept only for the cross-report case a busy server sees, and sized above
#: one report's working set so it cannot thrash — at 8,192 it scored exactly zero hits, because
#: the set is larger than the cache and every entry was evicted before its reuse.
#:
#: The second idea was to compute only the planets each sweep asks for, two of the three
#: wanting Saturn alone. That IS much faster — 81,984 ephemeris calls fall to 15,535 and the
#: build to 1.18s — and it is WRONG: `_vedha` reads `hfm_of` for every transiting graha to find
#: the obstructors, so a restricted set silently empties it. Caught by diffing two charts'
#: full output against the previous code: segment boundaries, signs and bindus were identical
#: and every `vedha_sample_fraction` had changed. Do not restrict the body set.
#:
#: What is left, if someone wants the time back: align the three sweeps to one absolute grid so
#: the cache hits. That changes WHICH dates are sampled, so vedha fractions and segment edges
#: move by up to `step_days` — a deliberate output change, not an optimisation, and it needs
#: sign-off rather than a quiet commit.
_TRANSIT_SIGN_CACHE = 32768


@lru_cache(maxsize=_TRANSIT_SIGN_CACHE)
def _transiting_signs(year: int, month: int, day: int, *, ayanamsa: str) -> dict[str, int]:
    """Sign (1..12) of all 9 grahas at noon UT.

    Deliberately skips `cast_chart`'s Shadbala/maraka/upagraha passes — a multi-year timeline
    sampled every few days cannot afford to recompute those per sample, and a Gochara outlook
    needs only the transiting sign. ALL nine are computed even when the caller wants one: the
    vedha check needs the others (see the note above).

    Memoised: pure in `(year, month, day, ayanamsa)` and the ephemeris is deterministic, so a
    hit returns exactly what a recomputation would. The returned dict is SHARED between callers
    — every call site reads it and none mutates it, and a mutation would now be visible to the
    next caller, so keep it that way.
    """
    jd = swe.julday(year, month, day, 12.0, swe.GREG_CAL)
    with sidereal_mode(ayanamsa):
        signs: dict[str, int] = {}
        for name, pid in SWE_PLANETS.items():
            res, _ = swe.calc_ut(jd, pid, _FLAGS_LIGHT)
            signs[name] = int((float(res[0]) % 360.0) // 30) + 1
        node, _ = swe.calc_ut(jd, swe.MEAN_NODE, _FLAGS_LIGHT)
        rahu_lon = float(node[0]) % 360.0
        signs["Rahu"] = int(rahu_lon // 30) + 1
        signs["Ketu"] = int(((rahu_lon + 180.0) % 360.0) // 30) + 1
    return signs


def gochara_timeline(
    natal: RamanChart, ref_jd: float, years_back: float, years_forward: float, *,
    ayanamsa: str | None = None, planets: tuple[str, ...] = _TIMELINE_PLANETS,
    step_days: float = 5.0,
) -> dict[str, tuple[GocharaSegment, ...]]:
    """The Jupiter/Saturn/Rahu/Ketu Gochara outlook across
    [ref_jd - years_back*365.2425, ref_jd + years_forward*365.2425] — one chronological tuple of
    `GocharaSegment` per planet, so a report can answer "which windows in the past/future are
    favourable" rather than only "is it favourable right now" (`gochara()` above).

    Segment boundaries are exact sign ingresses to within `step_days` (default 5) — a real
    boundary can fall anywhere in the sampling gap either side of what's reported; that is stated
    explicitly wherever this is rendered, per the project's no-silent-approximation rule.
    """
    az = ayanamsa or getattr(natal, "ayanamsa", "lahiri")
    moon = natal.planets.get("Moon")
    moon_sign = moon.sign if moon else natal.asc_sign
    start_jd = ref_jd - years_back * DAYS_PER_VEDIC_YEAR
    end_jd = ref_jd + years_forward * DAYS_PER_VEDIC_YEAR

    open_seg: dict[str, dict] = {}
    out: dict[str, list[GocharaSegment]] = {p: [] for p in planets}

    def _close(planet: str, end: float) -> None:
        st = open_seg.pop(planet, None)
        if st is None:
            return
        good = st["good"]
        bav = (av.bhinnashtakavarga(natal, planet)[st["sign"]]
               if good and planet in av.PLANETS else None)
        frac = (st["vedha_hits"] / st["total"]) if good and st["total"] else 0.0
        out[planet].append(GocharaSegment(
            planet=planet, start_jd=st["start"], end_jd=end, sign=st["sign"],
            house_from_moon=st["hfm"], gochara_good=good, bav_bindus=bav,
            vedha_sample_fraction=round(frac, 3)))

    jd = start_jd
    while jd <= end_jd:
        y, m, d, _h = swe.revjul(jd, swe.GREG_CAL)
        signs = _transiting_signs(int(y), int(m), int(d), ayanamsa=az)
        hfm_of = {g: ((s - moon_sign) % 12) + 1 for g, s in signs.items()}
        for planet in planets:
            sign = signs.get(planet)
            if sign is None:
                continue
            hfm = hfm_of[planet]
            good = hfm in _GOCHARA_GOOD.get(planet, frozenset())
            cur = open_seg.get(planet)
            if cur is None or cur["sign"] != sign:
                _close(planet, jd)
                open_seg[planet] = {"start": jd, "sign": sign, "hfm": hfm, "good": good,
                                    "vedha_hits": 0, "total": 0}
                cur = open_seg[planet]
            if good:
                _vh, obstr = _vedha(planet, hfm, hfm_of)
                if obstr:
                    cur["vedha_hits"] += 1
            cur["total"] += 1
        jd += step_days
    for planet in planets:
        _close(planet, end_jd)
    return {p: tuple(segs) for p, segs in out.items()}
