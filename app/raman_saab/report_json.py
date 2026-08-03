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
from typing import Any

from app.raman_saab.detailed_report import DetailedReport, graded_buckets
from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE


def _ad(obj: Any) -> Any:
    """asdict for a dataclass, identity otherwise (JSON-safe leaves pass straight through)."""
    return asdict(obj) if is_dataclass(obj) else obj


def _each(seq) -> list:
    return [_ad(x) for x in seq]


def _chart_dict(chart) -> dict:
    """Trimmed chart: the planet table a reader/consumer actually needs (not the full model)."""
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
            "ishta": p.ishta,
            "kashta": p.kashta,
        }
    return {"asc_sign": chart.asc_sign, "planets": planets}


def _timeline_dict(timeline, chart) -> list:
    """Trimmed windowed timeline: one row per bhukti with the houses it lights, each graded by
    Raman's FOUR-tier fructification scheme (par excellence / ordinary / limited / feeble) via the
    ONE shared `graded_buckets` implementation — so the interactive page shows the SAME grading as
    the standalone report, not a coarser view. `associated` is whether the AD lord is associated
    with the MD lord (the distinction between par-excellence and ordinary)."""
    out = []
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
                 "natal_verdict": str(a.natal_verdict)}
                for a in tp.activated
            ],
        })
    return out


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


def to_report_dict(r: DetailedReport) -> dict:
    """The full structured report as a JSON-safe dict — the shared grounding contract."""
    from app.raman_saab.judgment_graph import build_judgment_graph
    b = r.birth
    _jg = build_judgment_graph(r)
    return {
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

        # houses + the honesty overlay + the strength / preponderance cross-checks
        "proformas": [_proforma_dict(pf) for pf in r.proformas],
        "calibration": {str(h): _ad(cr) for h, cr in r.calibration.items()},
        "house_strength": _each(r.house_strength),
        "preponderance": _ad(r.preponderance),
        "dashboard": _ad(r.dashboard),
        "distinctive": [[h, _ad(e)] for h, e in r.distinctive],
        "info": _ad(r.info),

        # yogas (each carries its own Citation object) + the synthesis insights
        "yogas": _each(r.yogas),
        "yoga_timing": _each(r.yoga_timing),
        "insights": [
            {"rule_id": ins.rule.id, "name": ins.rule.name, "band": ins.rule.band,
             "simple_meaning": ins.rule.simple_meaning, "detail": ins.detail,
             "links": list(ins.rule.links),
             "source": (_ad(ins.rule.source) if ins.rule.source is not None else None)}
            for ins in r.insights
        ],

        # longevity + the maraka scheme
        "longevity": {"years": r.longevity_years, "ymd": list(r.longevity_ymd),
                      "class": r.longevity_class,
                      "balarishta": (_ad(r.balarishta) if r.balarishta is not None else None)},
        "maraka_saturn": _each(r.maraka_saturn),
        "maraka_period_now": r.maraka_period_now,
        "health_readout": _ad(r.health_readout),     # v17 — pure re-read, caveat included
        "interpretation_guide": INTERPRETATION_GUIDE,  # v18 — chart-independent doctrine metadata
        # S1 synthesis layer — the explicit judgment graph (pure re-read; PREC-10 applies)
        "judgment_graph": {"nodes": _each(_jg.nodes), "edges": _each(_jg.edges)},
        "planet_bios": _each(r.planet_bios),         # v20 — dominant-graha biographies (S2)
        "yoga_deep": _each(r.yoga_deep),             # v21 — per-yoga deep-reads

        # the life-narrative and its companions + the woven chapters
        "timeline": _timeline_dict(r.timeline, r.chart),
        "ishta_kashta": _each(r.ishta_kashta),
        "md_condition": _each(r.md_condition),
        "dasa_kakshya": _each(r.dasa_kakshya),
        "av_dasha_seats": _each(r.av_dasha_seats),
        "life_chapters": _each(r.life_chapters.chapters),

        # transits
        "gochara": _each(r.gochara),
        "gochara_outlook": {p: _each(segs) for p, segs in r.gochara_outlook.items()},
        "dasha_transit": _each(r.dasha_transit),

        # ashtakavarga + the divisional deep-reads (prose bodies) + soul/pitru surfaces
        "sav": {str(s): b_ for s, b_ in r.sav.items()},
        "divisional": [{"label": lbl, "body": body} for lbl, body in r.divisional],
        "soul": _ad(r.soul),
        "pitru": _ad(r.pitru),

        "window": {"ref_jd": r.ref_jd, "back": r.window_back, "forward": r.window_forward},
    }
