"""M7 — Dasha triple synthesis (KN Rao canonical method).

The single biggest gap from the v1.0.2 review. KN Rao's canonical
synthesis combines:

  1. MD-lord's NATAL placement (house, sign, dignity, yogas, aspects)
     -> what theme does this whole 19-year MD bring?
  2. AD-lord's MUTUAL-AXIS RELATIONSHIP to MD-lord (1-7, 4-10, 5-9,
     2-12, 3-11, 6-8 axis)
     -> how does the current sub-period interact?
  3. CURRENT TRANSIT of Jupiter + Saturn (double-transit doctrine) over
     MD-lord's natal house
     -> are the transit triggers active?

Public surface
--------------
- ``build_dasha_triple(reading)`` -> ``DashaTriple``
- ``DashaTriple`` Pydantic model with structured fields + composed paragraph

Classical basis
---------------
- KN Rao *Ups and Downs through Vimshottari* (canonical synthesis method)
- BPHS Ch.36 (double-transit doctrine)
- Sanjay Rath karaka-bhava synthesis
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.integration.dasha_now import ad_at_now, md_at_now, pd_at_now
from app.integration.md_lord_dossier import build_md_lord_dossier
from app.integration.transit_engine import transit_at_now


# Mutual-axis classification per KN Rao.
_AXIS_MEANING: dict[int, str] = {
    1: "AD-lord = MD-lord (own period within own MD): pure expression of MD theme",
    2: "AD-lord in 2nd from MD-lord: wealth / family / accumulation phase of the MD",
    3: "AD-lord in 3rd from MD-lord: effort / initiative / sibling phase — gains via action",
    4: "AD-lord in 4th from MD-lord: home / comfort / emotional foundation phase",
    5: "AD-lord in 5th from MD-lord: creativity / children / poorvapunya phase — generally fortunate",
    6: "AD-lord in 6th from MD-lord: stress / service / health phase — challenges to confront",
    7: "AD-lord in 7th from MD-lord: partnership / public phase — engagement with others",
    8: "AD-lord in 8th from MD-lord: transformation / occult / inheritance phase — depth work",
    9: "AD-lord in 9th from MD-lord: dharma / teaching / fortune phase — guidance themes",
    10: "AD-lord in 10th from MD-lord: career / status / action phase — visible outcomes",
    11: "AD-lord in 11th from MD-lord: gains / networks / fulfilment phase — supportive period",
    12: "AD-lord in 12th from MD-lord: dissolution / foreign / loss phase — retreat or release",
}

# Generally favourable / stressful axis tags per KN Rao
_AXIS_QUALITY: dict[int, str] = {
    1: "neutral", 2: "supportive", 3: "supportive", 4: "stressful",
    5: "highly_favourable", 6: "stressful", 7: "mixed",
    8: "stressful", 9: "highly_favourable", 10: "supportive",
    11: "supportive", 12: "stressful",
}


class DashaTriple(BaseModel):
    """KN Rao's three-component dasha synthesis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Component 1: MD natal profile
    md_lord: str
    md_natal_house: int = Field(ge=1, le=12)
    md_natal_sign_name: str
    md_window_start: str
    md_window_end: str
    md_summary: str

    # Component 2: AD mutual-axis
    ad_lord: str
    ad_natal_house: int = Field(ge=1, le=12)
    ad_window_start: str
    ad_window_end: str
    md_to_ad_axis: int = Field(ge=1, le=12)
    axis_meaning: str
    axis_quality: str

    # Component 3: transit overlay
    jupiter_transit_house_from_md: int | None = None
    saturn_transit_house_from_md: int | None = None
    double_transit_active: bool = False
    sade_sati_active: bool = False
    saturn_from_moon: int = Field(ge=1, le=12)

    # PD precision
    pd_lord: str
    pd_window_start: str
    pd_window_end: str

    # Synthesis paragraph
    paragraph: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _house_distance(from_house: int, to_house: int) -> int:
    """N-th house from from_house where to_house falls. 1-indexed inclusive."""
    return ((to_house - from_house) % 12) + 1


