"""Enriches a ReadingOutput's domains with modern-life signals (V1.5).

Public API
==========

    enrich_with_modern_signals(reading, chart, asc_sign) -> dict

For each of the 6 domains, the matching detector is invoked and its
Findings are APPENDED to that domain's ``cross_checks`` list. The V1
domain files are not touched; the enrichment lives entirely in this
synthesizer.

Two operating modes
-------------------

1. **Dict mode** (the documented API): ``reading`` is a plain dict
   shaped like ``ReadingOutput.model_dump()``. The function mutates a
   deep copy of the dict and returns it. Use this when the upstream
   pipeline is producing JSON and you want to add modern-life cross
   checks before serialisation.

2. **Object mode**: if ``reading`` is a real :class:`ReadingOutput`
   instance, the function rebuilds it (because :class:`DomainReading`
   is frozen) with augmented ``cross_checks`` and returns the new
   :class:`ReadingOutput`.

The discipline notes from each detector module apply:

- All emitted findings are ``classification="primitive"``.
- Marriage identity-fluidity findings carry the gender-agnostic
  disclaimer (the detector itself attaches it).
- Mental-health findings are CONTEXT, not diagnosis (the detector
  itself enforces verdict wording).
"""
from __future__ import annotations

import copy
from typing import Any

from app.reading.modern_life.career import detect_modern_career
from app.reading.modern_life.children import detect_modern_children
from app.reading.modern_life.education import detect_modern_education
from app.reading.modern_life.health import detect_modern_health
from app.reading.modern_life.marriage import detect_modern_marriage
from app.reading.modern_life.wealth import detect_modern_wealth
from app.reading.schema import DomainReading, Finding, ReadingOutput

# Domain -> detector callable map. Detectors share the same signature
# (chart, asc_sign) -> list[Finding].
_DETECTORS = {
    "career":    detect_modern_career,
    "marriage":  detect_modern_marriage,
    "children":  detect_modern_children,
    "wealth":    detect_modern_wealth,
    "health":    detect_modern_health,
    "education": detect_modern_education,
}


def _enrich_dict(reading: dict, chart: dict, asc_sign: int) -> dict:
    """Dict-mode enrichment: deep-copy + append findings to cross_checks."""
    out = copy.deepcopy(reading)
    domains_block = out.get("domains") or {}
    for name, detector in _DETECTORS.items():
        domain_entry = domains_block.get(name)
        if not isinstance(domain_entry, dict):
            continue
        findings = detector(chart, asc_sign)
        if not findings:
            continue
        existing = domain_entry.get("cross_checks") or []
        domain_entry["cross_checks"] = list(existing) + [
            f.model_dump() if hasattr(f, "model_dump") else f for f in findings
        ]
        domains_block[name] = domain_entry
    out["domains"] = domains_block
    return out


def _enrich_object(
    reading: ReadingOutput, chart: dict, asc_sign: int
) -> ReadingOutput:
    """Object-mode: rebuild ReadingOutput with augmented DomainReadings."""
    domains_block = reading.domains
    rebuilt: dict[str, DomainReading | None] = {}
    for name in _DETECTORS:
        original: DomainReading | None = getattr(domains_block, name)
        if original is None:
            rebuilt[name] = None
            continue
        new_findings = _DETECTORS[name](chart, asc_sign)
        if not new_findings:
            rebuilt[name] = original
            continue
        merged_cross_checks: list[Finding] = list(original.cross_checks) + new_findings
        rebuilt[name] = DomainReading(
            domain=original.domain,
            promise=original.promise,
            triggers=original.triggers,
            timing_windows=original.timing_windows,
            afflictions=original.afflictions,
            cross_checks=merged_cross_checks,
            remedies=original.remedies,
            overall_verdict=original.overall_verdict,
            confidence=original.confidence,
        )

    new_domains = domains_block.__class__(**rebuilt)
    return reading.__class__(
        meta=reading.meta,
        chart=reading.chart,
        primitives=reading.primitives,
        foundations=reading.foundations,
        practitioner=reading.practitioner,
        sequences=reading.sequences,
        domains=new_domains,
        contradictions=reading.contradictions,
        warnings=reading.warnings,
    )


def enrich_with_modern_signals(
    reading: Any, chart: dict, asc_sign: int
) -> Any:
    """Append modern-life Findings to each domain's ``cross_checks``.

    Args:
        reading: a :class:`ReadingOutput` instance, OR a plain dict
            (typically ``ReadingOutput.model_dump()``).
        chart: the full natal chart dict (the same that produced the
            reading) — detectors inspect ``chart["d1"]`` etc.
        asc_sign: 1-indexed natal ascendant rashi.

    Returns:
        Same type as the input ``reading`` (``ReadingOutput`` in, then
        ``ReadingOutput`` out; ``dict`` in, then ``dict`` out). The
        input is not mutated.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")

    if isinstance(reading, ReadingOutput):
        return _enrich_object(reading, chart, asc_sign)
    if isinstance(reading, dict):
        return _enrich_dict(reading, chart, asc_sign)
    raise TypeError(
        f"reading must be ReadingOutput or dict, got {type(reading).__name__}"
    )


__all__ = ["enrich_with_modern_signals"]
