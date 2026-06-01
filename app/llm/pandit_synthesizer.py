"""Pandit-grade chart-reading synthesizer (Phase-1 Draft pipeline).

Consumes the ``RetrievedCorpus`` bundle from ``pandit_retriever.py`` and
produces a narrative reading by injecting 40-60 classical passages,
the DKP Translation Engine layer, and Nadi context into an Anthropic
Sonnet 4.6 prompt.

## Phase-1 vs Phase-2

Phase-1 (this file, MVP): **Draft pass only**.
  - One LLM call with the full retrieved corpus + chart fingerprint.
  - Output: narrative reading with [Ref N] citation anchors.
  - Optional: DKP modernization sub-pass that rephrases each doctrine
    claim into modern desh-kaal-paristhiti language.

Phase-2 (deferred per CLAUDE.md 2026-06-01 decision):
  - Critic pass: adversarial specificity-score (rejects generic output).
  - Refinement pass: re-prompt with this-chart-specific evidence when
    Critic score < 7.
  - Quality gate: minimum citation count, minimum coverage.

The Phase-1 build deliberately ships without the Critic so we can
eyeball whether retrieval alone fixes the depth problem before
investing in the adversarial loop.

## Why this is the right abstraction

The synthesizer is a thin orchestrator. The retriever does the work of
choosing what doctrine to consult; the LLM does the work of writing
narrative; the synthesizer just stitches them together with the right
prompt contract. Swapping the LLM provider (Sonnet → Opus, or to a
local model) is a single line change at the constructor.

Usage:
    from app.llm.client import AnthropicClient
    from app.llm.pandit_retriever import retrieve_for_chart, ChartFingerprint
    from app.llm.pandit_synthesizer import PanditSynthesizer

    fingerprint = ChartFingerprint(...)
    bundle = retrieve_for_chart(fingerprint)
    synth = PanditSynthesizer(llm=AnthropicClient(model="claude-sonnet-4-6"))
    reading = synth.synthesize(bundle, focal_themes=("marriage", "career"))
    print(reading.narrative)
    for cit in reading.citations_used:
        print(f"[Ref {cit.ref_id}] {cit.source}/{cit.chapter}")
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Final

from app.llm.client import LLMClient
from app.llm.pandit_retriever import (
    RetrievedCorpus,
    RetrievedPassage,
    SIGN_NAMES,
    NAKSHATRA_NAMES,
)

logger = logging.getLogger(__name__)


# ─── Result shape ───────────────────────────────────────────────────


@dataclass(frozen=True)
class PanditReading:
    """The output of a single Draft synthesis pass.

    Attributes:
        narrative: The full reading text in pandit voice, with [Ref N]
            inline citation anchors preserved.
        citations_used: The subset of ``RetrievedCorpus.passages`` whose
            [Ref N] actually appears in narrative — provenance proof.
        unused_passages: Passages retrieved but not cited; useful for
            debugging retrieval relevance.
        prompt_token_estimate: Rough char-based token estimate of the
            prompt sent to the LLM.
        focal_themes: The themes the synthesizer was asked to weight.
        model: Which LLM model produced the narrative.
    """
    narrative: str
    citations_used: tuple[RetrievedPassage, ...]
    unused_passages: tuple[RetrievedPassage, ...]
    prompt_token_estimate: int
    focal_themes: tuple[str, ...]
    model: str


# ─── Prompt construction ────────────────────────────────────────────


SYSTEM_PROMPT: Final[str] = """You are a senior Vedic astrologer in the lineage \
of BV Raman, Sanjay Rath, and KN Rao. You write chart readings the way a \
seasoned pandit speaks: narrative not tabular, specific not generic, decisive \
not hedged. You cite classical doctrine the way you breathe — every claim \
about the chart's structure traces back to a specific shloka or rule, \
identified inline with [Ref N] where N references the numbered passages \
provided in the user prompt. You do NOT use bullet lists for the main reading \
prose — you write in paragraphs the way classical commentaries read.

The doctrinal worldview is locked: Lahiri sidereal ayanamsa, whole-sign \
houses and aspects, strict 7-karaka Jaimini (Rahu/Ketu are chayagrahas, \
NEVER atmakaraka), Vimshottari dasha as the primary timing system, \
desh-kaal-paristhiti modern translation (ancient predictions are translated \
into contemporary equivalents, never read literally). Saturn is NOT a \
yogakaraka unless the geometry actually fulfills BPHS Ch.32 criteria — \
verify before claiming.

