"""M8 — Master compose. The depth output the v1.0.2 review demanded.

Single-call entry that calls M1-M7 and weaves them into a single
master-astrologer-level reading:

    compose_master_reading(reading) -> MasterReading

The output replaces the data-dump style of summary.py with synthesis
paragraphs structured by domain. Each domain paragraph cross-references:
- The bhava's three-pillar reading (M4)
- Yogas whose effects touch the domain (M5)
- Arudha + Upapada when relevant (M6 — applies to marriage especially)
- Current dasha triple (M7) — colours every domain by the active period
- MD-lord dossier (M3) — when MD lord rules this domain's house

The 6 domains map to bhavas: career=10, marriage=7, children=5,
wealth=2, health=6, education=4.
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.integration.arudha_synthesis import ArudhaSynthesis, synthesise_arudha
from app.integration.dasha_triple import DashaTriple, build_dasha_triple
from app.integration.md_lord_dossier import MDLordDossier, build_md_lord_dossier
from app.integration.three_pillar import (
    ThreePillarBhava,
    ThreePillarReading,
    build_three_pillar_reading,
)
from app.integration.yoga_effects import YogaEffect, translate_yoga_effects


# Domain -> primary bhava
_DOMAIN_BHAVA: dict[str, int] = {
    "career": 10, "marriage": 7, "children": 5,
    "wealth": 2, "health": 6, "education": 4,
}


class DomainParagraph(BaseModel):
    """One domain's master-compose paragraph + structured backing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    bhava: int = Field(ge=1, le=12)
    paragraph: str
    three_pillar_label: str
    three_pillar_score: float
    yogas_touching_domain: tuple[str, ...]
    md_relevance: str  # "directly_rules" / "transit_active" / "ad_active" / "none"


