"""Detailed report — the engine's full reading as ONE honest document.

This composes what already exists into a single comprehensive report and adds the piece nothing
else joins in: the **population-calibration honesty overlay** woven through every house. For each
bhava it prints Raman's UNCHANGED verdict (the synthesis line — D1 promise, navamsa fruit,
matter-varga, activation windows, live transits) AND, beneath it, how that verdict sits against
16,450 real charts — the percentile, how common the exact reading is, and the atlas-proven INVERTED
warnings (H3 courage, H12 incarceration). It also carries the numeric Ayurdaya span, the fired
longevity combinations, the HTJAH-II career line, the Deeptadi avasthas and the Jaimini Karakamsa
soul reading.

The report is deliberately two-voiced: the doctrine speaks (faithful to Raman), and then the
instrument discloses its own information content (empirical, tagged NOT-Raman). Per the program's
governance the verdict path is untouched — this is assembly + disclosure, never re-judgment.

Usage:
    from app.raman_saab.detailed_report import build_detailed_report, to_markdown
    print(to_markdown(build_detailed_report(birth)))
    # or via the CLI:  py -3.12 -m app.raman_saab --name ... --format report
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.raman_saab import (
    render_dasamsa, render_dwadasamsa, render_navamsa, render_saptamsa,
    render_siddhamsa, render_trimsamsa,
)
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges.calibrated_reading import (
    _VALIDITY,
    CalibratedHouseReading,
    build_calibrated_reading,
)
from app.raman_saab.chart.model import PlanetPos
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.judges.chart_overview import ChartOverview, chart_overview
from app.raman_saab.judges.dasamsa_career_reading import build_dasamsa_career_reading
from app.raman_saab.judges.dwadasamsa_parents_reading import build_dwadasamsa_parents_reading
from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
from app.raman_saab.judges.saptamsa_reading import build_saptamsa_children_reading
from app.raman_saab.judges.siddhamsa_education_reading import build_siddhamsa_education_reading
from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading
from app.raman_saab.judges.house_template import HouseProforma
from app.raman_saab.primitives import ashtakavarga, ayurdaya, nakshatra_signature
from app.raman_saab.primitives.balarishta import BalarishtaState
from app.raman_saab.proforma import read_chart
from app.raman_saab.reading_timeline import DashaTimeline, reading_timeline
from app.raman_saab.synthesis import Synthesis, synthesize

_HOUSE_NAME = {1: "Self/Body", 2: "Wealth/Family", 3: "Siblings/Courage", 4: "Mother/Home",
               5: "Children/Mind", 6: "Health/Enemies", 7: "Spouse/Partnership", 8: "Longevity",
               9: "Father/Fortune", 10: "Career", 11: "Gains", 12: "Loss/Moksha/Spirituality"}

_SIGN_NAME = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
              "Sagittarius", "Capricorn", "Aquarius", "Pisces")

#: lay-reader life-area names (for the plain-language bhukti summary).
_PLAIN_AREA = {1: "self & health", 2: "wealth & family", 3: "courage & siblings",
               4: "home & mother", 5: "children & creativity", 6: "health & rivals",
               7: "marriage & partnership", 8: "longevity", 9: "fortune & father",
               10: "career", 11: "gains", 12: "losses & spirituality"}

#: one-line plain meaning of each fructification grade (shown once as a legend).
_TIER_MEANING = {
    "par excellence": "full, strong results — both period-lords reinforce the house",
    "ordinary": "normal results — both lords touch it, but do not reinforce",
    "limited": "slight results — only the current sub-period (bhukti) lord touches it",
    "feeble": "faint results — only the major-period (Mahadasha) lord touches it",
}


#: plain-language glossary — ONE source of truth, consumed by both renderers.
GLOSSARY: dict[str, str] = {
    "rasi": "the main birth chart (the 12 zodiac signs and where the planets sit in them)",
    "bhava": "a house — one of the 12 life-areas of the chart",
    "navamsa": "the 1/9th divisional chart; Raman treats it as the test of whether a promise is "
               "actually delivered",
    "karaka": "the natural significator of a matter (e.g. Jupiter for children, Venus for marriage)",
    "lord": "the planet that rules a house's sign, and therefore carries that house's affairs",
    "Ashtakavarga": "a bindu (dot) scoring system; more bindus in a sign = more support there. "
                    "Raman rates it corroborative, not decisive",
    "vargottama": "a planet in the same sign in the birth chart and the navamsa — doubly strong",
    "Arudha Lagna": "the chart's public image — how life appears to others, as distinct from "
                    "what it is",
    "Karakamsa": "the navamsa sign of the Atmakaraka — the Jaimini soul axis",
    "Upapada": "the marriage/spouse image point",
    "Sade-Sati": "Saturn's ~7.5-year passage over and around the natal Moon",
    "maraka": "literally 'killer' — a planet or period the classics associate with the end of life",
    "Balarishta": "classical combinations for early-childhood danger, and their cancellations",
    "Kuja dosha": "the 'Mars affliction' for marriage. NOTE: tested on 2,322 real charts by this "
                  "project it did NOT distinguish divorced from long-married (odds ratio 1.09)",
    "Deeptadi avastha": "each planet's result-state (Deepta = blazing, Deena = wretched, etc.)",
    "Beeja / Kshetra": "the male and female fertility points",
    "Atmakaraka": "the planet at the highest degree — the 'soul indicator' in Jaimini",
    "par excellence": "full, strong results (both period-lords reinforce the house)",
    "Mahadasha": "a major planetary period in the Vimshottari system (years to decades)",
    "Antardasha": "a sub-period (bhukti) inside a Mahadasha",
}


@dataclass(frozen=True)
class InfoContent:
    """How much of this reading actually distinguishes THIS chart (the honesty headline)."""
    total: int
    modal_verdict: str
    modal_count: int
    near_universal: int
    inverted: int
    distinctive: int

    @property
    def sentence(self) -> str:
        return (
            f"{self.total} readings. {self.modal_count} return the single most common verdict "
            f"({self.modal_verdict}). {self.near_universal} are near-universal — held by half the "
            f"population or more. {self.inverted} sit on channels this project's validation "
            f"program proved run backwards. {self.distinctive} are genuinely distinctive. "
            f"This is a disclosure about the method's output, not a statement about a life.")


def _all_entries(calibration: dict[int, CalibratedHouseReading]):
    """(house, entry) for every calibrated signification, house order."""
    for house in sorted(calibration):
        for e in calibration[house].entries:
            yield house, e


def information_content(calibration: dict[int, CalibratedHouseReading]) -> InfoContent:
    """Aggregate the calibration overlay into the report's honesty headline."""
    pairs = list(_all_entries(calibration))
    scored = [(h, e) for h, e in pairs if e.favourability_percentile is not None]
    counts: dict[str, int] = {}
    for _h, e in scored:
        key = f"{e.verdict} ({e.degree})"
        counts[key] = counts.get(key, 0) + 1
    modal_verdict, modal_count = max(counts.items(), key=lambda kv: kv[1]) if counts else ("-", 0)
    return InfoContent(
        total=len(pairs), modal_verdict=modal_verdict, modal_count=modal_count,
        near_universal=sum(1 for _h, e in scored if (e.band_share or 0) >= 0.5),
        inverted=sum(1 for _h, e in pairs if e.inverted_warning),
        distinctive=sum(1 for _h, e in scored if e.rarity != "common"),
    )


