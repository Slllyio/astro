"""Finding-ID selector: pick the most relevant findings per intent.

Given a classified question intent + a ReadingOutput dict, return the IDs
(and the underlying finding dicts) most relevant to the question. The
finding selector does not invent or alter findings; it routes the LLM to
the relevant slice of the chart's own JSON.

Routing rules:

- TIMING  -> MD timeline (current + immediately adjacent) + AD findings
            in the current MD + any domain timing_windows
- DOMAIN  -> the corresponding DomainReading block (promise, triggers,
            timing_windows, afflictions, cross_checks, overall_verdict)
- PLANET  -> primitives + foundations + practitioner findings whose
            ``id``, ``rule``, ``verdict``, or ``evidence`` mentions the
            planet name
- DASHA   -> sequences.md_judgments + sequences.ad_judgments overall
            verdicts; AD checks if the user named both MD and AD
- YOGA    -> practitioner findings with classification == "yoga"
- GENERIC -> a curated mix: current MD overall verdict, top yogas,
            overall domain verdicts

A hard cap of 10 findings keeps the LLM prompt bounded. Selection
prefers higher confidence (``very_strong`` > ``high`` > ``medium``) when
tie-breaking by recency or order is needed.
"""
from __future__ import annotations

from typing import Any, Final

from app.reading.query.intent_classifier import IntentClassification

# Hard cap on the number of findings forwarded to the LLM.
MAX_FINDINGS: Final[int] = 10

# Band ordering for confidence-based prioritisation. Higher number = stronger.
_BAND_RANK: Final[dict[str, int]] = {
    "very_strong": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "indicative_only": 1,
}


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _confidence_rank(finding: dict[str, Any]) -> int:
    """Numeric rank of a finding's confidence band. Unknown bands score 0."""
    band = (finding.get("confidence") or {}).get("band", "")
    return _BAND_RANK.get(band, 0)


def _id(finding: dict[str, Any] | None) -> str | None:
    """Safe ``id`` getter, tolerating missing or non-dict findings."""
    if not isinstance(finding, dict):
        return None
    fid = finding.get("id")
    return str(fid) if fid else None


def _mention_blob(finding: dict[str, Any]) -> str:
    """Lowercase concatenation of the fields we scan for entity mentions."""
    parts = [
        str(finding.get("id", "")),
        str(finding.get("rule", "")),
        str(finding.get("verdict", "")),
    ]
    evidence = finding.get("evidence") or []
    if isinstance(evidence, list):
        parts.extend(str(e) for e in evidence)
    return " ".join(parts).lower()


def _mentions_any(finding: dict[str, Any], tokens: list[str]) -> bool:
    """True iff any token appears in the finding's mention blob."""
    if not tokens:
        return False
    blob = _mention_blob(finding)
    return any(tok.lower() in blob for tok in tokens)


