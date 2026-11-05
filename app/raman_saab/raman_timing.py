"""Raman's timing checks the report lacked: the tables from the timing gap check (USER DECISION
2026-10-24, "timing gap check, all 16 fixes"; docs/raman_saab/research/engine-timing-gap-check.md).

Every table here is REPORT-ONLY. It reads the chart, the Vimshottari periods and transit
longitudes, and states a Raman rule beside each row with its citation; nothing here feeds a
verdict (PREC-10), and the golden ratchet cannot see it. Each table is a `TimingTable` whose
rows are plain strings, so the three renderers (markdown, standalone HTML, interactive page)
print every column the same way and none can drop one.

Period checks (rendered under the timeline):
  * ``period_lords`` — per graha: Mahadasha start and the lifespan gate (fix 5), the star lord
    and its houses/maraka status with Raman's veto/boost note (fix 4), the bhava-sandhi
    residential strength (fix 16), maraka order and delegation (fix 7).
  * ``bhukti_relations`` — each bhukti of the running Mahadasha read by Raman's relation rules
    (fix 6) and the 3rd/5th/7th-star rule (fix 4).
  * ``antaras`` — the running bhukti's antaras judged by position from the MD/AD lords (fix 15).
  * ``yoga_lords`` — each fired yoga's lords with the lifespan gate and sandhi (fixes 5, 16).
  * ``maraka_order`` — the maraka set in Raman's printed order (fix 7).

Transit checks (rendered under the gochara section):
  * ``sade_sati_rounds`` (fix 8), ``transit_dasa_gate`` (fix 10), ``transit_natal_points`` and
    ``malefic_meetings`` (fix 11), ``saturn_8_12_lords`` (fix 7), ``marriage_point`` (fix 12),
    ``sign_parts`` (fix 13).

Usage:
    from app.raman_saab.raman_timing import period_checks, transit_checks
    period_checks(chart, ref_jd, yogas, yoga_lords)
    transit_checks(chart, ref_jd, years_back=10, years_forward=20)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Final, Iterable, Optional

import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.ordinals import ordinal
from app.raman_saab.primitives import transits as tr
from app.raman_saab.primitives import vimshottari as vd

logger = logging.getLogger(__name__)

SIGN: Final[tuple[str, ...]] = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")
NAKSHATRA: Final[tuple[str, ...]] = (
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya",
    "Aslesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Visakha", "Anuradha", "Jyeshta", "Mula", "Purva Ashadha", "Uttara Ashadha", "Sravana",
    "Dhanishta", "Satabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati")
GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
#: Natural malefics, per the project's locked avastha classification (CLAUDE.md).
MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_NAK_SPAN: Final[float] = 360.0 / 27.0


@dataclass(frozen=True)
class TimingTable:
    """One Raman timing table: a key, a title, the note that carries its citations, the column
    names, and the rows (every cell already a string)."""
    key: str
    title: str
    note: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


# ── small helpers ─────────────────────────────────────────────────────────────

def _label(jd: float) -> str:
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')[int(m)-1]} {int(y)}"


def _span(a: float, b: float) -> str:
    return f"{_label(a)} to {_label(b)}"


def _sign_from(base: int, n: int) -> int:
    return (base - 1 + n - 1) % 12 + 1


def _count(from_sign: int, to_sign: int) -> int:
    """House of `to_sign` counted from `from_sign` (1..12)."""
    return (to_sign - from_sign) % 12 + 1


def _trines(sign: int) -> frozenset[int]:
    return frozenset(_sign_from(sign, k) for k in (1, 5, 9))


def _lord_of_house(chart: RamanChart, house: int) -> str:
    return SIGN_LORDS[_sign_from(chart.asc_sign, house)]


def _houses_owned(chart: RamanChart, planet: str) -> tuple[int, ...]:
    return tuple(h for h in range(1, 13) if _lord_of_house(chart, h) == planet)


def _nak_index(lon: float) -> int:
    return int((lon % 360.0) // _NAK_SPAN)


def _residential(chart: RamanChart, planet: str) -> Optional[tuple[int, float]]:
    from app.raman_saab.primitives.residential_strength import residential_strength
    p = chart.planets.get(planet)
    if p is None or len(chart.bhava_madhyas) != 12 or len(chart.bhava_sandhis) != 12:
        return None
    return residential_strength(p.lon, chart.bhava_madhyas, chart.bhava_sandhis)


def sandhi_cell(chart: RamanChart, planet: str) -> str:
    """The planet's residential strength, with Raman's sandhi rule: "The dasa periods of planets
    in Bhava sandhis (junctional points) will be unable to produce their full results"
    (HPA-24:98-100; residential strength is "the percentage of results a planet is capable of
    giving by virtue of occupation of a house", 3HC:1300-1304)."""
    rs = _residential(chart, planet)
    if rs is None:
        return "- (no cusps)"
    bhava, s = rs
    note = ("near a bhava sandhi: cannot give its full results" if s <= 0.2
            else "near the bhava madhya: nearly full results" if s >= 0.8
            else "part-way: a partial share of results")
    return f"{s:.2f} of bhava {bhava} ({note})"


def _all_bhuktis(chart: RamanChart) -> list[vd.DashaPeriod]:
    out: list[vd.DashaPeriod] = []
    for md in vd.mahadasha_timeline(chart, 120.0):
        out.extend(vd.bhuktis(md))
    return out


def _bhuktis_overlapping(bh: list[vd.DashaPeriod], lo: float, hi: float) -> list[vd.DashaPeriod]:
    return [b for b in bh if b.start_jd < hi and b.end_jd > lo]


def _quality(chart: RamanChart, lords: Iterable[str]) -> str:
    """'good' when every lord delivers well, 'bad' when one delivers poorly and none well,
    otherwise 'mixed' — from `vimshottari.lord_quality` (HTJAH-II:10004-10008)."""
    tags = [vd.lord_quality(chart, g).tag for g in lords]
    if tags and all(t == "well" for t in tags):
        return "good"
    if "poorly" in tags and "well" not in tags:
        return "bad"
    return "mixed"


def _maraka_cell(ms: vd.MarakaSet, weight: Callable[[str], int], g: str) -> str:
    if g in ms.primary:
        rank = {3: "conjunct a 2nd/7th lord", 2: "occupant / aspecting a 2nd/7th lord",
                1: "a 2nd/7th lord"}[ms.rank(g)]
        return f"primary ({rank}), weight {weight(g)}"
    if g in ms.secondary:
        return f"secondary, weight {weight(g)}"
    if g in ms.tertiary:
        return f"tertiary, weight {weight(g)}"
    w = weight(g)
    return f"delegated maraka, weight {w}" if w else "-"


def _sample(lo: float, hi: float, step: float) -> Iterable[float]:
    jd = lo
    while jd < hi:
        yield jd
        jd += step


def _merge(hits: list[tuple[float, bool]], step: float) -> list[tuple[float, float]]:
    """Consecutive True samples merged into [start, end) spans."""
    spans: list[tuple[float, float]] = []
    start: Optional[float] = None
    last = None
    for jd, ok in hits:
        if ok and start is None:
            start = jd
        if not ok and start is not None:
            spans.append((start, jd))
            start = None
        last = jd
    if start is not None and last is not None:
        spans.append((start, last + step))
    return spans


# ── period checks ─────────────────────────────────────────────────────────────

def star_lord_note(chart: RamanChart, planet: str, ms: vd.MarakaSet) -> tuple[str, str, str]:
    """(star lord, its houses, Raman's note) for `planet`'s natal nakshatra (fix 4).

    "the Moon in this case is in his own constellation, he could not cause the death of the
    mother in his own Dasha ... In Chart No. 64 on the other hand the Moon is in the
    constellation of Mars, a Maraka" (HTJAH-I:4515-4518); "Mercury's situation in the
    constellation of Mars [lord of the 2nd and 7th, a maraka] ... rendered him so powerful as to
    make the native fall from power in his sub-period" (NH:15255-15259); "Rahu is in the
    nakshatra of Mercury lord of the 9th, resulted in ... name and fame greatly increasing"
    (NH:14584-14586)."""
    sl = vd.nakshatra_lord_of(chart, planet)
    if sl is None:
        return "-", "-", "-"
    owned = _houses_owned(chart, sl)
    sp = chart.planets.get(sl)
    houses = ", ".join(f"owns {ordinal(h)}" for h in owned)
    if sp is not None:
        houses = (houses + "; " if houses else "") + f"in {ordinal(sp.rasi_house)}"
    if sl == planet:
        note = "own star: the planet's own significations stand (HTJAH-I:4515-4516)"
    elif sl in ms.primary:
        note = ("star lord is a primary maraka: the period can carry the star lord's maraka "
                "colour (HTJAH-I:4516-4518; NH:15255-15259)")
    elif set(owned) & {5, 9}:
        note = ("star lord rules a trine (5th/9th): the period is lifted "
                "(NH:14584-14586)")
    elif set(owned) & {6, 8, 12}:
        note = "star lord rules a dusthana (6th/8th/12th): the delivery is coloured by it"
    else:
        note = "-"
    return sl, houses or "-", note


def _period_lords(chart: RamanChart, ms: vd.MarakaSet, weight: Callable[[str], int],
                  gate: dict[str, bool], delegated: dict[str, str]) -> TimingTable:
    mds = {md.maha: md for md in reversed(vd.mahadasha_timeline(chart, 120.0))}
    rows: list[tuple[str, ...]] = []
    for g in GRAHAS:
        p = chart.planets.get(g)
        if p is None:
            continue
        md = mds.get(g)
        start = _label(md.start_jd) if md is not None else "-"
        if g in gate:
            gate_cell = ("MD begins inside the span" if gate[g]
                         else "MD begins after the span: acts only as a bhukti lord")
        else:
            gate_cell = "-"
        sl, sl_houses, note = star_lord_note(chart, g, ms)
        sl_maraka = _maraka_cell(ms, weight, sl) if sl != "-" else "-"
        deleg = (f"carries {delegated[g]}'s maraka power (HTJAH-I:11194-11203)"
                 if g in delegated else "-")
        rows.append((g, start, gate_cell, NAKSHATRA[_nak_index(p.lon)], sl, sl_houses,
                     sl_maraka, note, sandhi_cell(chart, g), _maraka_cell(ms, weight, g),
                     deleg))
    return TimingTable(
        "period_lords", "Period lords: lifespan gate, star lord, sandhi, maraka order",
        "Lifespan gate: \"Whether the native of the horoscope is likely to enjoy the Dasha of the "
        "ascendant lord or for that matter, the Dasha of the lord of any house in consideration. "
        "For knowing this, the longevity should be previously ascertained\" (HTJAH-I:1578-1580), "
        "with the ayurdaya span; a lord whose Mahadasha begins after it gives results only as a "
        "bhukti lord (\"Venus can give the effects of first house only as minor lord\", "
        "HTJAH-I:1622-1623; HPA-15:21-37). Star lord: \"the fact of a planet being situated in a "
        "particular constellation is of paramount importance especially in the matter of "
        "predicting significant events\" (HTJAH-I:4518-4520). Sandhi: \"The dasa periods of "
        "planets in Bhava sandhis (junctional points) will be unable to produce their full "
        "results\" (HPA-24:98-100). Maraka order: \"planets in conjunction with lords of 2nd and "
        "7th are the most powerful in causing death, while the lords themselves are least "
        "powerful\" (HTJAH-I:783-784); a node in a late maraka's sign carries its power "
        "(HTJAH-I:11194-11203). Report-only: no verdict reads these columns.",
        ("lord", "MD starts", "lifespan gate", "nakshatra", "star lord", "star lord's houses",
         "star lord as maraka", "star-lord note", "residential strength (sandhi)",
         "maraka tier", "delegation"),
        tuple(rows))


def bhukti_relation(chart: RamanChart, maha: str, antar: str,
                    raja_yogas: tuple[str, ...] = ()) -> tuple[int, tuple[str, ...]]:
    """(house of the AD lord counted from the MD lord, Raman's readings) — fix 6.

    Raman's rules, each cited where it is applied:
      * 6/8 and 12/2 adverse: "Unfavourable results will be realised when the sub-lord and the
        major lord are situated in the 6th and 8th or 12th and 2nd from each other" (HPA-24:150-152);
      * 3/11 ideal: "disposed in the 3rd and 11th from each other—an ideal combination"
        (HTJAH-I:14115-14116);
      * mutual quadrants (HTJAH-I:14122-14123) and mutual aspect (HTJAH-I:16101), favourable;
      * 5th/9th lords: "The sub-period of the lord of the 5th in the major period of the lord of
        the 9th or vice versa is supposed to produce good effects" (HPA-24:154-156);
      * Saturn-Venus: "the mutual periods of Saturn and Venus are fatal to Raja-Yogas" with the
        proviso "if the Raja-Yoga is powerful enough, the bhanga ... will be set right in
        appropriate Periods" (HTJAH-I:16106-16112);
      * the 2nd and 7th from the major lord read as maraka from him: "the 7th from the major
        lord" (NH:12230-12231), "a house of death from the major lord" (NH:13789-13790)."""
    pa, pb = chart.planets.get(maha), chart.planets.get(antar)
    if pa is None or pb is None or maha == antar:
        return 0, ("the major lord's own bhukti: no relation to read",) if maha == antar else ()
    seat = _count(pa.rasi_house, pb.rasi_house)
    out: list[str] = []
    if seat in (6, 8):
        out.append("6th/8th from each other: unfavourable (HPA-24:150-152)")
    if seat in (2, 12):
        out.append("2nd/12th from each other: unfavourable (HPA-24:150-152)")
    if seat in (3, 11):
        out.append("3rd/11th from each other: Raman's ideal combination (HTJAH-I:14115-14116)")
    if seat in (1, 4, 7, 10):
        out.append("mutual quadrants: favourable (HTJAH-I:14122-14123)")
    if drishti.mutual_aspect(maha, antar, chart):
        out.append("mutual aspect: favourable (HTJAH-I:16101)")
    l5, l9 = _lord_of_house(chart, 5), _lord_of_house(chart, 9)
    if {maha, antar} == {l5, l9} and l5 != l9:
        out.append("5th and 9th lords in each other's periods: good (HPA-24:154-156)")
    if {maha, antar} == {"Saturn", "Venus"}:
        if raja_yogas:
            out.append("Saturn-Venus mutual periods, against the fired raja yogas ("
                       + ", ".join(raja_yogas) + "): damaging to them unless the yoga is "
                       "powerful enough to be set right later (HTJAH-I:16106-16112)")
        else:
            out.append("Saturn-Venus mutual periods: no raja yoga fired here for them to "
                       "damage (HTJAH-I:16106-16112)")
    if seat in (2, 7):
        out.append(f"the {ordinal(seat)} from the major lord: a house of death from him "
                   "(NH:12230-12231, 13789-13790)")
    return seat, tuple(out)


def star_trial(chart: RamanChart, maha: str, antar: str) -> str:
    """Fix 4: "During the dasa period of a malefic planet when the sub-period of a planet ruling
    the 3rd, the 5th or the 7th star (reckoned for the natal star) is in progress the subject
    will have a period of trial and tribulation" (HPA-24:144-148)."""
    moon = chart.planets.get("Moon")
    if moon is None:
        return "-"
    janma = _nak_index(moon.lon)
    rulers = {n: vd._NAK_LORDS[(janma + n - 1) % 27 % 9] for n in (3, 5, 7)}
    hit = [ordinal(n) for n, lord in rulers.items() if lord == antar]
    if not hit:
        return "-"
    if maha in MALEFICS:
        return (f"rules the {'/'.join(hit)} star from the natal star in a malefic's Dasha: a "
                "period of trial (HPA-24:144-148)")
    return (f"rules the {'/'.join(hit)} star from the natal star, but the major lord is not a "
            "malefic: Raman's trial rule does not apply (HPA-24:144-148)")


def _bhukti_relations(chart: RamanChart, ref_jd: float,
                      raja: tuple[str, ...]) -> Optional[TimingTable]:
    cur = vd.dasha_on(chart, ref_jd)
    if cur is None:
        return None
    md = next((m for m in vd.mahadasha_timeline(chart, 120.0) if m.maha == cur.maha
               and m.start_jd <= ref_jd < m.end_jd), None)
    if md is None:
        return None
    rows: list[tuple[str, ...]] = []
    for b in vd.bhuktis(md):
        seat, reads = bhukti_relation(chart, b.maha, b.antar or b.maha, raja)
        now = " (now)" if b.contains(ref_jd) else ""
        rows.append((f"{b.maha}/{b.antar}{now}", _span(b.start_jd, b.end_jd),
                     ordinal(seat) if seat else "-", "; ".join(reads) or "-",
                     star_trial(chart, b.maha, b.antar or b.maha), sandhi_cell(chart, b.antar)))
    return TimingTable(
        "bhukti_relations", f"Bhuktis of the running {md.maha} Mahadasha, by Raman's relation rules",
        "Each bhukti lord read from the major lord, as Raman reads them: 6/8 and 12/2 "
        "unfavourable (HPA-24:150-152); 3/11 ideal (HTJAH-I:14115-14116); mutual quadrants "
        "(HTJAH-I:14122-14123) or mutual aspect (HTJAH-I:16101) favourable; 5th and 9th lords good "
        "(HPA-24:154-156); Saturn-Venus against fired raja yogas (HTJAH-I:16106-16112); the 2nd "
        "and 7th from the major lord as a house of death from him (NH:12230-12231, "
        "13789-13790). Star trial: the 3rd/5th/7th star from the natal star in a malefic's "
        "Dasha (HPA-24:144-148). Sandhi: the bhukti lord's residential strength (HPA-24:98-100). "
        "A row can carry readings that pull both ways; Raman weighs them with the houses the "
        "lords rule.",
        ("bhukti", "dates", "AD lord from MD lord", "Raman's relation reading", "star trial",
         "AD lord's residential strength (sandhi)"),
        tuple(rows))


def _antaras(chart: RamanChart, ref_jd: float, ms: vd.MarakaSet) -> Optional[TimingTable]:
    cur = vd.dasha_on(chart, ref_jd)
    if cur is None or cur.antar is None:
        return None
    pa, pb = chart.planets.get(cur.maha), chart.planets.get(cur.antar)
    if pa is None or pb is None:
        return None
    l8 = _lord_of_house(chart, 8)
    rows: list[tuple[str, ...]] = []
    for pr in vd.pratyantars(cur):
        pc = chart.planets.get(pr.pratyantar or "")
        if pc is None:
            continue
        f_md, f_ad = _count(pa.rasi_house, pc.rasi_house), _count(pb.rasi_house, pc.rasi_house)
        notes: list[str] = []
        if f_md == 12 and f_ad == 12:
            notes.append("12th from both the major and minor lords (HTJAH-I:6640)")
        if {f_md, f_ad} & {2, 12} and not (f_md == 12 and f_ad == 12):
            notes.append("dwirdwadasa (2nd/12th) from a period lord (HTJAH-I:6648-6649)")
        roles: list[str] = []
        if pr.pratyantar in ms.all():
            roles.append("maraka")
        if pr.pratyantar == l8:
            roles.append("8th lord")
        for h, k in vd.TIMER_KARAKA.items():
            if k == pr.pratyantar:
                roles.append(f"karaka of the {ordinal(h)}")
        rows.append((pr.pratyantar or "-", _span(pr.start_jd, pr.end_jd)
                     + (" (now)" if pr.contains(ref_jd) else ""),
                     ordinal(f_md), ordinal(f_ad), "; ".join(notes) or "-",
                     ", ".join(roles) or "-"))
    return TimingTable(
        "antaras", f"Antaras of the running {cur.maha}/{cur.antar} bhukti, by position",
        "Raman judges an antara lord by where it stands from the major and minor lords and by "
        "its role: \"The Sun is Chandra Lagnadhipati and occupies the 12th from the major and "
        "minor lords\" (HTJAH-I:6639-6640); \"The Sun is in the 8th from Lagna having "
        "DwirdwaDasha position from major and sub-lords\" (HTJAH-I:6648-6649); a maraka / 8th-lord "
        "role carries the antara (\"Hence mother's death took place in Rahu Dasha, Venus "
        "Bhukti, Venus Antara\", HTJAH-I:4476-4483).",
        ("antara lord", "dates", "from MD lord", "from AD lord", "position reading", "role"),
        tuple(rows))


def _yoga_lords(chart: RamanChart, yoga_lords: Iterable[tuple[str, str]],
                gate: dict[str, bool]) -> Optional[TimingTable]:
    rows: list[tuple[str, ...]] = []
    seen: set[tuple[str, str]] = set()
    for name, g in yoga_lords:
        if (name, g) in seen or g not in chart.planets:
            continue
        seen.add((name, g))
        gate_cell = ("-" if g not in gate else "MD inside the span" if gate[g]
                     else "MD after the span: ripens only in its bhuktis")
        rows.append((name, g, gate_cell, sandhi_cell(chart, g)))
    if not rows:
        return None
    return TimingTable(
        "yoga_lords", "Yoga lords: lifespan gate and sandhi",
        "A yoga ripens in its lords' periods (HTJAH-I:4324); a lord whose Mahadasha begins after "
        "the span gives it only in bhuktis (HTJAH-I:1578-1580, 1622-1623), and a lord near a "
        "bhava sandhi cannot give its full results (HPA-24:98-100; residential strength for "
        "yogas, 3HC:1300-1304). The lords are the grahas the yoga's own text names.",
        ("yoga", "lord", "lifespan gate", "residential strength (sandhi)"),
        tuple(rows))


def _maraka_order(chart: RamanChart, ms: vd.MarakaSet, weight: Callable[[str], int],
                  gate: dict[str, bool], delegated: dict[str, str]) -> TimingTable:
    rows: list[tuple[str, ...]] = []
    order = sorted(ms.all() | set(delegated), key=lambda g: (-weight(g), g))
    for g in order:
        tier = ("primary" if g in ms.primary else "secondary" if g in ms.secondary
                else "tertiary" if g in ms.tertiary else "delegated")
        gate_cell = ("-" if g not in gate else "inside the span" if gate[g]
                     else "after the span")
        rows.append((g, tier, str(weight(g)), gate_cell,
                     f"from {delegated[g]}" if g in delegated else "-"))
    return TimingTable(
        "maraka_order", "Marakas in Raman's order",
        "Primary: \"planets in conjunction with lords of 2nd and 7th are the most powerful in "
        "causing death, while the lords themselves are least powerful\" (HTJAH-I:783-784) — "
        "weights 5/4/3; secondary 2 (HTJAH-I:786-788); tertiary 1, Saturn \"in conjunction, "
        "association or aspect with the Maraka\" (HTJAH-I:793-794). Variant on record, not "
        "applied: HPA-15:41-46 ranks the 2nd over the 7th. A maraka whose Mahadasha begins after "
        "the span delegates to a node in its sign (HTJAH-I:11194-11203). An order of classical "
        "signals, not a date.",
        ("graha", "tier", "weight", "MD vs span", "delegation"),
        tuple(rows))


def period_checks(chart: RamanChart, ref_jd: float, yogas: tuple = (),
                  yoga_lords: Iterable[tuple[str, str]] = ()) -> tuple[TimingTable, ...]:
    """The period-side tables (fixes 4, 5, 6, 7, 15, 16). Empty on a Track-B chart."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    ms = vd.maraka_set(chart)
    gate = vd.lifespan_gate(chart)
    delegated = dict(vd.delegated_marakas(chart, ms, gate))
    weight = vd.death_weight_fn(chart, ms)
    raja = tuple(getattr(y, "name", "") for y in yogas if getattr(y, "kind", "") == "raja")
    out: list[TimingTable] = []
    for build in (lambda: _period_lords(chart, ms, weight, gate, delegated),
                  lambda: _bhukti_relations(chart, ref_jd, raja),
                  lambda: _antaras(chart, ref_jd, ms),
                  lambda: _yoga_lords(chart, tuple(yoga_lords), gate),
                  lambda: _maraka_order(chart, ms, weight, gate, delegated)):
        try:
            t = build()
        except Exception:  # noqa: BLE001 — one table must never cost the others
            logger.info("Raman period table skipped", exc_info=True)
            continue
        if t is not None and t.rows:
            out.append(t)
    return tuple(out)


# ── transit checks ────────────────────────────────────────────────────────────

def _lon(jd: float, planet: str, az: str) -> float:
    return tr.planet_longitude(jd, planet, ayanamsa=az)


def _sign(lon: float) -> int:
    return int((lon % 360.0) // 30.0) + 1


def _sade_sati_rounds(chart: RamanChart, az: str, dws: tuple,
                      bh: list[vd.DashaPeriod], ref_jd: float) -> Optional[TimingTable]:
    from app.raman_saab.primitives import ashtakavarga, ayurdaya
    moon = chart.planets.get("Moon")
    if moon is None:
        return None
    span = ayurdaya.longevity(chart).total_years
    lo = chart.jd_ut
    hi = chart.jd_ut + max(span, 1.0) * DAYS_PER_VEDIC_YEAR
    step = 10.0
    band = {_sign_from(moon.sign, 12), moon.sign, _sign_from(moon.sign, 2)}
    hits = [(jd, _sign(_lon(jd, "Saturn", az)) in band) for jd in _sample(lo, hi, step)]
    spans = _merge(hits, step)
    # a retrograde dip out of the band within ~2 years is the same episode
    episodes: list[list[float]] = []
    for a, b in spans:
        if episodes and a - episodes[-1][1] < 2 * DAYS_PER_VEDIC_YEAR:
            episodes[-1][1] = b
        else:
            episodes.append([a, b])
    try:
        sav = ashtakavarga.sarvashtakavarga(chart)
    except Exception:  # noqa: BLE001
        sav = {}
    sav_cells = ", ".join(f"{SIGN[s]} {sav.get(s, '-')}" for s in
                          (_sign_from(moon.sign, 12), moon.sign, _sign_from(moon.sign, 2)))
    all_over = bool(sav) and all(sav.get(s, 0) > 30 for s in band)
    reading = {1: "first round: most of the listed Sade-Sati results manifest (AFB-12:169-171)",
               2: "second round: Raman reads no evil in it (AFB-12:172); \"the evil effects "
                  "will only be moderate\" (HPA-33:294-296)",
               3: "third round: the round Raman reads for longevity, and only where the ruling "
                  "Dasa warrants it (AFB-12:172-174)"}
    rows: list[tuple[str, ...]] = []
    for i, (a, b) in enumerate(episodes, 1):
        running = _bhuktis_overlapping(bh, a, b)
        names = ", ".join(f"{p.maha}/{p.antar}" for p in running)
        dw = [w for w in dws if w.start_jd < b and w.end_jd > a]
        warrant = ("overlaps the engine's ranked maraka windows: "
                   + ", ".join(f"{w.maha}/{w.antar}" for w in dw) if dw
                   else "no ranked maraka window in this round")
        lords = {p.maha for p in running} | {p.antar for p in running if p.antar}
        strength = _quality(chart, sorted(lords))
        now = " (now)" if a <= ref_jd < b else ""
        rows.append((ordinal(i) + now, _span(a, b), reading.get(i, f"{ordinal(i)} round: beyond "
                     "the three rounds Raman describes"), names or "-",
                     f"running lords deliver: {strength}", warrant,
                     sav_cells + ("; all three above 30: the evil is minimised (ASP-13:613-616)"
                                  if all_over else "; not all above 30")))
    if not rows:
        return None
    return TimingTable(
        "sade_sati_rounds", "Sade-Sati rounds since birth (within the span)",
        "Raman counts the rounds: \"One having good longevity can come under the sway of 7½ "
        "years' Saturn thrice in his lifetime\" (AFB-12:169-170) — the first brings most of the "
        "results, the second no evil, the third is read for longevity only where the ruling "
        "Dasa warrants it (AFB-12:171-174); the period is malefic \"unless the ruling period is "
        "powerful\" (AFB-12:161); a good Dasa outweighs a second round (HPA-33:294-298); and "
        "\"The intensity of evil results produced during the period 7½ years' Saturn gets "
        "minimised if the 12th, 1st and 2nd from the Moon has more than 30 bindus in the "
        "Sarvashtakavarga\" (ASP-13:613-616). Whether the Dasa warrants it is read from the "
        "engine's ranked maraka windows (the maraka bhuktis near the ayurdaya span). Saturn "
        "sampled every 10 days in the chart's own ayanamsa; a retrograde dip of under two years "
        "stays in its round.",
        ("round", "dates", "Raman's reading", "bhuktis running", "ruling-period strength",
         "does the Dasa warrant it", "SAV of 12th/1st/2nd from the Moon"),
        tuple(rows))


def _house_tier(chart: RamanChart, house: int, b: vd.DashaPeriod) -> Optional[str]:
    timers = vd.timer_set(chart, house)
    return vd.period_tier(chart, b.maha, b.antar, b.maha in timers,
                          b.antar is not None and b.antar in timers)


def _transit_dasa_gate(chart: RamanChart, outlook: dict, bh: list[vd.DashaPeriod],
                       ref_jd: float) -> Optional[TimingTable]:
    rows: list[tuple[str, ...]] = []
    segs = sorted((s for v in outlook.values() for s in v if (s.end_jd - s.start_jd) >= 25),
                  key=lambda s: (s.start_jd, s.planet))
    for s in segs:
        house = _count(chart.asc_sign, s.sign)
        acts: list[str] = []
        lords: set[str] = set()
        for b in _bhuktis_overlapping(bh, s.start_jd, s.end_jd):
            t = _house_tier(chart, house, b)
            if t is not None:
                acts.append(f"{b.maha}/{b.antar} ({t})")
                lords |= {b.maha, b.antar or b.maha}
        if not acts:
            combo = ("no running period activates this house: the transit stands alone, which "
                     "Raman holds \"cannot be tenable\" (ASP-13:62-74)")
        else:
            q = _quality(chart, sorted(lords))
            good = s.gochara_good
            combo = {("bad", False): "bad Dasa with bad transit: the evil is heightened "
                                     "(AFB-12:38-48)",
                     ("good", False): "good Dasa with bad transit: the resultant is still "
                                      "favourable (HPA-33:294-298)",
                     ("bad", True): "bad Dasa with benign transit: the Dasa's evil is held back "
                                    "(NH:14074-14078)",
                     ("good", True): "good Dasa with good transit: both point the same way"
                     }.get((q, good), "mixed Dasa: weigh the period lords' strength")
        rows.append((s.planet, _span(s.start_jd, s.end_jd), SIGN[s.sign], ordinal(house),
                     "favourable" if s.gochara_good else "adverse",
                     "; ".join(acts) or "-", combo))
    if not rows:
        return None
    return TimingTable(
        "transit_dasa_gate", "Each transit window, gated by the running Dasa",
        "\"Gochara or transit results are always subordinate to the ... radical or birth "
        "influences\"; the view that transits act \"irrespective of directional influences\" "
        "\"cannot be tenable\" (ASP-13:62-74). A transit advances \"results of the bhava "
        "represented by the Rasi as reckoned from the ascendant\" (ASP-13:396-399), so each row "
        "names that house and the bhuktis that activate it (Raman's tiers on its own factor list). "
        "Combination labels: illness indicated by the Dasa turns \"of serious type\" when the "
        "Gochara is bad (AFB-12:38-48); a well-placed Dasa against bad transits leaves \"the "
        "resultant ... still favourable\" (HPA-33:294-298); a Dasa lord could not kill \"especially "
        "that Gochara or transiting positions were not adverse\" (NH:14074-14078). Dasa quality "
        "is the period lords' delivery tag (well/poorly).",
        ("planet", "window", "sign", "house from Lagna", "station from Moon",
         "bhuktis that activate the house", "Dasa x transit"),
        tuple(rows))


def _scan_window(chart: RamanChart, ref_jd: float) -> Optional[tuple[float, float, str]]:
    """The running bhukti and the next one: the span the natal-point scans cover."""
    bh = _all_bhuktis(chart)
    idx = next((i for i, b in enumerate(bh) if b.contains(ref_jd)), None)
    if idx is None:
        return None
    nxt = bh[idx + 1] if idx + 1 < len(bh) else bh[idx]
    cur = bh[idx]
    return cur.start_jd, nxt.end_jd, f"{cur.maha}/{cur.antar} and {nxt.maha}/{nxt.antar}"


def _transit_natal_points(chart: RamanChart, az: str, ref_jd: float,
                          ms: vd.MarakaSet) -> Optional[TimingTable]:
    win = _scan_window(chart, ref_jd)
    if win is None:
        return None
    lo, hi, label = win
    bh = [b for b in _all_bhuktis(chart) if b.start_jd < hi and b.end_jd > lo]
    points: dict[str, str] = {}
    for b in bh:
        points.setdefault(b.maha, "MD lord")
        if b.antar:
            points.setdefault(b.antar, "AD lord")
    for g in sorted(ms.all()):
        points.setdefault(g, "maraka")
    points.setdefault("Moon", "Moon")
    step = 5.0
    samples = list(_sample(lo, hi, step))
    tl = {pl: [_lon(jd, pl, az) for jd in samples] for pl in ("Saturn", "Rahu")}
    targets: list[tuple[str, str, int, int]] = [
        ("Lagna", "Lagna", chart.asc_sign, varga.navamsa_sign(chart.asc_lon))]
    for g, role in points.items():
        p = chart.planets.get(g)
        if p is not None:
            targets.append((g, role, p.sign, p.navamsa_sign))
    rows: list[tuple[str, ...]] = []
    for pl in ("Saturn", "Rahu"):
        for name, role, rs, ns in targets:
            if name == pl:
                continue
            kinds = (("rasi over natal rasi", lambda L: _sign(L) == rs),
                     ("rasi over natal Navamsa sign", lambda L: _sign(L) == ns),
                     ("Navamsa over natal Navamsa sign", lambda L: varga.navamsa_sign(L) == ns))
            for kind, test in kinds:
                spans = _merge([(jd, test(L)) for jd, L in zip(samples, tl[pl])], step)
                for a, b in spans:
                    rows.append((pl, f"{name} ({role})", kind, _span(a, b)))
    if not rows:
        return None
    return TimingTable(
        "transit_natal_points", f"Saturn and Rahu over natal points ({label})",
        "Raman times events by Saturn over a period lord's natal signs in both charts: \"The "
        "death occurred when Saturn (lord of the 2nd) was transiting Scorpio Navamsa in which "
        "Mercury [the sub-lord] is placed\" (NH:13784-13786); \"Saturn was about to leave Gemini "
        "by transit and the Sun [the major lord] is placed in Gemini Navamsa\" (NH:13792-13793); "
        "\"When Gochara Saturn passed through Lagna point, facial paralysis set in\" "
        "(HTJAH-I:6892-6893); the Rashi and Amsa of the natal position (HTJAH-I:11226-11228). "
        "Points: the period lords of the running and next bhukti, the marakas, Lagna and the "
        "Moon; scanned every 5 days in the chart's own ayanamsa. No orb is printed for natal "
        "points, so whole signs are used.",
        ("transit", "natal point", "contact", "dates"),
        tuple(rows))


def _malefic_meetings(chart: RamanChart, az: str, ref_jd: float) -> Optional[TimingTable]:
    win = _scan_window(chart, ref_jd)
    moon = chart.planets.get("Moon")
    if win is None or moon is None:
        return None
    lo, hi, label = win
    marks = {moon.sign: ("the Moon sign", "malefic"),
             _sign_from(moon.sign, 8): ("the 8th from the Moon", "malefic"),
             _sign_from(moon.sign, 11): ("the 11th from the Moon", "favourable")}
    aspects = {"Mars": (4, 7, 8), "Saturn": (3, 7, 10), "Rahu": (7,)}
    step = 5.0
    rows: list[tuple[str, ...]] = []
    for a_pl, b_pl in (("Mars", "Saturn"), ("Saturn", "Rahu")):
        state: list[tuple[float, Optional[str]]] = []
        for jd in _sample(lo, hi, step):
            la, lb = _lon(jd, a_pl, az), _lon(jd, b_pl, az)
            sa, sb = _sign(la), _sign(lb)
            gap = abs(la - lb) % 360.0
            gap = min(gap, 360.0 - gap)
            key: Optional[str] = None
            if sa == sb and sa in marks:
                key = f"conjunction in {SIGN[sa]}, {marks[sa][0]} ({marks[sa][1]})"
            elif gap <= 10.0 and (sa in marks or sb in marks):
                s = sa if sa in marks else sb
                key = f"within 10 degrees across {SIGN[sa]}/{SIGN[sb]}, on {marks[s][0]} ({marks[s][1]})"
            elif (_count(sa, sb) in aspects[a_pl] and _count(sb, sa) in aspects[b_pl]
                  and (sa in marks or sb in marks)):
                on = "; ".join(f"{marks[s][0]} ({marks[s][1]})" for s in (sa, sb) if s in marks)
                key = f"mutual aspect {SIGN[sa]}-{SIGN[sb]}, on {on}"
            state.append((jd, key))
        cur_key: Optional[str] = None
        start = lo
        for jd, key in state + [(hi, None)]:
            if key != cur_key:
                if cur_key is not None:
                    rows.append((f"{a_pl}-{b_pl}", cur_key, _span(start, jd)))
                cur_key, start = key, jd
    if not rows:
        return None
    return TimingTable(
        "malefic_meetings", f"Mars-Saturn and Saturn-Rahu meetings on the Moon's signs ({label})",
        "\"Saturn-Rahu conjunction was taking place in his Janma Rasi\" (NH:10211-10212); "
        "\"Remember this conjunction occurs in the 8th from Hitler's Janma Rasi\" (NH:12267-12268), "
        "where \"the distance between Rahu and Saturn will be about 10 degrees, implying for all "
        "practical purposes conjunction\" (NH:12265-12266); \"poweful mutual aspects between "
        "transiting Mars and Saturn\" (HTJAH-I:6718-6719); and as favourable, \"Mars almost in "
        "conjunction with Saturn in Pisces — the 11th from Franco's Janma Rasi\" "
        "(NH:12795-12796). Aspects as the engine locks them (Rahu 7th only).",
        ("pair", "meeting", "dates"),
        tuple(rows))


def _saturn_8_12_lords(chart: RamanChart, outlook: dict,
                       dws: tuple) -> Optional[TimingTable]:
    l8, l12 = _lord_of_house(chart, 8), _lord_of_house(chart, 12)
    p8, p12 = chart.planets.get(l8), chart.planets.get(l12)
    if p8 is None or p12 is None:
        return None
    seats = {p8.sign: f"sign of the 8th lord {l8}", p12.sign: f"sign of the 12th lord {l12}"}
    if p8.sign == p12.sign:
        seats = {p8.sign: f"sign of the 8th lord {l8} and the 12th lord {l12}"}
    rows: list[tuple[str, ...]] = []
    for s in outlook.get("Saturn", ()):
        hit = seats.get(s.sign)
        trine_of = next((v for k, v in seats.items() if s.sign in _trines(k) and s.sign != k),
                        None)
        if hit is None and trine_of is None:
            continue
        dw = [w for w in dws if w.start_jd < s.end_jd and w.end_jd > s.start_jd]
        ctx = ("inside the engine's ranked maraka windows ("
               + ", ".join(f"{w.maha}/{w.antar}" for w in dw) + ")" if dw
               else "outside the ranked maraka windows: read as misfortune, not death "
                    "(HTJAH-I:10989-10991)")
        what = (f"the {hit}: Raman's death-inflicting transit (HTJAH-I:10997-10998)" if hit
                else f"a trine of the {trine_of}: the {ordinal(_count(chart.asc_sign, s.sign))} "
                     "house is afflicted (HTJAH-I:10998-10999)")
        rows.append((_span(s.start_jd, s.end_jd), SIGN[s.sign], what, ctx))
    if not rows:
        return None
    return TimingTable(
        "saturn_8_12_lords", "Saturn over the 8th and 12th lords' signs",
        "\"When Saturn passes through the houses occupied by the 8th lord or the 12th lord from "
        "Lagna, death occurs. Passage of Saturn through these houses or their trines with "
        "reference to any other house in the horoscope results in the destruction of that "
        "house\" (HTJAH-I:10997-10999) — and \"Death indicated on the basis of transits can "
        "happen only when the directional influences in the birth charts warrant. Otherwise "
        "misfortunes such as ill-health, loss of money ... may happen\" (HTJAH-I:10989-10991). "
        "Each window is labelled by whether it overlaps the engine's ranked maraka windows "
        "(the maraka bhuktis near the ayurdaya span, `death_window`). A classical signal stated "
        "as method, never a date.",
        ("window", "sign", "what Saturn crosses", "Dasa context"),
        tuple(rows))


def marriage_points(chart: RamanChart) -> tuple[tuple[str, float], ...]:
    """(label, longitude) of Raman's marriage points (fix 12): the stated lords' sums (HTJAH-I:
    8401-8404) and the practised bhava sum, "adding the longitudes of the Lagna Bhava ... and the
    seventh house" (HTJAH-I:18296-18298; also HTJAH-I:18426-18427). The 7th bhava longitude is
    the Lagna's plus 180 degrees in Raman's worked cases (223 deg 17' and 43 deg 17')."""
    lagna_lord, l7 = SIGN_LORDS[chart.asc_sign], _lord_of_house(chart, 7)
    lp, sp, mp = (chart.planets.get(lagna_lord), chart.planets.get(l7),
                  chart.planets.get("Moon"))
    out: list[tuple[str, float]] = []
    if lp is not None and sp is not None:
        out.append(("Lagna lord + 7th lord", (lp.lon + sp.lon) % 360.0))
    if mp is not None and sp is not None:
        out.append(("Moon + 7th lord", (mp.lon + sp.lon) % 360.0))
    out.append(("Lagna bhava + 7th bhava", (2.0 * chart.asc_lon + 180.0) % 360.0))
    return tuple(out)


def _marriage_point(chart: RamanChart, az: str, ref_jd: float, years_back: float,
                    years_forward: float) -> Optional[TimingTable]:
    lo = ref_jd - years_back * DAYS_PER_VEDIC_YEAR
    hi = ref_jd + years_forward * DAYS_PER_VEDIC_YEAR
    step = 5.0
    samples = list(_sample(lo, hi, step))
    jup = [_sign(_lon(jd, "Jupiter", az)) for jd in samples]
    seventh = _sign_from(chart.asc_sign, 7)
    rows: list[tuple[str, ...]] = []
    for label, lon in marriage_points(chart):
        s = _sign(lon)
        lord = SIGN_LORDS[s]
        lord_p = chart.planets.get(lord)
        point = f"{SIGN[s]} {lon % 30.0:.1f} deg"
        for a, b in _merge([(jd, js in _trines(s)) for jd, js in zip(samples, jup)], step):
            rows.append((label, point, "Jupiter over the sign or its trines", _span(a, b)))
        asp = lambda js, tgt: _count(js, tgt) in (5, 7, 9)   # noqa: E731 — Jupiter's aspects
        for a, b in _merge([(jd, asp(js, seventh)) for jd, js in zip(samples, jup)], step):
            rows.append((label, point, f"Jupiter aspecting the natal 7th ({SIGN[seventh]})",
                         _span(a, b)))
        if lord_p is not None:
            for a, b in _merge([(jd, asp(js, lord_p.sign)) for jd, js in zip(samples, jup)],
                               step):
                rows.append((label, point, f"Jupiter aspecting natal {lord}, lord of the sum "
                             "sign", _span(a, b)))
    if not rows:
        return None
    return TimingTable(
        "marriage_point", "Marriage points and Jupiter's transits over them",
        "Raman's stated method: \"add the longitude of the lords of the Lagna and 7th house. When "
        "Jupiter transits the resultant Rashi or its trines, it is favourable for marriage\", and "
        "the Moon + 7th lord resultant likewise (HTJAH-I:8401-8404). His practised method adds the "
        "Lagna and 7th BHAVA longitudes: \"Jupiter from here was aspecting natal 7th house and "
        "natal Jupiter who is also the ruler of the sign signified by the sum\" "
        "(HTJAH-I:18296-18299); \"Jupiter in transit was moving over this sign\" "
        "(HTJAH-I:18426-18427). He subordinates all of it: \"Primary importance must be given to "
        "the natal positions and Dasha and only secondary consideration to transiting planets\" "
        "(HTJAH-I:8410-8411). Jupiter sampled every 5 days in the chart's own ayanamsa.",
        ("marriage point", "resultant", "Jupiter's contact", "dates"),
        tuple(rows))


def sign_part(planet: str, lon: float) -> str:
    """Fix 13: "Mars and the Sun produce effects during their transit when they are in the first
    10 degrees of a sign. Jupiter and Venus become effective when they are in the 2nd ten
    degrees while Rahu produces results throughout the entire sign" (AFB-12:197-201;
    HPA-34:83-85 for Mars and the Sun). Raman names no part for the Moon, Mercury, Saturn or
    Ketu."""
    deg = lon % 30.0
    if planet in ("Sun", "Mars"):
        return ("in the first 10 degrees: effective" if deg < 10.0
                else "past the first 10 degrees: not in its effective part")
    if planet in ("Jupiter", "Venus"):
        return ("in the middle 10 degrees: effective" if 10.0 <= deg < 20.0
                else "outside the middle 10 degrees: not in its effective part")
    if planet == "Rahu":
        return "effective throughout the sign"
    return "no sign part named by Raman"


def _sign_parts(az: str, ref_jd: float) -> TimingTable:
    rows = []
    for g in GRAHAS:
        lon = _lon(ref_jd, g, az)
        rows.append((g, SIGN[_sign(lon)], f"{lon % 30.0:.1f}", sign_part(g, lon)))
    return TimingTable(
        "sign_parts", "Which part of its sign each transit stands in (reference date)",
        "\"Mars and the Sun produce effects during their transit when they are in the first 10 "
        "degrees of a sign. Jupiter and Venus become effective when they are in the 2nd ten "
        "degrees while Rahu produces results throughout the entire sign\" (AFB-12:197-201; "
        "HPA-34:83-85). Nothing is named for the Moon, Mercury, Saturn or Ketu.",
        ("planet", "transit sign", "degree in sign", "Raman's sign part"),
        tuple(rows))


def transit_checks(chart: RamanChart, ref_jd: float, *, years_back: float = 10.0,
                   years_forward: float = 20.0,
                   outlook: Optional[dict] = None) -> tuple[TimingTable, ...]:
    """The transit-side tables (fixes 7, 8, 10, 11, 12, 13). Empty on a Track-B chart."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    az = getattr(chart, "ayanamsa", None) or "raman"
    if outlook is None:
        outlook = tr.gochara_timeline(chart, ref_jd, years_back, years_forward, ayanamsa=az)
    ms = vd.maraka_set(chart)
    bh = _all_bhuktis(chart)
    try:
        dws = vd.death_window(chart)
    except Exception:  # noqa: BLE001 — sparse chart
        dws = ()
    out: list[TimingTable] = []
    for build in (lambda: _sade_sati_rounds(chart, az, dws, bh, ref_jd),
                  lambda: _transit_dasa_gate(chart, outlook, bh, ref_jd),
                  lambda: _transit_natal_points(chart, az, ref_jd, ms),
                  lambda: _malefic_meetings(chart, az, ref_jd),
                  lambda: _saturn_8_12_lords(chart, outlook, dws),
                  lambda: _marriage_point(chart, az, ref_jd, years_back, years_forward),
                  lambda: _sign_parts(az, ref_jd)):
        try:
            t = build()
        except Exception:  # noqa: BLE001 — one table must never cost the others
            logger.info("Raman transit table skipped", exc_info=True)
            continue
        if t is not None and t.rows:
            out.append(t)
    return tuple(out)
