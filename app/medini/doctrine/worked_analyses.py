"""Raman's worked-chart ANALYSIS prose as style/reasoning exemplars (Track C).

The rule-compendium (`compendium.py`) holds Raman's atomic significations; it does NOT hold
his *worked-chart analyses* — the running reasoning by which he weighs one testimony against
another and delivers a verdict on an actual horoscope. That prose is what makes an
interpretation read like Raman. This module loads the extracted, verbatim, sha256-verified
exemplar corpus (`data/raman_doctrine/worked_analyses.jsonl`) and formats a few house-matched
exemplars for few-shot grounding of the LLM interpreter (`interpret.py`).

The exemplars teach IDIOM and REASONING ORDER only (bhava -> lord -> karaka -> Chandra Lagna
-> conclusion; Rasi then Navamsa; "This is good/bad" -> "Hence ... is <verdict>"). They are
never a source of chart facts -- the grounding contract still binds every claim to the engine's
own evidence.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CORPUS = (Path(__file__).resolve().parents[3]
           / "data/raman_doctrine/worked_analyses.jsonl")


@lru_cache(maxsize=1)
def load_exemplars(path: str | None = None) -> list[dict]:
    """All worked-chart analyses (the leading line is corpus metadata, skipped)."""
    p = Path(path) if path else _CORPUS
    out: list[dict] = []
    for i, line in enumerate(p.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if i == 0 and "analysis_text" not in rec:      # metadata header
            continue
        out.append(rec)
    return out


def exemplars_for(houses: list[int], k: int = 2,
                  path: str | None = None) -> list[dict]:
    """Up to ``k`` exemplars, preferring ones that (a) judge one of ``houses`` and (b)
    carry an explicit verdict sentence (the richest style samples). Deterministic order."""
    pool = load_exemplars(path)
    want = set(houses)
    scored = sorted(
        pool,
        key=lambda r: (r["house"] not in want,            # matching house first
                       not r.get("verdict_sentences"),     # then ones with a verdict sentence
                       r["chart_no"] or 0),                # stable tie-break
    )
    return scored[:k]


def exemplar_block(houses: list[int], k: int = 2, path: str | None = None) -> str:
    """A framed few-shot block for the interpreter's system prompt: Raman's verbatim
    analyses under an explicit STYLE-ONLY contract. Empty string if the corpus is absent."""
    try:
        picks = exemplars_for(houses, k=k, path=path)
    except FileNotFoundError:
        return ""
    if not picks:
        return ""
    parts = [
        "=== STYLE EXEMPLARS — B. V. Raman's own worked-chart analyses ===",
        "These are verbatim passages of Raman analysing real horoscopes. Imitate their "
        "REASONING ORDER and IDIOM only (bhava, then lord, then karaka; Rasi then Navamsa; "
        "plain 'this is good / this is bad' observations resolving into 'Hence the ... is "
        "<verdict>'). They are NOT facts about the current chart — never import a placement, "
        "planet, or verdict from an exemplar. Ground every claim in the engine evidence, as "
        "the rules above require.",
    ]
    for r in picks:
        parts.append(f"\n[Raman, {r['book'].replace('htjah_','HTJAH ').upper()}, "
                     f"{r['house']}th-house chart {r['chart_no']}]\n{r['analysis_text']}")
    return "\n".join(parts)
