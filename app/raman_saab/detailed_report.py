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
from app.raman_saab.judges.dasamsa_career_reading import build_dasamsa_career_reading
from app.raman_saab.judges.dwadasamsa_parents_reading import build_dwadasamsa_parents_reading
from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
from app.raman_saab.judges.saptamsa_reading import build_saptamsa_children_reading
from app.raman_saab.judges.siddhamsa_education_reading import build_siddhamsa_education_reading
from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading
from app.raman_saab.primitives import ayurdaya
from app.raman_saab.reading_timeline import DashaTimeline, reading_timeline
from app.raman_saab.synthesis import Synthesis, synthesize

_HOUSE_NAME = {1: "Self/Body", 2: "Wealth/Family", 3: "Siblings/Courage", 4: "Mother/Home",
               5: "Children/Mind", 6: "Health/Enemies", 7: "Spouse/Partnership", 8: "Longevity",
               9: "Father/Fortune", 10: "Career", 11: "Gains", 12: "Loss/Moksha/Spirituality"}

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
    synthesis: Synthesis
    calibration: dict[int, CalibratedHouseReading]   # house -> per-signification calibration
    longevity_years: float
    longevity_ymd: tuple[int, int, int]
    longevity_class: str
    divisional: tuple[tuple[str, str], ...]          # (label, full varga deep-read body)
    timeline: DashaTimeline                          # Vimshottari life-narrative (MD by MD)


def build_detailed_report(
    birth: BirthData, *, on: Optional[tuple[int, int, int]] = None, ayanamsa: str = "lahiri",
) -> DetailedReport:
    """Assemble the full reading + calibration for one chart (no verdict is re-judged)."""
    chart: RamanChart = cast_chart(birth, ayanamsa=ayanamsa)
    syn = synthesize(birth, on=on, ayanamsa=ayanamsa)
    calib = {h: build_calibrated_reading(chart, h) for h in range(1, 13)}
    ayur = ayurdaya.longevity(chart)
    return DetailedReport(
        birth=birth, synthesis=syn, calibration=calib,
        longevity_years=round(ayur.total_years, 2), longevity_ymd=ayur.ymd(),
        longevity_class=ayur.longevity_class, divisional=_divisional_sections(chart),
        timeline=reading_timeline(birth, ayanamsa=ayanamsa),
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
    L.append("> **How to read this.** Each house first states Raman's verdict, faithful to his "
             "texts. Beneath it, in _italics_, the instrument discloses how that verdict compares "
             "with 16,450 real charts — its information content, NOT a validated prediction about "
             "your life. " + _VALIDITY.split("(the astrobank")[0].strip())
    L.append("")

    # ── chart signature ───────────────────────────────────────────────────────
    L.append("## Chart signature")
    L.append("")
    L.append(f"- **Lagna** {s.lagna}  |  **Navamsa Lagna** {s.navamsa_lagna}  |  "
             f"**Atmakaraka** {s.atmakaraka}  |  **Arudha Lagna** {s.arudha_lagna}")
    L.append(f"- **Jaimini** — Karakamsa {s.karakamsa}  |  Upapada {s.upapada}  |  "
             f"spouse-lord (7th-from-D9) {s.spouse_significator}")
    L.append(f"- **Running periods** — Vimshottari {s.running_md} MD / {s.running_ad} AD  |  "
             f"Chara dasha {s.chara}" + (f"  |  {s.sade_sati}" if s.sade_sati else ""))
    if s.panchanga:
        L.append(f"- **Panchanga** — {s.panchanga}")
    L.append("")

    # ── longevity ─────────────────────────────────────────────────────────────
    L.append("## Longevity (Ayurdaya)")
    L.append("")
    L.append(f"Numeric span {r.longevity_years:g} years ({y}y {mo}m {d}d) — **{r.longevity_class}**.")
    if s.longevity_combos:
        L.append("")
        L.append("Fired longevity combinations (HTJAH-II):")
        for lcx in s.longevity_combos:
            L.append(f"- {lcx}")
    L.append("")

    # ── house-by-house, with calibration ──────────────────────────────────────
    L.append("## House-by-house reading")
    for mr in s.matters:
        L.append("")
        L.append(f"### House {mr.house} — {mr.name}")
        L.append("")
        L.append(mr.reading)
        cal = _calibration_lines(r.calibration[mr.house])
        if cal:
            L.append("")
            L.append("_Population context:_")
            L.extend(cal)

    # ── life-narrative (Vimshottari Dasha, MD by MD) ──────────────────────────
    L.append("")
    L.append("## Life-narrative (Vimshottari Dasha)")
    L.append("")
    L.append("_The same natal promises, read as they ripen: each Mahadasha lights the houses its "
             "lord activates. Verdicts are the UNCHANGED natal readings above._")
    from app.raman_saab.render import _jd_to_date
    for tp in r.timeline.periods:
        L.append("")
        L.append(f"### {tp.period.maha} Dasha ({_jd_to_date(tp.period.start_jd)} .. "
                 f"{_jd_to_date(tp.period.end_jd)})")
        pe = [a for a in tp.activated if a.grade == "par_excellence"]
        if pe:
            for a in pe:
                L.append(f"- **House {a.house} ({_HOUSE_NAME[a.house]}):** "
                         f"{a.natal_verdict} ({a.natal_degree})")
        else:
            L.append("- (no par-excellence house activated this period)")
        lim = [a.house for a in tp.activated if a.grade == "limited"]
        if lim:
            L.append(f"- _limited:_ {', '.join(map(str, lim))}")

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

    # ── footer ────────────────────────────────────────────────────────────────
    L.append("")
    L.append("---")
    L.append(f"_Italicised population context is EMPIRICAL_ASTRODATABANK provenance (n="
             f"{r.calibration[1].population_n:,}) - explicitly not Raman. {_VALIDITY}_")
    return _fold_ascii("\n".join(L))


def _fold_ascii(s: str) -> str:
    """ASCII-safe, but FOLD Sanskrit diacritics to base letters (Navamsa, karaka) rather than
    blanking them to '?' — the varga renderers emit UTF-8 IAST that a raw ascii-replace mangles."""
    import unicodedata

    from app.raman_saab.render import _ascii
    folded = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return _ascii(folded)
