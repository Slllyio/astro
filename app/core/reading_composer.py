"""Reading Composer — Phase 9, the final synthesis layer.

Chains Phases 1-8 into a single ``Reading`` per chart. Each prediction
claim carries its bhava + verdict label + classical citations + DKP
context note, ready for LLM prose-rendering or template-based display.

## Architecture

The composer is **deterministic and structure-first**. It computes:

* **Identity block** — person identifier + Lagna details
* **Chart-strength header** — strongest/weakest planet, active yoga list
* **Per-bhava sections** — 12 bhava verdicts with DKP modulation and
  optional gochara overlay
* **Active dasha block** — current Vimshottari + Chara lord at target JD
* **Open questions** — clarifying questions when DKP completeness is low

The output ``Reading`` dataclass is consumed by the existing
``app/llm/interpreter.py`` LLM layer for prose rendering, or by
``format_reading_text()`` here for terminal output.

## What this is NOT

This composer doesn't compute transits (caller passes them in) and
doesn't compute Vimshottari (caller passes lord names). It's a *pure
synthesis* layer over Phases 1-8 + caller-provided ephemeris facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from app.core.bhava_judge import BhavaVerdict, judge_all_bhavas
from app.core.chara_dasha import chara_active_at
from app.core.chart_model import Chart
from app.core.dkp_modulation import (
    DKPContext, ModulatedVerdict, apply_dkp_modulation, context_completeness,
)
from app.core.dkp_translation import (
    TranslationRecord, all_translations, translations_for_reading,
)
from app.core.functional_roles import (
    badhakesh_planet, functional_roles, yogakaraka_planets,
)
from app.core.gochara_engine import GocharaVerdict, compute_gochara
from app.core.shadbala_report import ShadbalaReport, compute_shadbala
from app.core.yoga_library import Yoga, active_yogas


@dataclass(frozen=True)
class ReadingClaim:
    """One per-bhava synthesized claim — the unit of doctrine output."""
    bhava: int
    verdict_label: str          # strong/medium/weak/afflicted
    composite_score: float
    confidence: str              # LOW/MEDIUM/HIGH from DKP
    reading_focus: str           # what flavour of this bhava is being asked
    key_findings: tuple[str, ...]     # top 3-5 reasonings, sorted by weight
    citations: tuple[str, ...]        # unique classical refs
    confirming_yogas: tuple[str, ...]
    afflicting_yogas: tuple[str, ...]
    gochara_triggered: bool      # is the bhava currently activated by transit?
    modulation_notes: tuple[str, ...]
    # Doctrine translations RELEVANT TO THIS SPECIFIC BHAVA — chosen by
    # matching the bhava's lord/karaka/occupants against the translation
    # registry, and by including yoga-translations from the confirming/
    # afflicting yoga lists. UI can render these next to the verdict
    # instead of only at the top level.
    relevant_translations: tuple[TranslationRecord, ...] = ()


@dataclass(frozen=True)
class Reading:
    """The full chart reading — the final framework output."""
    person_id: str | None
    asc_sign: int
    asc_lagna_lord: str
    yogakarakas: tuple[str, ...]
    badhakesh: str
    strongest_planet: str
    weakest_planet: str
    active_yogas: tuple[Yoga, ...]
    chara_md_at_target: int | None        # sign 1..12 or None
    vimshottari_md_at_target: str | None  # planet name (caller-provided)
    bhava_claims: Mapping[int, ReadingClaim]
    open_questions: tuple[str, ...]
    dkp_completeness: int
    chart_strength_summary: str
    # Doctrine Translation Engine output (Phase 8.5 — classical
    # shloka → modern manifestation translations).
    translations: tuple[TranslationRecord, ...] = ()


def _key_findings_for(verdict: BhavaVerdict, max_n: int = 4) -> tuple[str, ...]:
    """Top N reasonings across all pillars, sorted by absolute weight."""
    all_r = []
    for pillar in verdict.pillars:
        for r in pillar.reasonings:
            all_r.append((abs(r.weight), r.finding))
    all_r.sort(reverse=True)
    return tuple(f for _, f in all_r[:max_n])


def _unique_citations_for(verdict: BhavaVerdict) -> tuple[str, ...]:
    """De-duplicated citation references across all pillar reasonings."""
    seen: set[str] = set()
    out: list[str] = []
    for pillar in verdict.pillars:
        for r in pillar.reasonings:
            if r.reference not in seen:
                seen.add(r.reference)
                out.append(r.reference)
    return tuple(out)


def _build_bhava_claim(
    verdict: BhavaVerdict, modulated: ModulatedVerdict,
    gochara: GocharaVerdict | None,
    chart: Chart | None = None,
) -> ReadingClaim:
    """Compose one per-bhava ReadingClaim from underlying parts.

    Per-bhava translation lookup: when a chart is provided, find all
    translation records whose key matches this bhava's occupants AND
    the yoga-keyed translations from confirming/afflicting yoga lists.
    """
    gochara_trig = False
    if gochara is not None:
        ts = gochara.per_bhava.get(verdict.bhava)
        if ts is not None:
            gochara_trig = (
                ts.is_double_transit_bhava
                or ts.is_double_transit_lord
                or ts.is_double_transit_karaka
            )
    relevant_translations = _per_bhava_translations(
        verdict.bhava, verdict.confirming_yogas, verdict.afflicting_yogas,
        chart,
    )
    return ReadingClaim(
        bhava=verdict.bhava,
        verdict_label=verdict.label,
        composite_score=verdict.composite_score,
        confidence=modulated.confidence,
        reading_focus=modulated.bhava_reading_focus,
        key_findings=_key_findings_for(verdict),
        citations=_unique_citations_for(verdict),
        confirming_yogas=verdict.confirming_yogas,
        afflicting_yogas=verdict.afflicting_yogas,
        gochara_triggered=gochara_trig,
        modulation_notes=modulated.modulation_notes,
        relevant_translations=relevant_translations,
    )


def _per_bhava_translations(
    bhava: int,
    confirming_yogas: tuple[str, ...],
    afflicting_yogas: tuple[str, ...],
    chart: Chart | None,
) -> tuple[TranslationRecord, ...]:
    """Find translation records relevant to a specific bhava.

    Three sources:
      1. Yoga translations from confirming + afflicting yoga lists.
      2. Bhava-placement records where a planet sits IN this specific
         bhava (matches keys like ``bhava_{bhava}_planet_{planet}``).
      3. Bhava-placement records where this bhava's lord or karaka has
         a known placement record — surfaced only when the planet IS at
         the relevant configured house.
    """
    from app.core.dkp_translation import (
        translate_bhava_planet, translate_yoga,
    )
    seen: set[tuple[str, str]] = set()
    out: list[TranslationRecord] = []

    def _add(records: Iterable[TranslationRecord]) -> None:
        for r in records:
            sig = (r.key, r.domain)
            if sig not in seen:
                seen.add(sig)
                out.append(r)

    # Source 1 — yoga-keyed translations.
    for y in confirming_yogas + afflicting_yogas:
        _add(translate_yoga(y))

    # Source 2 — planets sitting in THIS bhava.
    if chart is not None:
        for planet, house in chart.planet_houses.items():
            if house == bhava:
                _add(translate_bhava_planet(bhava, planet))

    return tuple(out)


def _chart_strength_summary(
    report: ShadbalaReport, n_yogas: int, n_active: int,
) -> str:
    """Two-sentence chart-strength summary header."""
    sufficient = sum(
        1 for p in report.per_planet.values() if p.is_sufficient
    )
    return (
        f"Strongest: {report.strongest} (Pinda {report.per_planet[report.strongest].pinda_rupa:.2f} rupas). "
        f"Weakest: {report.weakest} (Pinda {report.per_planet[report.weakest].pinda_rupa:.2f} rupas). "
        f"{sufficient}/7 visible planets meet BPHS Ch.27 strength threshold. "
        f"{n_active}/{n_yogas} canonical yogas are active in this chart."
    )


def compose_reading(
    chart: Chart,
    context: DKPContext = DKPContext(),
    *,
    target_jd: float | None = None,
    birth_jd: float | None = None,
    transit_signs: Mapping[str, int] | None = None,
    vimshottari_md_lord: str | None = None,
) -> Reading:
    """The framework's full-stack call.

    Args:
        chart: The natal Chart.
        context: DKPContext for modulation (default empty → LOW confidence).
        target_jd: Julian Day for which to compute gochara + Chara MD.
        birth_jd: Required for Chara Dasha activation.
        transit_signs: planet → transit sign (caller-computed). If None,
            gochara is skipped.
        vimshottari_md_lord: Caller-provided active Vimshottari MD lord
            at target_jd.

    Returns:
        Reading with all 12 bhava claims + chart-level metadata.
    """
    # Phase 1
    roles = functional_roles(chart.asc_sign)
    asc_lord = next(
        (p for p, r in roles.items() if 1 in r.houses_ruled), "Unknown",
    )
    yks = yogakaraka_planets(chart.asc_sign)
    bd = badhakesh_planet(chart.asc_sign)

    # Phase 3 + 4
    all_active_yogas = active_yogas(chart)
    shadbala = compute_shadbala(chart)

    # Phase 5
    chara_md = None
    if target_jd is not None and birth_jd is not None:
        chara_md = chara_active_at(chart.asc_sign, birth_jd, target_jd)

    # Phase 6
    bhava_verdicts = judge_all_bhavas(chart)

    # Phase 7 (optional)
    gochara_verdict = None
    if transit_signs is not None:
        gochara_verdict = compute_gochara(chart, transit_signs)

    # Phase 8 — per-bhava DKP modulation + per-bhava translation lookup
    bhava_claims: dict[int, ReadingClaim] = {}
    all_questions: list[str] = []
    for b, v in bhava_verdicts.items():
        modulated = apply_dkp_modulation(v, context)
        bhava_claims[b] = _build_bhava_claim(
            v, modulated, gochara_verdict, chart=chart,
        )
        all_questions.extend(modulated.clarifying_questions)

    # De-dup open questions
    seen_q: set[str] = set()
    open_qs: list[str] = []
    for q in all_questions:
        if q not in seen_q:
            seen_q.add(q)
            open_qs.append(q)

    # Yoga count for header (limit cardinality of "active" list to avoid bloat).
    summary = _chart_strength_summary(
        shadbala, n_yogas=len(all_active_yogas), n_active=len(all_active_yogas),
    )

    # Doctrine translations — find all classical→modern translation records
    # that apply to the active yogas + the chart's bhava-placement patterns
    # the translation engine knows about.
    yoga_names = [y.name for y in all_active_yogas]
    placement_pairs = _placement_pairs_present_in_chart(chart)
    translations = translations_for_reading(yoga_names, placement_pairs)

    return Reading(
        person_id=chart.person_id,
        asc_sign=chart.asc_sign,
        asc_lagna_lord=asc_lord,
        yogakarakas=yks,
        badhakesh=bd,
        strongest_planet=shadbala.strongest,
        weakest_planet=shadbala.weakest,
        active_yogas=all_active_yogas,
        chara_md_at_target=chara_md,
        vimshottari_md_at_target=vimshottari_md_lord,
        bhava_claims=bhava_claims,
        open_questions=tuple(open_qs[:6]),
        dkp_completeness=context_completeness(context),
        chart_strength_summary=summary,
        translations=translations,
    )


def _placement_pairs_present_in_chart(
    chart: Chart,
) -> tuple[tuple[int, str], ...]:
    """Enumerate (bhava, planet) pairs present in the chart for which the
    translation engine has a record.

    Iterates the registry's bhava-placement records and checks whether the
    chart actually has the named planet in the named bhava. Deterministic
    and forward-compatible: adding a new placement record to the engine
    automatically picks it up here.
    """
    out: list[tuple[int, str]] = []
    for record in all_translations():
        if record.classification != "bhava_placement":
            continue
        # Key format: "bhava_<N>_planet_<P>" — parse defensively.
        parts = record.key.split("_")
        if len(parts) != 4 or parts[0] != "bhava" or parts[2] != "planet":
            continue
        try:
            bhava = int(parts[1])
        except ValueError:
            continue
        planet = parts[3]
        if chart.house_of(planet) == bhava:
            out.append((bhava, planet))
    return tuple(out)


def format_reading_text(reading: Reading) -> str:
    """Terminal-friendly rendering of the structured Reading.

    Used directly for debugging; the LLM-backed renderer in
    ``app/llm/interpreter.py`` is the production prose path.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("ASTROLOGER-LENS READING")
    lines.append("=" * 70)
    if reading.person_id:
        lines.append(f"Person: {reading.person_id}")
    lines.append(f"Lagna: sign {reading.asc_sign}  Lord: {reading.asc_lagna_lord}")
    lines.append(f"Yogakaraka(s) for this Lagna: {reading.yogakarakas or '(none)'}")
    lines.append(f"Badhakesh (obstruction lord): {reading.badhakesh}")
    lines.append("")
    lines.append("Chart strength:")
    lines.append(f"  {reading.chart_strength_summary}")
    lines.append(f"  Strongest: {reading.strongest_planet}  Weakest: {reading.weakest_planet}")
    if reading.vimshottari_md_at_target:
        lines.append(f"  Active Vimshottari MD: {reading.vimshottari_md_at_target}")
    if reading.chara_md_at_target:
        lines.append(f"  Active Chara MD sign: {reading.chara_md_at_target}")
    lines.append("")
    lines.append(f"Active yogas ({len(reading.active_yogas)}):")
    for y in reading.active_yogas:
        lines.append(f"  - {y.name:18s} (intensity {y.intensity:.2f}) — {y.reference}")
    lines.append("")
    lines.append(f"DKP completeness: {reading.dkp_completeness}/12")
    lines.append("")
    lines.append("Per-bhava verdicts:")
    for b in range(1, 13):
        claim = reading.bhava_claims[b]
        trig = " [TRIGGERED]" if claim.gochara_triggered else ""
        lines.append(
            f"  Bhava {b:2d}  {claim.verdict_label:>10s}  "
            f"composite={claim.composite_score:+.2f}  "
            f"confidence={claim.confidence}{trig}"
        )
        lines.append(f"          focus: {claim.reading_focus}")
        if claim.confirming_yogas:
            lines.append(f"          confirming: {', '.join(claim.confirming_yogas)}")
        for finding in claim.key_findings:
            lines.append(f"          - {finding}")
        if claim.citations:
            lines.append(f"          citations: {' | '.join(claim.citations)}")
        if claim.modulation_notes:
            for n in claim.modulation_notes:
                lines.append(f"          [DKP] {n}")
        lines.append("")
    if reading.open_questions:
        lines.append("Open clarifying questions:")
        for q in reading.open_questions:
            lines.append(f"  ? {q}")
    if reading.translations:
        lines.append("")
        lines.append("=" * 70)
        lines.append("DOCTRINE TRANSLATIONS (classical -> modern manifestation)")
        lines.append("=" * 70)
        lines.append(
            "The shloka encodes the karmic signature; desh-kaal-paristhiti "
            "provides the substrate. The translations below preserve the "
            "doctrine while re-locating its expression in 2026 context."
        )
        lines.append("")
        for t in reading.translations:
            lines.append(f"- [{t.domain}] {t.key}")
            lines.append(f"    Shloka: {t.shloka}")
            lines.append(f"    Modern: {t.modern_manifestation[:300]}")
            lines.append(f"    Invariant: {t.invariant_mechanism[:240]}")
            lines.append("")
    return "\n".join(lines)