Your readings have texture and stake. They speak TO the native, not ABOUT \
the chart. They make calls. They name what the chart actually shows about \
this specific life, using the chart's specific planet positions, yoga names, \
and dasha-period activations. Generic doctrinal language ("contradictions \
exist", "delays then stability") is a failure mode — replace it with \
this-chart-specific mechanism every time."""


def _passage_block(passages: tuple[RetrievedPassage, ...]) -> str:
    """Format the retrieved passages as a numbered evidence block.

    The LLM is instructed to anchor every doctrinal claim to one of
    these [Ref N] numbers. Keeping the block at the top of the prompt
    (right after the chart facts) means the model sees evidence before
    being asked to synthesize.
    """
    lines: list[str] = []
    for p in passages:
        lines.append(
            f"[Ref {p.ref_id}] ({p.source}/{p.chapter}) — {p.text}"
        )
    return "\n".join(lines)


def _dkp_block(corpus: RetrievedCorpus) -> str:
    """Format the DKP TranslationRecord layer as a distinct prompt section.

    DKP is hand-curated — each record carries ancient, desh-shift, kaal-shift,
    paristhiti-shift, modern, and invariant fields. The synthesizer instructs
    the LLM to use these for the desh-kaal-paristhiti modernization of any
    relevant claim. They're NOT the same as raw classical citations.
    """
    if not corpus.dkp_translations:
        return "(no DKP TranslationRecords matched this chart's keys)"
    lines: list[str] = []
    for i, r in enumerate(corpus.dkp_translations, 1):
        lines.append(f"[DKP {i}] {r.key} ({r.classification} | {r.domain})")
        lines.append(f"   Ancient: {r.ancient_manifestation[:280]}")
        lines.append(f"   Modern : {r.modern_manifestation[:280]}")
        lines.append(f"   Invariant mechanism: {r.invariant_mechanism[:260]}")
        if r.classical_references:
            lines.append(f"   Classical refs: {', '.join(r.classical_references[:3])}")
        lines.append("")
    return "\n".join(lines)


def _nadi_block(corpus: RetrievedCorpus) -> str:
    """Format the Nadi pattern match + Lagna contexts."""
    parts: list[str] = []
    if corpus.nadi_match and corpus.nadi_match.found:
        parts.append(
            f"NADI MATCH: {corpus.nadi_match.tradition} (specificity "
            f"{corpus.nadi_match.key_specificity})"
        )
        parts.append(f"  {corpus.nadi_match.reading or ''}")
        parts.append("")
    if corpus.nadi_contexts:
        parts.append(f"NADI LAGNA CONTEXTS ({len(corpus.nadi_contexts)} for "
                     f"this Lagna):")
        for i, ctx in enumerate(corpus.nadi_contexts, 1):
            txt = (ctx.get("context_text") or "")[:300]
            parts.append(
                f"  [Nadi {i}] ({ctx.get('source')}, Nadiamsa: "
                f"{ctx.get('nadiamsa') or 'n/a'}) — {txt}"
            )
    return "\n".join(parts) if parts else "(no Nadi material for this Lagna)"


def _chart_facts_block(corpus: RetrievedCorpus) -> str:
    """Restate the chart fingerprint in pandit-readable form."""
    fp = corpus.fingerprint
    asc = SIGN_NAMES[fp.asc_sign]
    moon_sign = SIGN_NAMES[fp.moon_sign]
    nak = NAKSHATRA_NAMES[fp.moon_nakshatra]
    karak = SIGN_NAMES[fp.karakamsa_sign]
    lines = [
        f"Ascendant (Lagna): {asc} (sign {fp.asc_sign})",
        f"Lagna lord: {fp.asc_lord_planet} in house {fp.asc_lord_house}",
        f"Moon: {moon_sign}, nakshatra {nak} (index {fp.moon_nakshatra})",
        f"Atmakaraka (strict 7-karaka, never Rahu/Ketu): {fp.atmakaraka}",
        f"Karakamsa: {karak} (sign {fp.karakamsa_sign})",
        f"Current Mahadasha lord: {fp.md_lord}",
    ]
    if fp.ad_lord:
        lines.append(f"Current Antardasha lord: {fp.ad_lord}")
    if fp.active_yoga_names:
        lines.append(f"Active yogas detected: {', '.join(fp.active_yoga_names)}")
    if fp.queried_bhava:
        lines.append(f"Bhava in focus: {fp.queried_bhava}")
    if fp.domain:
        lines.append(f"Domain in focus: {fp.domain}")
    return "\n".join(lines)


