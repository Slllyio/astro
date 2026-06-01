"""8-axis doctrinal-corpus retriever for pandit-grade chart reading.

The retriever bridges the gap diagnosed 2026-06-01: ``shloka_lookup.py``
(18,061 rules) and ``nadi_lookup.py`` (1,737 records) are orphaned —
no reading-composer ever imports them. This module IS that orchestrator.

## Pandit cognition emulation

A senior Vedic astrologer reading a chart doesn't search the corpus by
ONE keyword. They fan out across distinct doctrinal axes:

  1. Lagna sign character
  2. Lagna-lord placement (house + sign + dignity)
  3. Moon nakshatra temperament
  4. Atmakaraka in Karakamsa sign
  5. Current Mahadasha lord effects
  6. Current MD × Antardasha interaction
  7. Each active yoga (Mangal Dosha, Amala, Vipareeta Raja, etc.)
  8. Queried bhava (the specific domain a client asks about)

This retriever runs all 8 axes against the harvested corpus + DKP
Translation Engine + Nadi corpus, deduplicates by (source, chapter,
text-hash), and returns a ``RetrievedCorpus`` bundle ready for LLM
prompt-injection by ``pandit_synthesizer.py``.

## Output format

The bundle carries every retrieved passage with a stable ``[Ref N]``
citation id, so the synthesizer's prompt can instruct the LLM to anchor
every doctrinal claim back to a specific reference. The bundle also
carries the DKP TranslationRecord matches and the Nadi Lagna context —
distinct sections so the synthesizer can weight them differently
(DKP layer carries hand-curated invariant mechanisms; shloka layer
carries raw classical citation; Nadi layer carries Lagna-specific
hand-attested predictions).

## Why this is deterministic + cacheable

No LLM is called here. Given the same chart features the same passages
return — so the retrieval step caches cleanly per chart_id, and any
re-run of synthesis (e.g. trying a different model or prompt) reuses
the same bundle without paying retrieval cost.

Usage:
    from app.llm.pandit_retriever import retrieve_for_chart, ChartFingerprint
    fingerprint = ChartFingerprint(
        asc_sign=8, asc_lord_house=11, moon_nakshatra=23,
        atmakaraka="Sun", karakamsa_sign=5, md_lord="Saturn",
        ad_lord="Jupiter", active_yoga_names=("Amala", "Mangal Dosha"),
    )
    bundle = retrieve_for_chart(fingerprint)
    print(f"{len(bundle.passages)} passages, "
          f"{len(bundle.dkp_translations)} DKP records, "
          f"Nadi found: {bundle.nadi_match.found}")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Final

from app.core.dkp_translation import (
    TranslationRecord,
    translate_yoga,
    translate_by_key,
)
from app.core.nadi_lookup import (
    NadiPatternKey,
    NadiPatternMatch,
    contexts_for_lagna,
    lookup_nadi_pattern,
)
from app.core.shloka_lookup import (
    ShlokaRule,
    rules_for_domain_and_planet,
    rules_for_topic,
    rules_mentioning,
)

logger = logging.getLogger(__name__)


# ─── Constants ──────────────────────────────────────────────────────


SIGN_NAMES: Final[tuple[str, ...]] = (
    "?",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAKSHATRA_NAMES: Final[tuple[str, ...]] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "P.Phalguni", "U.Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "P.Ashadha", "U.Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "P.Bhadra", "U.Bhadra", "Revati",
)

# Per-axis retrieval budget. 6 × 8 = 48 max passages before dedup.
DEFAULT_PER_AXIS_LIMIT: Final[int] = 6


# ─── Data shapes ────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChartFingerprint:
    """The minimal chart features the retriever needs.

    Built from a ``MasterReading`` by ``ChartFingerprint.from_master_reading``
    or constructed manually for testing.

    Attributes:
        asc_sign: Lagna sign 1..12.
        asc_lord_house: House the Lagna-lord sits in (1..12).
        asc_lord_planet: The Lagna-lord planet name (e.g. "Mars" for
            Scorpio Lagna).
        moon_nakshatra: 0..26 nakshatra index of natal Moon.
        moon_sign: 1..12.
        atmakaraka: AK planet name (Sun..Saturn — never nodes per
            strict 7-karaka lock).
        karakamsa_sign: AK's D9 sign 1..12.
        md_lord: Current Vimshottari Mahadasha lord at the target_jd.
        ad_lord: Current Antardasha lord.
        active_yoga_names: Tuple of yoga names detected for this chart
            (e.g. "Amala", "Mangal Dosha", "Vipareeta Raja").
        queried_bhava: If the reading is bhava-specific (Prashna or
            domain-focused), the bhava number 1..12. None for full
            life-reading.
        domain: Optional domain label ("marriage", "career", "wealth",
            "health", "children", "dharma", "longevity") for domain
            convergence queries.
    """
    asc_sign: int
    asc_lord_house: int
    asc_lord_planet: str
    moon_nakshatra: int
    moon_sign: int
    atmakaraka: str
    karakamsa_sign: int
    md_lord: str
    ad_lord: str | None = None
    active_yoga_names: tuple[str, ...] = ()
    queried_bhava: int | None = None
    domain: str | None = None


@dataclass(frozen=True)
class RetrievedPassage:
    """One classical passage with a stable citation ID for prompt-injection."""
    ref_id: int                # [Ref N] for the LLM to anchor claims
    axis: str                  # which of the 8 axes pulled this
    source: str                # e.g. "bphs", "phaladeepika"
    chapter: str
    text: str                  # raw passage text (OCR-cleaned)


@dataclass(frozen=True)
class RetrievedCorpus:
    """Everything the synthesizer needs in one bundle.

    The passage list is deduplicated and globally numbered so the LLM's
    ``[Ref N]`` anchors are unambiguous. The DKP and Nadi sections sit
    separately because they carry different epistemic weight (DKP is
    hand-curated invariant + modern-translation; Nadi is Lagna-specific
    hand-attested prediction; shloka is raw classical text).
    """
    fingerprint: ChartFingerprint
    passages: tuple[RetrievedPassage, ...]
    dkp_translations: tuple[TranslationRecord, ...] = ()
    nadi_match: NadiPatternMatch | None = None
    nadi_contexts: tuple[dict, ...] = ()
    axis_counts: dict[str, int] = field(default_factory=dict)


# ─── Retrieval helpers ──────────────────────────────────────────────


def _dedup_key(rule: ShlokaRule) -> tuple[str, str, str]:
    """Stable dedup key per rule: source + chapter + first 60 chars of text.

    The text prefix catches the case where a single source has two
    distinct rules in the same chapter — without it dedup would collapse
    them. 60 chars is enough to discriminate while tolerating OCR noise
    in trailing characters.
    """
    return (rule.source, rule.chapter, " ".join(rule.raw_text.split())[:60])


def _retrieve_axis(
    axis_name: str,
    needles: tuple[str, ...],
    limit: int,
) -> tuple[ShlokaRule, ...]:
    """One axis = one rules_mentioning query (AND-filter across needles)."""
    rules = rules_mentioning(*needles, limit=limit * 3)  # over-fetch for dedup
    return rules[:limit]


# ─── Public API ─────────────────────────────────────────────────────


def retrieve_for_chart(
    fingerprint: ChartFingerprint,
    per_axis_limit: int = DEFAULT_PER_AXIS_LIMIT,
) -> RetrievedCorpus:
    """Fan-out across 8 doctrinal axes; dedup; assemble bundle.

    Wall-clock: ~50-200ms for a typical chart (in-memory dict scans).
    Network calls: zero. Deterministic given identical fingerprint.
    """
    asc_name = SIGN_NAMES[fingerprint.asc_sign]
    nak_name = NAKSHATRA_NAMES[fingerprint.moon_nakshatra]
    moon_sign_name = SIGN_NAMES[fingerprint.moon_sign]
    karakamsa_name = SIGN_NAMES[fingerprint.karakamsa_sign]

    # 8 retrieval axes — each yields up to per_axis_limit rules.
    axis_queries: dict[str, tuple[str, ...]] = {
        "lagna_character": (asc_name, "lagna"),
        "lagna_lord": (fingerprint.asc_lord_planet, asc_name),
        "moon_nakshatra": (nak_name,),
        "atmakaraka": (fingerprint.atmakaraka, "atmakaraka"),
        "md_lord": (fingerprint.md_lord, "dasa"),
        "md_ad": (
            (fingerprint.md_lord, fingerprint.ad_lord, "dasa")
            if fingerprint.ad_lord
            else (fingerprint.md_lord, "antardasa")
        ),
        # Moon-sign as a fallback ground (always has corpus coverage)
        "moon_sign": (moon_sign_name, "moon"),
        # Karakamsa-sign reading
        "karakamsa": (karakamsa_name, "navamsa"),
    }

    raw_per_axis: dict[str, tuple[ShlokaRule, ...]] = {}
    for axis_name, needles in axis_queries.items():
        try:
            rules = _retrieve_axis(axis_name, needles, per_axis_limit)
        except Exception as exc:
            logger.warning("Axis %s retrieval failed: %s", axis_name, exc)
            rules = ()
        raw_per_axis[axis_name] = rules

    # Yoga axis — one query per active yoga, up to limit/2 each
    yoga_rules: list[tuple[str, ShlokaRule]] = []
    yoga_limit_per = max(2, per_axis_limit // 2)
    for yoga in fingerprint.active_yoga_names[:8]:  # cap to keep retrieval bounded
        try:
            yrs = rules_mentioning(yoga, limit=yoga_limit_per * 2)[:yoga_limit_per]
            for y in yrs:
                yoga_rules.append((yoga, y))
        except Exception as exc:
            logger.warning("Yoga %s retrieval failed: %s", yoga, exc)

    # Domain + bhava-specific axis (only when supplied)
    domain_rules: tuple[ShlokaRule, ...] = ()
    if fingerprint.domain:
        try:
            domain_rules = rules_for_domain_and_planet(
                fingerprint.domain, fingerprint.atmakaraka, limit=per_axis_limit,
            )
        except Exception as exc:
            logger.warning("Domain axis retrieval failed: %s", exc)

    bhava_rules: tuple[ShlokaRule, ...] = ()
    if fingerprint.queried_bhava:
        bhava_topic = _bhava_topic_name(fingerprint.queried_bhava)
        try:
            bhava_rules = rules_for_topic(bhava_topic, limit=per_axis_limit)
        except Exception as exc:
            logger.warning("Bhava axis retrieval failed: %s", exc)

    # ── Dedup + global numbering ────────────────────────────────────
    seen_keys: set[tuple[str, str, str]] = set()
    passages: list[RetrievedPassage] = []
    axis_counts: dict[str, int] = {}
    next_ref_id = 1

    def _emit(axis: str, rule: ShlokaRule) -> None:
        nonlocal next_ref_id
        key = _dedup_key(rule)
        if key in seen_keys:
            return
        seen_keys.add(key)
        passages.append(RetrievedPassage(
            ref_id=next_ref_id,
            axis=axis,
            source=rule.source,
            chapter=rule.chapter,
            text=" ".join(rule.raw_text.split()),  # collapse whitespace
        ))
        axis_counts[axis] = axis_counts.get(axis, 0) + 1
        next_ref_id += 1

    # Order matters for the [Ref N] sequence — emit Lagna/lord first so
    # they get the lowest reference numbers (humans read those most).
    axis_order = (
        "lagna_character", "lagna_lord", "moon_sign", "moon_nakshatra",
        "atmakaraka", "karakamsa", "md_lord", "md_ad",
    )
    for axis in axis_order:
        for rule in raw_per_axis.get(axis, ()):
            _emit(axis, rule)
    for yoga, rule in yoga_rules:
        _emit(f"yoga:{yoga}", rule)
    for rule in domain_rules:
        _emit(f"domain:{fingerprint.domain}", rule)
    for rule in bhava_rules:
        _emit(f"bhava:{fingerprint.queried_bhava}", rule)

    # ── DKP TranslationRecord layer ─────────────────────────────────
    dkp_seen: set[tuple[str, str]] = set()
    dkp_records: list[TranslationRecord] = []
    for yoga in fingerprint.active_yoga_names:
        for r in translate_yoga(yoga):
            sig = (r.key, r.domain)
            if sig not in dkp_seen:
                dkp_seen.add(sig)
                dkp_records.append(r)
    # Bhava-placement DKP records (e.g. bhava_4_planet_Saturn for
    # Scorpio Lagna where Saturn rules + aspects 4H)
    for r in translate_by_key(f"bhava_{fingerprint.asc_lord_house}_planet_{fingerprint.asc_lord_planet}"):
        sig = (r.key, r.domain)
        if sig not in dkp_seen:
            dkp_seen.add(sig)
            dkp_records.append(r)

    # ── Nadi pattern lookup ─────────────────────────────────────────
    nadi_key = NadiPatternKey(
        asc_sign=fingerprint.asc_sign,
        moon_sign=fingerprint.moon_sign,
        moon_nakshatra=fingerprint.moon_nakshatra,
        atmakaraka=fingerprint.atmakaraka,
        md_lord=fingerprint.md_lord,
        ad_lord=fingerprint.ad_lord,
    )
    nadi_match = lookup_nadi_pattern(nadi_key)
    nadi_ctxs = contexts_for_lagna(fingerprint.asc_sign, limit=3)

    return RetrievedCorpus(
        fingerprint=fingerprint,
        passages=tuple(passages),
        dkp_translations=tuple(dkp_records),
        nadi_match=nadi_match,
        nadi_contexts=nadi_ctxs,
        axis_counts=axis_counts,
    )


def _bhava_topic_name(bhava: int) -> str:
    """Map bhava number to the topic-tag the harvester uses."""
    return {
        1: "first house", 2: "second house", 3: "third house",
        4: "fourth house", 5: "fifth house", 6: "sixth house",
        7: "seventh house", 8: "eighth house", 9: "ninth house",
        10: "tenth house", 11: "eleventh house", 12: "twelfth house",
    }.get(bhava, "house")


__all__ = [
    "ChartFingerprint",
    "RetrievedCorpus",
    "RetrievedPassage",
    "retrieve_for_chart",
    "DEFAULT_PER_AXIS_LIMIT",
]
