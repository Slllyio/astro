"""Prompt templates + deterministic template fallbacks for chart narration.

Two roles:
  1. Build the prompt sent to the LLM (build_summary_prompt, build_section_prompt).
  2. Render a deterministic narrative directly from chart data when no LLM
     is available (deterministic_summary, deterministic_section). The
     fallbacks are not as fluent as an LLM response but they're truthful,
     reproducible, and never 500.

Sections are defined as a closed allow-list so the route layer can validate
a path parameter against them without trusting client input.
"""
from __future__ import annotations

from typing import Any

# Allow-list of drill-down section names. The route layer enforces this so a
# request like /interpret/chart/<arbitrary-string> can't probe the LLM.
ALLOWED_SECTIONS: frozenset[str] = frozenset({
    "ascendant",
    "mahadasha",
    "yogas",
    "panchanga",
    "planetary",
    "ashtakavarga",
})


# ---------- Chart summarization helpers ----------

def _summarize_chart_facts(chart: dict[str, Any]) -> str:
    """Compact, factual snapshot of the chart that grounds the LLM.

    Returns a multi-line string keyed by section. We deliberately keep
    quantities (degrees, ages) so the model can cite specifics rather than
    hallucinate; we omit deeply nested feature dicts that would blow the
    context window without adding interpretive value.
    """
    lines: list[str] = []

    asc = chart.get("ascendant")
    if asc:
        lines.append(
            f"Ascendant: {asc['sign_name']} {asc['degree_in_sign']:.1f}° "
            f"(longitude {asc['longitude']:.2f}°)"
        )

    md = chart.get("current_mahadasha")
    if md:
        lines.append(
            f"Current Mahadasha: {md['mahadasha_lord']}, "
            f"{md['start_date']} → {md['end_date']} "
            f"({md['time_elapsed_years']:.1f}/{md['total_duration_years']} years elapsed)"
        )

    d1 = chart.get("d1") or {}
    if d1:
        planet_lines = []
        for name, p in d1.items():
            retro = " (R)" if p.get("is_retrograde") else ""
            nak = p.get("nakshatra") or {}
            nak_str = f" — {nak['name']} pada {nak['pada']}" if nak else ""
            house = f" / H{p['house']}" if p.get("house") else ""
            planet_lines.append(
                f"  {name}: {p['sign_name']} {p['degree_in_sign']:.1f}°{house}{nak_str}{retro}"
            )
        lines.append("D1 (Rashi):\n" + "\n".join(planet_lines))

    panch = chart.get("panchanga")
    if panch:
        lines.append(
            f"Panchanga: Tithi {panch['tithi']['name']} ({panch['tithi']['paksha']}), "
            f"Vara {panch['vara']['name']}, Yoga {panch['yoga']['name']}, "
            f"Karana {panch['karana']['name']}"
        )

    yogas = chart.get("yogas") or []
    if yogas:
        names = ", ".join(y["name"] for y in yogas[:8])
        lines.append(f"Yogas ({len(yogas)}): {names}")

    return "\n".join(lines)


# ---------- Prompt builders (sent TO the LLM) ----------

_BASE_SYSTEM = (
    "You are a Vedic astrologer narrator. Speak plainly, in 4-6 sentences, "
    "without disclaimers about astrology being non-scientific. Cite specifics "
    "from the chart facts below — do NOT invent placements. Tone: warm, grounded, "
    "constructive, never deterministic about negative outcomes."
)


def build_summary_prompt(chart: dict[str, Any]) -> str:
    """High-level chart summary prompt — single paragraph."""
    facts = _summarize_chart_facts(chart)
    return (
        f"{_BASE_SYSTEM}\n\n"
        f"Chart facts:\n{facts}\n\n"
        "Write a single short paragraph (4-6 sentences) describing the headline "
        "themes of this chart. Reference the ascendant, the current Mahadasha "
        "lord, and one or two standout placements (a strong yoga, a tight "
        "conjunction, or an angular planet). End with one constructive note "
        "for the current Mahadasha period."
    )