def build_prompt(
    corpus: RetrievedCorpus,
    focal_themes: tuple[str, ...] = (),
) -> str:
    """Assemble the full Draft-pass prompt."""
    themes_line = (
        "Themes the native wants you to address: " + ", ".join(focal_themes)
        if focal_themes else
        "No specific themes flagged — produce a full life-arc reading."
    )

    return f"""You are reading the following birth chart. Use the doctrinal \
evidence provided below to ground every claim with [Ref N] anchors. Where a \
DKP TranslationRecord matches, apply its modern translation — do NOT take \
ancient predictions literally.

CHART FACTS
{_chart_facts_block(corpus)}

{themes_line}

DOCTRINAL EVIDENCE — {len(corpus.passages)} numbered passages from the 18,061-\
rule classical corpus:
{_passage_block(corpus.passages)}

DKP TRANSLATION LAYER — hand-curated desh-kaal-paristhiti modernization for \
this chart's active yogas and key bhava placements:
{_dkp_block(corpus)}

NADI LAYER — Lagna-specific material from Deva Keralam, Saptarishi, and \
related Nadi traditions:
{_nadi_block(corpus)}

WRITE THE READING.

Structure your reading as flowing paragraphs (NOT bullet lists). Cover:
  1. Opening — the chart's central karmic argument in one paragraph.
  2. The body, the early years, the surface (Lagna + Lagna-lord).
  3. The mind and the foundation (Moon, nakshatra, 4H if relevant).
  4. The soul-purpose channel (Atmakaraka, Karakamsa, Karakamsa-derived \
Ishta Devata = 12th from Karakamsa).
  5. The active yogas — for each one detected, what it actually means \
for THIS native's life, using DKP modern translation when available.
  6. The dasha timeline — what the current MD/AD activates in this chart \
specifically (not in general).
  7. Marriage, children, career, wealth, health — each addressed with \
this-chart-specific evidence and citations.
  8. The current window — what to do with the next 12-24 months.
  9. Remedies — only those grounded in the chart's specific weaknesses.

Constraints (enforced — do not violate):
  - Every doctrinal claim about a placement, yoga, or dasha period must \
end with [Ref N] citing the numbered passage that supports it.
  - When a claim is not directly cited (you are reasoning from general \
doctrine), end it with [doctrine-derived inference] explicitly.
  - Saturn is NOT yogakaraka unless the BPHS Ch.32 geometry actually \
fulfills the kendra condition — verify and state explicitly.
  - Atmakaraka is NEVER Rahu or Ketu (chayagrahas cannot signify soul).
  - Speak TO the native ("You will...", "Your chart shows..."), not \
ABOUT the chart abstractly.
  - Make calls. Where doctrine produces a contradictory verdict, name \
what the contradiction means for THIS life, do not hedge into \
"contradictions exist".
  - Address the native directly. Use texture and specificity. Do not \
slip into generic Vedic-astrology language."""


# ─── Synthesizer ────────────────────────────────────────────────────


class PanditSynthesizer:
    """Driver that calls the LLM with the assembled prompt and parses the
    response into a ``PanditReading``.

    The synthesizer is intentionally thin — the prompt does the heavy
    lifting. Future phases (Critic, Refinement) will subclass or compose
    around this class without disturbing the Draft contract.
    """

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def synthesize(
        self,
        corpus: RetrievedCorpus,
        focal_themes: tuple[str, ...] = (),
    ) -> PanditReading:
        prompt = build_prompt(corpus, focal_themes=focal_themes)
        token_estimate = len(prompt) // 4  # rough chars-to-tokens

        narrative = self.llm.complete(prompt)

        # Parse out which [Ref N] anchors actually appeared in narrative
        cited_ids = set(int(m) for m in re.findall(r"\[Ref (\d+)\]", narrative))
        cited = tuple(p for p in corpus.passages if p.ref_id in cited_ids)
        uncited = tuple(p for p in corpus.passages if p.ref_id not in cited_ids)

        # Surface model name when the client exposes it; otherwise unknown
        model_name = getattr(self.llm, "model", "unknown")

        return PanditReading(
            narrative=narrative,
            citations_used=cited,
            unused_passages=uncited,
            prompt_token_estimate=token_estimate,
            focal_themes=focal_themes,
            model=model_name,
        )


__all__ = ["PanditReading", "PanditSynthesizer", "SYSTEM_PROMPT", "build_prompt"]
