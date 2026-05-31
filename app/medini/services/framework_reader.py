"""Bridge: calculate_all_charts → framework Reading.

Plugs the astrologer's-lens framework (Phases 1-9) into the existing
FastAPI ``/reading`` endpoint without disturbing the original RAG-based
``chart_reader.read_chart`` pipeline.

The flow:
  birth-data → calculate_all_charts → _to_framework_chart →
  compose_reading → format_reading_text (or JSON-serialise)

The output preserves every structured claim with its classical
citation, so the UI can render either as prose or as a table of
verdicts per bhava.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from app.core.chart_model import Chart
from app.core.dkp_modulation import DKPContext
from app.core.dkp_translation import TranslationRecord
from app.core.reading_composer import (
    Reading,
    compose_reading,
    format_reading_text,
)

logger = logging.getLogger(__name__)


def _to_framework_chart(
    chart_dict: dict[str, Any], person_id: str | None = None,
) -> Chart:
    """Convert calculate_all_charts output → framework Chart.

    Handles the existing dict shape:
      {
        "ascendant": {longitude, sign, ...},
        "d1": {planet: {longitude, sign, house, is_retrograde, ...}},
        "birth_jd": float,
      }
    """
    asc = chart_dict.get("ascendant") or chart_dict.get("asc") or {}
    d1 = chart_dict.get("d1") or {}
    if not asc or not d1:
        raise ValueError(
            "chart_dict missing required keys 'ascendant' and/or 'd1'"
        )
    planet_signs: dict[str, int] = {}
    planet_houses: dict[str, int] = {}
    planet_lons: dict[str, float] = {}
    planet_retrograde: dict[str, bool] = {}
    for graha, info in d1.items():
        if not isinstance(info, dict):
            continue
        if "sign" in info:
            planet_signs[graha] = int(info["sign"])
        if "house" in info:
            planet_houses[graha] = int(info["house"])
        if "longitude" in info:
            planet_lons[graha] = float(info["longitude"])
        planet_retrograde[graha] = bool(info.get("is_retrograde", False))

    return Chart(
        asc_sign=int(asc["sign"]),
        asc_lon=float(asc["longitude"]),
        planet_signs=planet_signs,
        planet_houses=planet_houses,
        planet_lons=planet_lons,
        planet_retrograde=planet_retrograde,
        person_id=person_id,
    )


def read_chart_via_framework(
    chart_dict: dict[str, Any],
    *,
    context: DKPContext | None = None,
    vimshottari_md_lord: str | None = None,
    person_id: str | None = None,
) -> Reading:
    """Compose a framework Reading from a calculate_all_charts dict.

    Args:
        chart_dict: Output of ``app.core.ephemeris_engine.calculate_all_charts``.
        context: DKPContext for modulation. Defaults to empty (LOW confidence).
        vimshottari_md_lord: Caller-provided active MD lord at target time.
            If not provided, attempts to extract from ``chart_dict["current_mahadasha"]``.
        person_id: Optional identifier for the chart.
    """
    chart = _to_framework_chart(chart_dict, person_id=person_id)
    if context is None:
        context = DKPContext()
    if vimshottari_md_lord is None:
        md_block = chart_dict.get("current_mahadasha") or {}
        vimshottari_md_lord = md_block.get("lord")
    birth_jd = chart_dict.get("birth_jd")
    return compose_reading(
        chart, context,
        birth_jd=float(birth_jd) if birth_jd is not None else None,
        vimshottari_md_lord=vimshottari_md_lord,
    )


def _translation_to_dict(t: "TranslationRecord") -> dict[str, Any]:
    """Serialise a TranslationRecord for JSON response."""
    return {
        "key": t.key,
        "classification": t.classification,
        "domain": t.domain,
        "shloka": t.shloka,
        "classical_references": list(t.classical_references),
        "ancient_manifestation": t.ancient_manifestation,
        "desh_shift": t.desh_shift,
        "kaal_shift": t.kaal_shift,
        "paristhiti_shift": t.paristhiti_shift,
        "modern_manifestation": t.modern_manifestation,
        "invariant_mechanism": t.invariant_mechanism,
        "modern_references": list(t.modern_references),
        "lagna_specific_notes": {
            int(k): v for k, v in t.lagna_specific_notes.items()
        },
        # Phase C: direct Sanskrit quotation
        "sanskrit_shloka": t.sanskrit_shloka,
        "transliteration": t.transliteration,
        "word_gloss": t.word_gloss,
        # Phase E: knowledge-library passage IDs
        "corpus_passage_ids": list(t.corpus_passage_ids),
    }


def read_chart_master(
    chart_dict: dict[str, Any],
    context=None,
    *,
    atmakaraka: str | None = None,
    atmakaraka_d9_sign: int | None = None,
    moon_nakshatra_index: int | None = None,
    target_nakshatra_index: int | None = None,
    day_of_week: int | None = None,
    is_day_birth: bool | None = None,
    target_jd: float | None = None,
    transit_signs: dict[str, int] | None = None,
    varga_pillar_scores: dict[int, float] | None = None,
):
    """Bridge from ephemeris-engine chart dict → MasterReading.

    Mirrors read_chart_via_framework but routes through
    compose_master_reading instead of compose_reading, integrating all
    13 master-technique layers.
    """
    from app.core.dkp_modulation import DKPContext
    from app.core.master_reading import compose_master_reading

    chart = _to_framework_chart(chart_dict)
    if context is None:
        context = DKPContext()
    md_block = chart_dict.get("current_mahadasha") or {}
    vimshottari_md_lord = md_block.get("lord")
    birth_jd = chart_dict.get("birth_jd")
    return compose_master_reading(
        chart, context,
        target_jd=target_jd,
        birth_jd=float(birth_jd) if birth_jd is not None else None,
        atmakaraka=atmakaraka,
        atmakaraka_d9_sign=atmakaraka_d9_sign,
        moon_nakshatra_index=moon_nakshatra_index,
        target_nakshatra_index=target_nakshatra_index,
        day_of_week=day_of_week,
        is_day_birth=is_day_birth,
        vimshottari_md_lord=vimshottari_md_lord,
        transit_signs=transit_signs,
        varga_pillar_scores=varga_pillar_scores,
    )


def _sensitive_point_to_dict(sp) -> dict[str, Any]:
    """Serialise a SensitivePoint."""
    return {
        "name": sp.name,
        "longitude": round(float(sp.longitude), 3),
        "sign": int(sp.sign),
        "natal_house": int(sp.natal_house),
        "degree_in_sign": round(float(sp.degree_in_sign), 3),
        "interpretation_hint": sp.interpretation_hint,
    }


def _arudha_to_dict(a) -> dict[str, Any]:
    """Serialise an ArudhaPada."""
    return {
        "bhava": int(a.bhava),
        "bhava_lord": a.bhava_lord,
        "arudha_sign": int(a.arudha_sign),
        "arudha_natal_house": int(a.arudha_natal_house),
        "interpretation_hint": a.interpretation_hint,
    }


def master_reading_to_dict(mr) -> dict[str, Any]:
    """Serialise a MasterReading for JSON API response.

    Wraps the base Reading dict (via reading_to_dict) and adds the
    13-gap layers as nested fields.
    """
    base = reading_to_dict(mr.base_reading)
    base["master_layers"] = {
        "ashtakavarga": {
            "strongest_bhava": int(mr.ashtakavarga.strongest_bhava),
            "weakest_bhava": int(mr.ashtakavarga.weakest_bhava),
            "total_sav": int(mr.ashtakavarga.total_sav),
            "sav_per_bhava": {
                str(b): {
                    "sav_points": int(r.sav_points),
                    "strength_label": r.strength_label,
                    "multiplier": round(float(r.multiplier), 2),
                }
                for b, r in mr.ashtakavarga.sav_per_bhava.items()
            },
        },
        "varga_confirmations": {
            str(b): {
                "varga_name": c.varga_name,
                "d1_label": c.d1_label,
                "varga_label": c.varga_label,
                "confirmation_label": c.confirmation_label,
                "rationale": c.rationale,
            }
            for b, c in mr.varga_confirmations.items()
        },
        "arudha_lagna": _arudha_to_dict(mr.arudha_lagna),
        "upapada_lagna": _arudha_to_dict(mr.upapada_lagna),
        "dara_pada": _arudha_to_dict(mr.dara_pada),
        "all_arudhas": {
            str(b): _arudha_to_dict(a) for b, a in mr.all_arudhas.items()
        },
        "karakamsa": None if mr.karakamsa is None else {
            "atmakaraka": mr.karakamsa.atmakaraka,
            "atmakaraka_d1_sign": int(mr.karakamsa.atmakaraka_d1_sign),
            "karakamsa_sign": int(mr.karakamsa.karakamsa_sign),
            "bhava_readings": {str(b): v for b, v in mr.karakamsa.bhava_readings.items()},
        },
        "sensitive_points": {
            "bhrigu_bindu": _sensitive_point_to_dict(mr.sensitive_points.bhrigu_bindu),
            "pranapada": _sensitive_point_to_dict(mr.sensitive_points.pranapada),
            "upagrahas": {
                name: _sensitive_point_to_dict(u)
                for name, u in mr.sensitive_points.upagrahas.items()
            },
            "beeja_sphuta": {
                "name": mr.sensitive_points.beeja_sphuta.name,
                "longitude": round(float(mr.sensitive_points.beeja_sphuta.longitude), 3),
                "sign": int(mr.sensitive_points.beeja_sphuta.sign),
                "sign_lord": mr.sensitive_points.beeja_sphuta.sign_lord,
                "dignity": mr.sensitive_points.beeja_sphuta.dignity,
                "fertility_grade": mr.sensitive_points.beeja_sphuta.fertility_grade,
            },
            "kshetra_sphuta": {
                "name": mr.sensitive_points.kshetra_sphuta.name,
                "longitude": round(float(mr.sensitive_points.kshetra_sphuta.longitude), 3),
                "sign": int(mr.sensitive_points.kshetra_sphuta.sign),
                "sign_lord": mr.sensitive_points.kshetra_sphuta.sign_lord,
                "dignity": mr.sensitive_points.kshetra_sphuta.dignity,
                "fertility_grade": mr.sensitive_points.kshetra_sphuta.fertility_grade,
            },
            "maandi": None if mr.sensitive_points.maandi is None
                      else _sensitive_point_to_dict(mr.sensitive_points.maandi),
        },
        "avastha": {
            "baladi": {
                p: {
                    "stage": b.stage,
                    "strength_multiplier": round(float(b.strength_multiplier), 3),
                    "degree_in_sign": round(float(b.degree_in_sign), 3),
                }
                for p, b in mr.avastha.baladi.items()
            },
            "deeptadi": {
                p: {
                    "state": d.state,
                    "strength_multiplier": round(float(d.strength_multiplier), 3),
                    "rationale": d.rationale,
                }
                for p, d in mr.avastha.deeptadi.items()
            },
            "composite_multipliers": {
                p: round(float(v), 3) for p, v in mr.avastha_multipliers.items()
            },
        },
        "vimsopaka": {
            p: {
                "scheme": r.scheme,
                "composite_rupas": round(float(r.composite_rupas), 3),
                "strength_label": r.strength_label,
                "per_varga_dignity": {
                    k: round(float(v), 3) for k, v in r.per_varga_dignity.items()
                },
            }
            for p, r in mr.vimsopaka.items()
        },
        "bhavat_chains": [
            {
                "base_bhava": int(c.base_bhava),
                "distance": int(c.distance),
                "derived_bhava": int(c.derived_bhava),
                "natural_karaka_of_derived": list(c.natural_karaka_of_derived),
                "interpretation_hint": c.interpretation_hint,
            }
            for c in mr.bhavat_chains
        ],
        "triple_lagna_per_bhava": {
            str(b): {k: int(v) for k, v in d.items()}
            for b, d in mr.triple_lagna_per_bhava.items()
        },
        "yogini_active": None if mr.yogini_active is None else {
            "yogini_name": mr.yogini_active.yogini_name,
            "presiding_planet": mr.yogini_active.presiding_planet,
            "period_years": int(mr.yogini_active.period_years),
            "start_jd": round(float(mr.yogini_active.start_jd), 4),
            "end_jd": round(float(mr.yogini_active.end_jd), 4),
        },
        "ashtottari_active": None if mr.ashtottari_active is None else {
            "lord": mr.ashtottari_active.lord,
            "period_years": int(mr.ashtottari_active.period_years),
            "start_jd": round(float(mr.ashtottari_active.start_jd), 4),
            "end_jd": round(float(mr.ashtottari_active.end_jd), 4),
        },
        "ashtottari_applicable": bool(mr.ashtottari_applicable_flag),
        "tara_at_target": None if mr.tara_at_target is None else {
            "janma_nakshatra_index": int(mr.tara_at_target.janma_nakshatra_index),
            "target_nakshatra_index": int(mr.tara_at_target.target_nakshatra_index),
            "distance": int(mr.tara_at_target.distance),
            "tara_label": mr.tara_at_target.tara_label,
            "is_auspicious": bool(mr.tara_at_target.is_auspicious),
        },
        "prescribed_remedies": [
            {
                "planet": rx.planet,
                "condition": rx.condition,
                "recommended_remedies": list(rx.recommended_remedies),
                "gemstone_caveat": rx.gemstone_caveat,
                "rationale": rx.rationale,
            }
            for rx in mr.prescribed_remedies
        ],
        # S-5 — cross-layer convergence verdicts per domain. Top-level
        # synthesis view: every verdict carries weighted_score, label,
        # confidence band, supporting + contradicting layer counts, and
        # the full per-layer Evidence list with classical citations.
        "convergence": {
            domain: {
                "primary_bhava": int(v.primary_bhava),
                "label": v.convergence_label,
                "confidence": v.confidence_band,
                "weighted_score": round(float(v.weighted_score), 3),
                "n_supporting": int(v.n_supporting),
                "n_contradicting": int(v.n_contradicting),
                "coverage_caveat": v.coverage_caveat,
                "evidence": [
                    {
                        "layer": e.layer,
                        "signal": int(e.signal),
                        "weight": round(float(e.weight), 3),
                        "says": e.what_it_says,
                        "citation": e.citation,
                    }
                    for e in v.evidence
                ],
                "contradictions": [
                    {"supports": s, "contradicts": c}
                    for s, c in v.contradictions
                ],
            }
            for domain, v in (mr.convergence_verdicts or {}).items()
        },
    }
    # Replace the base text with the richer master-format text
    from app.core.master_reading import format_master_reading_text
    base["rendered_text"] = format_master_reading_text(mr)
    return base


def reading_to_dict(reading: Reading) -> dict[str, Any]:
    """Serialise a framework Reading for JSON response.

    Lists/tuples become arrays; the per-bhava claims become a JSON-
    friendly dict keyed by bhava number (1..12 as strings).
    """
    bhava_claims_json = {}
    for b, claim in reading.bhava_claims.items():
        bhava_claims_json[str(b)] = {
            "verdict_label": claim.verdict_label,
            "composite_score": round(float(claim.composite_score), 3),
            "confidence": claim.confidence,
            "reading_focus": claim.reading_focus,
            "key_findings": list(claim.key_findings),
            "citations": list(claim.citations),
            "confirming_yogas": list(claim.confirming_yogas),
            "afflicting_yogas": list(claim.afflicting_yogas),
            "gochara_triggered": bool(claim.gochara_triggered),
            "modulation_notes": list(claim.modulation_notes),
            "relevant_translations": [
                _translation_to_dict(t) for t in claim.relevant_translations
            ],
        }
    return {
        "person_id": reading.person_id,
        "asc_sign": int(reading.asc_sign),
        "asc_lagna_lord": reading.asc_lagna_lord,
        "yogakarakas": list(reading.yogakarakas),
        "badhakesh": reading.badhakesh,
        "strongest_planet": reading.strongest_planet,
        "weakest_planet": reading.weakest_planet,
        "chart_strength_summary": reading.chart_strength_summary,
        "active_yogas": [
            {
                "name": y.name,
                "sanskrit": y.sanskrit,
                "intensity": round(float(y.intensity), 3),
                "participants": list(y.participants),
                "reference": y.reference,
                "description": y.description,
            }
            for y in reading.active_yogas
        ],
        "vimshottari_md_at_target": reading.vimshottari_md_at_target,
        "chara_md_at_target": reading.chara_md_at_target,
        "bhava_claims": bhava_claims_json,
        "open_questions": list(reading.open_questions),
        "dkp_completeness": int(reading.dkp_completeness),
        "translations": [_translation_to_dict(t) for t in reading.translations],
        "rendered_text": format_reading_text(reading),
    }