def distinctive_entries(calibration: dict[int, CalibratedHouseReading], n: int = 7):
    """The n readings that most distinguish this chart — furthest from the population midpoint,
    rare readings first. Returns [(house, entry)] ranked. Pure information content, not prediction."""
    scored = [(h, e) for h, e in _all_entries(calibration)
              if e.favourability_percentile is not None]
    scored.sort(key=lambda he: (-(0 if he[1].rarity == "common" else 1),
                                -abs(he[1].favourability_percentile - 0.5)))
    return tuple(scored[:n])


def rollup_driver(reading: CalibratedHouseReading, rollup: str) -> str | None:
    """Which signification drove the house rollup — the engine grades a bhava by its WORST decided
    matter, so one afflicted signification makes the whole house read afflicted. Naming it prevents
    the reader seeing a contradiction when the other significations look sound."""
    hits = [e.signification for e in reading.entries if e.verdict == rollup]
    return hits[0] if hits else None


ROLLUP_RULE = ("A bhava is graded by its weakest decided matter — one afflicted signification "
               "makes the whole house read afflicted even when the rest are sound.")


def graded_buckets(tp, chart) -> tuple[bool, dict[str, list]]:
    """(AD-associated-with-MD, {tier: [ActivatedHouseReading]}) for one bhukti.

    Hoisted here so BOTH renderers consume one implementation — the doctrine grading must never
    be duplicated in presentation code where the two could silently drift apart.
    """
    from app.raman_saab.primitives import vimshottari as vd
    maha, antar = tp.period.maha, tp.period.antar
    associated = antar is not None and vd.lords_associated(chart, maha, antar)
    buckets: dict[str, list] = {"par excellence": [], "ordinary": [], "limited": [], "feeble": []}
    for a in tp.activated:
        tier = vd.bhukti_tier(a.md_activates, a.antar_activates, associated)
        if tier:
            buckets[tier].append(a)
    return associated, buckets