class MasterReading(BaseModel):
    """Top-level master-astrologer reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "1.1.0"
    chart_basics: dict[str, Any]
    dasha_triple_paragraph: str
    arudha_image_summary: str
    upapada_marriage_summary: str
    domain_paragraphs: list[DomainParagraph]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Yogas that classically touch each domain
_DOMAIN_YOGAS: dict[str, frozenset[str]] = {
    "career": frozenset({
        "adhi", "raja", "gajakesari", "amala", "budha-aditya",
        "hamsa", "ruchaka", "bhadra", "sasa", "malavya",
    }),
    "marriage": frozenset({"mangal", "lakshmi", "sarpa"}),
    "children": frozenset({"adhi", "gajakesari"}),
    "wealth": frozenset({
        "lakshmi", "vipareeta raja", "amala", "daridra",
        "parijata", "sunapha", "anapha", "chandra-mangal",
    }),
    "health": frozenset({"kemadruma", "matr"}),
    "education": frozenset({"saraswati", "budha-aditya", "gajakesari"}),
}


def _md_relevance_for_domain(
    md_dossier: MDLordDossier, dasha_triple: DashaTriple,
    domain: str, bhava: int,
) -> str:
    """Classify how the current MD relates to this domain."""
    if bhava in md_dossier.houses_ruled_from_lagna:
        return "directly_rules"
    if md_dossier.house == bhava:
        return "placed_in_domain"
    # If transit Jupiter+Saturn are favourable to MD-lord's natal house
    # and that house is the domain bhava, MD is active for this domain
    if dasha_triple.double_transit_active and md_dossier.house == bhava:
        return "double_transit_active"
    return "indirect"


def _compose_domain_paragraph(
    domain: str, bhava: int,
    pillar: ThreePillarBhava,
    yoga_effects_touching: list[YogaEffect],
    md_dossier: MDLordDossier,
    dasha_triple: DashaTriple,
    arudha: ArudhaSynthesis,
) -> str:
    """Weave the layers into one paragraph per domain."""
    sentences: list[str] = []

    # Pillar 1: the bhava itself
    label = pillar.composite_label.replace("_", " ")
    pillar_intro = (
        f"{domain.upper()} (H{bhava} {pillar.bhava_sign_name}, "
        f"{label} composite): {pillar.synthesis_lines[0]}."
    )
    sentences.append(pillar_intro)

    # Pillar 2 + 3: lord + karaka
    sentences.append(f"{pillar.synthesis_lines[1]}. {pillar.synthesis_lines[2]}.")

    # Yogas
    if yoga_effects_touching:
        yoga_bits: list[str] = []
        for ye in yoga_effects_touching:
            if ye.classical_effect:
                yoga_bits.append(
                    f"{ye.yoga_name.upper()} yoga active "
                    f"({ye.classical_source}): {ye.classical_effect}"
                )
        if yoga_bits:
            sentences.append(" ".join(yoga_bits))

    # MD relevance
    md_rel = _md_relevance_for_domain(md_dossier, dasha_triple, domain, bhava)
    if md_rel == "directly_rules":
        sentences.append(
            f"Current MD lord {md_dossier.planet} rules this house "
            f"(natally in {md_dossier.house}H {md_dossier.sign_name}), "
            f"so the MD period {dasha_triple.md_window_start}->{dasha_triple.md_window_end} "
            f"is directly active for {domain}."
        )
    elif md_rel == "placed_in_domain":
        sentences.append(
            f"Current MD lord {md_dossier.planet} sits natally IN this "
            f"house — the MD activates {domain} themes directly."
        )

    # Arudha relevance (only for marriage)
    if domain == "marriage":
        sentences.append(
            f"Upapada signifier: {arudha.upapada_lord} in "
            f"{arudha.upapada_lord_house}H. {arudha.marriage_summary}"
        )

    # Always note Sade-Sati if active and relevant
    if dasha_triple.sade_sati_active and bhava in (2, 4, 12, 1):
        sentences.append(
            f"Note: Sade-Sati currently active "
            f"(Saturn in {dasha_triple.saturn_from_moon}H from Moon) "
            f"can pressure this domain."
        )

    return " ".join(sentences)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compose_master_reading(
    reading: Mapping[str, Any],
) -> MasterReading:
    """Compose the master-astrologer-level reading.

    Single call that invokes M1-M7 internally and weaves them into a
    coherent narrative. Returns a structured MasterReading with one
    paragraph per of the 6 domains plus chart basics, the current dasha
    triple, and Arudha/Upapada synthesis at the top level.
    """
    chart = reading.get("chart") or {}
    cusps = chart.get("cusps") or {}
    moon = (chart.get("planets") or {}).get("Moon") or {}
    sun = (chart.get("planets") or {}).get("Sun") or {}

    chart_basics = {
        "lagna_sign": int(cusps.get("sign", 1)),
        "lagna_sign_name": (
            "Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio "
            "Sagittarius Capricorn Aquarius Pisces"
        ).split()[int(cusps.get("sign", 1)) - 1],
        "moon_sign_name": str(moon.get("sign_name", "?")),
        "moon_nakshatra": str((moon.get("nakshatra") or {}).get("name", "?")),
        "sun_sign_name": str(sun.get("sign_name", "?")),
    }

    # Compose layers
    pillars: ThreePillarReading = build_three_pillar_reading(reading)
    yoga_effects: list[YogaEffect] = translate_yoga_effects(reading)
    md_dossier: MDLordDossier = build_md_lord_dossier(reading)
    dasha_triple: DashaTriple = build_dasha_triple(reading)
    arudha: ArudhaSynthesis = synthesise_arudha(reading)

    # Build per-domain paragraphs
    domain_paragraphs: list[DomainParagraph] = []
    for domain, bhava in _DOMAIN_BHAVA.items():
        pillar = pillars.per_bhava[bhava]
        relevant_yoga_names = _DOMAIN_YOGAS.get(domain, frozenset())
        yoga_effects_touching = [
            ye for ye in yoga_effects
            if ye.yoga_name in relevant_yoga_names and ye.classical_effect
        ]
        paragraph = _compose_domain_paragraph(
            domain, bhava, pillar, yoga_effects_touching,
            md_dossier, dasha_triple, arudha,
        )
        md_rel = _md_relevance_for_domain(md_dossier, dasha_triple, domain, bhava)

        domain_paragraphs.append(DomainParagraph(
            domain=domain,
            bhava=bhava,
            paragraph=paragraph,
            three_pillar_label=pillar.composite_label,
            three_pillar_score=pillar.composite_score,
            yogas_touching_domain=tuple(ye.yoga_name for ye in yoga_effects_touching),
            md_relevance=md_rel,
        ))

    return MasterReading(
        chart_basics=chart_basics,
        dasha_triple_paragraph=dasha_triple.paragraph,
        arudha_image_summary=arudha.image_summary,
        upapada_marriage_summary=arudha.marriage_summary,
        domain_paragraphs=domain_paragraphs,
    )
