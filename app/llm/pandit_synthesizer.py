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
    BhriguPassage,
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
    bhrigu_citations_used: tuple[BhriguPassage, ...] = ()


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


def _bhrigu_block(corpus: RetrievedCorpus) -> str:
    """Format the Bhrigu Nadi rule corpus as a numbered evidence block.

    Bhrigu rules are condition -> outcome statements (rule-format, not
    free shloka prose), so they render in a distinct section with
    [Bhrigu N] anchors. The ``ref_id`` namespace is globally unique with
    shloka [Ref N] anchors (Bhrigu ref_ids start at len(passages)+1),
    so the LLM can cite both without collision.
    """
    if not corpus.bhrigu_passages:
        return "(no Bhrigu Nadi rules matched this chart's fingerprint)"
    lines: list[str] = []
    for p in corpus.bhrigu_passages:
        lines.append(f"[Bhrigu {p.ref_id}] (bhrigu#{p.rule_id}) — {p.text}")
    return "\n".join(lines)


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
    # Phase-2 doctrine extensions — surface every populated field so the
    # LLM actually sees the enriched fingerprint (without these lines the
    # pipe is wider but the funnel stays the same size).
    if fp.upapada_sign:
        lines.append(
            f"Upapada Lagna (UPL, marriage axis): sign {fp.upapada_sign}; "
            f"2nd-from-UPL: sign {fp.second_from_upl_sign}"
        )
    if fp.kalasarpa_variant:
        lines.append(f"Kalasarpa Dosha variant: {fp.kalasarpa_variant}")
    active_extra_yogas: list[str] = []
    if fp.dignified_eighth_lord:
        active_extra_yogas.append("Sarala-dignified (8L in own/exalt/MT)")
    if fp.chandra_mangala_active:
        active_extra_yogas.append(
            "Chandra-Mangala (Moon-Mars conjunction/opposition)"
        )
    if fp.adhi_yoga_active:
        active_extra_yogas.append(
            "Adhi Yoga strict (Mer+Jup+Ven all in 6/7/8 from Moon)"
        )
    if fp.saraswati_active:
        active_extra_yogas.append(
            "Saraswati Yoga (Mer+Jup+Ven all in kendra/trikona/2H, "
            "Jupiter dignified)"
        )
    if active_extra_yogas:
        lines.append(
            f"Extra yogas detected (Phase-2 lib): {'; '.join(active_extra_yogas)}"
        )
    if fp.pushkara_planets:
        lines.append(
            f"Planets in Pushkara navamsa: {', '.join(fp.pushkara_planets)}"
        )
    return "\n".join(lines)


