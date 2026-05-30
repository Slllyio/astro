"""Deterministic skeleton builders — one per narrated section.

Each builder takes a slice of the ReadingOutput dict (already shape-validated
upstream) and returns a short factual prose skeleton using the project's
locked safe-language:

  USE     : "indicates", "suggests", "favors", "may bring", "tends to",
            "points toward", "supports", "highlights"
  AVOID   : "will", "guaranteed", "definitely", "certainly", "always",
            "never" (in predictive context)

The skeleton is returned as-is when no LLM is available and is fed as a
"starting point" to the LLM when one is. The LLM prompt explicitly forbids
the avoid-list (see `prompts.py`).

Each builder is defensive against missing/None keys: a reading produced with
`enrich=False` or with a sequence that didn't fire will still narrate
gracefully ("Mahadasha data not available", etc.).
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Vocabulary helpers
# ---------------------------------------------------------------------------

# Direction-keyed lead-ins. Used uniformly so callers don't have to invent
# phrasing per-section; keeps language consistent across the 9 builders.
_DIRECTION_LEAD = {
    "positive": "suggests",
    "negative": "indicates a challenge with",
    "neutral": "points to",
    "mixed": "shows mixed signals around",
}

# Confidence-band lead-in modifiers. These are inserted before the verdict
# noun so the reader gets a quick "how strong is this finding?" cue.
_BAND_MODIFIER = {
    "very_strong": "a very strong",
    "high": "a clear",
    "medium": "a moderate",
    "low": "a tentative",
    "indicative_only": "an indicative",
}


def _safe_get(d: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    """Walk a chain of optional nested keys; return default if any link is None."""
    cur: Any = d
    for k in keys:
        if cur is None or not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _finding_phrase(finding: dict[str, Any] | None) -> str:
    """Render one Finding as a short, safe-language phrase.

    Produces e.g. "suggests a moderate Career promise: indicative (confidence
    medium)" — never an absolute prediction.
    """
    if not finding:
        return "no finding available"
    direction = finding.get("direction", "neutral")
    lead = _DIRECTION_LEAD.get(direction, "points to")
    band = _safe_get(finding, "confidence", "band", default="indicative_only")
    modifier = _BAND_MODIFIER.get(band, "an indicative")
    verdict = finding.get("verdict") or finding.get("rule") or "an unnamed finding"
    return f"{lead} {modifier} reading: {verdict}"


def _citations_inline(finding: dict[str, Any] | None, max_cites: int = 2) -> str:
    """Compose an inline citation suffix like ' (sources: BPHS Ch.27, Phaladeepika)'.

    Returns empty string when no Tier-3 citations are present.
    """
    cites = _safe_get(finding, "citations", default=[]) or []
    if not cites:
        return ""
    names = [c.get("source") for c in cites[:max_cites] if c.get("source")]
    if not names:
        return ""
    return f" (sources: {', '.join(names)})"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def build_chart_overview(
    chart_block: dict[str, Any] | None,
    primitives: dict[str, Any] | None,
) -> str:
    """Render a one-paragraph natal chart overview (ascendant + key extras)."""
    chart_block = chart_block or {}
    primitives = primitives or {}
    cusps = chart_block.get("cusps") or {}
    asc_sign = cusps.get("sign_name") or cusps.get("sign")
    asc_deg = cusps.get("degree_in_sign")
    extras = chart_block.get("extras") or {}
    is_daytime = extras.get("is_daytime")
    panch = extras.get("panchanga") or {}

    parts: list[str] = []
    if asc_sign is not None:
        if asc_deg is not None:
            parts.append(
                f"The chart indicates a {asc_sign} ascendant at "
                f"{float(asc_deg):.1f} degrees."
            )
        else:
            parts.append(f"The chart indicates a {asc_sign} ascendant.")
    else:
        parts.append("The ascendant could not be determined from the chart data.")

    if is_daytime is True:
        parts.append("Born during the day, the solar signature tends to lead.")
    elif is_daytime is False:
        parts.append("Born at night, the lunar signature tends to lead.")

    if panch:
        tithi = _safe_get(panch, "tithi", "name")
        nak = _safe_get(panch, "nakshatra", "name")
        if tithi or nak:
            bits = []
            if tithi:
                bits.append(f"Tithi {tithi}")
            if nak:
                bits.append(f"Moon in {nak}")
            parts.append("Panchanga context: " + ", ".join(bits) + ".")

    prim_findings = primitives.get("findings") or []
    if prim_findings:
        parts.append(
            f"The primitive layer surfaces {len(prim_findings)} foundational "
            f"observations that anchor later judgments."
        )

    return " ".join(parts)


def build_current_mahadasha(seq_block: dict[str, Any] | None) -> str:
    """Render the currently-active mahadasha as a short prose paragraph."""
    seq_block = seq_block or {}
    mds = seq_block.get("md_judgments") or []
    current = next((m for m in mds if m.get("is_current")), None)
    if not current:
        return (
            "No active mahadasha judgment is available for this chart at the "
            "present time."
        )

    lord = current.get("md_lord", "an unknown")
    start = current.get("start_date", "?")
    end = current.get("end_date", "?")
    overall = current.get("overall_verdict") or {}
    phrase = _finding_phrase(overall)
    cites = _citations_inline(overall)

    return (
        f"The current mahadasha is ruled by {lord}, running from {start} to "
        f"{end}. Overall, the 19-check judgment {phrase}{cites}. "
        f"This period favors themes connected with {lord}'s natural "
        f"significations and the house it occupies natally."
    )


def build_current_antardasha(seq_block: dict[str, Any] | None) -> str:
    """Render the currently-active antardasha as a short prose paragraph."""
    seq_block = seq_block or {}
    ads = seq_block.get("ad_judgments") or []
    current = next((a for a in ads if a.get("is_current")), None)
    if not current:
        return (
            "No active antardasha judgment is available for this chart at the "
            "present time."
        )

    ad_lord = current.get("ad_lord", "an unknown")
    md_lord = current.get("md_lord", "the active mahadasha lord")
    start = current.get("start_date", "?")
    end = current.get("end_date", "?")
    overall = current.get("overall_verdict") or {}
    phrase = _finding_phrase(overall)
    cites = _citations_inline(overall)

    return (
        f"Within the {md_lord} mahadasha, the running antardasha is led by "
        f"{ad_lord} from {start} to {end}. The 7-check sub-period judgment "
        f"{phrase}{cites}. The mutual position of {md_lord} and {ad_lord} "
        f"in the natal chart tends to color how these months unfold."
    )


def build_domain_section(
    domain_name: str,
    domain_reading: dict[str, Any] | None,
) -> str:
    """Render one of the 6 domain syntheses.

    Used uniformly for career / marriage / health / wealth / children / education.
    """
    if not domain_reading:
        return (
            f"No domain reading is available for {domain_name}. This may "
            f"happen when upstream inputs are partial or the doctrine has "
            f"nothing to flag."
        )

    promise = domain_reading.get("promise") or {}
    overall = domain_reading.get("overall_verdict") or {}
    triggers = domain_reading.get("triggers") or []
    timing = domain_reading.get("timing_windows") or []
    afflictions = domain_reading.get("afflictions") or []
    remedies = domain_reading.get("remedies") or []
    confidence = domain_reading.get("confidence") or {}

    parts: list[str] = [f"Domain: {domain_name}."]

    promise_phrase = _finding_phrase(promise)
    promise_cites = _citations_inline(promise)
    parts.append(f"The natal promise {promise_phrase}{promise_cites}.")

    if triggers:
        parts.append(
            f"There are {len(triggers)} trigger condition(s) recorded that "
            f"may activate this domain across the dasha sequence."
        )
    else:
        parts.append("No active triggers are recorded for this domain at present.")

    if timing:
        parts.append(
            f"{len(timing)} dated window(s) are flagged as potentially "
            f"significant for {domain_name}-related themes."
        )

    if afflictions:
        parts.append(
            f"{len(afflictions)} affliction(s) suggest counter-currents to "
            f"be aware of; these are limiters, not verdicts."
        )

    band = confidence.get("band", "indicative_only")
    overall_phrase = _finding_phrase(overall)
    parts.append(
        f"Overall, the {domain_name} reading is held at the "
        f"{band.replace('_', ' ')} band, and {overall_phrase}."
    )

    if remedies:
        kinds = sorted({r.get("kind", "other") for r in remedies})
        parts.append(
            f"Doctrine-cited supports include: {', '.join(kinds)}. These are "
            f"traditional adjuncts and may complement other practices the "
            f"reader already follows."
        )

    return " ".join(parts)


def build_yogas_section(practitioner_findings: list[dict[str, Any]] | None) -> str:
    """Render the yoga findings surfaced by the practitioner layer."""
    findings = practitioner_findings or []
    yogas = [f for f in findings if f.get("classification") == "yoga"]
    if not yogas:
        return (
            "No notable yogas are flagged by the practitioner layer for this "
            "chart. The reading rests on the primitive and foundation layers."
        )

    # Highlight the strongest few by confidence band.
    band_order = {
        "very_strong": 5, "high": 4, "medium": 3, "low": 2, "indicative_only": 1,
    }
    yogas_sorted = sorted(
        yogas,
        key=lambda f: band_order.get(
            _safe_get(f, "confidence", "band", default="indicative_only"), 0
        ),
        reverse=True,
    )
    top = yogas_sorted[:5]

    parts: list[str] = [
        f"The practitioner layer surfaces {len(yogas)} yoga(s) in this chart."
    ]
    for y in top:
        verdict = y.get("verdict") or y.get("rule") or "an unnamed yoga"
        direction = y.get("direction", "neutral")
        lead = _DIRECTION_LEAD.get(direction, "points to")
        cites = _citations_inline(y)
        parts.append(f"One {lead} {verdict}{cites}.")

    if len(yogas) > 5:
        parts.append(
            f"A further {len(yogas) - 5} yoga(s) are recorded in the full "
            f"findings list and may be reviewed in detail."
        )

    return " ".join(parts)


def build_contradictions_section(
    contradictions: list[dict[str, Any]] | None,
) -> str:
    """Render the cross-finding contradictions detected by Tier-3."""
    contras = contradictions or []
    if not contras:
        return (
            "No contradictions were detected across the findings layers. "
            "The doctrine signals broadly cohere for this chart."
        )

    soft = [c for c in contras if c.get("severity") == "soft"]
    hard = [c for c in contras if c.get("severity") == "hard"]

    parts: list[str] = [
        f"The contradiction detector flagged {len(contras)} cross-finding "
        f"disagreement(s) in this reading."
    ]
    if hard:
        parts.append(
            f"{len(hard)} of these are hard contradictions: at least one of "
            f"the findings involved may need to yield to the other."
        )
    if soft:
        parts.append(
            f"{len(soft)} are soft contradictions: the directions disagree "
            f"but both findings may stand and contribute nuance."
        )

    # Mention up to 2 domains involved for grounding.
    domains = sorted({c.get("domain", "general") for c in contras if c.get("domain")})
    if domains:
        parts.append(
            f"Domains touched by these tensions include: "
            f"{', '.join(domains[:4])}."
        )

    parts.append(
        "Surfaced for transparency per project doctrine; arbitration is "
        "descriptive only and never picks a winner."
    )
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Section dispatch table — used by synthesize.py
# ---------------------------------------------------------------------------

# Closed allow-list of section names callers may request. Mirrors the spirit
# of `app.llm.templates.ALLOWED_SECTIONS` but adapted for ReadingOutput.
NARRATIVE_SECTIONS: tuple[str, ...] = (
    "chart_overview",
    "current_mahadasha",
    "current_antardasha",
    "career",
    "marriage",
    "health",
    "wealth",
    "children",
    "education",
    "yogas",
    "contradictions",
)

# Sections that are members of the "6 domains" group — handy for full-mode
# rendering, and for the test that asserts all 6 are present.
DOMAIN_SECTIONS: tuple[str, ...] = (
    "career", "marriage", "health", "wealth", "children", "education",
)