def _compose_paragraph(
    md_lord: str, md_natal_house: int, md_natal_sign_name: str,
    md_window: tuple[str, str], md_summary: str,
    ad_lord: str, ad_natal_house: int, ad_window: tuple[str, str],
    md_to_ad_axis: int, axis_meaning: str, axis_quality: str,
    jupiter_transit_house: int | None, saturn_transit_house: int | None,
    double_transit: bool, sade_sati: bool, saturn_from_moon: int,
    pd_lord: str, pd_window: tuple[str, str],
) -> str:
    """Compose the synthesis paragraph from structured fields."""
    parts: list[str] = []
    parts.append(
        f"{md_lord.upper()} MD ({md_window[0]} -> {md_window[1]}) — "
        f"{md_summary}."
    )
    parts.append(
        f"Current Antardasha is {ad_lord} ({ad_window[0]} -> {ad_window[1]}). "
        f"{ad_lord} sits natally in {ad_natal_house}H. "
        f"Mutual axis from {md_lord}: {md_to_ad_axis}-position ({axis_quality}). "
        f"{axis_meaning}."
    )
    if jupiter_transit_house is not None or saturn_transit_house is not None:
        transit_bits: list[str] = []
        if jupiter_transit_house is not None:
            transit_bits.append(
                f"Jupiter currently in {jupiter_transit_house}H from {md_lord}'s natal position"
            )
        if saturn_transit_house is not None:
            transit_bits.append(
                f"Saturn in {saturn_transit_house}H from same"
            )
        if transit_bits:
            parts.append(" / ".join(transit_bits) + ".")
        if double_transit:
            parts.append("Double-transit of Jupiter+Saturn active.")
    if sade_sati:
        parts.append(
            f"Sade-Sati active (Saturn in {saturn_from_moon}H from natal Moon)."
        )
    parts.append(
        f"Current Pratyantar: {pd_lord} ({pd_window[0]} -> {pd_window[1]})."
    )
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_dasha_triple(reading: Mapping[str, Any]) -> DashaTriple:
    """Build the KN Rao dasha-triple synthesis for current moment."""
    md = md_at_now(reading)
    ad = ad_at_now(reading)
    pd = pd_at_now(reading)

    md_dossier = build_md_lord_dossier(reading)
    transit = transit_at_now(reading)

    chart = reading.get("chart") or {}
    planets = chart.get("planets") or {}

    # AD-lord's natal house
    ad_lord_body = planets.get(ad.ad_lord) or {}
    ad_natal_house = int(ad_lord_body.get("house", 0))

    # Mutual axis: AD-lord's natal house FROM MD-lord's natal house
    md_to_ad_axis = _house_distance(md_dossier.house, ad_natal_house)
    axis_meaning = _AXIS_MEANING.get(md_to_ad_axis, "")
    axis_quality = _AXIS_QUALITY.get(md_to_ad_axis, "mixed")

    # Transit overlay: Jupiter + Saturn current signs vs MD-lord's natal sign
    jupiter_transit_sign = transit.transit_signs.get("Jupiter")
    saturn_transit_sign = transit.transit_signs.get("Saturn")
    md_lord_natal_sign = md_dossier.sign
    jupiter_house_from_md = None
    saturn_house_from_md = None
    if jupiter_transit_sign:
        jupiter_house_from_md = _house_distance(md_lord_natal_sign, jupiter_transit_sign)
    if saturn_transit_sign:
        saturn_house_from_md = _house_distance(md_lord_natal_sign, saturn_transit_sign)

    # Double-transit: Jupiter AND Saturn both aspect/transit MD-lord's house
    # Per BPHS Ch.36: when both luminaries-of-time (J+S) are positioned to
    # trigger a bhava, the bhava activates.
    favourable_houses = {1, 3, 5, 7, 9, 10, 11}
    double_transit_active = bool(
        jupiter_house_from_md in favourable_houses
        and saturn_house_from_md in favourable_houses
    )

    md_window = (md.start_date, md.end_date)
    ad_window = (ad.start_date, ad.end_date)
    pd_window = (pd.start_date, pd.end_date)

    paragraph = _compose_paragraph(
        md_lord=md.md_lord,
        md_natal_house=md_dossier.house,
        md_natal_sign_name=md_dossier.sign_name,
        md_window=md_window,
        md_summary=md_dossier.summary,
        ad_lord=ad.ad_lord,
        ad_natal_house=ad_natal_house,
        ad_window=ad_window,
        md_to_ad_axis=md_to_ad_axis,
        axis_meaning=axis_meaning,
        axis_quality=axis_quality,
        jupiter_transit_house=jupiter_house_from_md,
        saturn_transit_house=saturn_house_from_md,
        double_transit=double_transit_active,
        sade_sati=transit.sade_sati_active,
        saturn_from_moon=transit.saturn_from_moon,
        pd_lord=pd.pd_lord,
        pd_window=pd_window,
    )

    return DashaTriple(
        md_lord=md.md_lord,
        md_natal_house=md_dossier.house,
        md_natal_sign_name=md_dossier.sign_name,
        md_window_start=md_window[0],
        md_window_end=md_window[1],
        md_summary=md_dossier.summary,
        ad_lord=ad.ad_lord,
        ad_natal_house=ad_natal_house,
        ad_window_start=ad_window[0],
        ad_window_end=ad_window[1],
        md_to_ad_axis=md_to_ad_axis,
        axis_meaning=axis_meaning,
        axis_quality=axis_quality,
        jupiter_transit_house_from_md=jupiter_house_from_md,
        saturn_transit_house_from_md=saturn_house_from_md,
        double_transit_active=double_transit_active,
        sade_sati_active=transit.sade_sati_active,
        saturn_from_moon=transit.saturn_from_moon,
        pd_lord=pd.pd_lord,
        pd_window_start=pd_window[0],
        pd_window_end=pd_window[1],
        paragraph=paragraph,
    )
