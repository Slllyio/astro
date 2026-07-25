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
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.primitives import ashtakavarga
from app.raman_saab.primitives import dignity as _dig
from app.raman_saab.primitives import vimshottari as vd
from app.raman_saab.primitives.functional_nature import is_yogakaraka
from app.raman_saab.primitives.shadbala import total as _sb_total
from app.raman_saab.primitives.transits import TransitRow

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


#: Yoga constituents where they are structurally certain. Anything else returns None and the
#: yoga-specific rules simply do not fire for it (never guess a constituent).
def _yoga_planets(chart: RamanChart, y: FiredYoga) -> Optional[tuple[str, ...]]:
    n = y.name.lower()
    if "gajakesari" in n:
        return ("Jupiter", "Moon")
    if "budha-aditya" in n or "budha aditya" in n:
        return ("Sun", "Mercury")
    if "9th-10th" in n or "9th and 10th" in n:
        asc = chart.asc_sign
        return (SIGN_LORDS[(asc - 1 + 8) % 12 + 1], SIGN_LORDS[(asc - 1 + 9) % 12 + 1])
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
        "Residential strength quantifies the period's yield", "descriptive", _R,
        "A planet's residential strength gives the exact quantity of its house's effects, which "
        "finds expression during its Dasha — modified by aspects, the Bhava's own strength and "
        "the yoga-karakas. (Encoded pending a residential-strength primitive.)",
        "How much of a house a planet can deliver in its period is itself a measured quantity.",
        ("Life-narrative", "House-by-house"), Citation("GBB-1", 203)),
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
    outs = []
    for y in ctx.yogas:
        pls = _yoga_planets(ctx.chart, y)
        if not pls:
            continue
        pairs = [(p, _rupas(ctx.chart, p)) for p in pls]
        if any(r is None for _p, r in pairs):
            continue
        pairs.sort(key=lambda pr: -pr[1])
        lead, sub = pairs[0], pairs[-1]
        win = _md_window(ctx, lead[0])
        when = f" — his MD runs {_jd_date(win[0])}..{_jd_date(win[1])}" if win else ""
        outs.append(f"{y.name}: {lead[0]} ({lead[1]:.2f} rupas) outweighs {sub[0]} "
                    f"({sub[1]:.2f}) and delivers the larger part{when}")
        if len(outs) == 2:
            break
    return "; ".join(outs) if outs else None


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
    if ctx.period is None:
        return None
    running = {ctx.period.maha, ctx.period.antar} - {None}
    outs = []
    for y in ctx.yogas:
        pls = _yoga_planets(ctx.chart, y)
        if not pls:
            continue
        hit = sorted(set(pls) & running)
        if hit:
            outs.append(f"{y.name} is capable of fructifying NOW ({'/'.join(hit)} runs)")
        else:
            for p in pls:
                win = _md_window(ctx, p)
                if win:
                    outs.append(f"{y.name} ripens in {p}'s MD "
                                f"({_jd_date(win[0])}..{_jd_date(win[1])})")
                    break
        if len(outs) == 2:
            break
    return "; ".join(outs) if outs else None


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
    "SYN_R8_TRANSIT_CATALYST": _chk_r8,
    "SYN_R9_MARAKA_SATURN_SIGNAL": _chk_r9,
    "SYN_R10_STRENGTH_OVERRIDES_ARISHTA": _chk_r10,
    "SYN_R11_TRANSIT_BINDU_SCALE": _chk_r11,
    "SYN_R12_YOGA_FUNCTIONAL_DILUTION": _chk_r12,
    "SYN_R13_RAJA_VARGOTTAMA_RANK": _chk_r13,
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
        "Whether a period delivers cleanly, weakly or mixed depends on how its two ruling "
        "planets stand to each other — by role and by relation.",
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
        "dispositors (ch003:1594-1599) — the full three-legged test. (Encoded pending a "
        "hemming primitive; the engine's three-pillar judge is the Raman-side analogue.)",
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


_register_checkers({
    "SYN_N1_LP_MATRIX": _chk_n1_matrix,
    "SYN_N1_OWN_BHUKTI": _chk_n1_own,
    "SYN_N1_YK_ORDER": _chk_n1_yk,
    "SYN_N2_SAMBANDHA_RANK": _chk_n2,
    "SYN_N3_KENDRADHIPATYA": _chk_n3_kendra,
    "SYN_N3_EIGHTH_LORD": _chk_n3_eighth,
    "SYN_N4_AD_FROM_MD": _chk_n4,
})

SYNTHESIS_RULES: Final[tuple[SynthesisRule, ...]] = RAMAN_RULES + CLASSICAL_RULES


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