def planet_rows(chart: RamanChart) -> tuple[tuple[str, PlanetPos], ...]:
    """Planets in canonical order for the positions table (a reading must be checkable)."""
    order = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    return tuple((n, chart.planets[n]) for n in order if n in chart.planets)


def _human_list(items: list[str]) -> str:
    """Join names for prose: 'a', 'a and b', 'a, b and c'."""
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def plain_bhukti_summary(rows, associated: bool) -> str:
    """A lay-reader gloss of one bhukti: its overall intensity (from the association tier) and the
    life-areas under strain (the afflicted houses at that tier, named). A plain restatement of
    Raman's reading — never a prediction of real events."""
    from app.raman_saab.primitives.vimshottari import bhukti_tier
    top = "par excellence" if associated else "ordinary"
    strained = sorted({(a.house, _PLAIN_AREA[a.house]) for a in rows
                       if a.natal_verdict == "afflicted"
                       and bhukti_tier(a.md_activates, a.antar_activates, associated) == top})
    intensity = ("a strong, well-supported stretch" if associated
                 else "a steady, ordinary stretch")
    s = f"In plain terms: {intensity}; most matters run supportively"
    if strained:
        names = [name for _, name in strained]
        s += f", but {_human_list(names)} {'meets' if len(names) == 1 else 'meet'} friction"
    return s + "."

#: Shodasavarga deep-reads: (label, build_reading(chart), render.to_text(reading)).
_DIVISIONAL: tuple[tuple[str, object, object], ...] = (
    ("D-9 Marriage (Navamsa)", build_navamsa_marriage_reading, render_navamsa.to_text),
    ("D-10 Career (Dasamsa)", build_dasamsa_career_reading, render_dasamsa.to_text),
    ("D-7 Children (Saptamsa)", build_saptamsa_children_reading, render_saptamsa.to_text),
    ("D-12 Parents (Dwadasamsa)", build_dwadasamsa_parents_reading, render_dwadasamsa.to_text),
    ("D-30 Health (Trimsamsa)", build_trimsamsa_health_reading, render_trimsamsa.to_text),
    ("D-24 Education (Siddhamsa)", build_siddhamsa_education_reading, render_siddhamsa.to_text),
)


