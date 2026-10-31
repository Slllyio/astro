"""Timing in Raman's practice: five selection rules, chosen by the kind of event (spec 5.2).

1. ``good_event`` — a good event of the house itself: the house's influence set
   (``vimshottari.timer_roles``, HTJAH:1586-1589); for the 11th's gains also the 2nd house's
   owner, occupants and aspecters (HTJAH:16795-16801) and the planets of the wealth yogas
   (HTJAH:16809-16811).
2. ``rank`` — rise and fall in rank: the constituents of the raja yogas of HTJAH:613-634
   (yogakaraka; a 4th/7th/10th lord associated with a 5th/9th lord; the 9th and 10th lords
   exchanged, placed in each other's house or in mutual aspect), HTJAH:4324-4325.
3. ``relative_death`` — the relative's house, its lord and its karaka are each taken as a Lagna
   and their marakas found (bhavat bhavam): the 2nd and 7th lords, the occupants of the 2nd,
   7th, 8th and 12th, planets conjoined with the 2nd/7th lords (the strongest, HTJAH:783-784),
   and the 12th lord (Raman's practice in the father and spouse charts; spec 5.2, 7.5). For the
   father also the 9th from the Moon (Charts 88-90).
4. ``marriage`` — the seven-slot ordered list (HTJAH:8524-8527), pruned by age.
5. ``native_death`` — the span window first, then marakas from the Lagna, the Moon
   (``vimshottari.maraka_set``), the Navamsa Lagna and the Navamsa Moon.

Always: dasas outside the span (or the age window) are struck out; both lords must qualify and
the bhukti lord carries the event; a node qualifies through its sign lord, star lord, a
conjoined planet or Sanivad Rahu / Kujavad Ketu; a planet in its own star is not proposed as
the Mahadasha lord of a death (HTJAH:4515-4516); the MD-AD relation is stated where rank or
survival is at stake (``raman_timing.bhukti_relation``); a transit is noted last, as an
accelerator only (Saturn; Jupiter for marriage), never as a timer.

The engine's fructification tier (par excellence / ordinary / limited / feeble) is carried as a
separately labelled field ``engine_tier``: Raman prints those words and never applies them in a
worked chart (spec 7.1), so the reader itself never uses them.

CONVENTIONS: the marriageable window is ages 16-33 (Raman rejects a Mahadasha that begins
"after 33 years" when the chart shows no late marriage, HTJAH:8638-8640; the lower bound is his
"ends in childhood", HTJAH:8549-8551). Wealth-yoga planets beyond HTJAH:16809-16811 are the
2nd/5th/9th/11th lords associated with another of them (conjunction or mutual aspect,
HTJAH:4321-4322), Raman's practice in Charts 217-232. For a vehicle or a house, the 4th's
printed karaka slot (HTJAH:4309-4310) is filled with the matter's karaka (Venus, Mars).

Usage:
    from app.raman_saab.procedure.timing import timing_for
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.ordinals import ordinal
from app.raman_saab.primitives import vimshottari as vd
from app.raman_saab.primitives.functional_nature import is_yogakaraka
from app.raman_saab.procedure.citations import cite
from app.raman_saab.procedure.grading import SIGNS, count, lord_of, sign_from
from app.raman_saab.procedure.matters import RELATIVE_HOUSE, Event, Matter
from app.raman_saab.procedure.model import Candidate, TimingRule

logger = logging.getLogger(__name__)

_NODES = ("Rahu", "Ketu")
_MARRIAGE_AGES = (16.0, 33.0)


def _label(jd: float) -> str:
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y)}-{int(m):02d}"


def _age(chart: RamanChart, jd: float) -> float:
    return (jd - chart.jd_ut) / DAYS_PER_VEDIC_YEAR


def _add(q: dict[str, list[str]], planet: str, reason: str) -> None:
    rs = q.setdefault(planet, [])
    if reason not in rs:
        rs.append(reason)


def _with_nodes(chart: RamanChart, q: dict[str, list[str]]) -> None:
    """A node qualifies through any of its four channels to a qualifying planet."""
    base = {p for p in q if p not in _NODES}
    for node in _NODES:
        np_ = chart.planets.get(node)
        if np_ is None:
            continue
        sl = SIGN_LORDS[np_.sign]
        if sl in base:
            _add(q, node, f"gives the results of its sign lord {sl} ({cite('node_sign_lord')})")
        st = vd.nakshatra_lord_of(chart, node)
        if st in base:
            _add(q, node, f"in the star of {st} ({cite('node_star_lord')})")
        for n, p in chart.planets.items():
            if n in base and n not in _NODES and p.rasi_house == np_.rasi_house:
                _add(q, node, f"conjoined with {n}")
        dictum = vd.NODE_DICTUM[node]
        if dictum in base:
            _add(q, node, ("Sanivad Rahu" if node == "Rahu" else "Kujavad Ketu")
                 + f", acting like {dictum}")


def _bhuktis(chart: RamanChart, lo_age: float, hi_age: float) -> list[vd.DashaPeriod]:
    lo = chart.jd_ut + lo_age * DAYS_PER_VEDIC_YEAR
    hi = chart.jd_ut + hi_age * DAYS_PER_VEDIC_YEAR
    out: list[vd.DashaPeriod] = []
    for md in vd.mahadasha_timeline(chart, 130.0):
        if md.start_jd > hi:
            break
        if md.end_jd < lo:
            continue
        out.extend(b for b in vd.bhuktis(md) if b.end_jd > lo and b.start_jd < hi)
    return out


def _candidates(chart: RamanChart, q: dict[str, list[str]], lo_age: float, hi_age: float, *,
                no_md: frozenset[str] = frozenset(), relation: bool = False,
                transit: Optional[Callable[[vd.DashaPeriod], str]] = None,
                tier_house: Optional[int] = None,
                weights: Optional[dict[str, int]] = None) -> tuple[Candidate, ...]:
    out: list[Candidate] = []
    timers = vd.timer_set(chart, tier_house) if tier_house else frozenset()
    for b in _bhuktis(chart, lo_age, hi_age):
        if b.maha not in q or b.antar not in q or b.maha in no_md:
            continue
        rel = ""
        if relation:
            _seat, notes = _relation(chart, b.maha, b.antar)
            rel = "; ".join(notes)
        tier = ""
        if tier_house:
            t = vd.period_tier(chart, b.maha, b.antar, b.maha in timers, b.antar in timers)
            tier = f"engine tier for the {ordinal(tier_house)}: {t}" if t else ""
        start = max(b.start_jd, chart.jd_ut)
        out.append(Candidate(b.maha, b.antar, _label(start), _label(b.end_jd),
                             round(_age(chart, start), 1), "; ".join(q[b.maha]),
                             "; ".join(q[b.antar]), rel, transit(b) if transit else "", tier,
                             (weights.get(b.maha, 0) + weights.get(b.antar, 0)) if weights else 0))
    return tuple(out)


def _node_weights(chart: RamanChart, w: dict[str, int]) -> None:
    """A node carries the weight of the strongest planet it acts through (convention)."""
    for node in _NODES:
        np_ = chart.planets.get(node)
        if np_ is None:
            continue
        via = [SIGN_LORDS[np_.sign], vd.nakshatra_lord_of(chart, node), vd.NODE_DICTUM[node]]
        via += [n for n, p in chart.planets.items()
                if n not in _NODES and p.rasi_house == np_.rasi_house]
        w[node] = max([w.get(node, 0)] + [w.get(v, 0) for v in via if v])


def _relation(chart: RamanChart, maha: str, antar: str) -> tuple[int, tuple[str, ...]]:
    from app.raman_saab.raman_timing import bhukti_relation
    return bhukti_relation(chart, maha, antar)


def _span_pruned(chart: RamanChart, span: float) -> tuple[str, ...]:
    gate = vd.lifespan_gate(chart, span)
    return tuple(f"{p}: its Mahadasha begins after the span of about {span:.0f} years, so it "
                 f"can act only as a bhukti lord ({cite('minor_lord_only')})"
                 for p, ok in gate.items() if not ok)


# -- rule 1: good event of the house ----------------------------------------------------------

def good_event(chart: RamanChart, matter: Matter, event: Event, span: float) -> TimingRule:
    house = matter.house
    q: dict[str, list[str]] = {}
    for planet, roles in vd.timer_roles(chart, house).items():
        _add(q, planet, f"{', '.join(roles)} (the {ordinal(house)})")
    notes: list[str] = []
    if house in vd.TIMER_KARAKA and matter.karaka and matter.karaka != vd.TIMER_KARAKA[house]:
        _add(q, matter.karaka, f"the karaka of {matter.label} (convention: fills the printed "
                               "karaka slot)")
    cite_key = "influence_set"
    if matter.key == "gains":
        cite_key = "gains_with_second"
        _add(q, lord_of(chart, 2), "owns the 2nd")
        for n, p in chart.planets.items():
            if p.rasi_house == 2:
                _add(q, n, "occupies the 2nd")
            if drishti.aspects_house(n, 2, chart):
                _add(q, n, "aspects the 2nd")
        for planet, why in wealth_yoga_planets(chart):
            _add(q, planet, why)
        _with_nodes(chart, q)
    return TimingRule(event.label, event.kind, cite(cite_key),
                      tuple((p, "; ".join(r)) for p, r in q.items()), _span_pruned(chart, span),
                      f"birth to about age {span:.0f} (the span)",
                      _candidates(chart, q, 0.0, span, tier_house=house), tuple(notes))


def wealth_yoga_planets(chart: RamanChart) -> tuple[tuple[str, str], ...]:
    """Planets of the wealth yogas: HTJAH:16809-16811, then 2nd/5th/9th/11th lords associated
    with another of them (convention, Raman's practice in Charts 217-232)."""
    out: list[tuple[str, str]] = []
    l = {h: lord_of(chart, h) for h in (2, 5, 9, 11)}
    from app.raman_saab.primitives.bhangas import exchange

    def _pos(p: str) -> int:
        q = chart.planets.get(p)
        return q.rasi_house if q else 0
    for a, b in ((2, 5), (2, 11)):
        if l[a] != l[b] and exchange(l[a], l[b], chart):
            why = f"the {ordinal(a)} and {ordinal(b)} lords exchanged ({cite('gains_yogas')})"
            out += [(l[a], why), (l[b], why)]
    if _pos(l[5]) == 5 and _pos(l[9]) == 9:
        why = f"the 5th and 9th lords in the 5th and 9th ({cite('gains_yogas')})"
        out += [(l[5], why), (l[9], why)]
    hs = (2, 5, 9, 11)
    for i, a in enumerate(hs):
        for b in hs[i + 1:]:
            pa, pb = l[a], l[b]
            if pa == pb or pa not in chart.planets or pb not in chart.planets:
                continue
            if _pos(pa) == _pos(pb) or drishti.mutual_aspect(pa, pb, chart):
                why = (f"the {ordinal(a)} lord {pa} associated with the {ordinal(b)} lord {pb} "
                       f"(convention; {cite('association_defined')})")
                out += [(pa, why), (pb, why)]
    return tuple(out)


def wealth_links(chart: RamanChart) -> tuple[str, ...]:
    """The wealth-yoga reasons, de-duplicated (used by the gains conclusion)."""
    seen: list[str] = []
    for _p, why in wealth_yoga_planets(chart):
        if why not in seen:
            seen.append(why)
    return tuple(seen)


# -- rule 2: rise and fall in rank --------------------------------------------------------------

def raja_constituents(chart: RamanChart) -> dict[str, list[str]]:
    q: dict[str, list[str]] = {}
    for p in ("Mars", "Venus", "Saturn"):
        if p in chart.planets and is_yogakaraka(p, chart.asc_sign):
            _add(q, p, f"yogakaraka ({cite('yogakaraka')})")
    for k in (4, 7, 10):
        for t in (5, 9):
            kl, tl = lord_of(chart, k), lord_of(chart, t)
            pk, pt = chart.planets.get(kl), chart.planets.get(tl)
            if kl == tl or pk is None or pt is None:
                continue
            if pk.rasi_house == pt.rasi_house or drishti.mutual_aspect(kl, tl, chart):
                why = (f"the {ordinal(k)} lord {kl} associated with the {ordinal(t)} lord {tl} "
                       f"({cite('raja_kendra_trikona')})")
                _add(q, kl, why)
                _add(q, tl, why)
    l9, l10 = lord_of(chart, 9), lord_of(chart, 10)
    p9, p10 = chart.planets.get(l9), chart.planets.get(l10)
    if l9 != l10 and p9 is not None and p10 is not None:
        if p9.rasi_house == 10 or p10.rasi_house == 9:
            why = f"the 9th and 10th lords in each other's house ({cite('raja_nine_ten')})"
            _add(q, l9, why)
            _add(q, l10, why)
        if drishti.mutual_aspect(l9, l10, chart):
            why = f"the 9th and 10th lords in mutual aspect ({cite('raja_nine_ten_aspect')})"
            _add(q, l9, why)
            _add(q, l10, why)
    return q


def rank(chart: RamanChart, matter: Matter, event: Event, span: float) -> TimingRule:
    q = raja_constituents(chart)
    notes: list[str] = []
    if not q:
        notes.append("no raja yoga of HTJAH:613-634 is formed, so no period is proposed for "
                     "rank")
    else:
        _with_nodes(chart, q)
    return TimingRule(event.label, event.kind, cite("raja_lord_times"),
                      tuple((p, "; ".join(r)) for p, r in q.items()), _span_pruned(chart, span),
                      f"birth to about age {span:.0f} (the span)",
                      _candidates(chart, q, 0.0, span, relation=True, tier_house=10) if q else (),
                      tuple(notes))


# -- rule 3: death of a relative ----------------------------------------------------------------

def marakas_from(chart: RamanChart, ref_sign: int, what: str,
                 planet_sign: Optional[Callable[[str], int]] = None,
                 weights: Optional[dict[str, int]] = None) -> dict[str, list[str]]:
    """Marakas counted from ``ref_sign`` taken as a Lagna (bhavat bhavam). ``weights``, when
    given, collects each planet's strongest channel from this reference in Raman's order
    (HTJAH:783-784): conjoined with a 2nd/7th lord 3, occupant of the 2nd/7th 2, the lord
    itself 1, the 8th/12th occupants and the 12th lord 1 (convention for the last two)."""
    where = planet_sign or (lambda n: chart.planets[n].sign)
    q: dict[str, list[str]] = {}
    best: dict[str, int] = {}

    def _w(p: str, v: int) -> None:
        best[p] = max(best.get(p, 0), v)
    l2, l7 = SIGN_LORDS[sign_from(ref_sign, 2)], SIGN_LORDS[sign_from(ref_sign, 7)]
    _add(q, l2, f"2nd lord from {what} ({cite('maraka_primary')})")
    _add(q, l7, f"7th lord from {what} ({cite('maraka_primary')})")
    _w(l2, 1)
    _w(l7, 1)
    for n in chart.planets:
        c = count(ref_sign, where(n))
        if c in (2, 7, 8, 12):
            _add(q, n, f"in the {ordinal(c)} from {what}")
            _w(n, 2 if c in (2, 7) else 1)
        for lord, num in ((l2, 2), (l7, 7)):
            if n != lord and lord in chart.planets and where(n) == where(lord):
                _add(q, n, f"conjoined with the {ordinal(num)} lord from {what}, the strongest "
                           f"killer ({cite('maraka_associates_strongest')})")
                _w(n, 3)
    l12 = SIGN_LORDS[sign_from(ref_sign, 12)]
    _add(q, l12, f"12th lord from {what} (Raman's practice)")
    _w(l12, 1)
    if weights is not None:
        for p, v in best.items():
            weights[p] = weights.get(p, 0) + v
    return q


def _own_star(chart: RamanChart, q: dict[str, list[str]]) -> frozenset[str]:
    return frozenset(p for p in q if p not in _NODES and vd.nakshatra_lord_of(chart, p) == p)


def relative_death(chart: RamanChart, matter: Matter, event: Event, span: float) -> TimingRule:
    house = RELATIVE_HOUSE[matter.key]
    q: dict[str, list[str]] = {}
    refs: list[tuple[int, str]] = [(sign_from(chart.asc_sign, house),
                                    f"the {ordinal(house)} house")]
    lord = lord_of(chart, house)
    if lord in chart.planets:
        refs.append((chart.planets[lord].sign, f"the {ordinal(house)} lord {lord}"))
    if matter.karaka and matter.karaka in chart.planets:
        refs.append((chart.planets[matter.karaka].sign, f"the karaka {matter.karaka}"))
    moon = chart.planets.get("Moon")
    if matter.key == "father" and moon is not None:
        refs.append((sign_from(moon.sign, 9), "the 9th from the Moon"))
    weights: dict[str, int] = {}
    for ref, what in refs:
        for p, rs in marakas_from(chart, ref, what, weights=weights).items():
            for r in rs:
                _add(q, p, r)
    _with_nodes(chart, q)
    _node_weights(chart, weights)
    no_md = _own_star(chart, q)
    notes = [f"{p} occupies its own star, so it is not proposed as the Mahadasha lord of this "
             f"death ({cite('own_star_cannot_kill')})" for p in sorted(no_md)]
    key = {"mother": "mother_death_marakas", "father": "father_marakas",
           "marriage": "spouse_death_loss_house", "elder_brothers": "brother_death",
           "brothers": "brother_death"}[matter.key]

    def _sade(b: vd.DashaPeriod) -> str:
        return _saturn_note(chart, b, sade_sati=True)
    return TimingRule(event.label, event.kind, cite(key),
                      tuple((p, "; ".join(r)) for p, r in q.items()), _span_pruned(chart, span),
                      f"birth to about age {span:.0f} (the native's span)",
                      _candidates(chart, q, 0.0, span, no_md=no_md, relation=True,
                                  transit=_sade, weights=weights), tuple(notes))


# -- rule 4: marriage ----------------------------------------------------------------------------

def marriage_slots(chart: RamanChart) -> list[tuple[int, str, str]]:
    """The seven slots in Raman's respective order (HTJAH:8524-8527): (slot, planet, why)."""
    out: list[tuple[int, str, str]] = []
    l7, l2 = lord_of(chart, 7), lord_of(chart, 2)
    p7, p2 = chart.planets.get(l7), chart.planets.get(l2)
    if p7 is not None:
        out.append((1, SIGN_LORDS[p7.sign], f"lord of the Rasi occupied by the 7th lord {l7}"))
        out.append((1, SIGN_LORDS[p7.navamsa_sign],
                    f"lord of the Navamsa occupied by the 7th lord {l7}"))
    out.append((2, "Venus", "Venus"))
    out.append((3, "Moon", "the Moon"))
    if p2 is not None:
        out.append((4, SIGN_LORDS[p2.sign], f"lord of the sign occupied by the 2nd lord {l2}"))
    out.append((5, lord_of(chart, 10), "the 10th lord"))
    out.append((6, lord_of(chart, 9), "the 9th lord"))
    out.append((7, l7, "the 7th lord"))
    for n, p in chart.planets.items():
        if p.rasi_house == 7:
            out.append((7, n, "occupant of the 7th"))
    return out


def marriage(chart: RamanChart, matter: Matter, event: Event, span: float) -> TimingRule:
    q: dict[str, list[str]] = {}
    for slot, planet, why in marriage_slots(chart):
        _add(q, planet, f"slot {slot}: {why}")
    _with_nodes(chart, q)
    lo, hi = _MARRIAGE_AGES
    hi = min(hi, span)
    pruned = []
    for md in vd.mahadasha_timeline(chart, 130.0):
        if md.maha in q and (_age(chart, md.end_jd) < lo or _age(chart, md.start_jd) > hi):
            when = "ends in childhood" if _age(chart, md.end_jd) < lo else "operates too late"
            pruned.append(f"{md.maha} Mahadasha {_label(max(md.start_jd, chart.jd_ut))} to "
                          f"{_label(md.end_jd)} {when} ({cite('marriage_age_prune')})")
    points = _marriage_signs(chart)

    def _jup(b: vd.DashaPeriod) -> str:
        return _jupiter_note(chart, b, points)
    cands = _candidates(chart, q, lo, hi, transit=_jup)
    order = {p: min(int(r.split(":")[0].split()[1]) for r in rs if r.startswith("slot"))
             for p, rs in q.items() if any(r.startswith("slot") for r in rs)}
    cands = tuple(sorted(cands, key=lambda c: (order.get(c.maha, 9), order.get(c.antar, 9),
                                                c.start)))
    return TimingRule(event.label, event.kind, cite("marriage_seven_slots"),
                      tuple((p, "; ".join(r)) for p, r in q.items()), tuple(pruned),
                      f"ages {lo:.0f} to {hi:.0f} (convention; {cite('marriage_late_33')})",
                      cands, ("candidates are listed in Raman's slot order, Mahadasha first",))


def _marriage_signs(chart: RamanChart) -> frozenset[int]:
    from app.raman_saab.raman_timing import marriage_points
    signs: set[int] = set()
    for label, lon in marriage_points(chart):
        if label.startswith("Lagna bhava"):
            s = int((lon % 360.0) // 30) + 1
            signs |= {s, sign_from(s, 5), sign_from(s, 9)}
    return frozenset(signs)


# -- rule 5: the native's death -----------------------------------------------------------------

def native_death(chart: RamanChart, matter: Matter, event: Event, span: float,
                 span_class: str) -> TimingRule:
    q: dict[str, list[str]] = {}
    ms = vd.maraka_set(chart)
    for tier, group in (("primary", ms.primary), ("secondary", ms.secondary),
                        ("tertiary", ms.tertiary)):
        for p in sorted(group):
            _add(q, p, f"{tier} maraka from the Lagna or the Moon ({cite('maraka_primary')})")
    nl = varga.navamsa_sign(chart.asc_lon)
    nav = lambda n: chart.planets[n].navamsa_sign  # noqa: E731
    for ref, what in ((nl, "the Navamsa Lagna"),):
        for p, rs in _two_seven(chart, ref, what, nav).items():
            for r in rs:
                _add(q, p, r)
    if "Moon" in chart.planets:
        for p, rs in _two_seven(chart, chart.planets["Moon"].navamsa_sign, "the Navamsa Moon",
                                nav).items():
            for r in rs:
                _add(q, p, r)
    for node, m in vd.delegated_marakas(chart, ms, vd.lifespan_gate(chart, span)):
        _add(q, node, f"{m}'s Mahadasha falls outside the span, so it passes its killing "
                      f"power to {node} ({cite('node_delegation')})")
    _with_nodes(chart, q)
    dw = vd.death_weight_fn(chart, ms, span)
    weights = {p: dw(p) + sum(1 for r in rs if "Navamsa" in r) for p, rs in q.items()}
    _node_weights(chart, weights)
    late = frozenset(p for p, ok in vd.lifespan_gate(chart, span).items() if not ok)
    no_md = _own_star(chart, q) | late
    band = vd._SPAN_BAND_YEARS.get(span_class, 8.0)
    lo, hi = max(0.0, span - band), span + band
    notes = [f"{p} occupies its own star, so it is not proposed as the Mahadasha lord of "
             f"death ({cite('own_star_cannot_kill')})" for p in sorted(no_md - late)]
    notes.append("the window is the span; a strong earlier maraka can end life before it, "
                 f"which this rule does not search (Raman's own caveat, {cite('maraka_caveat')})")

    def _sat(b: vd.DashaPeriod) -> str:
        return _saturn_note(chart, b, sade_sati=False)
    return TimingRule(event.label, event.kind, cite("span_first"),
                      tuple((p, "; ".join(r)) for p, r in q.items()), _span_pruned(chart, span),
                      f"ages {lo:.0f} to {hi:.0f} (the span of about {span:.0f} years, "
                      f"{span_class}, with its band)",
                      _candidates(chart, q, lo, hi, no_md=no_md, relation=True, transit=_sat,
                                  weights=weights),
                      tuple(notes))


def _two_seven(chart: RamanChart, ref: int, what: str,
               where: Callable[[str], int]) -> dict[str, list[str]]:
    q: dict[str, list[str]] = {}
    for n_ in (2, 7):
        _add(q, SIGN_LORDS[sign_from(ref, n_)], f"{ordinal(n_)} lord from {what}")
    for n in chart.planets:
        c = count(ref, where(n))
        if c in (2, 7):
            _add(q, n, f"in the {ordinal(c)} from {what}")
    return q


# -- transits (last; accelerators only) ---------------------------------------------------------

def _sample(b: vd.DashaPeriod, step: float = 30.0) -> list[float]:
    out, jd = [], b.start_jd
    while jd < b.end_jd:
        out.append(jd)
        jd += step
    return out


def _saturn_note(chart: RamanChart, b: vd.DashaPeriod, *, sade_sati: bool) -> str:
    from app.raman_saab.primitives.transits import planet_longitude
    sat, moon = chart.planets.get("Saturn"), chart.planets.get("Moon")
    if sat is None or moon is None or chart.jd_ut is None:
        return ""
    trines = {sign_from(s, k) for s in (sat.sign,) for k in (1, 5, 9)}
    nav_trines = {sign_from(sat.navamsa_sign, k) for k in (1, 5, 9)}
    for jd in _sample(b):
        lon = planet_longitude(jd, "Saturn", ayanamsa=chart.ayanamsa)
        s = int(lon // 30) + 1
        if sade_sati and count(moon.sign, s) in (12, 1, 2):
            return (f"accelerator: Saturn transits the {ordinal(count(moon.sign, s))} from the "
                    f"natal Moon (sade sati) from {_label(jd)} ({cite('transit_accelerator')})")
        if not sade_sati and s in trines and varga.navamsa_sign(lon) in nav_trines:
            return (f"accelerator: Saturn transits {SIGNS[s]}, a trine to its natal Rasi and "
                    f"Navamsa, from {_label(jd)} ({cite('saturn_transit_death')})")
    return ""


def _jupiter_note(chart: RamanChart, b: vd.DashaPeriod, signs: frozenset[int]) -> str:
    from app.raman_saab.primitives.transits import planet_longitude
    if not signs or chart.jd_ut is None:
        return ""
    for jd in _sample(b):
        s = int(planet_longitude(jd, "Jupiter", ayanamsa=chart.ayanamsa) // 30) + 1
        if s in signs:
            return (f"accelerator: Jupiter transits {SIGNS[s]}, the Lagna-plus-7th point or its "
                    f"trine, from {_label(jd)} (Charts A and B)")
    return ""


def timing_for(chart: RamanChart, matter: Matter, span: Optional[float],
               span_class: Optional[str]) -> tuple[TimingRule, ...]:
    """Every timing rule that applies to ``matter``'s events. Empty without an ephemeris chart
    (a printed-position chart has no birth time, so no periods)."""
    if chart.jd_ut is None or span is None:
        return ()
    out: list[TimingRule] = []
    for ev in matter.events:
        try:
            if ev.kind == "good_event":
                out.append(good_event(chart, matter, ev, span))
            elif ev.kind == "rank":
                out.append(rank(chart, matter, ev, span))
            elif ev.kind == "relative_death":
                out.append(relative_death(chart, matter, ev, span))
            elif ev.kind == "marriage":
                out.append(marriage(chart, matter, ev, span))
            elif ev.kind == "native_death":
                out.append(native_death(chart, matter, ev, span, span_class or "madhya"))
        except Exception:  # a timing defect must never cost the reader its verdict; logged
            logger.exception("procedure timing failed for H%s %s %s", matter.house,
                             matter.key, ev.kind)
    return tuple(out)