def build_prompt(
    corpus: RetrievedCorpus,
    focal_themes: tuple[str, ...] = (),
) -> str:
    """Assemble the full Draft-pass prompt."""
    fp = corpus.fingerprint
    themes_line = (
        "Themes the native wants you to address: " + ", ".join(focal_themes)
        if focal_themes else
        "No specific themes flagged — produce a full life-arc reading."
    )

    # UPL marriage-axis instruction — only meaningful when UPL was computed
    if fp.upapada_sign:
        upl_marriage_instruction = (
            f"MARRIAGE — anchor marriage timing on the Upapada Lagna "
            f"(UPL=sign {fp.upapada_sign}) and 2nd-from-UPL "
            f"(sign {fp.second_from_upl_sign}). If a planet conjoins or "
            f"aspects 2nd-from-UPL, name the consequence for marital years "
            f"per Sanjay Rath's UPL doctrine."
        )
    else:
        upl_marriage_instruction = (
            "MARRIAGE — apply the 7H lord placement, Venus/Jupiter "
            "condition, and the dasha period activating the 7H axis."
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

BHRIGU NADI RULES — conditional rule-format predictions from the Bhrigu \
Samhita corpus (cite as [Bhrigu N]):
{_bhrigu_block(corpus)}

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
  5b. Special yoga callouts — for each yoga detected by the Phase-2 \
library, address by name: Kalasarpa variant (if present — name it: \
Anant/Kulika/Vasuki/Shankhapal/Padma/Mahapadma/Takshaka/Karkotaka/\
Shankhachuda/Ghatak/Vishadhar/Sheshnag), Sarala-dignified, \
Chandra-Mangala, Adhi Yoga strict, Saraswati Yoga, Pushkara navamsa \
planets. Cite Bhrigu rules with [Bhrigu N] where applicable.
  6. The dasha timeline — what the current MD/AD activates in this chart \
specifically (not in general).
  7. Marriage, children, career, wealth, health — each addressed with \
this-chart-specific evidence and citations. {upl_marriage_instruction}
  8. The current window — what to do with the next 12-24 months.
  9. Remedies — only those grounded in the chart's specific weaknesses.

Constraints (enforced — do not violate):
  - Every doctrinal claim about a placement, yoga, or dasha period must \
end with [Ref N] citing the numbered passage that supports it.
  - When a claim is not directly cited (you are reasoning from general \
doctrine), end it with [doctrine-derived inference] explicitly.
  - Use [Bhrigu N] to anchor Bhrigu-Nadi-style predictions (rule-format, \
often: When X then Y). Bhrigu citations are DISTINCT from [Ref N] shloka \
citations.
  - When fingerprint reports Kalasarpa variant by name, you MUST address \
it in the opening paragraph by that name — do not gloss it as "Rahu-Ketu \
axis material".
  - When fingerprint reports Upapada Lagna, you MUST cite UPL in any \
marriage-related claim.
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


# ─── Critic + Refinement (Phase-2, opt-in) ──────────────────────────


@dataclass(frozen=True)
class CriticReview:
    """Adversarial reviewer output: per-dimension scores and must-fix list.

    The four scoring dimensions deliberately probe the failure modes
    seen during Phase-1 diagnosis: generic doctrinal prose, missing
    citations, missing this-chart-specific facts, and silent doctrine
    violations (Saturn-yogakaraka without geometry, AK=Rahu/Ketu, etc.).
    """
    specificity_score: int
    citation_density_score: int
    this_chart_grounding_score: int
    doctrinal_accuracy_score: int
    overall_score: float  # mean of the four sub-scores
    weaknesses: tuple[str, ...]
    must_fix: tuple[str, ...]
    raw_critique: str


@dataclass(frozen=True)
class RefinedReading:
    """Result of a critic-gated synthesis.

    Attributes:
        draft: The first-pass narrative.
        critic_review: The structured critique of the draft.
        refined: The second-pass narrative if refinement was triggered;
            ``None`` when the draft passed the critic gate.
        passes_used: 1 if no refinement was needed (draft accepted or
            critic disabled), 2 if a refinement pass executed.
    """
    draft: PanditReading
    critic_review: CriticReview
    refined: PanditReading | None
    passes_used: int


CRITIC_SYSTEM_PROMPT: Final[str] = """You are an adversarial reviewer of a \
Vedic-astrology chart reading produced by another senior pandit. Your job is \
NOT to write a kinder version of the reading — it is to find every place \
where the draft fails the pandit-grade specificity bar and force the \
author to fix it.

DOCTRINE LOCKS (any violation is an automatic critical must-fix):
  - Lahiri sidereal ayanamsa only (NEVER tropical, KP, Raman).
  - Whole-sign houses and whole-sign drishti (aspect) geometry.
  - Strict 7-karaka Jaimini: Atmakaraka can NEVER be Rahu or Ketu \
(chayagrahas cannot signify the soul). Flag any claim that names Rahu/Ketu \
in any karaka role.
  - Saturn is NOT yogakaraka by default — only when BPHS Ch.32 kendra \
geometry actually fulfills. Flag any unsupported Saturn-yogakaraka claim.
  - DAYS_PER_VEDIC_YEAR = 365.2425 (Gregorian mean); JD arithmetic for \
calendar dates (never datetime.timedelta).
  - We do NOT statistically "validate" classical doctrine — modern context \
applies via DKP modernization, not statistical re-derivation.

SCORE THE DRAFT (1-10 integer per dimension; higher is better):
  1. Specificity — does the draft speak to THIS chart's actual placements, \
yoga names, dasha lords, nakshatras, by name? Generic doctrinal prose \
("delays then stability", "contradictions exist", "trust the process", \
"karmic lessons unfold") collapses this score toward 1.
  2. Citation density — are doctrinal claims actually anchored by [Ref N] \
inline? A reading with <1 citation per paragraph fails this dimension.
  3. This-chart grounding — does the draft name the specific houses planets \
occupy in THIS chart, the specific dasha lord active now, the specific \
nakshatra of the Moon? Missing chart-specific facts (Saturn's house \
unstated, dasha lord unnamed, AK's sign-from-Lagna unstated) collapses \
this score.
  4. Doctrinal accuracy — does the draft respect every doctrine lock above? \
Any silent violation collapses this score to 1.

THEN OUTPUT — in this exact schema, nothing else, no preamble:

Specificity: <N>/10
Citation density: <N>/10
This-chart grounding: <N>/10
Doctrinal accuracy: <N>/10

Top weaknesses (up to 5, most severe first):
- <weakness 1>
- <weakness 2>
- <weakness 3>
- <weakness 4>
- <weakness 5>

Must-fix (3-5 concrete actions the author must take in the refinement pass):
- <must-fix 1>
- <must-fix 2>
- <must-fix 3>
- <must-fix 4>
- <must-fix 5>

Be adversarial. Flag GENERIC patterns. Flag missing this-chart facts. \
Flag missing [Ref N] anchors. Flag any doctrine-lock violation. Do not \
hedge — your job is to make the next pass better."""


def _corpus_summary(corpus: RetrievedCorpus) -> str:
    """Compact corpus summary for the critic prompt (avoids re-flooding it
    with all 40-60 passages)."""
    fp = corpus.fingerprint
    asc = SIGN_NAMES[fp.asc_sign]
    moon_sign = SIGN_NAMES[fp.moon_sign]
    nak = NAKSHATRA_NAMES[fp.moon_nakshatra]
    yogas = ", ".join(fp.active_yoga_names) if fp.active_yoga_names else "none"
    return (
        f"Lagna={asc}, Lagna-lord={fp.asc_lord_planet} in house "
        f"{fp.asc_lord_house}; Moon={moon_sign} in {nak}; "
        f"Atmakaraka={fp.atmakaraka}; MD={fp.md_lord}, AD={fp.ad_lord or 'n/a'}; "
        f"active_yogas=[{yogas}]; passages_retrieved={len(corpus.passages)}; "
        f"dkp_records={len(corpus.dkp_translations)}; "
        f"nadi_contexts={len(corpus.nadi_contexts)}"
    )


def build_critic_prompt(
    draft: PanditReading,
    corpus: RetrievedCorpus,
) -> str:
    """Assemble the adversarial-critic prompt.

    Includes the draft narrative, a compact corpus summary (so the critic
    knows what evidence WAS available without re-reading it all), and
    explicit marching orders from ``CRITIC_SYSTEM_PROMPT``.
    """
    cited = len(draft.citations_used)
    unused = len(draft.unused_passages)
    return f"""{CRITIC_SYSTEM_PROMPT}

CHART AND CORPUS UNDER REVIEW
{_corpus_summary(corpus)}
Draft cited {cited} of {cited + unused} retrieved passages.

DRAFT NARRATIVE TO CRITIQUE
{draft.narrative}

Now produce the structured critique using the exact output schema above."""


def _parse_critic_review(raw: str) -> CriticReview:
    """Regex-parse the critic LLM output into a ``CriticReview``.

    Falls back to a 5/5/5/5 score with weakness ``("parse_failed",)`` if
    the LLM returned malformed output — this keeps the refinement gate
    deterministic (overall=5 < 8 forces a refinement only if a must-fix
    list also appears; otherwise the draft is accepted).
    """
    def _score(label: str) -> int | None:
        m = re.search(
            rf"{re.escape(label)}\s*:\s*(\d+)\s*/\s*10",
            raw,
            re.IGNORECASE,
        )
        if not m:
            return None
        try:
            return max(1, min(10, int(m.group(1))))
        except ValueError:
            return None

    spec = _score("Specificity")
    cite = _score("Citation density")
    grnd = _score("This-chart grounding")
    doct = _score("Doctrinal accuracy")

    if any(s is None for s in (spec, cite, grnd, doct)):
        logger.warning("critic output failed to parse; using fallback scores")
        return CriticReview(
            specificity_score=5,
            citation_density_score=5,
            this_chart_grounding_score=5,
            doctrinal_accuracy_score=5,
            overall_score=5.0,
            weaknesses=("parse_failed",),
            must_fix=(),
            raw_critique=raw,
        )

    def _bullets(section_label: str) -> tuple[str, ...]:
        # Locate the section heading and slurp bulleted lines until the
        # next blank line or next heading.
        pattern = (
            rf"{re.escape(section_label)}[^\n]*\n"
            r"((?:[ \t]*[-*][^\n]*\n?)+)"
        )
        m = re.search(pattern, raw, re.IGNORECASE)
        if not m:
            return ()
        bullets: list[str] = []
        for line in m.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith(("-", "*")):
                item = stripped.lstrip("-* ").strip()
                if item:
                    bullets.append(item)
        return tuple(bullets)

    weaknesses = _bullets("Top weaknesses")
    must_fix = _bullets("Must-fix")

    overall = round((spec + cite + grnd + doct) / 4.0, 2)

    return CriticReview(
        specificity_score=spec,
        citation_density_score=cite,
        this_chart_grounding_score=grnd,
        doctrinal_accuracy_score=doct,
        overall_score=overall,
        weaknesses=weaknesses,
        must_fix=must_fix,
        raw_critique=raw,
    )


def build_refinement_prompt(
    corpus: RetrievedCorpus,
    draft: PanditReading,
    review: CriticReview,
) -> str:
    """Assemble the refinement prompt.

    Restates the full corpus (so the rewrite has full evidence access),
    includes the draft and the critic's must-fix list as hard constraints,
    and instructs the LLM to preserve structure and citation anchors that
    still apply.
    """
    base = build_prompt(corpus, focal_themes=draft.focal_themes)
    must_fix_block = (
        "\n".join(f"  - {item}" for item in review.must_fix)
        if review.must_fix else "  (none specified)"
    )
    weaknesses_block = (
        "\n".join(f"  - {item}" for item in review.weaknesses)
        if review.weaknesses else "  (none specified)"
    )

    return f"""{base}

PRIOR DRAFT (the version the critic just reviewed):
{draft.narrative}

CRITIC SCORES
  Specificity: {review.specificity_score}/10
  Citation density: {review.citation_density_score}/10
  This-chart grounding: {review.this_chart_grounding_score}/10
  Doctrinal accuracy: {review.doctrinal_accuracy_score}/10
  Overall: {review.overall_score}/10

CRITIC WEAKNESSES FLAGGED
{weaknesses_block}

MUST-FIX (every item below is a hard constraint for this rewrite):
{must_fix_block}

Rewrite the reading addressing EVERY must-fix item above. Keep the same \
section structure (opening, lagna, mind, atmakaraka, yogas, dasha, life \
domains, current window, remedies). Replace any flagged generic passage \
with this-chart-specific evidence drawn from the numbered passages and \
the chart facts. Preserve all [Ref N] anchors from the prior draft that \
remain applicable; add new [Ref N] anchors where the rewrite leans on \
additional doctrinal evidence. Do NOT reintroduce the patterns the \
critic flagged."""


# ─── Synthesizer ────────────────────────────────────────────────────


class PanditSynthesizer:
    """Driver that calls the LLM with the assembled prompt and parses the
    response into a ``PanditReading``.

    The synthesizer is intentionally thin — the prompt does the heavy
    lifting. Future phases (Critic, Refinement) will subclass or compose
    around this class without disturbing the Draft contract.
    """

    def __init__(self, llm: LLMClient, enable_critic: bool = False) -> None:
        self.llm = llm
        self.enable_critic = enable_critic

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

        # Parse [Bhrigu N] anchors — distinct namespace from [Ref N]
        bhrigu_ids = set(
            int(m) for m in re.findall(r"\[Bhrigu (\d+)\]", narrative)
        )
        bhrigu_cited = tuple(
            p for p in corpus.bhrigu_passages if p.ref_id in bhrigu_ids
        )

        # Surface model name when the client exposes it; otherwise unknown
        model_name = getattr(self.llm, "model", "unknown")

        return PanditReading(
            narrative=narrative,
            citations_used=cited,
            unused_passages=uncited,
            prompt_token_estimate=token_estimate,
            focal_themes=focal_themes,
            model=model_name,
            bhrigu_citations_used=bhrigu_cited,
        )

    def synthesize_with_critic(
        self,
        corpus: RetrievedCorpus,
        focal_themes: tuple[str, ...] = (),
    ) -> RefinedReading:
        """Three-pass pipeline: Draft → Critic → (optional) Refinement.

        When ``enable_critic`` is False (default), this method returns the
        draft alongside a dummy 10/10 review with zero passes used beyond
        the draft synthesis, skipping the critic LLM call entirely.

        When enabled, the critic adversarially scores the draft on
        specificity, citation density, this-chart grounding, and doctrinal
        accuracy. If the overall score is at least 8.0 OR the critic
        produces no must-fix items, the draft is returned as-is. Otherwise
        a refinement pass rewrites the draft using the must-fix list as
        constraints.
        """
        draft = self.synthesize(corpus, focal_themes=focal_themes)

        if not self.enable_critic:
            dummy = CriticReview(
                specificity_score=10,
                citation_density_score=10,
                this_chart_grounding_score=10,
                doctrinal_accuracy_score=10,
                overall_score=10.0,
                weaknesses=(),
                must_fix=(),
                raw_critique="(critic disabled)",
            )
            return RefinedReading(
                draft=draft,
                critic_review=dummy,
                refined=None,
                passes_used=1,
            )

        critic_prompt = build_critic_prompt(draft, corpus)
        raw_critique = self.llm.complete(critic_prompt)
        review = _parse_critic_review(raw_critique)

        if review.overall_score >= 8.0 or not review.must_fix:
            return RefinedReading(
                draft=draft,
                critic_review=review,
                refined=None,
                passes_used=1,
            )

        refinement_prompt = build_refinement_prompt(corpus, draft, review)
        refined_narrative = self.llm.complete(refinement_prompt)

        cited_ids = set(
            int(m) for m in re.findall(r"\[Ref (\d+)\]", refined_narrative)
        )
        cited = tuple(p for p in corpus.passages if p.ref_id in cited_ids)
        uncited = tuple(
            p for p in corpus.passages if p.ref_id not in cited_ids
        )
        bhrigu_ids = set(
            int(m) for m in re.findall(r"\[Bhrigu (\d+)\]", refined_narrative)
        )
        bhrigu_cited = tuple(
            p for p in corpus.bhrigu_passages if p.ref_id in bhrigu_ids
        )
        model_name = getattr(self.llm, "model", "unknown")

        refined = PanditReading(
            narrative=refined_narrative,
            citations_used=cited,
            unused_passages=uncited,
            prompt_token_estimate=len(refinement_prompt) // 4,
            focal_themes=focal_themes,
            model=model_name,
            bhrigu_citations_used=bhrigu_cited,
        )

        return RefinedReading(
            draft=draft,
            critic_review=review,
            refined=refined,
            passes_used=2,
        )


__all__ = [
    "PanditReading",
    "PanditSynthesizer",
    "CriticReview",
    "RefinedReading",
    "SYSTEM_PROMPT",
    "CRITIC_SYSTEM_PROMPT",
    "build_prompt",
    "build_critic_prompt",
    "build_refinement_prompt",
]