def _clean_box(text: str) -> str:
    """Drop a renderer's own ==== rule lines (we supply the markdown heading instead)."""
    return "\n".join(ln for ln in text.splitlines()
                     if not (ln.strip() and set(ln.strip()) <= {"="}))


def _divisional_sections(chart: RamanChart) -> tuple[tuple[str, str], ...]:
    """Full varga deep-reads; a varga that cannot be cast on this chart is skipped."""
    out: list[tuple[str, str]] = []
    for label, build, render in _DIVISIONAL:
        try:
            out.append((label, _clean_box(render(build(chart)))))
        except Exception:  # noqa: BLE001 — same silent-skip contract as synthesis
            continue
    return tuple(out)


@dataclass(frozen=True)
class DetailedReport:
    """Everything the engine can say about one chart, plus the honesty overlay."""
    birth: BirthData
    chart: RamanChart                                # kept for pillars / positions / grading
    synthesis: Synthesis
    calibration: dict[int, CalibratedHouseReading]   # house -> per-signification calibration
    proformas: tuple[HouseProforma, ...]             # per-house lord + rule evidence (Raman's core)
    overview: ChartOverview                          # stronger frame, functional natures
    yogas: tuple[FiredYoga, ...]                     # fired yogas, each with its citation
    sav: dict[int, int]                              # Sarvashtakavarga bindus per sign
    info: InfoContent                                # the honesty headline
    distinctive: tuple[tuple[int, object], ...]      # (house, CalibratedEntry) most distinguishing
    balarishta: BalarishtaState | None
    longevity_years: float
    longevity_ymd: tuple[int, int, int]
    longevity_class: str
    divisional: tuple[tuple[str, str], ...]          # (label, full varga deep-read body)
    timeline: DashaTimeline                          # windowed Vimshottari MD -> AD narrative
    ref_jd: float                                    # the "now" anchor (on-date or today)
    window_back: int                                 # years of past shown
    window_forward: int                              # years of future shown


_DAYS_PER_VEDIC_YEAR: float = 365.2425


def _windowed_timeline(
    birth: BirthData, on: Optional[tuple[int, int, int]], ayanamsa: str,
    back: int, forward: int,
) -> tuple[DashaTimeline, float]:
    """MD -> AD (bhukti) timeline clipped to [ref - back yr, ref + forward yr].

    ref = the on-date (if given) else today. JD arithmetic per project convention. The full-life
    bhukti walk is built once, then filtered to the periods overlapping the window.
    """
    import swisseph as swe

    if on is not None:
        y, m, d = on
    else:
        from datetime import datetime, timezone
        t = datetime.now(timezone.utc)
        y, m, d = t.year, t.month, t.day
    ref_jd = swe.julday(y, m, d, 12.0)
    lo, hi = ref_jd - back * _DAYS_PER_VEDIC_YEAR, ref_jd + forward * _DAYS_PER_VEDIC_YEAR
    full = reading_timeline(birth, ayanamsa=ayanamsa, expand_bhuktis=True)
    periods = tuple(p for p in full.periods
                    if p.period.end_jd >= lo and p.period.start_jd <= hi)
    return DashaTimeline(birth=full.birth, promise=full.promise, periods=periods), ref_jd


