"""DKP-translation enhancer for Track-A reading output.

Takes a Track-A ``ReadingOutput`` (Pydantic model or dict from ``compute()``)
and decorates it with Track-B's Doctrine Translation Engine lookups:

- **Per-finding sidecar** — every Finding object gains a parallel
  ``dkp_translations`` list with TranslationRecords whose keys match the
  finding's rule ID, classification, or evidence content.
- **Top-level summary** — a deduplicated ``dkp_translations_summary``
  block at the envelope level, with ``cross_references`` mapping each
  record's ``key`` back to the finding IDs that cite it.

Methodology
-----------
This is pure post-hoc annotation. Neither Track A nor Track B is invoked
during enhancement — we work over the materialized Track-A output and
the static Track-B translation registry. Determinism is preserved: the
same ``ReadingOutput`` always produces the same ``IntegratedReadingOutput``.

Three lookup strategies are tried per finding, in order:

1. **Direct key match** — ``rule`` IDs like ``yogas_extended.lakshmi`` or
   ``karaka.career.10H`` are passed to ``translate_by_key()`` as substring
   matches against the registry's ``key`` field.
2. **Yoga lookup** — when ``classification == "yoga"``, the rule's last
   namespace segment is passed to ``translate_yoga()``.
3. **Bhava+planet pair** — if the finding's ``evidence`` strings or ``rule``
   mention a bhava number (1-12) and a planet name, ``translate_bhava_planet()``
   is called with each pair.

Matched records from all three strategies are deduplicated by ``key`` and
attached to the finding's ``dkp_translations`` sidecar. The top-level
summary then deduplicates again across all findings.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.dkp_translation import (
    TranslationRecord,
    all_translations,
    translate_bhava_planet,
    translate_by_key,
    translate_yoga,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Planets recognised by Track B's translation engine. Used to scan rule/evidence
# strings for bhava+planet pair extraction.
_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)

# Regex matching "Nth bhava" / "Nth house" / "N H" anywhere in a string.
# Bounded to 1..12 to avoid spurious matches.
_BHAVA_PATTERN = re.compile(
    r"\b(1[0-2]|[1-9])(?:st|nd|rd|th)?\s*(?:H|bhava|house)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class TranslationRecordView(BaseModel):
    """JSON-friendly view of ``app.core.dkp_translation.TranslationRecord``.

    We project the dataclass into a Pydantic model so the integrated envelope
    stays a single Pydantic tree (uniform ``.model_dump()`` behaviour, single
    JSON schema). All TranslationRecord fields are preserved verbatim.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    classification: str
    domain: str
    shloka: str
    classical_references: tuple[str, ...]
    ancient_manifestation: str
    desh_shift: str
    kaal_shift: str
    paristhiti_shift: str
    modern_manifestation: str
    invariant_mechanism: str
    modern_references: tuple[str, ...]
    lagna_specific_notes: dict[int, str] = Field(default_factory=dict)
    sanskrit_shloka: str = ""
    transliteration: str = ""
    word_gloss: str = ""
    corpus_passage_ids: tuple[str, ...] = ()

    @classmethod
    def from_record(cls, rec: TranslationRecord) -> TranslationRecordView:
        return cls(
            key=rec.key,
            classification=rec.classification,
            domain=rec.domain,
            shloka=rec.shloka,
            classical_references=tuple(rec.classical_references),
            ancient_manifestation=rec.ancient_manifestation,
            desh_shift=rec.desh_shift,
            kaal_shift=rec.kaal_shift,
            paristhiti_shift=rec.paristhiti_shift,
            modern_manifestation=rec.modern_manifestation,
            invariant_mechanism=rec.invariant_mechanism,
            modern_references=tuple(rec.modern_references),
            lagna_specific_notes=dict(rec.lagna_specific_notes),
            sanskrit_shloka=rec.sanskrit_shloka,
            transliteration=rec.transliteration,
            word_gloss=rec.word_gloss,
            corpus_passage_ids=tuple(rec.corpus_passage_ids),
        )


class DkpTranslationsSummary(BaseModel):
    """Top-level summary of every TranslationRecord cited across the reading.

    ``records`` is keyed by the TranslationRecord ``key`` field so consumers
    can dereference by key. ``cross_references`` maps each key to the list of
    Track-A Finding IDs that surfaced it. ``total_records_attached`` counts
    sidecar attachments (with multiplicity — same record cited by two findings
    counts as two)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    records: dict[str, TranslationRecordView]
    cross_references: dict[str, list[str]]
    total_records_attached: int


class IntegratedReadingOutput(BaseModel):
    """The integrated envelope returned by ``enhance()``.

    Wraps the original Track-A reading verbatim under ``reading`` plus a new
    ``dkp_translations_summary`` block with the top-level deduplicated view.
    Per-finding sidecars live INSIDE ``reading`` — each Finding dict gains a
    ``dkp_translations: list[TranslationRecordView]`` key without breaking
    the original ``ReadingOutput`` schema (because we work on dumped dicts,
    not Pydantic instances).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.1.0"
    reading: dict[str, Any]
    dkp_translations_summary: DkpTranslationsSummary


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _extract_bhava_planet_pairs(text: str) -> list[tuple[int, str]]:
    """Scan ``text`` for co-occurring bhava number + planet name.

    Returns deduplicated ``(bhava, planet)`` tuples. A planet only pairs with
    a bhava if both appear in the same string; we do NOT cross strings.
    """
    bhavas = {int(m.group(1)) for m in _BHAVA_PATTERN.finditer(text)}
    if not bhavas:
        return []
    pairs: set[tuple[int, str]] = set()
    for planet in _PLANETS:
        if planet.lower() in text.lower():
            for bhava in bhavas:
                pairs.add((bhava, planet))
    return sorted(pairs)


