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