def build_detailed_report(
    birth: BirthData, *, on: Optional[tuple[int, int, int]] = None, ayanamsa: str = "lahiri",
    years_back: int = 10, years_forward: int = 20,
) -> DetailedReport:
    """Assemble the full reading + calibration for one chart (no verdict is re-judged).

    The life-narrative is focused on [now - years_back, now + years_forward] and expanded to
    Mahadasha -> Antardasha, so the near-term periods are the ones detailed.
    """
    chart: RamanChart = cast_chart(birth, ayanamsa=ayanamsa)
    syn = synthesize(birth, on=on, ayanamsa=ayanamsa)
    calib = {h: build_calibrated_reading(chart, h) for h in range(1, 13)}
    ayur = ayurdaya.longevity(chart)
    timeline, ref_jd = _windowed_timeline(birth, on, ayanamsa, years_back, years_forward)
    reading = read_chart(birth, ayanamsa=ayanamsa)       # carries the per-house pillars + evidence
    try:
        sav = ashtakavarga.sarvashtakavarga(chart)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        sav = {}
    return DetailedReport(
        birth=birth, chart=chart, synthesis=syn, calibration=calib,
        proformas=reading.proformas, overview=chart_overview(chart),
        yogas=detect_yogas(chart), sav=sav,
        info=information_content(calib), distinctive=distinctive_entries(calib),
        balarishta=getattr(chart, "balarishta", None),
        longevity_years=round(ayur.total_years, 2), longevity_ymd=ayur.ymd(),
        longevity_class=ayur.longevity_class, divisional=_divisional_sections(chart),
        timeline=timeline, ref_jd=ref_jd,
        window_back=years_back, window_forward=years_forward,
    )


def _calibration_lines(reading: CalibratedHouseReading) -> list[str]:
    """Per-signification honesty rows for one house (empirical, not Raman)."""
    out: list[str] = []
    for e in reading.entries:
        if e.favourability_percentile is None:               # abstained / uncalibrated
            out.append(f"  - _{e.signification}_: {e.verdict} — (uncalibrated)")
            continue
        flags = []
        if e.band_share is not None and e.band_share >= 0.5:
            flags.append("NEAR-UNIVERSAL — carries little information")
        if e.inverted_warning:
            flags.append("INVERTED channel — real cases ran opposite; treat with maximal skepticism")
        tail = f"  [{'; '.join(flags)}]" if flags else ""
        out.append(
            f"  - _{e.signification}_: **{e.verdict} ({e.degree})** — more favourable than "
            f"{e.favourability_percentile:.0%} of charts; this exact reading in "
            f"{e.band_share:.0%} ({e.rarity}){tail}")
    return out


