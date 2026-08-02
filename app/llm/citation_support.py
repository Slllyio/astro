"""Citation SUPPORT — does the cited [Fact N] actually contain what the sentence asserts?

`provenance_check` (`report_explainer.py`) answers a different question: does every paragraph
carry SOME valid citation? It scores citation *presence*. It is blind to a sentence that cites
[Fact 4] while asserting a number, planet, sign, nakshatra or yoga that lives in [Fact 7] — or
in no fact at all.

Measured on the Phase-2 teacher corpus (2026-08-02, 588 teacher rows): **12.8%** of checkable
single-cite sentences cited a fact that did not contain the token they asserted, and **29.8%**
of rows carried at least one. Of the unsupported tokens, **78% were present in a DIFFERENT
fact** (mis-attribution — the claim is true of the evidence, the pointer is wrong) and **22% in
no fact at all** (fabrication). The student was trained on that distribution, which is why the
residual "cites a technically wrong [Fact N]" behaviour survived the Phase-7 evidence
decomposition: the training targets contained it.

The two failures get different treatment, so they are reported separately:

- `repair_citations` retargets a mis-attributed citation onto the fact that actually supports
  it. Deterministic and conservative: it NEVER invents a citation number, only ever moves or
  adds one that the evidence itself supports, and leaves the sentence untouched whenever the
  supporting fact is ambiguous rather than guessing.
- `audit_citations().unsupported` lists tokens no fact supports — the safety case, consumed by
  `refusal_reason` (a model asserting what the engine never computed is exactly what the guard
  exists to stop).

Deliberately conservative by construction, because a false "unsupported" would refuse a good
answer on a live surface:

- only sentences citing EXACTLY ONE fact are audited (a two-citation sentence has genuinely
  ambiguous attribution, and guessing which half belongs to which fact would invent errors);
- number-WORDS are never checked ("one of the clearest strengths", "three areas" are idiomatic
  English, not assertions of a count — scoring them produced only false positives);
- numbers >= 10 match within +-1 to survive the engine's own rounding ("about 72 years" against
  72.4), while numbers < 10 must match exactly, since those are house numbers and witness counts
  where a near-miss is precisely the error being hunted.

Usage:
    audit = audit_citations(answer_text, evidence)
    if audit.unsupported:          # nothing in the evidence backs these
        ...
    repaired, n = repair_citations(answer_text, evidence)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from app.core.nakshatra import NAKSHATRAS

#: The closed entity vocabulary a claim can be checked against. Planets and signs are duplicated
#: here rather than imported from `app/raman_saab/judges/house_template.py` on purpose: this is
#: the LLM safety layer, which consumes only the report DICT and must not pull the judges package
#: into its import graph. They are fixed cosmological names, not tunable doctrine.
PLANETS: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                            "Saturn", "Rahu", "Ketu")
SIGNS: tuple[str, ...] = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
#: NOT grahas in Raman's system — the engine never computes them, so no fact can ever support
#: one, and a model that drags one in from its general astrology training is asserting something
#: the engine did not say. Kept in their own tuple rather than folded into PLANETS so the
#: doctrine stays honest: these are CHECKED, never recognised as bodies the system reads.
NON_VEDIC_BODIES: tuple[str, ...] = ("Uranus", "Neptune", "Pluto", "Chiron", "Lilith")

_FACTREF_RE = re.compile(r"\[(Fact|Ref) (\d+)\]", re.I)
_FACT_CITE_RE = re.compile(r"\[Fact (\d+)\]", re.I)
_SENT_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")
_NUM_RE = re.compile(r"\b(\d{1,4})\b")
_YOGA_RE = re.compile(r"\b([A-Z][\w-]+(?: [A-Z][\w-]+)?) Yoga\b")

#: below this, a number is a house/count/pada where a near-miss IS the error; at or above it, a
#: number is an age/year/percentage the engine itself rounds when it renders prose.
_ROUNDING_FLOOR = 10


class _HasFacts(Protocol):
    """Structural view of `report_explainer.Evidence` — kept structural so this module never
    imports the explainer that imports it."""

    facts: Sequence


@dataclass(frozen=True)
class CitationAudit:
    """One answer's citation-support trace.

    `mis_attributed` and `unsupported` hold `(token, cited_fact_n)` pairs; `mis_attributed`
    additionally carries the fact that DOES support the token (None when several do, i.e. the
    attribution is real but ambiguous)."""

    mis_attributed: tuple[tuple[str, int, Optional[int]], ...] = ()
    unsupported: tuple[tuple[str, int], ...] = ()
    checked_sentences: int = 0

    @property
    def is_clean(self) -> bool:
        return not self.mis_attributed and not self.unsupported


def checkable_tokens(sentence: str) -> frozenset[str]:
    """The assertions in `sentence` whose presence in the cited fact is checkable: integers
    (as ``#N``), planet / sign / nakshatra names, and yoga names. Citation markers are stripped
    first so their own digits are never harvested as claims."""
    body = _FACTREF_RE.sub(" ", sentence)
    toks: set[str] = {f"#{int(n)}" for n in _NUM_RE.findall(body)}
    for name in (*PLANETS, *NON_VEDIC_BODIES, *SIGNS, *NAKSHATRAS):
        if re.search(rf"\b{re.escape(name)}\b", body):
            toks.add(name)
    toks.update(f"{y} Yoga" for y in _YOGA_RE.findall(body))
    return frozenset(toks)


def fact_supports(token: str, fact_text: str) -> bool:
    """True iff `fact_text` carries `token` (see the module docstring for the rounding rule)."""
    if not token.startswith("#"):
        return re.search(rf"\b{re.escape(token)}\b", fact_text, re.I) is not None
    value = int(token[1:])
    numbers = [int(n) for n in _NUM_RE.findall(fact_text)]
    if value in numbers:
        return True
    return value >= _ROUNDING_FLOOR and any(abs(n - value) <= 1 for n in numbers)


def _facts_of(ev: _HasFacts) -> dict[int, str]:
    return {f.n: f.text for f in ev.facts}


def _audited_sentences(text: str, facts: dict[int, str]):
    """Yield `(sentence, cited_n, tokens)` for every sentence with exactly one [Fact N] whose
    N is real and which asserts at least one checkable token."""
    for sentence in _SENT_RE.findall(text):
        cites = {int(n) for n in _FACT_CITE_RE.findall(sentence)}
        if len(cites) != 1:
            continue
        cited = cites.pop()
        if cited not in facts:
            continue                      # a bogus N is already `bad_anchors`' job
        tokens = checkable_tokens(sentence)
        if tokens:
            yield sentence, cited, tokens


def audit_citations(text: str, ev: _HasFacts) -> CitationAudit:
    """Trace every checkable claim in `text` to the fact it cites."""
    facts = _facts_of(ev)
    mis: list[tuple[str, int, Optional[int]]] = []
    unsupported: list[tuple[str, int]] = []
    checked = 0
    for _sentence, cited, tokens in _audited_sentences(text, facts):
        checked += 1
        for token in sorted(tokens):
            if fact_supports(token, facts[cited]):
                continue
            supporters = [n for n, t in facts.items() if fact_supports(token, t)]
            if not supporters:
                unsupported.append((token, cited))
            else:
                mis.append((token, cited, supporters[0] if len(supporters) == 1 else None))
    return CitationAudit(mis_attributed=tuple(mis), unsupported=tuple(unsupported),
                         checked_sentences=checked)


def repair_citations(text: str, ev: _HasFacts) -> tuple[str, int]:
    """Retarget mis-attributed citations onto the facts that support them.

    Returns `(repaired_text, sentences_changed)`. Two moves, in order of preference:

    1. **Replace** — when ONE other fact supports every checkable token in the sentence, the
       citation was simply pointing at the wrong line; swap it.
    2. **Append** — when the sentence legitimately draws on more than one fact (the cited one
       supports some tokens, another supports the rest), add the supporting citation rather
       than moving it, so both claims are anchored.

    A token supported by several facts, or by none, is left alone — the first is genuinely
    ambiguous and the second is fabrication, which repair must never paper over."""
    facts = _facts_of(ev)
    out = text
    changed = 0
    for sentence, cited, tokens in _audited_sentences(text, facts):
        unsupported = [t for t in tokens if not fact_supports(t, facts[cited])]
        if not unsupported:
            continue
        # (1) one fact that covers the WHOLE sentence -> the citation was simply misaimed.
        whole = [n for n, t in facts.items()
                 if n != cited and all(fact_supports(tok, t) for tok in tokens)]
        if len(whole) == 1:
            fixed = _FACT_CITE_RE.sub(f"[Fact {whole[0]}]", sentence)
        else:
            # (2) add the unambiguous supporter of each unsupported token.
            extra: set[int] = set()
            for token in unsupported:
                supporters = [n for n, t in facts.items() if fact_supports(token, t)]
                if len(supporters) == 1:
                    extra.add(supporters[0])
            if not extra:
                continue
            marker = f"[Fact {cited}]"
            addition = " " + " ".join(f"[Fact {n}]" for n in sorted(extra))
            fixed = sentence.replace(marker, marker + addition, 1)
        if fixed != sentence:
            out = out.replace(sentence, fixed, 1)
            changed += 1
    return out, changed