def _all_block_findings(reading: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten every Finding-shaped dict the reading carries.

    Used by PLANET and GENERIC selection. Skips judgment ``checks`` to
    avoid drowning the LLM in 19 MD-check rows per dasha; the AD/MD
    ``overall_verdict`` already summarises those.
    """
    out: list[dict[str, Any]] = []
    for block_name in ("primitives", "foundations", "practitioner"):
        block = reading.get(block_name) or {}
        findings = block.get("findings") or []
        if isinstance(findings, list):
            out.extend(f for f in findings if isinstance(f, dict))
    return out


def _top_by_confidence(
    findings: list[dict[str, Any]], limit: int,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` findings sorted by confidence band, desc.

    Ties preserve insertion order (Python's sort is stable).
    """
    return sorted(findings, key=_confidence_rank, reverse=True)[:limit]


# --------------------------------------------------------------------------- #
# Per-intent selectors                                                         #
# --------------------------------------------------------------------------- #


def _select_for_timing(reading: dict[str, Any]) -> list[dict[str, Any]]:
    """Pick MD/AD overall verdicts + domain timing windows."""
    out: list[dict[str, Any]] = []
    sequences = reading.get("sequences") or {}

    md_judgments = sequences.get("md_judgments") or []
    if isinstance(md_judgments, list):
        # Current MD verdict first, then the immediate past + future MDs.
        for md in md_judgments:
            if not isinstance(md, dict):
                continue
            if md.get("is_current"):
                verdict = md.get("overall_verdict")
                if isinstance(verdict, dict):
                    out.append(verdict)
                break
        # Add adjacent (past/future neighbour) MD verdicts.
        for md in md_judgments:
            if not isinstance(md, dict) or md.get("is_current"):
                continue
            verdict = md.get("overall_verdict")
            if isinstance(verdict, dict):
                out.append(verdict)
                if len(out) >= 3:
                    break

    ad_judgments = sequences.get("ad_judgments") or []
    if isinstance(ad_judgments, list):
        for ad in ad_judgments:
            if not isinstance(ad, dict):
                continue
            if ad.get("is_current"):
                verdict = ad.get("overall_verdict")
                if isinstance(verdict, dict):
                    out.append(verdict)
                break

    return out[:MAX_FINDINGS]


def _select_for_domain(
    reading: dict[str, Any], entities: list[str],
) -> list[dict[str, Any]]:
    """Pick findings from the matching DomainReading block."""
    out: list[dict[str, Any]] = []
    domains = reading.get("domains") or {}
    if not isinstance(domains, dict):
        return out

    # The first entity that names a real domain wins.
    chosen: str | None = None
    for entity in entities:
        if entity in domains:
            chosen = entity
            break
    if chosen is None:
        return out

    domain_reading = domains.get(chosen)
    if not isinstance(domain_reading, dict):
        return out

    promise = domain_reading.get("promise")
    if isinstance(promise, dict):
        out.append(promise)
    overall = domain_reading.get("overall_verdict")
    if isinstance(overall, dict):
        out.append(overall)

    triggers = domain_reading.get("triggers") or []
    if isinstance(triggers, list):
        out.extend(_top_by_confidence([t for t in triggers if isinstance(t, dict)], 3))

    afflictions = domain_reading.get("afflictions") or []
    if isinstance(afflictions, list):
        out.extend(
            _top_by_confidence([a for a in afflictions if isinstance(a, dict)], 2),
        )

    cross_checks = domain_reading.get("cross_checks") or []
    if isinstance(cross_checks, list):
        out.extend(
            _top_by_confidence(
                [c for c in cross_checks if isinstance(c, dict)], 2,
            ),
        )

    return out[:MAX_FINDINGS]


def _select_for_planet(
    reading: dict[str, Any], entities: list[str],
) -> list[dict[str, Any]]:
    """Pick findings whose mention blob references any planet entity."""
    if not entities:
        return []
    all_findings = _all_block_findings(reading)
    matching = [f for f in all_findings if _mentions_any(f, entities)]
    return _top_by_confidence(matching, MAX_FINDINGS)


def _select_for_dasha(reading: dict[str, Any]) -> list[dict[str, Any]]:
    """Pick MD + AD overall verdicts; falls back to all MD verdicts."""
    out: list[dict[str, Any]] = []
    sequences = reading.get("sequences") or {}

    md_judgments = sequences.get("md_judgments") or []
    if isinstance(md_judgments, list):
        # Prioritise current; then walk through up to 5 more.
        sorted_mds = sorted(
            (md for md in md_judgments if isinstance(md, dict)),
            key=lambda m: 0 if m.get("is_current") else 1,
        )
        for md in sorted_mds:
            verdict = md.get("overall_verdict")
            if isinstance(verdict, dict):
                out.append(verdict)
            if len(out) >= 6:
                break

    ad_judgments = sequences.get("ad_judgments") or []
    if isinstance(ad_judgments, list):
        for ad in ad_judgments:
            if not isinstance(ad, dict) or not ad.get("is_current"):
                continue
            verdict = ad.get("overall_verdict")
            if isinstance(verdict, dict):
                out.append(verdict)
                break

    return out[:MAX_FINDINGS]


def _select_for_yoga(reading: dict[str, Any]) -> list[dict[str, Any]]:
    """Pick practitioner-layer findings classified as 'yoga'."""
    practitioner = reading.get("practitioner") or {}
    findings = practitioner.get("findings") or []
    if not isinstance(findings, list):
        return []
    yoga_findings = [
        f for f in findings
        if isinstance(f, dict) and f.get("classification") == "yoga"
    ]
    return _top_by_confidence(yoga_findings, MAX_FINDINGS)


def _select_for_generic(reading: dict[str, Any]) -> list[dict[str, Any]]:
    """Curated mix: current MD verdict, top yogas, domain overall verdicts."""
    out: list[dict[str, Any]] = []

    sequences = reading.get("sequences") or {}
    md_judgments = sequences.get("md_judgments") or []
    if isinstance(md_judgments, list):
        for md in md_judgments:
            if isinstance(md, dict) and md.get("is_current"):
                verdict = md.get("overall_verdict")
                if isinstance(verdict, dict):
                    out.append(verdict)
                break

    # Top 3 yogas
    out.extend(_select_for_yoga(reading)[:3])

    # Domain overall verdicts (up to 6)
    domains = reading.get("domains") or {}
    if isinstance(domains, dict):
        for _name, domain_reading in domains.items():
            if not isinstance(domain_reading, dict):
                continue
            verdict = domain_reading.get("overall_verdict")
            if isinstance(verdict, dict):
                out.append(verdict)
            if len(out) >= MAX_FINDINGS:
                break

    return out[:MAX_FINDINGS]


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def select_findings(
    reading: dict[str, Any], classification: IntentClassification,
) -> list[dict[str, Any]]:
    """Select the most relevant findings for a classified question.

    Args:
        reading: A ReadingOutput-shaped dict.
        classification: Output of ``classify_intent``.

    Returns:
        List of finding dicts (length capped at MAX_FINDINGS). Each entry
        is a dict matching the Finding schema. The list may be empty if
        the reading has no findings matching the intent.
    """
    if not isinstance(reading, dict):
        return []

    intent = classification.intent
    entities = classification.extracted_entities

    if intent == "TIMING":
        return _select_for_timing(reading)
    if intent == "DOMAIN":
        return _select_for_domain(reading, entities)
    if intent == "PLANET":
        return _select_for_planet(reading, entities)
    if intent == "DASHA":
        return _select_for_dasha(reading)
    if intent == "YOGA":
        return _select_for_yoga(reading)
    return _select_for_generic(reading)


def select_finding_ids(
    reading: dict[str, Any], classification: IntentClassification,
) -> list[str]:
    """Convenience: return only the IDs of the selected findings."""
    out: list[str] = []
    for f in select_findings(reading, classification):
        fid = _id(f)
        if fid:
            out.append(fid)
    return out