def build_section_prompt(chart: dict[str, Any], section: str) -> str:
    """Drill-down prompt for one section. Caller has already validated
    `section` against ALLOWED_SECTIONS."""
    facts = _summarize_chart_facts(chart)
    section_focus = {
        "ascendant": (
            "Focus only on the ascendant. Describe what the ascendant sign + "
            "degree implies about temperament and physical bearing. Mention "
            "the ascendant's nakshatra if available."
        ),
        "mahadasha": (
            "Focus only on the current Mahadasha. Describe the lord's general "
            "character, where the dasha sits chronologically (early/middle/late), "
            "and what life themes typically activate during this lord's period."
        ),
        "yogas": (
            "Focus only on the yogas in this chart. For each notable yoga, "
            "explain which planets form it and one practical implication. "
            "If there are no yogas, say so plainly."
        ),
        "panchanga": (
            "Focus only on the panchanga elements: tithi, vara, yoga, karana, "
            "and the moon's nakshatra. Explain what each contributes to the "
            "person's natural rhythm."
        ),
        "planetary": (
            "Focus only on the D1 planetary placements. Highlight the 2-3 most "
            "significant placements (angular houses, strong dignities, retrogrades, "
            "tight conjunctions). Skip an exhaustive planet-by-planet recap."
        ),
        "ashtakavarga": (
            "Focus only on the ashtakavarga (BAV/SAV) data if present. Identify "
            "the strongest house by SAV and one or two BAV-strong planets. If "
            "ashtakavarga isn't in the chart, say so plainly."
        ),
    }[section]

    return (
        f"{_BASE_SYSTEM}\n\n"
        f"Chart facts:\n{facts}\n\n"
        f"{section_focus}\n\n"
        "Keep the response to 3-5 sentences."
    )


# ---------- Deterministic fallbacks (no LLM) ----------

def deterministic_summary(chart: dict[str, Any]) -> str:
    """Templated summary used when OLLAMA_ENABLED is False or Ollama is down.

    Strictly factual — no interpretation beyond what the data carries. The
    point is for the endpoint to never 500; users who want narrative depth
    enable Ollama.
    """
    asc = chart.get("ascendant")
    md = chart.get("current_mahadasha")
    yogas = chart.get("yogas") or []

    parts: list[str] = []
    if asc:
        parts.append(
            f"Ascendant: {asc['sign_name']} {asc['degree_in_sign']:.1f}°."
        )
    if md:
        parts.append(
            f"Currently in {md['mahadasha_lord']} Mahadasha "
            f"({md['start_date']} → {md['end_date']}, "
            f"{md['time_elapsed_years']:.1f}/{md['total_duration_years']} years elapsed)."
        )
    if yogas:
        names = ", ".join(y["name"] for y in yogas[:5])
        parts.append(f"Yogas present: {names}.")
    else:
        parts.append("No notable yogas detected by the rule engine.")

    parts.append(
        "(Deterministic narrative — enable OLLAMA_ENABLED=true for an LLM-driven reading.)"
    )
    return " ".join(parts)


def deterministic_section(chart: dict[str, Any], section: str) -> str:
    """Section-specific factual rendering. Mirrors the LLM prompts so a
    caller can compare LLM output against the ground-truth template."""
    if section == "ascendant":
        asc = chart.get("ascendant")
        if not asc:
            return "Ascendant not available for this chart."
        return (
            f"The ascendant is {asc['sign_name']} at {asc['degree_in_sign']:.2f}°, "
            f"longitude {asc['longitude']:.2f}°."
        )
    if section == "mahadasha":
        md = chart.get("current_mahadasha")
        if not md:
            return "Mahadasha data not available for this chart."
        return (
            f"{md['mahadasha_lord']} Mahadasha runs {md['start_date']} → {md['end_date']} "
            f"({md['time_elapsed_years']:.2f} of {md['total_duration_years']} years elapsed)."
        )
    if section == "yogas":
        yogas = chart.get("yogas") or []
        if not yogas:
            return "No notable yogas detected by the rule engine."
        return "Yogas: " + "; ".join(
            f"{y['name']} ({y['type']}, planets: {', '.join(y['planets_involved'])})"
            for y in yogas
        )
    if section == "panchanga":
        p = chart.get("panchanga")
        if not p:
            return "Panchanga not available for this chart."
        return (
            f"Tithi: {p['tithi']['name']} ({p['tithi']['paksha']}). "
            f"Vara: {p['vara']['name']}. "
            f"Yoga: {p['yoga']['name']}. "
            f"Karana: {p['karana']['name']}. "
            f"Nakshatra: {p['nakshatra']['name']}."
        )
    if section == "planetary":
        d1 = chart.get("d1") or {}
        if not d1:
            return "Planetary placements not available."
        lines = []
        for name, pl in d1.items():
            retro = " R" if pl.get("is_retrograde") else ""
            lines.append(
                f"{name}: {pl['sign_name']} {pl['degree_in_sign']:.1f}°{retro}"
            )
        return " · ".join(lines)
    if section == "ashtakavarga":
        av = chart.get("ashtakavarga")
        if not av:
            return "Ashtakavarga not computed for this chart (needs lat/lon)."
        sav = av.get("sav") or []
        if not sav:
            return "Ashtakavarga present but SAV missing."
        max_idx = max(range(len(sav)), key=lambda i: sav[i])
        return (
            f"SAV per house: {sav}. Strongest house: {max_idx + 1} "
            f"with {sav[max_idx]} bindus."
        )
    # Defensive: caller validates against ALLOWED_SECTIONS first.
    return f"Unknown section: {section}"
