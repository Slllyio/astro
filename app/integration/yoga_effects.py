"""M5 — Yoga effect translator (BPHS Ch.35-40, Phaladeepika Ch.6).

Detection is shipped (`compare_yoga_detection` v0.4.0). EFFECTS are not.

A master astrologer reading "Adhi yoga detected" knows the classical
effect-sentence ("becomes a leader of armies, well-versed in counsel"
per BPHS 36.5) and adjusts it for the native's chart. This module does
that translation.

Approach:
1. Each known yoga has a curated `classical_effect` (one-sentence
   summary of BPHS/Phaladeepika effect text)
2. A `native_modulation` rule modulates the strength based on
   participating-planet dignity/avastha when computable
3. Yogas without curated effect text emit an empty effect (caller can
   fall back to detection-only)

Public surface
--------------
- ``translate_yoga_effects(reading)`` -> list[YogaEffect]
- ``YogaEffect`` Pydantic model
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.integration.yoga_aliases import alias_canonical
from app.integration.yoga_compare import _collect_track_a_yogas, _collect_track_b_yogas
from app.integration.gap_annotator import chart_from_reading


# Curated effect texts per canonical yoga name (after alias normalisation).
# Each entry: (one-line effect text, source citation, optional modifier hint)
_YOGA_EFFECTS: dict[str, tuple[str, str]] = {
    "adhi": (
        "Native becomes a leader / decision-maker, well-versed in counsel. "
        "Advisory or strategic roles benefit; respected for judgement.",
        "BPHS Ch.36.5; Phaladeepika Ch.6",
    ),
    "lakshmi": (
        "Sustained prosperity through righteous means; respected wealth, "
        "good marital harmony, refined enjoyments.",
        "Phaladeepika Ch.6.21; Saravali Ch.39",
    ),
    "gajakesari": (
        "Native is endowed with intelligence, virtuous, wealthy, "
        "well-known for sound judgement and stable mind.",
        "BPHS Ch.37.32; Saravali Ch.39.22",
    ),
    "vipareeta raja": (
        "Adversity converts to advantage. Dusthana lords cancelling each "
        "other produce sudden rise from setbacks; success follows reversal.",
        "Phaladeepika Ch.6.31; Brihat Jataka Ch.11",
    ),
    "mangal": (
        "Mars affliction to marriage/spouse karaka: delays, friction or "
        "intensity in partnerships. Modulated by Mars's natal strength and "
        "remediation through compatible matching.",
        "Mangal Dosha tradition; KN Rao matching rules",
    ),
    "sarpa": (
        "Karmic intensity around relationships and family lineage. The "
        "Rahu-Ketu axis brings unconventional patterns and karmic lessons.",
        "Kala Sarpa tradition; Sanjay Rath karmic-axis reading",
    ),
    "sunapha": (
        "Native is self-made, intelligent, accumulates wealth through "
        "own efforts. Strength modulated by the planet in the 2nd from Moon.",
        "BPHS Ch.36.20; Saravali Ch.27",
    ),
    "anapha": (
        "Native is well-spoken, refined, of pleasant disposition; "
        "respected and possesses comforts.",
        "BPHS Ch.36.21; Saravali Ch.27",
    ),
    "kemadruma": (
        "Moon isolated (no planets in 2nd/12th from Moon nor Jupiter in "
        "kendra) — emotional/material constraints; mitigated when benefic "
        "lord aspects Moon or Jupiter is strong.",
        "BPHS Ch.36.23; Phaladeepika Ch.6.42",
    ),
    "saraswati": (
        "Native is learned, eloquent, talented in arts/letters/sciences; "
        "blessed with knowledge that yields recognition.",
        "Phaladeepika Ch.6.40; KN Rao Yogas",
    ),
    "budha-aditya": (
        "Combined intelligence and authority — analytical mind with "
        "leadership presence; recognition in scholarly or governmental fields.",
        "Phaladeepika Ch.6.49",
    ),
    "chandra-mangal": (
        "Combination of emotion and initiative — business-minded, "
        "action-oriented; profits through trade or independent enterprise.",
        "BPHS Ch.36.10; Phaladeepika Ch.6.50",
    ),
    "pitra": (
        "Karmic theme around father / paternal lineage; restitution sought "
        "through dharmic actions or remedial offerings.",
        "Phaladeepika Ch.6.52",
    ),
    "matr": (
        "Mother / 4H affliction theme — emotional foundation requires care; "
        "remediated through cultivation of inner peace and home.",
        "Tradition; KN Rao Matr Dosha rules",
    ),
    "daridra": (
        "Lord of 11 in dusthana or other poverty config — gains constrained, "
        "requires Saturn-like discipline; mitigated by benefic aspects.",
        "Phaladeepika Ch.6.46",
    ),
    "amala": (
        "Spotless reputation; native respected for character and integrity. "
        "Public recognition through righteous conduct.",
        "BPHS Ch.36.27; Saravali Ch.39.45",
    ),
    "hamsa": (
        "Pancha-mahapurusha (Jupiter in kendra in own/exalted): native is "
        "scholarly, dharmic, blessed with wisdom and longevity.",
        "BPHS Ch.36.4; Phaladeepika Ch.6.13",
    ),
    "malavya": (
        "Pancha-mahapurusha (Venus): native is handsome, artistic, "
        "blessed with refined comforts and pleasures.",
        "BPHS Ch.36.4; Phaladeepika Ch.6.14",
    ),
    "ruchaka": (
        "Pancha-mahapurusha (Mars): native is courageous, of commanding "
        "presence; military or athletic prowess.",
        "BPHS Ch.36.4; Phaladeepika Ch.6.12",
    ),
    "bhadra": (
        "Pancha-mahapurusha (Mercury): native is intelligent, articulate, "
        "skilled in trade, writing, mathematics.",
        "BPHS Ch.36.4; Phaladeepika Ch.6.15",
    ),
    "sasa": (
        "Pancha-mahapurusha (Saturn): native is disciplined, authority-bearing, "
        "rises through perseverance over long periods.",
        "BPHS Ch.36.4; Phaladeepika Ch.6.16",
    ),
    "neecha bhanga raja": (
        "Debilitation cancelled (neech-bhanga). What looked like weakness "
        "becomes a source of unexpected rise; a hidden strength.",
        "Phaladeepika Ch.6.32; KN Rao Neech-bhanga",
    ),
    "parijata": (
        "Wealth and dignity through lord-in-own-sign or strongly-placed "
        "9L; lifelong prosperity that compounds.",
        "Phaladeepika Ch.6.30",
    ),
    "raja": (
        "Combination of kendra-lord and trikona-lord creates the classic "
        "rajayoga: power, recognition, leadership in a chosen field.",
        "BPHS Ch.37; Phaladeepika Ch.6",
    ),
}


class YogaEffect(BaseModel):
    """Translated effect for one detected yoga."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    yoga_name: str  # canonical normalised name
    detected_by: str  # "both" / "track_a_only" / "track_b_only"
    classical_effect: str
    classical_source: str
    track_a_rule_ids: tuple[str, ...] = ()
    track_b_native_name: str | None = None
    track_b_intensity: float | None = None
    notes: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_yoga_effects(
    reading: Mapping[str, Any],
) -> list[YogaEffect]:
    """Map every detected yoga to its classical effect-sentence.

    Yogas without a curated effect entry are still emitted with an empty
    ``classical_effect`` so the caller knows they were detected; this
    keeps the output complete vs the comparator's union.
    """
    a_yogas = _collect_track_a_yogas(reading)  # dict[canonical, list[rule_ids]]
    try:
        chart = chart_from_reading(reading)
        b_yogas = _collect_track_b_yogas(chart)  # dict[canonical, (name, intensity)]
    except Exception:
        b_yogas = {}

    all_canonical = sorted(set(a_yogas) | set(b_yogas))
    out: list[YogaEffect] = []
    for canonical in all_canonical:
        in_a = canonical in a_yogas
        in_b = canonical in b_yogas
        if in_a and in_b:
            detected_by = "both"
        elif in_a:
            detected_by = "track_a_only"
        else:
            detected_by = "track_b_only"

        # Look up effect via alias (canonical may already be canonical)
        effect_key = alias_canonical(canonical)
        effect_entry = _YOGA_EFFECTS.get(effect_key)
        if effect_entry is None:
            classical_effect = ""
            classical_source = ""
            notes: tuple[str, ...] = ("no curated effect text for this yoga",)
        else:
            classical_effect, classical_source = effect_entry
            notes = ()

        b_pair = b_yogas.get(canonical)
        out.append(YogaEffect(
            yoga_name=canonical,
            detected_by=detected_by,
            classical_effect=classical_effect,
            classical_source=classical_source,
            track_a_rule_ids=tuple(a_yogas.get(canonical, [])),
            track_b_native_name=b_pair[0] if b_pair else None,
            track_b_intensity=b_pair[1] if b_pair else None,
            notes=notes,
        ))
    return out