def to_markdown(r: DetailedReport) -> str:
    """Render the full detailed report as a Markdown document (ASCII-safe)."""
    s, b = r.synthesis, r.birth
    y, mo, d = r.longevity_ymd
    L: list[str] = []
    L.append(f"# Detailed reading — {b.name}")
    L.append("")
    L.append(f"**Born** {b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d} "
             f"(tz {b.tz_offset:+g}) at lat {b.latitude:.4f}, lon {b.longitude:.4f}  |  "
             f"ayanamsa Lahiri sidereal")
    L.append("")

    # ── the two-voice preamble ────────────────────────────────────────────────
    pop = r.calibration[1].population_n
    L.append(f"> **How to read this.** Each house first states Raman's verdict, faithful to his "
             f"texts. Beneath it, in _italics_, the instrument discloses how that verdict compares "
             f"with {pop:,} real charts — its information content, NOT a validated prediction about "
             f"your life.")
    L.append("")

    # ── the honesty headline (aggregate information content) ──────────────────
    L.append("## Information content of this reading")
    L.append("")
    L.append(r.info.sentence)
    L.append("")

    # ── what actually distinguishes this chart ────────────────────────────────
    if r.distinctive:
        L.append("## What stands out in this chart")
        L.append("")
        L.append("_The readings furthest from the population midpoint — where this chart is least "
                 "like everyone else's. Rare readings first._")
        L.append("")
        L.append("| house | matter | verdict | percentile | share |")
        L.append("|---|---|---|---:|---:|")
        for house, e in r.distinctive:
            L.append(f"| H{house} {_HOUSE_NAME[house]} | {e.signification} | "
                     f"{e.verdict} ({e.degree}) | {e.favourability_percentile:.0%} | "
                     f"{e.band_share:.0%} ({e.rarity}) |")
        L.append("")

    # ── chart signature ───────────────────────────────────────────────────────
    L.append("## Chart signature")
    L.append("")
    L.append(f"- **Lagna** {s.lagna}  |  **Navamsa Lagna** {s.navamsa_lagna}  |  "
             f"**Atmakaraka** {s.atmakaraka}  |  **Arudha Lagna** {s.arudha_lagna}")
    moon = r.chart.planets.get("Moon")
    if moon is not None:
        sig = nakshatra_signature.signature_for(moon.nakshatra)
        if sig is not None:
            L.append(f"- **Birth nakshatra** (Moon) — {sig.name} pada {moon.pada}, "
                     f"devata {sig.devata}, gana {sig.gana} — _{sig.soul_keyword}_")
    L.append(f"- **Stronger frame** — {r.overview.stronger_frame.upper()} "
             f"(Raman: begin from the ascendant or the Moon, whichever is stronger; HTJAH-I:645-646)")
    L.append(f"- **Jaimini** — Karakamsa {s.karakamsa}  |  Upapada {s.upapada}  |  "
             f"spouse-lord (7th-from-D9) {s.spouse_significator}")
    L.append(f"- **Running periods** — Vimshottari {s.running_md} MD / {s.running_ad} AD  |  "
             f"Chara dasha {s.chara}" + (f"  |  {s.sade_sati}" if s.sade_sati else ""))
    if s.panchanga:
        L.append(f"- **Panchanga** — {s.panchanga}")
    if r.overview.functional_natures:
        nat = "; ".join(f"{p} {n}" for p, n in r.overview.functional_natures)
        L.append(f"- **Functional nature for this Lagna** — {nat}")
    L.append("")

    # ── planet positions (a reading must be checkable) ────────────────────────
    L.append("## Planetary positions")
    L.append("")
    L.append("| graha | sign | house | nakshatra (pada) | navamsa | notes |")
    L.append("|---|---|---:|---|---|---|")
    for name, p in planet_rows(r.chart):
        nk = nakshatra_signature.signature_for(p.nakshatra)
        notes = []
        if p.retrograde:
            notes.append("retrograde")
        if p.vargottama:
            notes.append("vargottama")
        if getattr(p, "combust_fraction", 0) >= 0.5:
            notes.append("combust")
        L.append(f"| {name} | {_SIGN_NAME[p.sign]} | {p.rasi_house} | "
                 f"{nk.name if nk else '?'} ({p.pada}) | {_SIGN_NAME[p.navamsa_sign]} | "
                 f"{', '.join(notes) or '-'} |")
    L.append("")

    # ── fired yogas ───────────────────────────────────────────────────────────
    L.append("## Yogas present in this chart")
    L.append("")
    if r.yogas:
        L.append("_Each carries its citation. A yoga's effect depends on the strength of the "
                 "planets causing it (HTJAH-I:611)._")
        L.append("")
        for yg in r.yogas:
            L.append(f"- **{yg.name}** ({yg.kind}) — {yg.effect}  "
                     f"`{yg.source.work}:{yg.source.line}`")
    else:
        L.append("_No encoded yoga fires on this chart._")
    L.append("")

    # ── Ashtakavarga strength row ─────────────────────────────────────────────
    if r.sav:
        L.append("## Ashtakavarga (Sarvashtakavarga bindus by sign)")
        L.append("")
        L.append("| " + " | ".join(_SIGN_NAME[i][:3] for i in range(1, 13)) + " |")
        L.append("|" + "---:|" * 12)
        L.append("| " + " | ".join(str(r.sav.get(i, 0)) for i in range(1, 13)) + " |")
        L.append("")
        L.append("_Average is 28 per sign (total 337). Raman rates Ashtakavarga corroborative, "
                 "not decisive: \"it does not seem to be quite reliable\" (HTJAH-II:4453-4456)._")
        L.append("")

    # ── house-by-house, with pillars + calibration ────────────────────────────
    L.append("## House-by-house reading")
    L.append("")
    L.append(f"_{ROLLUP_RULE}_")
    for mr in s.matters:
        pf = r.proformas[mr.house - 1] if len(r.proformas) >= mr.house else None
        cal_reading = r.calibration[mr.house]
        L.append("")
        driver = rollup_driver(cal_reading, mr.verdict)
        head = f"### House {mr.house} — {mr.name}: {mr.verdict.upper()}"
        if driver:
            head += f" (driven by _{driver}_)"
        L.append(head)
        L.append("")
        if pf is not None:
            led = pf.significations[0].ledger
            lord_p = r.chart.planets.get(pf.lord)
            lord_bits = f"**Lord** {pf.lord}"
            if lord_p is not None:
                lord_bits += f" in H{lord_p.rasi_house}"
            if led.lord_strong is not None:
                lord_bits += f" ({'strong' if led.lord_strong else 'weak'})"
            kar_bits = f"**Karaka** {led.karaka}"
            if led.karaka_strong is not None:
                kar_bits += f" ({'strong' if led.karaka_strong else 'weak'})"
            if not led.karaka_intact:
                kar_bits += " [afflicted]"
            bb = f"  |  **Bhava Bala** {led.bhava_bala:.1f}" if led.bhava_bala is not None else ""
            L.append(f"{lord_bits}  |  {kar_bits}{bb}  |  **Navamsa** {led.navamsa_status}")
            L.append("")
        L.append(mr.reading)
        cal = _calibration_lines(cal_reading)
        if cal:
            L.append("")
            L.append("_Population context:_")
            L.extend(cal)

    # ── longevity (band FIRST, per Raman's own order) ─────────────────────────
    L.append("")
    L.append("## Longevity")
    L.append("")
    L.append("_Raman's order: first establish the band by combination (Balarishta / Alpayu / "
             "Madhyayu / Purnayu), THEN fix the period by the marakas (HTJAH-II:4465-4472). The "
             "numeric span is a cross-check, never a prediction of death._")
    L.append("")
    if r.balarishta is not None:
        bal = ("applies" if r.balarishta.applies and not r.balarishta.cancelled
               else "cancelled" if r.balarishta.cancelled else "does not apply")
        L.append(f"1. **Balarishta** (early-childhood danger): {bal}"
                 + (f" — {'; '.join(r.balarishta.reasons)}" if r.balarishta.reasons else ""))
    if s.longevity_combos:
        L.append("2. **Band by combination** (HTJAH-II):")
        for lcx in s.longevity_combos:
            L.append(f"   - {lcx}")
    L.append(f"3. **Numeric cross-check (Ayurdaya)**: about **{round(r.longevity_years)} years** "
             f"({y}y {mo}m {d}d) — class **{r.longevity_class}**. Treat as a band, not a date; the "
             f"engine's own health layer defers lifespan.")
    L.append("")

    # ── life-narrative (Vimshottari MD -> AD, windowed) ───────────────────────
    from app.raman_saab.render import _jd_to_date
    w_lo = _jd_to_date(r.ref_jd - r.window_back * _DAYS_PER_VEDIC_YEAR)
    w_hi = _jd_to_date(r.ref_jd + r.window_forward * _DAYS_PER_VEDIC_YEAR)
    L.append("")
    L.append(f"## Life-narrative (Vimshottari Dasha) - {w_lo} to {w_hi}")
    L.append("")
    from app.raman_saab.primitives import vimshottari as vd
    L.append(f"_Mahadasha -> Antardasha across the near term ({r.window_back} years back, "
             f"{r.window_forward} years ahead). A planet influences a house by owning, occupying or "
             f"aspecting the house OR its lord (HTJAH-I:1586-1629). Grades (uniform for every house, "
             f"HTJAH-I:1592-1640, 2588-2599): both lords influence + AD associated with MD = PAR "
             f"EXCELLENCE, both but not associated = ORDINARY, bhukti lord only = LIMITED, MD lord "
             f"only = FEEBLE. Verdicts are the UNCHANGED natal readings above._")
    L.append("")
    L.append("**What the grades mean:** " + "; ".join(
        f"_{k}_ = {v}" for k, v in _TIER_MEANING.items()) + ".")
    _TIER_LABEL = {"par excellence": "par excellence", "ordinary": "ordinary",
                   "limited": "limited (bhukti lord only)", "feeble": "feeble (MD lord only)"}
    cur_md: Optional[str] = None
    for tp in r.timeline.periods:
        rows, maha, antar = tp.activated, tp.period.maha, tp.period.antar
        if maha != cur_md:
            cur_md = maha
            L.append("")
            L.append(f"### {cur_md} Mahadasha")
        associated, raw = graded_buckets(tp, r.chart)     # ONE grading implementation
        buckets = {k: [f"H{a.house} {a.natal_verdict}" for a in v] for k, v in raw.items()}
        assoc = "own bhukti" if antar == maha else \
            ("AD associated with MD" if associated else "AD not associated with MD")
        now = "  **<- now**" if tp.period.start_jd <= r.ref_jd < tp.period.end_jd else ""
        ad = antar or maha
        seg = [f"{'**' if k in ('par excellence', 'ordinary') else ''}{_TIER_LABEL[k]}: "
               f"{', '.join(buckets[k])}{'**' if k in ('par excellence', 'ordinary') else ''}"
               for k in _TIER_LABEL if buckets[k]]
        L.append(f"- **{ad} AD** ({_jd_to_date(tp.period.start_jd)} .. "
                 f"{_jd_to_date(tp.period.end_jd)}){now} - {assoc}; "
                 f"{'; '.join(seg) or '(no house influenced)'}")
        L.append(f"  - _{plain_bhukti_summary(rows, associated)}_")

    # ── divisional deep-reads (Shodasavarga) ──────────────────────────────────
    if r.divisional:
        L.append("")
        L.append("## Divisional deep-reads (Shodasavarga)")
        L.append("")
        L.append("_Each divisional chart magnifies one matter. The Raman core is authoritative; "
                 "the varga block corroborates (report-only)._")
        for label, body in r.divisional:
            L.append("")
            L.append(f"### {label}")
            L.append("")
            L.append("```")
            L.append(body.strip("\n"))
            L.append("```")

    # ── the parallel doctrine layers ──────────────────────────────────────────
    if s.career:
        L.append("")
        L.append("## Career (HTJAH-II — navamsa-dispositor of the 10th lord)")
        L.append("")
        L.append(s.career)
    if s.deeptadi:
        L.append("")
        L.append("## Deeptadi avasthas (each graha's result-state, HPA Ch.7)")
        L.append("")
        L.append(", ".join(s.deeptadi))
    if s.karakamsa_reading:
        L.append("")
        L.append("## Jaimini Karakamsa (the soul's inclination)")
        L.append("")
        for line in s.karakamsa_reading:
            L.append(f"- {line}")

    # ── glossary ──────────────────────────────────────────────────────────────
    L.append("")
    L.append("## Glossary")
    L.append("")
    for term, meaning in GLOSSARY.items():
        L.append(f"- **{term}** — {meaning}")

    # ── footer ────────────────────────────────────────────────────────────────
    L.append("")
    L.append("---")
    L.append(f"_Italicised population context is EMPIRICAL_ASTRODATABANK provenance (n="
             f"{pop:,}) - explicitly not Raman. {_VALIDITY}_")
    return _fold_ascii("\n".join(L))


def _fold_ascii(s: str) -> str:
    """ASCII-safe, but FOLD Sanskrit diacritics to base letters (Navamsa, karaka) rather than
    blanking them to '?' — the varga renderers emit UTF-8 IAST that a raw ascii-replace mangles."""
    import unicodedata

    from app.raman_saab.render import _ascii
    folded = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return _ascii(folded)
