"""Structured JSON serializer for the detailed report — the grounding contract.

`to_report_dict(report)` turns the frozen `DetailedReport` into a plain, JSON-safe dict that
BOTH the interactive frontend (drill-down, click-to-source) and the grounded LLM explainer
consume. It is a sibling of `report_html.py` (which renders prose) — this one preserves the
STRUCTURE (~85% of the report is already typed dataclasses) so a consumer can bind to fields
rather than parse text.

Design:
- Whitelist each section's structured fields; `dataclasses.asdict` handles the clean subtrees
  (including nested `Citation` -> {work, line} and `Tagged` -> {text, provenance, cite}).
- `chart` and `timeline` are TRIMMED to display essentials (not raw-dumped — they are large).
- Citations that already exist as objects (yogas, insights, the Tagged lines in soul/pitru)
  surface as objects; citations interpolated into prose stay in the prose (the frontend's
  click-to-source regexes any WORK:line token out of any string, so no per-claim re-plumb is
  needed — see `doctrine.sources.passage`).
- No verdict is recomputed; this is a pure re-read of an already-built report.

Usage:
    from app.raman_saab.report_json import to_report_dict
    d = to_report_dict(build_detailed_report(birth))   # json.dumps(d) is safe
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Optional

from app.raman_saab.detailed_report import (DetailedReport, distinctive_gloss,
                                            gochara_synthesis_sentence, graded_buckets,
                                            influence_basis, influence_basis_table)
from app.raman_saab.detailed_report import POPULATION_NOTE as _POPULATION_NOTE
from app.raman_saab.detailed_report import deeptadi_table as _deeptadi_table
from app.raman_saab.detailed_report import signature_first_glance as _signature_first_glance
from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE
from app.raman_saab.plain_terms import SECTION_METHOD as _SECTION_METHOD
from app.raman_saab.plain_terms import gloss_dict as _gloss
from app.raman_saab.section_meta import section_meta_json as _section_meta
from app.raman_saab.detailed_report import longevity_band_label as _band_label
from app.raman_saab.primitives.balarishta import screened_conditions as _bala_screened
from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED as _MIN_REQ


def _ad(obj: Any) -> Any:
    """asdict for a dataclass, identity otherwise (JSON-safe leaves pass straight through)."""
    return asdict(obj) if is_dataclass(obj) else obj


def _each(seq) -> list:
    return [_ad(x) for x in seq]


def _marriage_json(m: Any) -> Any:
    """The marriage monograph, with each fired kalatra rule's maintainer notes routed
    into their own field instead of reaching client prose.

    ADD-ONLY: `fired_kalatra` keeps the raw rule text exactly as before; the two new
    parallel keys carry the same rows already split by
    `monographs.split_maintainer_notes` (the markdown and standalone-HTML surfaces
    route them the same way). A client renders `fired_kalatra_client` and shows
    `fired_kalatra_notes` as fine print."""
    if m is None:
        return None
    from app.raman_saab.monographs import split_maintainer_notes

    d = _ad(m)
    rows = d.get("fired_kalatra") or ()
    client: list = []
    notes: list = []
    for row in rows:
        row = list(row)
        text = row[1] if len(row) > 1 else ""
        kept, note = split_maintainer_notes(str(text))
        client.append([row[0], kept, *row[2:]])
        if note:
            notes.append([row[0], note])
    d["fired_kalatra_client"] = client
    d["fired_kalatra_notes"] = notes
    return d


def _chart_dict(chart) -> dict:
    """Trimmed chart: the planet table a reader/consumer actually needs (not the full model)."""
    from app.raman_saab.detailed_report import (ascendant_position, format_longitude,
                                                nakshatra_lord)
    planets = {}
    for name, p in chart.planets.items():
        planets[name] = {
            "sign": p.sign,
            "rasi_house": p.rasi_house,
            "nakshatra": p.nakshatra,
            "pada": p.pada,
            "navamsa_sign": p.navamsa_sign,
            "retrograde": p.retrograde,
            "vargottama": p.vargottama,
            "combust_fraction": round(p.combust_fraction, 3),
            "shadbala_rupas": (round(p.shadbala_rupas.total / 60.0, 2)
                               if p.shadbala_rupas is not None else None),
            # Raman's own required minimum (GBB-8:303) — so any consumer can band the
            # value against HIS threshold, never an invented one.
            "shadbala_required": _MIN_REQ.get(name),
            "ishta": p.ishta,
            "kashta": p.kashta,
            # append-only 2026-08-17 (report-critique: exact degrees + Vimshottari audit
            # trail): the sidereal longitude, its checkable sign-degree form, and the
            # nakshatra's Vimshottari lord (Moon's row explains the birth Mahadasha).
            "lon": round(p.lon, 6),
            "longitude": format_longitude(p.lon),
            "nakshatra_lord": nakshatra_lord(p.nakshatra),
        }
    # append-only 2026-08-17: the Ascendant as a checkable row of its own.
    asc_lon_s, asc_nak, asc_pada, asc_nav, asc_sign = ascendant_position(chart)
    ascendant = {
        "lon": round(chart.asc_lon, 6),
        "longitude": asc_lon_s,
        "sign": asc_sign,
        "nakshatra": asc_nak,
        "pada": asc_pada,
        "nakshatra_lord": nakshatra_lord(asc_nak),
        "navamsa_sign": asc_nav,
    }
    return {"asc_sign": chart.asc_sign, "planets": planets,
            "asc_lon": round(chart.asc_lon, 6), "ascendant": ascendant}


def _timeline_dict(timeline, chart) -> list:
    """Trimmed windowed timeline: one row per bhukti with the houses it lights, each graded by
    Raman's FOUR-tier fructification scheme (par excellence / ordinary / limited / feeble) via the
    ONE shared `graded_buckets` implementation — so the interactive page shows the SAME grading as
    the standalone report, not a coarser view. `associated` is whether the AD lord is associated
    with the MD lord (the distinction between par-excellence and ordinary)."""
    out = []
    # append-only 2026-08-18 (Wave-2): the influence-basis table, computed ONCE per report
    # via the role-preserving `timer_roles` (pinned equal to timer_set by test) — so every
    # activated-house row can say BY WHICH factor each period-lord influences the house
    # (HTJAH-I:1586-1596), instead of asserting the tier bare.
    basis = influence_basis_table(chart)
    for tp in timeline.periods:
        pr = tp.period
        associated, buckets = graded_buckets(tp, chart)
        tier_of = {a.house: tier for tier, items in buckets.items() for a in items}
        out.append({
            "maha": pr.maha, "antar": pr.antar,
            "start_jd": pr.start_jd, "end_jd": pr.end_jd,
            "associated": associated,
            "activated": [
                {"house": a.house, "grade": a.grade, "tier": tier_of.get(a.house),
                 "natal_verdict": str(a.natal_verdict),
                 # append-only 2026-08-17 (Wave-1): the lord_quality delivery tags the
                 # rows always carried (HTJAH-II:10004-10008) — full LordQuality objects,
                 # so a consumer can show 'MD delivers well, AD mixed' per row.
                 "md_quality": _ad(a.md_quality),
                 "antar_quality": (_ad(a.antar_quality)
                                   if a.antar_quality is not None else None),
                 # append-only 2026-08-18 (Wave-2): the influence-basis tag strings
                 # ("owns+karaka", "aspects lord", "via H11 owns") per period-lord.
                 "md_basis": (influence_basis(basis, a.house, a.md_lord)
                              if a.md_activates else None),
                 "antar_basis": (influence_basis(basis, a.house, a.antar_lord)
                                 if a.antar_activates and a.antar_lord is not None
                                 else None)}
                for a in tp.activated
            ],
        })
    return out


def _baladi_jagradadi(chart) -> dict:
    """Per-planet Baladi/Jagradadi states, re-read through the judge's own read-only accessor
    (append-only 2026-08-17). {} on Track-B charts, same degradation the judge uses."""
    from app.raman_saab.judges.house_template import baladi_jagradadi_states
    return baladi_jagradadi_states(chart)


def _proforma_dict(pf) -> dict:
    """Trimmed house proforma: the verdict + per-signification verdicts (not the full ledger)."""
    return {
        "house": pf.house,
        "lord": pf.lord,
        "rollup": str(pf.rollup),
        "significations": [
            {"signification": sv.signification, "verdict": str(sv.verdict),
             "karaka": sv.karaka, "degree": sv.degree}
            for sv in pf.significations
        ],
    }


def _yoga_coverage(r: DetailedReport) -> dict:
    """Append-only 2026-08-18 (Wave-2): the yoga coverage-honesty block — pure re-reads
    of `doctrine.yogas` metadata and the bhanga primitives; no verdict logic."""
    from app.raman_saab.doctrine.yogas import (MAHAPURUSHA_IDS, YOGAS,
                                               family_breakdown, yoga_family)
    from app.raman_saab.primitives.bhangas import kemadruma
    from app.raman_saab.yoga_deep_read import kemadruma_cancellation_branch
    kem_state = "no geometry"
    kem_branch = None
    if kemadruma(r.chart):
        kem_branch = kemadruma_cancellation_branch(r.chart)
        kem_state = "cancelled" if kem_branch is not None else "fires"
    absences = []
    if not any(y.id in MAHAPURUSHA_IDS for y in r.yogas):
        absences.append("no Pancha Mahapurusha yoga fires")
    if not any(y.kind == "arishta" for y in r.yogas):
        absences.append("no encoded arishta yoga fires")
    return {
        "encoded": len(YOGAS),
        "of_about": 300,
        "families": [{"family": fam, "count": n} for fam, n in family_breakdown()],
        "fired_families": {y.id: yoga_family(y.id) for y in r.yogas},
        "notable_absences": absences,
        "kemadruma": {"state": kem_state, "cancelled_by": kem_branch},
        "note": "a yoga absent from this list is unchecked, not absent",
    }


def feedback_instrument_for(r: DetailedReport) -> dict:
    """The instrument, from the four projections it actually reads.

    `build_feedback_instrument` takes the report DICT, and calling `to_report_dict` from inside
    `to_report_dict` is not an option — so the inputs are projected once here, with the same
    helpers the full dict uses, and handed over. Keep this list in step with what the module
    reads; a silently missing key degrades a part rather than raising.

    Public because the markdown and standalone renderers need it too and hold a DetailedReport,
    not a dict. They import it lazily inside their own function bodies: this module imports
    `detailed_report` at module level, so a top-level import back the other way would cycle.
    """
    from app.raman_saab.feedback_instrument import build_feedback_instrument
    b = r.birth
    return build_feedback_instrument({
        "birth": {"year": b.year, "month": b.month, "day": b.day, "hour": b.hour,
                  "minute": b.minute, "tz_offset": b.tz_offset,
                  "latitude": b.latitude, "longitude": b.longitude},
        "chart": {"asc_sign": r.chart.asc_sign, "asc_lon": round(r.chart.asc_lon, 6)},
        "calibration": {str(h): _ad(cr) for h, cr in r.calibration.items()},
        "timeline": _timeline_dict(r.timeline, r.chart),
    })


def simple_summary_for_dict(report: dict) -> Optional[dict]:
    """The plain-words summary as a JSON-safe dict, from an already-built report dict."""
    from dataclasses import asdict

    from app.raman_saab.simple_summary import build_simple_summary
    summary = build_simple_summary(report)
    return asdict(summary) if summary is not None else None


def simple_summary_for(r: DetailedReport) -> Optional[dict]:
    """The same, from a DetailedReport — for the markdown and standalone renderers, which hold
    the report object rather than the dict. Imported lazily by them: this module imports
    `detailed_report` at module level, so a top-level import back the other way would cycle."""
    return simple_summary_for_dict(to_report_dict(r))


def to_report_dict(r: DetailedReport) -> dict:
    """The full structured report as a JSON-safe dict — the shared grounding contract."""
    from app.raman_saab.judgment_graph import build_judgment_graph
    b = r.birth
    _jg = build_judgment_graph(r)
    out: dict = {
        "birth": {"name": b.name, "year": b.year, "month": b.month, "day": b.day,
                  "hour": b.hour, "minute": b.minute, "tz_offset": b.tz_offset,
                  "latitude": b.latitude, "longitude": b.longitude},
        "chart": _chart_dict(r.chart),

        # top-of-page human summary layers (labeled prose slots)
        "plain_reading": _ad(r.plain_reading),
        "nichod": _ad(r.nichod),

        # the engine's ranked "what matters most" — a re-read of the sections below, cross-linked
        "digest": _ad(r.digest),

        # chart signature + first impression
        "synthesis": _ad(r.synthesis),
        "overview": _ad(r.overview),
        "ruler": _ad(r.ruler),
        # append-only 2026-08-18 (report-critique, foundation): Raman's first-glance rows
        # (balance of dasha at birth, Lagna/Moon degrees, paksha-vs-Shadbala, luminary
        # strength flags, Lagna-lord disposition, day-lord observation) and the Deeptadi
        # per-planet testimony table (state + secondary states + Raman's HPA Ch.7 result
        # + rules/occupies) — the same computed rows the markdown/HTML surfaces render.
        "signature_first_glance": [list(row) for row in _signature_first_glance(r)],
        "deeptadi_table": [list(row) for row in _deeptadi_table(r)],

        # houses + the honesty overlay + the strength / preponderance cross-checks
        "proformas": [_proforma_dict(pf) for pf in r.proformas],
        "calibration": {str(h): _ad(cr) for h, cr in r.calibration.items()},
        # The feedback instrument — the questionnaire the reader answers about their own life.
        # Built here rather than in the route so every surface gets the same one, and built
        # WITHOUT its answer key: `feedback_instrument.instrument_key` recomputes that
        # server-side for scoring, and shipping it beside the questions would destroy the only
        # property that makes the answers worth collecting (see that module's docstring).
        "feedback_instrument": feedback_instrument_for(r),
        "house_strength": _each(r.house_strength),
        "preponderance": _ad(r.preponderance),
        "dashboard": _ad(r.dashboard),
        # append-only 2026-08-17: `gloss` — the plain-language midpoint-side sentence the
        # markdown "What stands out" table shows; existing fields untouched.
        "distinctive": [[h, {**_ad(e), "gloss": distinctive_gloss(e)}]
                        for h, e in r.distinctive],
        # append-only 2026-08-17 (Wave-2): `sentence` (the property asdict drops) and the
        # canonical measured `population_note` the info section now renders — calibration
        # framing, never validation. Existing keys untouched.
        "info": {**_ad(r.info), "sentence": r.info.sentence,
                 "population_note": _POPULATION_NOTE},

        # yogas (each carries its own Citation object) + the synthesis insights
        "yogas": _each(r.yogas),
        # append-only 2026-08-18 (Wave-2, coverage honesty): what the yoga list actually
        # checks — encoded-record count + Raman-taxonomy family breakdown, each fired
        # yoga's family, the notable absences, and the cancelled-Kemadruma three-state —
        # the same disclosures the markdown/HTML "Yogas present" section now renders.
        "yoga_coverage": _yoga_coverage(r),
        "yoga_timing": _each(r.yoga_timing),
        "insights": [
            {"rule_id": ins.rule.id, "name": ins.rule.name, "band": ins.rule.band,
             "simple_meaning": ins.rule.simple_meaning, "detail": ins.detail,
             "links": list(ins.rule.links),
             "source": (_ad(ins.rule.source) if ins.rule.source is not None else None)}
            for ins in r.insights
        ],

        # longevity + the maraka scheme
        # append-only 2026-08-18 (Wave-2 items 5a/5b): `class_label` — the harmonised
        # band label the markdown/HTML now show ("Purnayu (purna band)"); and
        # `balarishta_screened` — the primitive's own checked conditions (label, cite),
        # the clear-case screen disclosure. Existing keys untouched.
        "longevity": {"years": r.longevity_years, "ymd": list(r.longevity_ymd),
                      "class": r.longevity_class,
                      "class_label": _band_label(r.longevity_class),
                      "balarishta": (_ad(r.balarishta) if r.balarishta is not None else None),
                      "balarishta_screened": [list(x) for x in _bala_screened()]},
        "maraka_saturn": _each(r.maraka_saturn),
        "maraka_period_now": r.maraka_period_now,
        # append-only 2026-08-17 (report-critique: per-planet maraka reasons): the full
        # tiered maraka scheme the markdown/HTML "The maraka scheme" section renders —
        # each unit now carries the qualifying clause(s) recorded at assignment.
        "maraka": (
            {"units": _each(r.chart.maraka_points.units),
             "drekkana22_lord": r.chart.maraka_points.drekkana22_lord,
             "navamsa64_lord": r.chart.maraka_points.navamsa64_lord}
            if getattr(r.chart, "maraka_points", None) is not None else None),
        # append-only 2026-08-17 (report-critique: avasthas computed/used, never shown):
        # per-planet Baladi + Jagradadi states via the judge's own read-only accessor
        # (judges/house_template.baladi_jagradadi_states) — CLASSICAL_NONCITABLE
        # (Phaladeepika Ch.3; BPHS Ch.1), intensity dial only, no verdict logic touched.
        "baladi_jagradadi": _baladi_jagradadi(r.chart),
        "health_readout": _ad(r.health_readout),     # v17 — pure re-read, caveat included
        "interpretation_guide": INTERPRETATION_GUIDE,  # v18 — chart-independent doctrine metadata
        # per-section plain-language layer (2026-08-17 reframe) — chart-independent,
        # same transport precedent as interpretation_guide. section_meta carries the
        # EN+HI subtitles / reader-questions / guided-reading steps; section_method
        # carries the "Why astrologers examine this" preambles already rendered on
        # the markdown + standalone surfaces, so the interactive page can too.
        "section_meta": _section_meta(),
        "section_method": {k: {"why": why, "order": list(order)}
                           for k, (why, order) in _SECTION_METHOD.items()},
        # S1 synthesis layer — the explicit judgment graph (pure re-read; PREC-10 applies)
        "judgment_graph": {"nodes": _each(_jg.nodes), "edges": _each(_jg.edges)},
        "planet_bios": _each(r.planet_bios),         # v20 — dominant-graha biographies (S2)
        "yoga_deep": _each(r.yoga_deep),             # v21 — per-yoga deep-reads
        "arishta": _ad(r.arishta) if r.arishta is not None else None,        # v22
        "profession": _ad(r.profession) if r.profession is not None else None,  # v23
        "wealth": _ad(r.wealth) if r.wealth is not None else None,           # v24
        "marriage": _marriage_json(r.marriage),                              # v25
        "children": _ad(r.children) if r.children is not None else None,     # v26
        "psych": _ad(r.psych) if r.psych is not None else None,              # v27
        "decades": _ad(r.decades) if r.decades is not None else None,        # v28
        "life_synthesis": (_ad(r.life_synthesis)
                           if r.life_synthesis is not None else None),       # v29
        "karmic": _ad(r.karmic) if r.karmic is not None else None,           # v30
        "rect_confidence": (_ad(r.rect_confidence)
                            if r.rect_confidence is not None else None),     # v31
        "aptitude": _ad(r.aptitude) if r.aptitude is not None else None,     # v33
        # v35: the HPA-29 medical read (sign -> body region, planet -> complaint, applied
        # through Raman's own 6th-house procedure). Every field ships; the page quotes
        # `application` rather than re-importing the doctrine module.
        "medical": _ad(r.medical) if getattr(r, "medical", None) is not None else None,
        "themes": _ad(r.themes) if r.themes is not None else None,           # v34 integrated reading
        # the plain-terms layer (2026-08-04) — the ONE glossary source every surface
        # renders from; vocabulary only, never new astrology.
        "plain_terms": _gloss(),
        # item 15 — testimony support per house (a re-read of preponderance)
        # append-only 2026-08-18 (Wave-2 E): core_favourable / core_adverse — the same
        # second count pair the table renders (core = lord/karaka/navamsa,
        # HTJAH-I:983-991); existing keys untouched.
        "testimony_support": {
            str(ht.house): {"label": ("High" if "corrobor" in ht.status
                                      else "Low" if "contest" in ht.status
                                      else "Medium"),
                            "favourable": ht.favourable, "adverse": ht.adverse,
                            "neutral": ht.neutral, "status": ht.status,
                            "core_favourable": ht.core_favourable,
                            "core_adverse": ht.core_adverse}
            for ht in r.preponderance.houses},

        # the life-narrative and its companions + the woven chapters
        "timeline": _timeline_dict(r.timeline, r.chart),
        "ishta_kashta": _each(r.ishta_kashta),
        "md_condition": _each(r.md_condition),
        "dasa_kakshya": _each(r.dasa_kakshya),
        "av_dasha_seats": _each(r.av_dasha_seats),
        "life_chapters": _each(r.life_chapters.chapters),

        # transits
        # append-only 2026-08-18 (Wave-2): each snapshot row gains `synthesis` — the one
        # deterministic sentence joining the row's own columns (station + support + vedha
        # + net) the way Raman narrates a transit; existing fields untouched.
        "gochara": [{**_ad(g), "synthesis": gochara_synthesis_sentence(g)}
                    for g in r.gochara],
        "gochara_outlook": {p: _each(segs) for p, segs in r.gochara_outlook.items()},
        "dasha_transit": _each(r.dasha_transit),
        # append-only 2026-08-18 (Wave-2): the ADVERSE mirror of dasha_transit — the same
        # cross-check with the `gochara_good` filter inverted (HPA-34:369-381 blending
        # frame); the favourable rows above are byte-identical to before.
        "dasha_transit_adverse": _each(r.dasha_transit_adverse),

        # ashtakavarga + the divisional deep-reads (prose bodies) + soul/pitru surfaces
        "sav": {str(s): b_ for s, b_ in r.sav.items()},
        # append-only 2026-08-17 (AV completeness): the full Bhinnashtakavarga matrix, the
        # HPA-26 reduced tables and the Sodya Pinda — same rows the markdown/HTML AV section
        # renders; existing keys untouched.
        "bav_matrix": _each(r.bav_matrix),
        "bav_reduced": _each(r.bav_reduced),
        "sodya_pinda": _each(r.sodya_pinda),
        "divisional": [{"label": lbl, "body": body} for lbl, body in r.divisional],
        "soul": _ad(r.soul),
        "pitru": _ad(r.pitru),

        "window": {"ref_jd": r.ref_jd, "back": r.window_back, "forward": r.window_forward},

        # Wave-1 timing additions (2026-08-17, append-only): the current bhukti's
        # pratyantar drill-down, the dated Sade-Sati phase spans (method-only; no
        # result doctrine on record) and the dated Chara dasha sequence — the same
        # objects the markdown and standalone-HTML surfaces render.
        "pratyantar_now": _each(r.pratyantar_now),
        "sade_sati_phases": _each(r.sade_sati_phases),
        "chara_sequence": _each(r.chara_sequence),
    }
    # The plain-words summary is composed FROM the finished dict — it re-reads the house
    # verdicts, the distinctive readings, the honesty counts and the running period, all of
    # which are keys above. Building it here rather than inside the literal is what lets it
    # read them without `to_report_dict` calling itself.
    out["simple_summary"] = simple_summary_for_dict(out)
    return out
