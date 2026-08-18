"""Cross-feature synthesis rules — encoded combination readings (REPORT-ONLY).

The report's sections are individually faithful but stand-alone; this module encodes the
doctrine that CONNECTS them — how Shadbala grades yoga fruition, how the dasha gates transits,
how Ishta/Kashta colours a period — each rule carrying its textual source. Three bands:

  * ``raman``     — Raman's own combination doctrine, live Citations (verify()-checked,
                    source-locked): the only band with citable authority.
  * ``classical`` — the classical spine (Laghu Parashari, BPHS, Uttara Kalamrita, Saravali),
                    CLASSICAL_NONCITABLE: quoted in the rule text, never resolved against the
                    corpus, rendered under a provenance banner.
  * ``av``        — Ashtakavarga combination methods (Patel/BPHS/Phaladeepika),
                    CLASSICAL_NONCITABLE **plus** Raman's own caveat ("it does not seem to be
                    quite reliable", HTJAH-II:4453-4456) printed at the band head. An AV insight
                    never overrides a Raman-band insight.

Rules are ``evaluable`` (a checker fires them against the chart, producing personalised detail)
or ``descriptive`` (doctrine on record whose inputs the engine does not yet compute — e.g.
residential strength GBB-1:203, kakshya transits, Shodhyapinda — listed compactly, never fired).

EXCLUDED by project locks (recorded here, deliberately NOT encoded): BPHS rasi-dasha Argala
grading (no-Argala lock); the KP sub-lord chain (Lahiri ayanamsa lock); nodal Vedha from the
Sarvatobhadra scheme (no-nodal-drishti lock — nodes act by occupation/conjunction, which
Laghu Parashari v1:2177 independently supports).

ABSENCE FINDINGS honoured (no rule invents a combination the texts do not state): Shadbala x
Ashtakavarga directly is NOT Raman; GBB prescribes per-planet strength minima (GBB-8:303,
already encoded in shadbala.total.is_powerful) but NO minima for grading combinations — his
combination use is comparative + Ishta/Kashta; Bhava Bala has no numeric cutoff, only ranking;
Sade-Sati x Moon-condition is an incidental mention, not doctrine.

VERDICT-AUTHORITY INVARIANT: this module is imported ONLY by the report composers. It must
never be imported from house_template / proforma / the rule_sets — it reads verdict-layer
outputs and never feeds them.

Usage:
    from app.raman_saab.doctrine.synthesis_rules import detect_synthesis, descriptive_rules
    insights = detect_synthesis(chart, jd, gochara=rows, yogas=fired, sav=sav)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Final, Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.residential_strength import residential_strength
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.primitives import ashtakavarga
from app.raman_saab.primitives import bhangas
from app.raman_saab.primitives import dignity as _dig
from app.raman_saab.primitives import vimshottari as vd
from app.raman_saab.primitives.functional_nature import is_yogakaraka
from app.raman_saab.primitives.shadbala import total as _sb_total
from app.raman_saab.primitives.transits import TransitRow
from app.raman_saab.ordinals import ordinal

Band = Literal["raman", "classical", "av"]
Kind = Literal["evaluable", "descriptive"]

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


# ─────────────────────────────────────────────────────────────────────────────
# context + records
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SynthesisContext:
    """Everything a checker may read. Assembled once in detect_synthesis."""
    chart: RamanChart
    jd: float
    period: Optional[vd.DashaPeriod]                 # running MD/AD at jd
    md_timeline: tuple[vd.DashaPeriod, ...]          # future+current MDs (for timing statements)
    gochara: tuple[TransitRow, ...]
    yogas: tuple[FiredYoga, ...]
    sav: dict[int, int]
    bhava_balas: dict[int, float]
    maraka_now: bool


@dataclass(frozen=True)
class SynthesisRule:
    """One encoded combination rule. `source` is a live Citation only for the raman band;
    the flagged bands carry their reference as free text inside `doctrine`."""
    id: str
    band: Band
    family: str
    name: str
    kind: Kind
    provenance: str                                  # RAMAN_EXPLICIT / CLASSICAL_NONCITABLE / MODERN
    doctrine: str                                    # the doctrine statement (with ref for non-Raman)
    simple_meaning: str                              # the lay reader's line
    links: tuple[str, ...]                           # report sections this insight connects
    source: Optional[Citation] = None


@dataclass(frozen=True)
class FiredInsight:
    rule: SynthesisRule
    detail: str                                      # chart-personalised finding


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rupas(chart: RamanChart, planet: str) -> Optional[float]:
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return None
    return p.shadbala_rupas.total / 60.0


def _strong(chart: RamanChart, planet: str) -> Optional[bool]:
    r = _rupas(chart, planet)
    return None if r is None else _sb_total.is_powerful(planet, r)


def _jd_date(jd: float) -> str:
    import swisseph as swe
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _md_window(ctx: SynthesisContext, lord: str) -> Optional[tuple[float, float]]:
    for p in ctx.md_timeline:
        if p.maha == lord and p.end_jd > ctx.jd:
            return (p.start_jd, p.end_jd)
    return None


def _house_lord(chart: RamanChart, house: int) -> str:
    """Lord of whole-sign house `house` (1..12) counted from the Lagna — the same computation
    `yogas.py`'s own `_house_lord` uses, duplicated here rather than imported to keep this a
    pure REPORT-layer module (VERDICT-AUTHORITY INVARIANT: no import from house_template/
    proforma; yogas.py itself is a doctrine sibling, safe to import for FiredYoga/detect_yogas,
    but its private helper is not re-exported)."""
    asc = chart.asc_sign
    return SIGN_LORDS[((asc - 1) + (house - 1)) % 12 + 1]


#: Pancha Mahapurusha yogas — each is caused by exactly ONE named planet (3HC:3434-3973, the
#: five citations already verified in yogas.py: Hamsa 3434, Malavya 3680, Ruchaka 3884, Sasa
#: 3737, Bhadra 3973).
_MAHAPURUSHA_PLANET: Final[dict[str, str]] = {
    "ruchaka": "Mars", "bhadra": "Mercury", "hamsa": "Jupiter",
    "malavya": "Venus", "sasa": "Saturn",
}

#: Sunapha/Anapha/Durudhara/Vesi/Vasi/Ubhayachari candidates: "a planet other than the Moon"
#: (3HC:1834-1846) — the Sun and the chaya-grahas never count either, per the same passage.
_FLANK_CANDIDATES: Final[tuple[str, ...]] = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")

#: Amala/Parvata candidates: the natural benefics this project's own functional_nature module
#: already uses (Jupiter, Venus, Mercury, Moon) — see primitives/functional_nature.py.
_BENEFIC_CANDIDATES: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury", "Moon")


def _house_from(rasi_house: int, origin_rasi_house: int) -> int:
    """Whole-sign house of `rasi_house` counted from `origin_rasi_house` — the same arithmetic
    `conditions._house_from` uses (duplicated for the same import-boundary reason as
    `_house_lord`)."""
    return ((rasi_house - origin_rasi_house) % 12) + 1


def _which_of(chart: RamanChart, candidates: tuple[str, ...], origin_rasi_house: int,
             n: int) -> tuple[str, ...]:
    """WHICH of `candidates` actually sits in the `n`th house from `origin_rasi_house` — the
    concrete planet(s) behind a "some planet satisfies X" yoga condition (Vesi/Vasi/Sunapha/
    Anapha/Durudhara/Ubhayachari are all "a planet other than the Moon/Sun" — the condition
    fires on ANY of 5 candidates, but a specific chart has a definite, checkable answer)."""
    return tuple(p for p in candidates
                if chart.planets.get(p) is not None
                and _house_from(chart.planets[p].rasi_house, origin_rasi_house) == n)


#: Kendra x trikona house-pairs to try, in priority order: the 10th/9th lords FIRST — Raman
#: names that combination the STRONGEST form of this yoga (HTJAH-I:625-626, separately encoded
#: as Y.RAJA.910X/910A) — then every other pair in a FIXED house order. A plain `set` iteration
#: (Python's string-hash order, not guaranteed stable across process runs) would make `_kt_pair`
#: report a different pair for the same chart on different runs whenever more than one pair is
#: valid; a fixed list has no such risk.
_KT_HOUSE_PAIRS: Final[tuple[tuple[int, int], ...]] = (
    (10, 9), *((k, t) for k in (1, 4, 7, 10) for t in (1, 5, 9) if (k, t) != (10, 9)))


def _kt_pair(chart: RamanChart) -> Optional[tuple[str, str]]:
    """The SPECIFIC kendra-lord/trikona-lord pair that is conjunct — re-derives exactly what
    `yogas._KendraTrikonaLordsConjoined.evaluate` already found, but keeps WHICH pair instead of
    discarding it as a bare boolean (HTJAH-I:622-623)."""
    for k_house, t_house in _KT_HOUSE_PAIRS:
        k, t = _house_lord(chart, k_house), _house_lord(chart, t_house)
        if k == t:
            continue
        pk, pt = chart.planets.get(k), chart.planets.get(t)
        if pk is not None and pt is not None and pk.rasi_house == pt.rasi_house:
            return (k, t)
    return None


def _vipareeta_pair(chart: RamanChart) -> Optional[tuple[str, ...]]:
    """The SPECIFIC dusthana lords (of 6/8/12) conjunct in a dusthana — re-derives exactly what
    `yogas._DusthanaLordsConjoinedInDusthana.evaluate` already found (HTJAH-I:6302-6303)."""
    seen: dict[int, set[str]] = {}
    for h in (6, 8, 12):
        lord = _house_lord(chart, h)
        p = chart.planets.get(lord)
        if p is not None:
            seen.setdefault(p.rasi_house, set()).add(lord)
    for house, lords in seen.items():
        if house in (6, 8, 12) and len(lords) >= 2:
            return tuple(sorted(lords))
    return None


#: Yoga constituents where they are structurally certain. Anything else returns None and the
#: yoga-specific rules simply do not fire for it (never guess a constituent). Covers the yogas
#: whose "who" is a fixed named planet, a specific house-lord (a deterministic function of the
#: Lagna, same technique as the original 9th/10th case), or a small, exactly-checkable candidate
#: set (the "which planet satisfies this" flank/benefic yogas). Left UNRESOLVED, deliberately:
#: the Nabhasa whole-chart-distribution yogas (Asraya/Dala/Sankhya/Akriti — ~33 records) have no
#: single "lord" in Raman's own definition, since they are properties of all seven visible
#: planets together, not caused by one, two or three specific ones; and the rare multi-arm
#: HPA-20 yogas (Sarada, Brihadbija) are deferred — discriminating which of their several,
#: differently-worded disjuncts fired needs more care than this pass gives it.
def _yoga_planets(chart: RamanChart, y: FiredYoga) -> Optional[tuple[str, ...]]:
    """Public entry point: dedupes `_yoga_planets_impl`'s result. Two DIFFERENT houses can share
    the same lord (e.g. Mars rules both Aries and Scorpio), so a fixed multi-house lookup like
    Khadga's (2nd/9th/1st lords) can legitimately name the same planet twice — collapsed here to
    one entry, preserving first-seen order, so a report row never reads "Venus, Venus, Mercury"."""
    pls = _yoga_planets_impl(chart, y)
    return tuple(dict.fromkeys(pls)) if pls else None


def yoga_house_bearings(chart: RamanChart, y: FiredYoga) -> Optional[frozenset[int]]:
    """The houses a fired yoga "has a bearing on" (Raman's Primary Considerations phrase,
    HTJAH-I:4135-4139) — REPORT-ONLY.

    Raman's own operationalization, taken from where he works charts rather than the template
    (which never defines it): a yoga bears on the houses its CONSTITUENT PLANETS own, occupy
    or aspect. His worked examples DEMONSTRATE ownership and occupancy: Chandramangala — "the
    nature of results depends also on the nature of ownership of the planets causing the
    yoga" (HTJAH-I:2879-2890; the passage's own Libra-Lagna example names the 2nd and 11th,
    of which only the 2nd is derivable from the constituents' own/occupy/aspect — the cite
    supports the ownership PRINCIPLE, not an exact house-set derivation); Truman's Gajakesari
    "has reference to the 2nd, the 10th, the 4th and the 7th houses" via the constituents'
    placements (HTJAH-I:15824-15826); Dhana and Raja yogas repeatedly named FOR the houses
    their constituent lords own (HTJAH-I:17049-17052, 15831-15832). The ASPECT factor is
    included by extension from "if Jupiter is connected in any way with the second house...
    he is bound to make a person earn well" (HTJAH-I:2955-2956), not by a worked
    demonstration.

    SCOPE — the DIRECT factors only (ownership, occupancy, whole-sign aspect): the first
    three of the locked five/six-factor influence method (HTJAH-I:1586-1596). The remaining
    factors (planets aspecting/conjoining the house LORD, the lord-from-the-Moon, the karaka
    — the full `vimshottari.timer_set`) are the dasha-fructification extensions; including
    them saturates multi-planet yogas onto all twelve houses. Even so, this mapping is
    deliberately COARSER than Raman's demonstrated four (typically 5-8 houses for a
    two-planet yoga): under the locked whole-sign convention it reproduces the Truman set
    3-of-4 (his bhava-reckoned 10th reads as the 11th rasi here) plus aspect-derived houses
    he does not name. A disclosed approximation built only from locked-doctrine factors —
    never a new influence rule.

    Returns None for the whole-chart pattern yogas `_yoga_planets` cannot resolve (the
    Nabhasa/Akriti/Sankhya shapes carry no constituent-planet identity — an honest gap,
    disclosed by callers, never guessed). Formation-strength modifiers are NOT graded here
    and callers must disclose them: dusthana formation can nullify Gajakesari
    (HTJAH-I:2948-2956) and can bring Raja-Yoga Bhanga (HTJAH-I:15903, 16139) — though not
    absolutely (HTJAH-I:15531 credits an 8th-house-formed Raja yoga; 16111-16112 lets a
    powerful yoga set the bhanga right)."""
    from app.raman_saab.doctrine import drishti   # function-level, matching _sambandha
    pls = _yoga_planets(chart, y)
    if not pls:
        return None
    houses: set[int] = set()
    for p in pls:
        pos = chart.planets.get(p)
        if pos is None:
            continue
        for h in range(1, 13):
            sign = ((chart.asc_sign - 1) + (h - 1)) % 12 + 1
            if (SIGN_LORDS[sign] == p or pos.rasi_house == h
                    or drishti.aspects_house(p, h, chart)):
                houses.add(h)
    return frozenset(houses) or None


def yoga_house_bearings_detail(chart: RamanChart, y: FiredYoga
                               ) -> Optional[dict[int, str]]:
    """APPEND-ONLY companion to :func:`yoga_house_bearings` (2026-08-18, Wave-2
    preponderance disclosure): the SAME house set, each house tagged by the strongest
    factor that matched — ``"direct"`` when a constituent OWNS or OCCUPIES the house
    (the factors Raman's worked charts demonstrate) or ``"aspect"`` when only the
    whole-sign aspect reaches it (the admitted extension from HTJAH-I:2955-2956).
    No new influence rule and no new house: `yoga_house_bearings` stays authoritative
    and this mapping's key-set must always equal it (paired test pins that)."""
    from app.raman_saab.doctrine import drishti   # function-level, matching _sambandha
    pls = _yoga_planets(chart, y)
    if not pls:
        return None
    tags: dict[int, str] = {}
    for p in pls:
        pos = chart.planets.get(p)
        if pos is None:
            continue
        for h in range(1, 13):
            sign = ((chart.asc_sign - 1) + (h - 1)) % 12 + 1
            if SIGN_LORDS[sign] == p or pos.rasi_house == h:
                tags[h] = "direct"                       # own/occupy always wins
            elif drishti.aspects_house(p, h, chart):
                tags.setdefault(h, "aspect")             # aspect only if nothing direct
    return tags or None


def _yoga_planets_impl(chart: RamanChart, y: FiredYoga) -> Optional[tuple[str, ...]]:
    n = y.name.lower()

    for key, planet in _MAHAPURUSHA_PLANET.items():
        if key in n:
            return (planet,)
    if "gajakesari" in n:
        return ("Jupiter", "Moon")
    if "budha-aditya" in n or "budha aditya" in n:
        return ("Sun", "Mercury")
    if "chandramangala" in n:
        return ("Moon", "Mars")
    if "vasumathi" in n:                                  # 3HC:2708 — all three, jointly
        return ("Jupiter", "Venus", "Mercury")
    if n == "adhi yoga":                                  # 3HC:2461-2466 — all three, jointly
        return ("Mercury", "Jupiter", "Venus")
    if "sakata" in n and "akriti" not in n:               # arishta Sakata: Moon x Jupiter houses
        return ("Moon", "Jupiter")
    if "kusuma" in n:                                     # HPA-20:200 — Venus, waning Moon, Sun
        return ("Venus", "Moon", "Sun")
    if "kemadruma" in n:                                  # 3HC:2172 — the Moon's own isolation
        return ("Moon",)
    if "9th-10th" in n or "9th and 10th" in n:
        return (_house_lord(chart, 9), _house_lord(chart, 10))
    if "5th and 9th lords in own houses" in n:
        return (_house_lord(chart, 5), _house_lord(chart, 9))
    if "bahudravyarjana" in n:
        return (_house_lord(chart, 1), _house_lord(chart, 2), _house_lord(chart, 11))
    if "1st-2nd-11th lord chain" in n:                    # Y.DHANA.CHAIN — discriminate which
        hits = []                                         # of the 3 disjuncts actually fired
        for h, in_h in ((1, 2), (2, 11), (11, 1)):
            lord = _house_lord(chart, h)
            p = chart.planets.get(lord)
            if p is not None and p.rasi_house == in_h:
                hits.append(lord)
        return tuple(dict.fromkeys(hits)) or None
    if "venus-5th" in n:                                  # Y.DHANA.122
        return ("Venus", "Saturn")
    if "sun own-5th" in n:                                # Y.DHANA.125
        return ("Sun", "Moon", "Jupiter")
    if "jaya yoga" in n:
        return (_house_lord(chart, 6), _house_lord(chart, 10))
    if "daridra" in n:
        return (_house_lord(chart, 11),)
    if "khadga" in n:
        return (_house_lord(chart, 2), _house_lord(chart, 9), _house_lord(chart, 1))
    if "sreenatha" in n:
        return (_house_lord(chart, 7), _house_lord(chart, 9), _house_lord(chart, 10))
    if "chamara" in n:
        return (_house_lord(chart, 1), "Jupiter")
    if "asatyavadi" in n:
        return (_house_lord(chart, 2), "Saturn")
    if "2nd-5th" in n:                                    # Y.DHANA.EXCH — discriminate the
        if bhangas.parivartana(2, 5, chart):              # branch that actually fired
            return (_house_lord(chart, 2), _house_lord(chart, 5))
        if bhangas.parivartana(2, 11, chart):
            return (_house_lord(chart, 2), _house_lord(chart, 11))
        return None
    if "kendra-trikona" in n:
        return _kt_pair(chart)
    if "vipareeta" in n:
        return _vipareeta_pair(chart)

    sun = chart.planets.get("Sun")
    moon = chart.planets.get("Moon")
    if "vesi" in n and sun is not None:
        return _which_of(chart, _FLANK_CANDIDATES, sun.rasi_house, 2) or None
    if "vasi" in n and "ubhaya" not in n and sun is not None:
        return _which_of(chart, _FLANK_CANDIDATES, sun.rasi_house, 12) or None
    if "ubhayachari" in n and sun is not None:
        hits = (_which_of(chart, _FLANK_CANDIDATES, sun.rasi_house, 2)
               + _which_of(chart, _FLANK_CANDIDATES, sun.rasi_house, 12))
        return tuple(dict.fromkeys(hits)) or None
    if "sunapha" in n and moon is not None:
        return _which_of(chart, _FLANK_CANDIDATES, moon.rasi_house, 2) or None
    if "anapha" in n and moon is not None:
        return _which_of(chart, _FLANK_CANDIDATES, moon.rasi_house, 12) or None
    if "durudhara" in n and moon is not None:
        hits = (_which_of(chart, _FLANK_CANDIDATES, moon.rasi_house, 2)
               + _which_of(chart, _FLANK_CANDIDATES, moon.rasi_house, 12))
        return tuple(dict.fromkeys(hits)) or None
    if "amala" in n:
        hits = _which_of(chart, _BENEFIC_CANDIDATES, 1, 10)   # 10th from Lagna
        if moon is not None:
            hits += _which_of(chart, _BENEFIC_CANDIDATES, moon.rasi_house, 10)  # 10th from Moon
        return tuple(dict.fromkeys(hits)) or None
    if "parvata" in n:
        hits = tuple(p for p in _BENEFIC_CANDIDATES
                    if chart.planets.get(p) is not None
                    and chart.planets[p].rasi_house in (1, 4, 7, 10))
        return hits or None
    return None


def _lordships(chart: RamanChart, planet: str) -> tuple[int, ...]:
    asc = chart.asc_sign
    return tuple(h for h in range(1, 13)
                 if SIGN_LORDS[(asc - 1 + h - 1) % 12 + 1] == planet)


# ─────────────────────────────────────────────────────────────────────────────
# Phase A — the RAMAN band (live citations; verified in the mining pass)
# ─────────────────────────────────────────────────────────────────────────────

_R = "RAMAN_EXPLICIT"

RAMAN_RULES: Final[tuple[SynthesisRule, ...]] = (
    SynthesisRule(
        "SYN_R1_STRONGER_LORD_DELIVERS", "raman", "R1",
        "Shadbala-ordered yoga fruition", "evaluable", _R,
        "When two planets cause a yoga, the one with greater Shadbala fulfils the larger part "
        "of the yoga's indications in his own Dasha; the weaker acts as sub-lord to a lesser "
        "extent.",
        "Of the planets forming a yoga, the stronger one delivers most of it — during its own "
        "period.",
        ("Yogas", "Shadbala", "Life-narrative"), Citation("3HC", 1359)),
    SynthesisRule(
        "SYN_R2_RUNNING_TIER", "raman", "R2",
        "Bhukti-tier of the running period", "evaluable", _R,
        "Sub-periods of planets influencing a house, in major periods of planets also "
        "influencing it, give results par excellence when the two lords are associated; "
        "otherwise to a limited/ordinary extent.",
        "The current sub-period's strength depends on whether its lord and the major-period "
        "lord work together.",
        ("Life-narrative", "House-by-house"), Citation("HTJAH-I", 1635)),
    SynthesisRule(
        "SYN_R3_YOGA_LORD_PERIOD", "raman", "R3",
        "Yoga fructifies in its lord's period", "evaluable", _R,
        "A lord involved in a Raja-yoga or Arishta-yoga is capable of producing that yoga's "
        "results in his Dasha or Bhukti.",
        "A yoga is not always 'on' — it ripens when the period of a planet causing it runs.",
        ("Yogas", "Life-narrative"), Citation("HTJAH-I", 4324)),
    SynthesisRule(
        "SYN_R4_MD_LORD_CONDITION", "raman", "R4",
        "Dasha result modified by the lord's condition", "evaluable", _R,
        "The result of a Dasha is modified by the strength/weakness of its lord, the nature of "
        "its house and sign, its Navamsa disposition and the aspecting bodies — at its maximum "
        "only when strong in both charts.",
        "A period delivers in proportion to how well-placed its ruling planet actually is.",
        ("Life-narrative", "Shadbala", "Planetary positions"), Citation("HPA-24", 80)),
    SynthesisRule(
        "SYN_R5_ISHTA_KASHTA_PERIOD", "raman", "R5",
        "Ishta/Kashta colours the period", "evaluable", _R,
        "A planet with more Ishta Phala inclines to do good in its Dasha or Bhukti; more Kashta "
        "Phala gives rise to evil results; the Dasha lord's character prevails over the Bhukti "
        "lord's when his strength predominates.",
        "Each planet carries a measured 'good vs hard' tendency that flavours its periods.",
        ("Shadbala", "Life-narrative"), Citation("GBB-10", 134)),
    SynthesisRule(
        "SYN_R6_BHAVA_BALA_RANK", "raman", "R6",
        "Bhava Bala ranks the houses", "evaluable", _R,
        "Each house's strength (lord's Shadbala + Bhavadig + Bhava-Drig) grades whether its "
        "indications are enjoyed fully; ranking houses strongest to weakest prepares the ground "
        "for prediction. Raman gives a ranking, never a numeric cutoff.",
        "The chart's houses are not equal — the strongest deliver most fully.",
        ("House-by-house", "Shadbala"), Citation("GBB-9", 332)),
    SynthesisRule(
        "SYN_R7_RESIDENTIAL_QUANTITY", "raman", "R7",
        "Residential strength quantifies the period's yield", "evaluable", _R,
        "A planet's residential strength gives the exact quantity of its house's effects, which "
        "finds expression during its Dasha — modified by aspects, the Bhava's own strength and "
        "the yoga-karakas.",
        "How much of a house a planet can deliver in its period is itself a measured quantity.",
        ("Life-narrative", "House-by-house"), Citation("GBB-1", 203)),
    SynthesisRule(
        "SYN_R14_BR_LIBRA_SATURN_DASA", "raman", "R14",
        "Bhavartha Ratnakara's Libra-Saturn combination", "evaluable", _R,
        "Bhavartha Ratnakara: one born in Libra becomes fortunate during Saturn's Dasa, provided "
        "Jupiter is in the 6th or 12th and the Moon is in Lagna. Encoded strictly as stated; "
        "Raman's own application allowed 'a slight modification' on one chart, which is his "
        "judgment there rather than a widening of the dictum.",
        "A classical Libra-ascendant combination that marks Saturn's period as the fortunate one.",
        ("Life-narrative", "Chart signature"), Citation("NH", 9580)),
    SynthesisRule(
        "SYN_R8_TRANSIT_CATALYST", "raman", "R8",
        "Transits are catalysts gated by the dasha", "evaluable", _R,
        "Transits must be looked into only after determining the operative Dasha; they are "
        "always secondary — like catalytic agents — and conclusions rest primarily on "
        "Dasa-vichara.",
        "A good transit only delivers what the running period already permits.",
        ("Current transits", "Life-narrative"), Citation("HTJAH-II", 4679)),
    SynthesisRule(
        "SYN_R9_MARAKA_SATURN_SIGNAL", "raman", "R9",
        "Maraka period x Saturn's transit signal", "evaluable", _R,
        "When a maraka Dasha operates, the last signal is given by Ayushkaraka Saturn "
        "transiting the Rasi/Amsa he occupied at birth, or its trines. A statement of the "
        "method, not a prediction — the validation program measured no death-timing signal.",
        "The classical death-timing test needs BOTH the period and Saturn's specific transit — "
        "and this project measured that it does not predict real outcomes.",
        ("The maraka scheme", "Current transits", "Life-narrative"), Citation("HTJAH-II", 4846)),
    SynthesisRule(
        "SYN_R10_STRENGTH_OVERRIDES_ARISHTA", "raman", "R10",
        "Strength lifts the longevity band", "evaluable", _R,
        "The strength of the Karaka pushes longevity into a higher band even where the "
        "combinations alone read Balarishta/Alpayu (Raman's Chart 56); Balarishta itself is "
        "nullified by the classical antidotes — benefic aspect and dispositions "
        "(HTJAH-I:9803-9814).",
        "Danger combinations are cancelled or outweighed by real planetary strength.",
        ("Longevity", "Shadbala", "Planetary positions"), Citation("HTJAH-I", 11703)),
    SynthesisRule(
        "SYN_R11_TRANSIT_BINDU_SCALE", "raman", "R11",
        "Transit results scale with Ashtakavarga bindus", "evaluable", _R,
        "A transit produces benefic results provided the transiting planet's own-Ashtakavarga "
        "bindus in that sign exceed 4; below 4 it cannot do as much good — obstructed further "
        "by Vedha. (Raman's later caveat on AV is scoped to longevity determination.)",
        "The same transit is stronger or weaker depending on that planet's dot-score in the "
        "sign it crosses.",
        ("Current transits", "Ashtakavarga"), Citation("HPA-34", 127)),
    SynthesisRule(
        "SYN_R12_YOGA_FUNCTIONAL_DILUTION", "raman", "R12",
        "Yoga pre-graded by its lords' functional nature", "evaluable", _R,
        "A yoga's value is modified by the houses its constituent planets own — per Raman's own "
        "scheme in the same discussion, lords of the 3rd, 6th and 11th are the malefic owners "
        "that dilute a yoga (his Gajakesari example: Moon and Jupiter as 6th and 11th lords); "
        "lords of the 2nd, 8th and 12th count as neutral (3HC:1105-1111).",
        "Who forms the yoga matters: the same yoga from ill-placed lords gives less.",
        ("Yogas", "Chart signature"), Citation("3HC", 1030)),
    SynthesisRule(
        "SYN_R13_RAJA_VARGOTTAMA_RANK", "raman", "R13",
        "Raja-yoga rank scales with strength and vargottama", "evaluable", _R,
        "For the raja-yogas formed by the trikona and kendra lords, Raman states the rank "
        "conferred is consistent with the strength of the lords concerned; when they attain "
        "Vargottama the position acquired is the highest, and the yoga is enjoyed during the "
        "relevant lord's Dasha (stated for the 5th/10th-lord family; applied here to the "
        "structurally-resolvable raja yogas of the same kind).",
        "The same royal combination gives a bigger or smaller rise depending on its makers' "
        "strength.",
        ("Yogas", "Planetary positions", "Life-narrative"), Citation("HTJAH-I", 5372)),
)


# ─────────────────────────────────────────────────────────────────────────────
# checkers (Phase A)
# ─────────────────────────────────────────────────────────────────────────────

def _chk_r1(ctx: SynthesisContext) -> Optional[str]:
    """Reports ONLY the single strongest qualifying yoga (locked 2026-07-30) — joining two
    yogas' planets/timing into one string was a real, live-confirmed source of LLM confusion:
    the narrator swapped one yoga's lead planet or MD window for the other's when both shared
    one citable insight. Each yoga still gets its own separate Fact via R["yogas"] regardless
    (report_explainer.py's _summary_facts); this rule is specifically "who delivers it and
    when", and now names exactly one clear, unambiguous answer instead of two conflatable ones."""
    for y in ctx.yogas:
        pls = _yoga_planets(ctx.chart, y)
        # a single-constituent yoga has no "stronger of two" to name — skip it rather than
        # report a degenerate "X outweighs X" (a latent defect this fix's stricter one-answer
        # return exposed: previously masked because it could still be joined alongside a
        # second, more meaningful yoga in the same string).
        if not pls or len(pls) < 2:
            continue
        pairs = [(p, _rupas(ctx.chart, p)) for p in pls]
        if any(r is None for _p, r in pairs):
            continue
        pairs.sort(key=lambda pr: -pr[1])
        lead, sub = pairs[0], pairs[-1]
        if lead[0] == sub[0]:
            continue
        win = _md_window(ctx, lead[0])
        when = f" — his MD runs {_jd_date(win[0])}..{_jd_date(win[1])}" if win else ""
        return (f"{y.name}: {lead[0]} ({lead[1]:.2f} rupas) outweighs {sub[0]} "
                f"({sub[1]:.2f}) and delivers the larger part{when}")
    return None


def _chk_r2(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or p.antar is None:
        return None
    assoc = vd.lords_associated(ctx.chart, p.maha, p.antar)
    tier = "par excellence" if assoc else "ordinary"
    rel = "associated (conjunct/mutual aspect)" if assoc else "NOT associated"
    return (f"running {p.maha} MD / {p.antar} AD: the two lords are {rel}, so the houses both "
            f"influence give results {tier}")


def _chk_r3(ctx: SynthesisContext) -> Optional[str]:
    """Reports ONLY the single most decisive qualifying yoga (locked 2026-08-02) — the same fix
    `_chk_r1` received on 2026-07-30, which this sibling rule was missed by. Joining two yogas'
    timing into one "; "-separated string put, e.g., "Budha-Aditya Yoga ... (Mercury runs)" and
    "Amala Yoga ripens in Venus's MD" under ONE citable insight, and the narrator was live-caught
    swapping the second yoga's planet into the first's claim. A yoga already ripe NOW outranks one
    that ripens later; ties go to the engine's own yoga order. Nothing is lost: every yoga keeps
    its own Fact via R["yogas"], and the exhaustive per-yoga fructification windows are their own
    report section (R["yoga_timing"], one row per yoga per period)."""
    if ctx.period is None:
        return None
    running = {ctx.period.maha, ctx.period.antar} - {None}
    later: Optional[str] = None
    for y in ctx.yogas:
        pls = _yoga_planets(ctx.chart, y)
        if not pls:
            continue
        hit = sorted(set(pls) & running)
        if hit:                                   # ripe NOW — the most decisive answer, take it
            return f"{y.name} is capable of fructifying NOW ({'/'.join(hit)} runs)"
        if later is None:
            for p in pls:
                win = _md_window(ctx, p)
                if win:
                    later = (f"{y.name} ripens in {p}'s MD "
                             f"({_jd_date(win[0])}..{_jd_date(win[1])})")
                    break
    return later


def _chk_r4(ctx: SynthesisContext) -> Optional[str]:
    if ctx.period is None:
        return None
    lord = ctx.period.maha
    pos = ctx.chart.planets.get(lord)
    if pos is None:
        return None
    strong = _strong(ctx.chart, lord)
    bits = [f"MD lord {lord}: " + ("strong" if strong else "weak" if strong is False
                                   else "strength unknown") + " by Shadbala"]
    if pos.vargottama and strong:
        # the maximum needs BOTH: rasi strength AND equal navamsa strength (HPA-24:69-72)
        bits.append("and vargottama — strong in both charts, results at their maximum")
    elif pos.vargottama:
        bits.append("vargottama, but the rasi strength is not established — not the maximum")
    else:
        bits.append(f"navamsa {_SIGN[pos.navamsa_sign]}")
    return ", ".join(bits)


def _chk_r5(ctx: SynthesisContext) -> Optional[str]:
    if ctx.period is None:
        return None
    outs = []
    for role, lord in (("MD", ctx.period.maha), ("AD", ctx.period.antar)):
        if lord is None:
            continue
        p = ctx.chart.planets.get(lord)
        if p is None or p.ishta is None or p.kashta is None:
            continue
        lean = "good (Ishta prevails)" if p.ishta > p.kashta else \
            "hard (Kashta prevails)" if p.kashta > p.ishta else "balanced"
        outs.append(f"{role} {lord}: Ishta {p.ishta:.1f} vs Kashta {p.kashta:.1f} — {lean}")
    if not outs:
        return None
    rm, ra = _rupas(ctx.chart, ctx.period.maha), (
        _rupas(ctx.chart, ctx.period.antar) if ctx.period.antar else None)
    # GBB-10:145-152 states only the MD-predominates direction; no converse is asserted.
    if rm is not None and ra is not None and rm >= ra:
        outs.append(f"{ctx.period.maha}'s character prevails in the sub-period "
                    f"(the Dasha lord's strength predominates)")
    return "; ".join(outs)


def _chk_r6(ctx: SynthesisContext) -> Optional[str]:
    if len(ctx.bhava_balas) < 12:
        return None
    rank = sorted(ctx.bhava_balas.items(), key=lambda kv: -kv[1])
    hi, lo = rank[0], rank[-1]
    return (f"strongest bhava H{hi[0]} ({hi[1]:.0f}); weakest H{lo[0]} ({lo[1]:.0f}) — "
            f"H{hi[0]}'s indications are enjoyed most fully")


def _chk_r7(ctx: SynthesisContext) -> Optional[str]:
    """The running MD lord's residential strength in the bhava it occupies (GBB-1:203).

    Raman states the quantity plainly — "Jupiter gives 0.64 units of the total effects of the
    6th Bhava. This effect will materialise during his Dasa or Bhukthi" — so this reports the
    same measure for the lord whose Dasa is actually running. It is a QUANTITY, never a
    verdict: Raman immediately qualifies it as "a general statement standing to be modified"
    by aspects, the Bhava's own strength and the yoga-karakas (GBB-1:207-211), so the text
    says how much of the house the period can express, not what will happen."""
    if ctx.period is None:
        return None
    lord = ctx.period.maha
    p = ctx.chart.planets.get(lord)
    # from_stated_positions charts carry no cusps (jd_ut None) — nothing to measure against.
    if p is None or len(ctx.chart.bhava_madhyas) != 12 or len(ctx.chart.bhava_sandhis) != 12:
        return None
    bhava, strength = residential_strength(
        p.lon, ctx.chart.bhava_madhyas, ctx.chart.bhava_sandhis)
    near = ("sitting close to the Bhava Madhya, so nearly the whole of it" if strength >= 0.8
            else "close to a Bhava Sandhi, so very little of it" if strength <= 0.2
            else "part-way between the Madhya and a Sandhi, so a moderate part of it")
    return (f"running MD lord {lord} holds {strength:.2f} of bhava {bhava}'s residential "
            f"strength — {near} can find expression through him this period")


def _chk_r14(ctx: SynthesisContext) -> Optional[str]:
    """Bhavartha Ratnakara's Libra dictum, as Raman reproduces it (NH:9578-9581).

    "The dictum of Bhavartha Ratnakara, with a slight modification, is eminently applicable in
    this case. The combination suggests that 'one born in Libra becomes fortunate during Saturn
    Dasa, provided Jupiter is in the 6th or 12th and the Moon is in Lagna'."

    Encoded in its STRICT form. Raman applied it to Franco with "a slight modification" (there
    the Moon is exalted in the 8th, not in Lagna) — that relaxation is his judgment on a
    specific chart, not part of the stated dictum, so widening the rule to match it would be
    inventing doctrine. BR enters only where a registered Raman book reproduces it; the
    project's other BR rule (the karaka-in-12th list) is sourced the same way, via HTJAH-II."""
    if ctx.chart.asc_sign != 7:                       # Libra
        return None
    jup, moon = ctx.chart.planets.get("Jupiter"), ctx.chart.planets.get("Moon")
    if jup is None or moon is None:
        return None
    if jup.bhava not in (6, 12) or moon.bhava != 1:
        return None
    win = _md_window(ctx, "Saturn")
    when = (f" — his MD runs {_jd_date(win[0])}..{_jd_date(win[1])}" if win
            else " — no Saturn MD falls inside the displayed window")
    return (f"Libra Lagna with Jupiter in the {ordinal(jup.bhava)} and the Moon in Lagna: Bhavartha "
            f"Ratnakara's combination for fortune during Saturn's Dasa is present{when}")


def _chk_r8(ctx: SynthesisContext) -> Optional[str]:
    if not ctx.gochara or ctx.period is None:
        return None
    fav = [g.planet for g in ctx.gochara if g.net_good]
    adv = [g.planet for g in ctx.gochara if not g.net_good]
    return (f"current transits (net): favourable {', '.join(fav) or 'none'}; "
            f"adverse/obstructed {', '.join(adv) or 'none'} — all subordinate to the running "
            f"{ctx.period.maha} MD / {ctx.period.antar or ctx.period.maha} AD, which alone "
            f"decides what they can deliver")


def _chk_r9(ctx: SynthesisContext) -> Optional[str]:
    sat_row = next((g for g in ctx.gochara if g.planet == "Saturn"), None)
    sat = ctx.chart.planets.get("Saturn")
    if sat_row is None or sat is None:
        return None
    trines = {sat.sign, (sat.sign - 1 + 4) % 12 + 1, (sat.sign - 1 + 8) % 12 + 1}
    on_signal = sat_row.sign in trines
    if ctx.maraka_now and on_signal:
        # the classical signature is Rasi AND Amsa (HTJAH-II:4846-4849); transit navamsa is
        # not computed here, so only the rasi half is claimed.
        return (f"maraka-tier period runs AND transit Saturn ({_SIGN[sat_row.sign]}) is on the "
                f"natal-Saturn rasi/trine signal — the RASI half of the classical signature "
                f"(the Amsa half is not computed here; still not a prediction)")
    if ctx.maraka_now:
        return (f"a maraka-tier period runs, but transit Saturn ({_SIGN[sat_row.sign]}) is NOT "
                f"on the natal rasi/trine signal ({_SIGN[sat.sign]} trines) — the classical "
                f"signature is incomplete")
    return None


def _chk_r10(ctx: SynthesisContext) -> Optional[str]:
    bal = getattr(ctx.chart, "balarishta", None)
    if bal is None:
        return None
    if bal.cancelled and bal.reasons:
        return f"Balarishta present but CANCELLED — {'; '.join(bal.reasons[:2])}"
    if not bal.applies:
        strong_karaka = _strong(ctx.chart, "Saturn")
        if strong_karaka:
            return ("no Balarishta, and Ayushkaraka Saturn is Shadbala-strong — strength "
                    "supports the higher longevity band")
    return None


def _chk_r11(ctx: SynthesisContext) -> Optional[str]:
    rows = [g for g in ctx.gochara if g.bav_bindus is not None]
    if not rows:
        return None
    # HPA-34:127: "above 4" good, "below 4" weak; the text is silent on exactly 4 — so a
    # 4-bindu transit lands in neither bucket (deliberately unclaimed).
    strong_t = [f"{g.planet} ({g.bav_bindus} bindus)" for g in rows
                if g.gochara_good and (g.bav_bindus or 0) > 4 and not g.vedha_by]
    weak_t = [f"{g.planet} ({g.bav_bindus})" for g in rows
              if g.gochara_good and (g.bav_bindus if g.bav_bindus is not None else 9) < 4]
    bits = []
    if strong_t:
        bits.append("bindu-supported favourable: " + ", ".join(strong_t))
    if weak_t:
        bits.append("favourable but bindu-weak (cannot do as much good): " + ", ".join(weak_t))
    return "; ".join(bits) if bits else None


def _chk_r12(ctx: SynthesisContext) -> Optional[str]:
    # Raman's OWN ownership scheme in the cited discussion (3HC:1105-1111): malefic owners are
    # lords of 3, 6 and 11 (his Gajakesari example uses exactly 6th+11th lordship); lords of
    # 2, 8 and 12 are NEUTRAL — they do not dilute. No 'yogakaraka strengthens' branch: the
    # cited passage explicitly sets lagna-yogakarakas aside (3HC:1018-1022).
    outs = []
    for y in ctx.yogas:
        pls = _yoga_planets(ctx.chart, y)
        if not pls:
            continue
        malefic_owners = []
        for p in pls:
            owned = _lordships(ctx.chart, p)
            bad = sorted(set(owned) & {3, 6, 11})
            if bad:
                malefic_owners.append(f"{p} (lord of {'/'.join(map(str, bad))})")
        if malefic_owners:
            outs.append(f"{y.name} is diluted by ownership: {', '.join(malefic_owners)}")
        if len(outs) == 2:
            break
    return "; ".join(outs) if outs else None


def _chk_r13(ctx: SynthesisContext) -> Optional[str]:
    for y in ctx.yogas:
        if y.kind != "raja":
            continue
        pls = _yoga_planets(ctx.chart, y)
        if not pls:
            continue
        vg = [p for p in pls if getattr(ctx.chart.planets.get(p), "vargottama", False)]
        if vg:
            return (f"{y.name}: constituent {', '.join(vg)} is VARGOTTAMA — the conferred rank "
                    f"is of the highest order the chart's strength allows")
    return None


_CHECKERS: Final[dict[str, Callable[[SynthesisContext], Optional[str]]]] = {
    "SYN_R1_STRONGER_LORD_DELIVERS": _chk_r1,
    "SYN_R2_RUNNING_TIER": _chk_r2,
    "SYN_R3_YOGA_LORD_PERIOD": _chk_r3,
    "SYN_R4_MD_LORD_CONDITION": _chk_r4,
    "SYN_R5_ISHTA_KASHTA_PERIOD": _chk_r5,
    "SYN_R6_BHAVA_BALA_RANK": _chk_r6,
    "SYN_R7_RESIDENTIAL_QUANTITY": _chk_r7,
    "SYN_R8_TRANSIT_CATALYST": _chk_r8,
    "SYN_R9_MARAKA_SATURN_SIGNAL": _chk_r9,
    "SYN_R10_STRENGTH_OVERRIDES_ARISHTA": _chk_r10,
    "SYN_R11_TRANSIT_BINDU_SCALE": _chk_r11,
    "SYN_R12_YOGA_FUNCTIONAL_DILUTION": _chk_r12,
    "SYN_R13_RAJA_VARGOTTAMA_RANK": _chk_r13,
    "SYN_R14_BR_LIBRA_SATURN_DASA": _chk_r14,
}


def _register_checkers(mapping: dict[str, Callable[[SynthesisContext], Optional[str]]]) -> None:
    """Later phases extend the checker table without re-declaring it."""
    _CHECKERS.update(mapping)


# ─────────────────────────────────────────────────────────────────────────────
# Phase B — the CLASSICAL band (CLASSICAL_NONCITABLE; refs quoted in the text)
# ─────────────────────────────────────────────────────────────────────────────

_C = "CLASSICAL_NONCITABLE"


def _lp_label(chart: RamanChart, planet: str) -> str:
    """Laghu Parashari functional label (LP v1:967/1155/2124): yogakaraka > trikona-benefic >
    trishadaya-malefic > neutral (kendra/2/8/12 only)."""
    if is_yogakaraka(planet, chart.asc_sign):
        return "yogakaraka"
    owned = set(_lordships(chart, planet))
    if owned & {1, 5, 9}:
        return "functional benefic (trikona lord)"
    if owned & {3, 6, 11}:
        return "functional malefic (trishadaya lord)"
    return "neutral"


def _sambandha(chart: RamanChart, a: str, b: str) -> Optional[str]:
    """The relation between two lords, ranked per LP v1:2415: exchange > mutual aspect >
    conjunction (dispositor-aspect omitted — weakest and rarely decisive)."""
    pa, pb = chart.planets.get(a), chart.planets.get(b)
    if pa is None or pb is None or a == b:
        return None
    if SIGN_LORDS[pa.sign] == b and SIGN_LORDS[pb.sign] == a:
        return "exchange (the most powerful relation)"
    from app.raman_saab.doctrine import drishti
    if drishti.aspects_planet(a, b, chart) and drishti.aspects_planet(b, a, chart):
        return "mutual aspect (the second relation)"
    if pa.rasi_house == pb.rasi_house:
        return "conjunction (the least of the ranked relations)"
    return None


CLASSICAL_RULES: Final[tuple[SynthesisRule, ...]] = (
    SynthesisRule(
        "SYN_N1_LP_MATRIX", "classical", "N1",
        "Laghu Parashari MD x AD grading matrix", "evaluable", _C,
        "The result of a Mahadasha-Antardasha follows the two lords' functional characters AND "
        "their relation: related lords of the same character give the Dasha lord's results "
        "exclusively; related but opposite characters give very few; unrelated same-character "
        "gives the Dasha lord's results; unrelated opposites give mixed results "
        "(Laghu Parashari v1:4569-4601).",
        "Whether a period delivers cleanly, weakly or mixed here depends on how its two ruling "
        "planets' Laghu Parashari roles stand to each other by relation — a narrower, "
        "house-ownership-only role scheme, NOT the same as Raman's own per-Lagna functional-nature "
        "table printed in Chart signature above (that one also weighs natural nature, "
        "HTJAH-I:523-604, and yogakaraka status, HTJAH-I:606, separately). The resulting grade "
        "is likewise a different, narrower classical framework than Raman's own Bhukti-tier "
        "grading in Life-narrative (the house-influence-plus-association test, "
        "HTJAH-I:1588-1596, 1635-1640, 2588-2599) — the two "
        "measure different things and can legitimately read differently for the same period; "
        "per this project's own governance, Raman's own grading is authoritative wherever they "
        "diverge.",
        ("Life-narrative", "Chart signature"), None),
    SynthesisRule(
        "SYN_N1_OWN_BHUKTI", "classical", "N1",
        "A lord's own bhukti is muted", "evaluable", _C,
        "When the Dasha and Bhukti lord are one and the same planet, he does not give his "
        "entire results (Laghu Parashari v1:4366).",
        "A planet's own sub-period inside its own major period under-delivers.",
        ("Life-narrative",), None),
    SynthesisRule(
        "SYN_N1_YK_ORDER", "classical", "N1",
        "Yogakaraka fructification order", "evaluable", _C,
        "A Yogakaraka's Dasha yields least in a related maraka's bhukti and to the full extent "
        "in a related fellow-yogakaraka's bhukti — an ascending order of fruition "
        "(Laghu Parashari v1:4844-4852).",
        "Even a excellent period ripens unevenly — best in the sub-periods of its allies.",
        ("Life-narrative", "Chart signature"), None),
    SynthesisRule(
        "SYN_N2_SAMBANDHA_RANK", "classical", "N2",
        "The relation between the period lords, ranked", "evaluable", _C,
        "Two lords combine only through a fixed set of relations, ranked by potency: mutual "
        "exchange of houses is the most powerful, next mutual aspect, then aspect by "
        "dispositor, and the least is occupation of the same house (Laghu Parashari v1:2415).",
        "HOW two planets are linked matters as much as THAT they are linked.",
        ("Life-narrative", "Planetary positions"), None),
    SynthesisRule(
        "SYN_N3_KENDRADHIPATYA", "classical", "N3",
        "Kendradhipatya dosha, graded", "evaluable", _C,
        "A natural benefic owning kendras loses its benefic yield — the blemish descending in "
        "magnitude Jupiter > Venus > Mercury > Moon (Laghu Parashari v1:1155, 1923).",
        "A gentle planet saddled with power-houses becomes a reluctant giver.",
        ("Chart signature", "Life-narrative"), None),
    SynthesisRule(
        "SYN_N3_EIGHTH_LORD", "classical", "N3",
        "The 8th lord's period", "evaluable", _C,
        "The 8th lord is deadly evil unless he is also the lord of the Lagna "
        "(Laghu Parashari v1:1769, 1811).",
        "The planet ruling the 8th house runs hard periods — unless it also rules the self.",
        ("Life-narrative", "The maraka scheme"), None),
    SynthesisRule(
        "SYN_N4_AD_FROM_MD", "classical", "N4",
        "The AD lord's seat counted from the MD lord", "evaluable", _C,
        "Antardasha results are conditioned on the sub-lord's position reckoned FROM the Dasha "
        "lord: kendra/trikona from him favourable, 6th/8th/12th from him adverse "
        "(BPHS vol2 ch.52-64, e.g. ch052:87).",
        "Where the sub-period's planet sits relative to the main period's planet colours the "
        "whole stretch.",
        ("Life-narrative", "Planetary positions"), None),
    SynthesisRule(
        "SYN_N5_BPHS_ISHTA_ROOT", "classical", "N5",
        "Ishta/Kashta as the dasha discriminator (BPHS root)", "descriptive", _C,
        "BPHS: 'the benefic and evil tendencies of the planets based on which the Dasa effects "
        "— good or bad — can be decided' (vol1 ch028:28-110) — the classical root of Raman's "
        "GBB treatment (rule SYN_R5).",
        "The good-vs-hard scoring of periods is ancient, not modern.",
        ("Shadbala", "Life-narrative"), None),
    SynthesisRule(
        "SYN_N6_UK_TRIPOD", "classical", "N6",
        "Bhava + lord + karaka judged as one tripod", "descriptive", _C,
        "Uttara Kalamrita: a house is ruined only when the bhava, its lord AND its karaka are "
        "all hemmed by malefics, conjoined with malefics and weak, with hostile navamsa "
        "dispositors (ch003:1594-1599) — the full three-legged test. (On record: the hemming "
        "primitive it needed now exists — `doctrine.hemming` covers both the planet-leg (lord/"
        "karaka) and the house-leg (the bhava) — so the tripod is buildable; the engine's "
        "three-pillar judge remains the Raman-side analogue that already decides the verdict.)",
        "A life-area truly fails only when all three of its supports fail together.",
        ("House-by-house",), None),
    SynthesisRule(
        "SYN_N12_SUBPERIOD_ALLOCATION", "classical", "N12",
        "Sub-period share by seat from the dasha lord", "descriptive", _C,
        "Saravali: sub-periods are allotted by the sub-lord's seat from the dasha lord "
        "(conjunct 1/2; 3rd/9th 1/3; 7th 1/7; 4th/8th 1/4) and ripen according to their own "
        "nature (ch042:23-33). (On record; Vimshottari's fixed proportions govern this "
        "project's timeline.)",
        "The classics also apportioned sub-periods by geometry, not only by fixed fractions.",
        ("Life-narrative",), None),
)


def _chk_n1_matrix(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or p.antar is None or p.antar == p.maha:
        return None
    la, lb = _lp_label(ctx.chart, p.maha), _lp_label(ctx.chart, p.antar)
    related = vd.lords_associated(ctx.chart, p.maha, p.antar) or \
        _sambandha(ctx.chart, p.maha, p.antar) is not None
    benefic_like = {"yogakaraka", "functional benefic (trikona lord)"}
    same = (la in benefic_like) == (lb in benefic_like)
    if related and same:
        cell = "the Dasha lord's results, exclusively and fully"
    elif related and not same:
        cell = "very few results — the lords pull opposite ways despite the link"
    elif not related and same:
        cell = "the Dasha lord's results (no reinforcing link)"
    else:
        cell = "mixed results"
    return (f"{p.maha} MD ({la}) x {p.antar} AD ({lb}), "
            f"{'related' if related else 'unrelated'} -> {cell}")


def _chk_n1_own(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or p.antar != p.maha:
        return None
    return f"{p.maha}'s own bhukti runs — he does not give his entire results here"


def _chk_n1_yk(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or not is_yogakaraka(p.maha, ctx.chart.asc_sign):
        return None
    return (f"MD lord {p.maha} is the Yogakaraka for this Lagna — his Dasha ripens least in a "
            f"related maraka's bhukti and fully in a related ally's bhukti")


def _chk_n2(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or p.antar is None or p.antar == p.maha:
        return None
    rel = _sambandha(ctx.chart, p.maha, p.antar)
    if rel is None:
        return f"{p.maha} and {p.antar} form NO ranked relation — the weakest configuration"
    return f"{p.maha} and {p.antar} are linked by {rel}"


def _chk_n3_kendra(ctx: SynthesisContext) -> Optional[str]:
    grade = {"Jupiter": "greatest", "Venus": "second", "Mercury": "third", "Moon": "least"}
    outs = []
    for planet in ("Jupiter", "Venus", "Mercury", "Moon"):
        owned = set(_lordships(ctx.chart, planet))
        # the dosha needs kendra lordship WITHOUT any trikona share — and the Lagna counts as
        # a trikona (it is kendra AND kona), so lagna-lords are exempt (LP v1:1155 scheme)
        if owned & {4, 7, 10} and not owned & {1, 5, 9}:
            kendras = sorted(owned & {4, 7, 10})
            outs.append(f"{planet} (lord of {'/'.join(map(str, kendras))}) carries the "
                        f"kendradhipatya blemish to the {grade[planet]} degree")
    return "; ".join(outs) if outs else None


def _chk_n3_eighth(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None:
        return None
    for role, lord in (("MD", p.maha), ("AD", p.antar)):
        if lord is None:
            continue
        owned = set(_lordships(ctx.chart, lord))
        if 8 in owned:
            if 1 in owned:
                return (f"{role} lord {lord} rules the 8th but ALSO the Lagna — the classical "
                        f"exemption applies")
            return f"{role} lord {lord} rules the 8th house — the classics read his period hard"
    return None


def _chk_n4(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or p.antar is None or p.antar == p.maha:
        return None
    pa, pb = ctx.chart.planets.get(p.maha), ctx.chart.planets.get(p.antar)
    if pa is None or pb is None:
        return None
    seat = (pb.rasi_house - pa.rasi_house) % 12 + 1
    if seat in (1, 4, 7, 10, 5, 9):
        read = "a kendra/trikona from him — favourable by the BPHS reckoning"
    elif seat in (6, 8, 12):
        read = "the 6th/8th/12th from him — adverse by the BPHS reckoning"
    else:
        read = "a neutral seat"
    return f"AD lord {p.antar} sits in house {seat} counted from MD lord {p.maha}: {read}"


# ─────────────────────────────────────────────────────────────────────────────
# Phase C — the AV band (CLASSICAL_NONCITABLE; Raman's own caveat governs it and
# is printed at the band head by the renderers; never outranks the bands above)
# ─────────────────────────────────────────────────────────────────────────────

AV_RULES: Final[tuple[SynthesisRule, ...]] = (
    SynthesisRule(
        "SYN_N7_AV_DASHA_SEAT", "av", "N7",
        "The dasha graded by its lord's own bindus at his seat", "evaluable", _C,
        "A planet's Dasha is auspicious when the sign he occupies at birth carries an excess of "
        "bindus in his OWN Ashtakavarga; adverse when deficient; mixed when balanced "
        "(Ashtakavarga of Patel ch015:996-1034, proportional 8=full down to 5=quarter).",
        "A period's promise can be read from the dot-score under its ruler's own feet.",
        ("Life-narrative", "Ashtakavarga"), None),
    SynthesisRule(
        "SYN_N7_AV_ANTARDASHA", "av", "N7",
        "The bhukti graded inside the MD lord's Ashtakavarga", "evaluable", _C,
        "The Antardasha of the lord of a bhava carrying only 1-3 bindus in the Mahadasha lord's "
        "Ashtakavarga brings distress; of a bhava carrying 5 or more, benefit "
        "(Ashtakavarga of Patel ch015:1140).",
        "Sub-periods are coloured by how the main period's own chart of dots scores the "
        "sub-lord's houses.",
        ("Life-narrative", "Ashtakavarga"), None),
    SynthesisRule(
        "SYN_N8_SAV_THRESHOLD", "av", "N8",
        "Sarvashtakavarga thresholds by house", "evaluable", _C,
        "A sign with more than 30 bindus is very good, 25-30 middling, below 25 bad — and a "
        "planet in a dusthana with a high bindu count still gives good results (the bindus can "
        "override position; Ashtakavarga of Patel ch014:185-306). The per-bhava minima table "
        "is left on record unencoded.",
        "The dot-totals grade every house on an absolute scale, sometimes overriding placement.",
        ("Ashtakavarga", "House-by-house"), None),
    SynthesisRule(
        "SYN_N9_KAKSHYA_TRANSIT", "av", "N9",
        "Kakshya-level transits over bindus", "descriptive", _C,
        "A transiting planet gives good or bad kakshya by kakshya (eighth-of-sign) according to "
        "the presence of a bindu in that kakshya of its own Ashtakavarga — with roughly 4-day "
        "resolution (Ashtakavarga of Patel ch016:59-97; Phaladeepika ch28 sl.41: high-bindu "
        "signs give good transits even in the 6th/8th/12th). (Kakshya positions not computed.)",
        "The finest classical transit clock — each planet's path is scored segment by segment.",
        ("Current transits", "Ashtakavarga"), None),
    SynthesisRule(
        "SYN_N10_AV_LONGEVITY", "av", "N10",
        "Ashtakavarga longevity and the Shodhyapinda timing", "descriptive", _C,
        "Longevity summed from bindu-spans across the eight Ashtakavargas, and bhava-destruction "
        "timed by Saturn's transit over the Shodhyapinda-derived nakshatra (BPHS vol2 ch071:40; "
        "Patel ch014:941-1027, ch015:132-674). Raman's caveat is aimed PRECISELY here: the AV "
        "method of longevity 'does not seem to be quite reliable' (HTJAH-II:4453-4456). "
        "(Shodhyapinda not computed; on record only.)",
        "The classics could turn the dot-tables into a lifespan clock — Raman himself did not "
        "trust that use.",
        ("Longevity", "Ashtakavarga"), None),
    SynthesisRule(
        "SYN_N11_TRANSIT_VOID", "av", "N11",
        "A transit voided by the planet's own natal state", "evaluable", _C,
        "A planet transiting a favourable house while natally debilitated (or eclipsed) yields "
        "void results; transiting an unfavourable house while debilitated, aggravated ones "
        "(Phaladeepika ch28 sl.31-32).",
        "A transit is only as good as the planet making it.",
        ("Current transits", "Planetary positions"), None),
    SynthesisRule(
        "SYN_N13_VARGOTTAMA_SAV", "av", "N13",
        "Vargottama amplified or reversed by the bindu-count", "evaluable", _C,
        "A vargottama planet in a sign carrying 30 or more SAV bindus enhances the good results "
        "to the greatest extent; with a low count the reverse (Navamsa of Patel ch003:297-306).",
        "Double-strength placement delivers only where the dot-support exists.",
        ("Planetary positions", "Ashtakavarga"), None),
    SynthesisRule(
        "SYN_N14_MODERN_PROTOCOL", "av", "N14",
        "Multi-system agreement (modern practice)", "descriptive", "MODERN",
        "K.N. Rao's protocol: a prediction stands only when Vimshottari, Chara and a third dasha "
        "concur, checked against transit Saturn/Jupiter and the Ashtakavarga points — applied "
        "simultaneously and synthesised (Advanced Techniques:5458, 5833, 9039). On record as "
        "modern practice, not doctrine.",
        "Modern practitioners demand that several independent clocks agree before trusting one.",
        ("Life-narrative", "Current transits"), None),
)


def _chk_n7_seat(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None:
        return None
    pos = ctx.chart.planets.get(p.maha)
    if pos is None:
        return None
    try:
        bav = ashtakavarga.bhinnashtakavarga(ctx.chart, p.maha)
    except Exception:  # noqa: BLE001 — nodes have no BAV
        return None
    b = bav.get(pos.sign)
    if b is None:
        return None
    read = "auspicious (excess)" if b >= 5 else "adverse (deficit)" if b <= 3 else "mixed (4)"
    return (f"MD lord {p.maha} sits in {_SIGN[pos.sign]} holding {b} bindus in his own "
            f"Ashtakavarga — his Dasha reads {read} by this method")


def _chk_n7_ad(ctx: SynthesisContext) -> Optional[str]:
    p = ctx.period
    if p is None or p.antar is None or p.antar == p.maha:
        return None
    try:
        md_bav = ashtakavarga.bhinnashtakavarga(ctx.chart, p.maha)
    except Exception:  # noqa: BLE001
        return None
    outs = []
    for house in _lordships(ctx.chart, p.antar):
        sign = (ctx.chart.asc_sign - 1 + house - 1) % 12 + 1
        b = md_bav.get(sign)
        if b is None:
            continue
        if b <= 3:
            outs.append(f"H{house} (which {p.antar} rules) holds only {b} bindus in "
                        f"{p.maha}'s Ashtakavarga — distress-leaning")
        elif b >= 5:
            outs.append(f"H{house} holds {b} bindus in {p.maha}'s Ashtakavarga — "
                        f"benefit-leaning")
    return "; ".join(outs) if outs else None


def _chk_n8(ctx: SynthesisContext) -> Optional[str]:
    if not ctx.sav:
        return None
    asc = ctx.chart.asc_sign
    by_house = {h: ctx.sav.get((asc - 1 + h - 1) % 12 + 1, 0) for h in range(1, 13)}
    good = [f"H{h} ({b})" for h, b in by_house.items() if b > 30]
    bad = [f"H{h} ({b})" for h, b in by_house.items() if b < 25]
    if not good and not bad:
        return None
    bits = []
    if good:
        bits.append("very good by bindu-count: " + ", ".join(good))
    if bad:
        bits.append("weak by bindu-count: " + ", ".join(bad))
    return "; ".join(bits)


def _chk_n11(ctx: SynthesisContext) -> Optional[str]:
    outs = []
    for g in ctx.gochara:
        try:
            nat = _dig.dignity(g.planet, ctx.chart)
        except Exception:  # noqa: BLE001
            continue
        if nat != "debil":
            continue
        if g.gochara_good:
            outs.append(f"{g.planet}'s favourable transit is VOID — natally debilitated")
        else:
            outs.append(f"{g.planet}'s adverse transit is AGGRAVATED — natally debilitated")
    return "; ".join(outs) if outs else None


def _chk_n13(ctx: SynthesisContext) -> Optional[str]:
    if not ctx.sav:
        return None
    outs = []
    for name, pos in ctx.chart.planets.items():
        if not getattr(pos, "vargottama", False):
            continue
        b = ctx.sav.get(pos.sign)
        if b is None:
            continue
        if b >= 30:
            outs.append(f"vargottama {name} in {_SIGN[pos.sign]} with {b} SAV bindus — "
                        f"enhanced to the greatest extent")
        elif b < 20:
            outs.append(f"vargottama {name} in {_SIGN[pos.sign]} with only {b} bindus — "
                        f"the enhancement reverses")
    return "; ".join(outs) if outs else None


_register_checkers({
    "SYN_N1_LP_MATRIX": _chk_n1_matrix,
    "SYN_N1_OWN_BHUKTI": _chk_n1_own,
    "SYN_N1_YK_ORDER": _chk_n1_yk,
    "SYN_N2_SAMBANDHA_RANK": _chk_n2,
    "SYN_N3_KENDRADHIPATYA": _chk_n3_kendra,
    "SYN_N3_EIGHTH_LORD": _chk_n3_eighth,
    "SYN_N4_AD_FROM_MD": _chk_n4,
    "SYN_N7_AV_DASHA_SEAT": _chk_n7_seat,
    "SYN_N7_AV_ANTARDASHA": _chk_n7_ad,
    "SYN_N8_SAV_THRESHOLD": _chk_n8,
    "SYN_N11_TRANSIT_VOID": _chk_n11,
    "SYN_N13_VARGOTTAMA_SAV": _chk_n13,
})

SYNTHESIS_RULES: Final[tuple[SynthesisRule, ...]] = RAMAN_RULES + CLASSICAL_RULES + AV_RULES


def descriptive_rules(band: Optional[Band] = None) -> tuple[SynthesisRule, ...]:
    """Doctrine on record that the engine cannot yet evaluate (never fired)."""
    return tuple(r for r in SYNTHESIS_RULES
                 if r.kind == "descriptive" and (band is None or r.band == band))


def detect_synthesis(
    chart: RamanChart, jd: float, *,
    gochara: tuple[TransitRow, ...] = (),
    yogas: Optional[tuple[FiredYoga, ...]] = None,
    sav: Optional[dict[int, int]] = None,
    bhava_balas: Optional[dict[int, float]] = None,
    maraka_now: bool = False,
) -> tuple[FiredInsight, ...]:
    """Evaluate every evaluable synthesis rule against the chart at ``jd``.

    Report-only: reads verdict-layer outputs, never feeds them. Raman-band insights are listed
    first (the AV band, when present, never overrides them — the ORDER encodes the precedence).
    """
    if yogas is None:
        yogas = detect_yogas(chart)
    if sav is None:
        try:
            sav = ashtakavarga.sarvashtakavarga(chart)
        except Exception:  # noqa: BLE001 — sparse chart
            sav = {}
    period = vd.dasha_on(chart, jd) if getattr(chart, "jd_ut", None) is not None else None
    timeline = tuple(vd.mahadasha_timeline(chart)) \
        if getattr(chart, "jd_ut", None) is not None else ()
    ctx = SynthesisContext(
        chart=chart, jd=jd, period=period, md_timeline=timeline,
        gochara=tuple(gochara), yogas=tuple(yogas), sav=dict(sav),
        bhava_balas=dict(bhava_balas or {}), maraka_now=maraka_now,
    )
    out: list[FiredInsight] = []
    band_order = {"raman": 0, "classical": 1, "av": 2}
    for rule in sorted(SYNTHESIS_RULES, key=lambda r: band_order[r.band]):
        if rule.kind != "evaluable":
            continue
        chk = _CHECKERS.get(rule.id)
        if chk is None:
            continue
        try:
            detail = chk(ctx)
        except Exception:  # noqa: BLE001 — a checker must never break the report
            detail = None
        if detail:
            out.append(FiredInsight(rule=rule, detail=detail))
    return tuple(out)
