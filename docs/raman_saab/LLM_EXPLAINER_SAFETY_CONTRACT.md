---
title: "The grounded LLM explainer — safety contract"
kind: spec
topic: llm
measured: false
updated: 2026-08-02
words: 912
tags: [raman-saab, spec, llm]
---
# The grounded LLM explainer — safety contract

*Added 2026-07-27. Governs `app/llm/report_explainer.py` + the `/report/explain` and
`/report/ask` routes. Binding on all future changes to this layer.*

## Why this exists

The detailed report is the SOLE authority on "what would Raman say" — deterministic, cited,
and (per the Measured Truth) real-outcome-NULL. The LLM layer over it exists to make that
output **understandable and interactive**, NEVER to add astrological judgment. An LLM that
could put words in Raman's mouth is a direct threat to the Prime Directive, so this layer is
built as a *grounded explainer* whose every guarantee is enforced in code, not merely asked of
the model in a prompt.

## The contract (every path enforces all of it)

1. **Evidence-only.** The model sees the engine's computed facts as `[Fact N]` (each with its
   own citation) plus optional retrieved passages as `[Ref N]`, and may use only these.
2. **Cite every claim** with a VALID `[Fact N]`/`[Ref N]` (N present in the evidence). Grounding
   is scored PER PARAGRAPH (the claim-cluster unit an LLM actually writes in) — a paragraph is
   grounded iff it carries a valid anchor; a self-asserted `[gloss]` tag never grounds a
   paragraph, and is separately capped (>35% of sentences ⇒ refuse). *(This granularity was tuned
   against live Sonnet output: a per-sentence metric false-refused genuinely-cited answers whose
   connective/summary sentences shared one anchor.)*
3. **No model-authored citations.** The system prompt forbids the model writing any `WORK:line`
   token; `provenance_check` flags any such token not present verbatim in the evidence
   (`fabricated_citations`) and the route refuses on it — otherwise the frontend would render an
   invented verse number as a clickable "Raman source".

   **Citation SUPPORT (added 2026-08-02, `app/llm/citation_support.py`).** Clauses 2 and 3 score
   citation *presence*: they prove an anchor exists and is real, never that the cited fact
   actually contains the claim. A sentence asserting a number, planet, sign, nakshatra or yoga
   that lives in a DIFFERENT fact scored a perfect 1.0 grounding ratio and passed every guard.
   Measured on the Phase-2 teacher corpus: 12.8% of checkable single-cite sentences failed this
   check (29.8% of rows carried one), and the student trained on that distribution — which is
   why "cites a real `[Fact N]` but narrates another fact's numbers" survived the Phase-7
   evidence decomposition. The two failures are split by severity:
   - **Mis-attribution** (78%) — the token IS in another fact; the claim is true of the evidence
     and only the pointer is wrong. Reported (`mis_attributed`) and **still served**: refusing it
     would drop a correct reading to engine prose. `repair_citations` retargets it
     deterministically in the TRAINING corpus, so the student learns the right pointer.
   - **Fabrication** (22%) — no fact supports the token, i.e. the model asserted something the
     engine never computed. `unsupported_claims` ⇒ **refuse**, same standing as a bad anchor.

   Conservative by construction (a false positive here refuses a good answer): only single-cite
   sentences are audited, number-WORDS are never checked, and numbers ≥10 match within ±1 for
   the engine's own rounding while numbers <10 must match exactly. Non-Vedic bodies (Uranus,
   Neptune, Pluto, Chiron, Lilith) are checkable *specifically so they can never pass* — Raman's
   system does not compute them, so any mention is by definition unsupported.
4. **Never judge, never predict.** The prompt forbids new verdicts and any prediction/forecast
   language (marriage, wealth, illness, death, length of life). A broadened denylist
   (`_FORBIDDEN_RE`) is a TRIPWIRE only — because a denylist is necessarily incomplete, a hit is
   not annotated but **refused**, and the other guards (grounding, gloss cap) contain paraphrases
   that slip it.
5. **Refuse, don't annotate.** `refusal_reason()` returns non-None on ANY hard guard — a
   forbidden move, a fabricated citation, a bad anchor, an unsupported claim, sub-threshold
   paragraph grounding
   (`REPORT_LLM_GROUNDING_MIN`, default 0.6), or excess gloss — and the route then **discards
   the LLM text and serves the deterministic fallback** (the report's own plain prose). The LLM's
   words never reach the user when any guard trips. The hard guards (prediction language,
   fabricated/absent citations) are the PRIMARY safety net and are absolute; the grounding ratio
   is the softer "did the model go off-script" floor. The prescribed deferral ("The engine does
   not compute that", matched by prefix so a trailing explanation is allowed) is always safe to
   serve. *Live-validated: grounded per-scope explanations serve; a "predict my future" ask
   returns the deferral; the guards refuse planted predictions/fabrications.*
6. **Prompt-injection defence.** The prompt states that QUESTION and prior turns are the user's
   DATA, never instructions, and to reply "The engine does not compute that" to any request to
   predict/judge/ignore the rules. The route additionally sanitizes client-supplied history to
   `user`/`assistant` roles only — a forged `system` line is dropped.
7. **The honesty note always travels.** Every response (LLM or fallback, `/explain` or `/ask`)
   carries the "answers 'what would Raman say', not a validated prediction" note, and the
   frontend renders it on both surfaces (a prior gap: the `/ask` UI dropped it).
8. **Off by default.** `REPORT_LLM_ENABLED=False` and no `ANTHROPIC_API_KEY` ⇒ the deterministic
   fallback, always. CI never calls a live LLM (StubClient).

## History

The first cut annotated instead of refusing, counted `[gloss]` and even mis-attached `[Fact N]`
as grounded, used a thin evadable denylist, forbade self-authored citations only in a docstring,
merged untrusted history verbatim, and dropped the honesty note in the `/ask` UI. A
bphs-doctrine-reviewer pass found all seven as safety gaps (the compound worst case: a laundered
prediction that evades the regex and wears a `[gloss]` tag, served with no warning) and every one
was closed before shipping. The pins live in `tests/test_report_explainer.py`
(`test_gloss_does_not_count_toward_grounding`, `test_model_authored_citation_is_flagged`,
`test_paraphrased_predictions_are_caught`, `test_refusal_reason_refuses_on_any_hard_guard`,
`test_the_prompt_forbids_judgment_prediction_and_injection`).