def _name_variants(segment: str) -> list[str]:
    """Yield case/spacing variants of ``segment`` that might appear in the
    Track-B translation registry.

    Track-B keys use Sanskrit-derived TitleCase ("Lakshmi", "Gajakesari"),
    sometimes with a space ("Vipareeta Raja", "Mangal Dosha"). Track-A rule
    IDs are namespaced lowercase ("yogas_extended.lakshmi",
    "yogas_extended.vipareeta"). We try several normalizations so the
    matcher is robust without requiring a hand-curated alias map.

    Variants yielded for ``"vipareeta_raja"``:
    - ``"vipareeta_raja"`` (as-is)
    - ``"Vipareeta_Raja"`` (per-word title-case, underscores kept)
    - ``"Vipareeta Raja"`` (per-word title-case, space-separated)
    - ``"vipareeta raja"`` (lowercase, space-separated)
    """
    if not segment:
        return []
    raw = segment
    spaced = segment.replace("_", " ")
    title_spaced = " ".join(w.capitalize() for w in spaced.split())
    title_underscored = "_".join(w.capitalize() for w in segment.split("_"))
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for v in (raw, title_underscored, title_spaced, spaced):
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _lookup_for_finding(finding: dict[str, Any]) -> list[TranslationRecord]:
    """Run all three lookup strategies for a single Finding dict.

    Returns deduplicated ``TranslationRecord`` instances, preserving first-seen
    order across strategies (key match → yoga match → bhava+planet match).
    """
    rule = finding.get("rule", "") or ""
    classification = finding.get("classification", "") or ""
    evidence = finding.get("evidence", []) or []
    evidence_text = " ".join(str(e) for e in evidence)

    seen_keys: set[str] = set()
    matches: list[TranslationRecord] = []

    def _record(rec: TranslationRecord) -> None:
        # Deduplicate by (key, domain) — same key can appear in multiple
        # domains (Saraswati spans career_wealth + dharma) and we want both.
        composite = f"{rec.key}|{rec.domain}"
        if composite not in seen_keys:
            seen_keys.add(composite)
            matches.append(rec)

    # Strategy 1: direct key match against rule ID + segments + variants.
    rule_segments = [rule, *rule.split("."), *rule.split("_")] if rule else []
    for candidate in rule_segments:
        for variant in _name_variants(candidate):
            for rec in translate_by_key(variant):
                _record(rec)

    # Strategy 2: yoga lookup when classification flags it.
    if classification == "yoga" and rule:
        last_segment = rule.rsplit(".", 1)[-1]
        for variant in _name_variants(last_segment):
            for rec in translate_yoga(variant):
                _record(rec)

    # Strategy 3: bhava+planet pair extraction over rule + evidence text.
    combined_text = f"{rule} {evidence_text}"
    for bhava, planet in _extract_bhava_planet_pairs(combined_text):
        for rec in translate_bhava_planet(bhava, planet):
            _record(rec)

    return matches


# ---------------------------------------------------------------------------
# Tree walker
# ---------------------------------------------------------------------------

def _walk_findings(node: Any) -> Iterable[dict[str, Any]]:
    """Yield every Finding-shaped dict reachable from ``node``.

    A Finding is identified structurally: a dict with the keys ``id``,
    ``rule``, ``classification``, and ``verdict``. This avoids importing
    the Pydantic class and lets us walk a dumped JSON tree.
    """
    if isinstance(node, dict):
        if {"id", "rule", "classification", "verdict"}.issubset(node.keys()):
            yield node
        else:
            for value in node.values():
                yield from _walk_findings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_findings(item)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def enhance(reading: dict[str, Any] | BaseModel) -> IntegratedReadingOutput:
    """Annotate a Track-A reading with Track-B DKP translations.

    Parameters
    ----------
    reading
        Either a ``ReadingOutput`` Pydantic model (will be dumped) or its
        already-dumped dict form (e.g. the dict returned by
        ``app.reading.proforma.compute(...)``).

    Returns
    -------
    IntegratedReadingOutput
        Envelope containing the (mutated) reading dict with per-finding
        ``dkp_translations`` sidecars + a deduplicated top-level
        ``dkp_translations_summary``.

    Notes
    -----
    The input dict is MUTATED in place (sidecars are appended to each Finding).
    Callers who need to preserve the original should deep-copy first.
    """
    if isinstance(reading, BaseModel):
        reading_dict: dict[str, Any] = reading.model_dump(mode="json")
    else:
        reading_dict = reading

    # Per-finding sidecars + cross-reference accumulator.
    all_records: dict[str, TranslationRecord] = {}
    cross_refs: dict[str, list[str]] = {}
    total_attached = 0

    for finding in _walk_findings(reading_dict):
        matches = _lookup_for_finding(finding)
        finding["dkp_translations"] = [
            TranslationRecordView.from_record(r).model_dump(mode="json")
            for r in matches
        ]
        total_attached += len(matches)
        finding_id = finding.get("id", "")
        for rec in matches:
            all_records.setdefault(rec.key, rec)
            cross_refs.setdefault(rec.key, []).append(finding_id)

    summary = DkpTranslationsSummary(
        records={
            key: TranslationRecordView.from_record(rec)
            for key, rec in all_records.items()
        },
        cross_references=cross_refs,
        total_records_attached=total_attached,
    )

    return IntegratedReadingOutput(
        reading=reading_dict,
        dkp_translations_summary=summary,
    )


def registry_size() -> int:
    """Return the number of Doctrine Translation records currently registered.

    Useful for smoke tests / health checks of the Track-B translation engine.
    """
    return len(all_translations())
