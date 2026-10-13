# Golden-corpus pipeline — design

**Date:** 2026-10-13 · **Status:** approved design, not yet implemented
**Goal:** turn the 2026-08-23 one-off adjudication (94 DRAFT rows, four blind
`bphs-doctrine-reviewer` agents) into a repeatable, auditable pipeline that grows the
golden corpus — CLAUDE.md North Star Playbook rule 7: *"The accuracy lever now is the
GOLDEN CORPUS, not the judge."*

## Non-negotiables (from CLAUDE.md)

1. **Confirm what Raman CONCLUDED, regardless of whether the engine agrees.** Never
   confirm to pad, never withhold to protect the number.
2. **Conclusion, not observation.** A factor Raman is still weighing is never a verdict.
3. **A contested label never enters the scored pool.** Reviewer disagreement → HOLD.
4. **Blind review.** Reviewers never see engine output.
5. **Re-base deliberately, with lineage, user-signed.** The pipeline PROPOSES; only the
   user's explicit `apply` changes the scored pool or the baseline.

## Architecture — staged CLI over a file queue

```
tools/raman_saab/golden_pipeline/
  __main__.py      CLI: extract | packets | ingest | propose | apply | status
  extract.py       local gemma4:12b: book section -> DRAFT candidate rows
  splice_check.py  deterministic checks (+ gemma fallback) for the 3 known splice classes
  packets.py       writes one self-contained reviewer packet per row per reviewer
  ingest.py        validates answers: schema, verbatim quote, then reconcile
  reconcile.py     pure function: two answers -> CONFIRM | REVISE | REJECT | HOLD
  propose.py       ONLY stage that runs the engine; writes proposal.md + projected ratchet
  apply.py         writes approved verdict_review changes + baseline re-base + backlog entry
.claude/agents/golden-reviewer.md   Read-only reviewer subagent
data/pipeline_runs/<run_id>/         manifest.json + one JSONL/dir per stage (gitignored)
```

Each stage reads the previous stage's file and writes its own; every stage is idempotent
per row id, so a crashed run resumes by re-running the stage.

### Flow

```
extract (gemma, $0) -> splice_check -> packets
  -> [Claude Code session: 2 blind golden-reviewer subagents per packet, $0 API]
  -> ingest (quote check + reconcile) -> propose (engine) -> USER SIGN-OFF -> apply
```

## Extraction (local, $0)

- Python chunks the book text per worked chart, reusing the heading patterns in
  `tools/raman_saab/extract_htjah_goldens.py` / `extract_nh_goldens.py` (reuse, not rewrite).
- gemma4:12b emits rows conforming to `docs/raman_saab/golden_schema.md`, always
  `verdict_review: "DRAFT"`. Requires `REPORT_LLM_THINK=false`, `REPORT_LLM_NUM_CTX=8192`
  (without them gemma returns empty output — CLAUDE.md).
- Output is untrusted: schema-validated, and `stated_positions` cross-checked against a
  deterministic re-parse of the printed planet table. Failures are dropped and logged.
- Ollama unavailable / empty response → the stage fails loudly and writes nothing.

## Splice checks

| Class | Deterministic test | Known instance |
|---|---|---|
| Footnote | prose overlaps a footnote region | NH.chart_5 (inverted polarity) |
| Section heading | prose spans a heading; signification taken from it | HTJAH-I.x75 |
| Two-passage | prose drawn from non-adjacent ranges, dropping an interleaved hedge | NH.chart_41 H10 |

Flagged rows go to review **with the flag attached** (reviewer may REJECT as `splice`);
they are never silently dropped.

## Reviewer contract

**Packet contents** (built by Python, which does not import the judge at this stage):
candidate `{book, citation line, signification, proposed verdict, verdict_prose}`, the
printed source passage (cited line ± 40), the ordinal scale
`afflicted < mixed < favourable`, and the single question:

> Is this Raman's CONCLUSION about the matter, or an OBSERVATION about one contributing
> factor he is still weighing?

**Never in a packet:** engine output, the other reviewer's answer, any fidelity figure.
Reviewers A and B get differently-worded prompts with the identical question and schema.

**Answer schema** (the subagent's final message, strict JSON):

```json
{"decision": "CONFIRM|REVISE|REJECT",
 "kind": "conclusion|observation|splice|not_found",
 "verdict": "afflicted|mixed|favourable",
 "signification": "...",
 "decisive_quote": "<= 40 words, verbatim",
 "quote_line": 6013,
 "reason": "one sentence"}
```

**Reviewer agent** `.claude/agents/golden-reviewer.md`: tools = `Read` only. Fresh context
per packet. The dispatching session saves each reply to `answers/<row_id>.<A|B>.json`.

## Ingest and reconcile (pure Python)

1. Schema-invalid answer → HOLD (`reason: invalid_answer`).
2. `decisive_quote` not found verbatim in the source within a small window of
   `quote_line` → HOLD (`kind: not_found`). This makes every claim falsifiable by string
   search.
3. Either reviewer REJECT → row stays DRAFT.
4. Both CONFIRM/REVISE with identical decision, verdict and signification → that outcome.
5. Any other disagreement → HOLD.
6. Missing answer → listed by `packets --missing` for re-dispatch.

**Invariant:** every failure path ends in HOLD or DRAFT, never CONFIRM.

## Propose

The only stage that runs the engine. Writes `proposal.md`: per row, Raman's decisive quote
and line, the reconciled verdict, the engine's verdict, and the projected ratchet movement
on **both** axes side by side (exact and within-1) — never averaged.

## Apply (user-signed)

- Refuses unless the git tree is clean (prevents mixing with another session's edits).
- Changes only `verdict_review` (and REVISE'd verdict/signification) for the approved ids
  in `tests/fixtures/raman_goldens.jsonl`.
- Re-runs the ratchet, writes the new floor to `tests/fixtures/golden_accuracy_baseline.json`
  with a `_comment` recording run id, date, and "user-signed".
- Appends a `docs/raman_saab/DOCTRINE_BACKLOG.md` entry with CONFIRM/REVISE/REJECT/HOLD
  tables in the 2026-08-23 format.

## Testing (`tests/raman_saab/test_golden_pipeline.py`, no live model)

| Test | Proves |
|---|---|
| `test_packet_contains_no_engine_output` | Blindness by construction |
| `test_quote_not_in_source_goes_to_hold` | A fabricated quote cannot confirm |
| `test_reviewers_disagree_goes_to_hold` | Contested labels are never scored |
| `test_either_reject_keeps_draft` | Asymmetric gate |
| `test_splice_footnote/heading/two_passage` | Fixtures: NH.chart_5, HTJAH-I.x75, NH.chart_41 |
| `test_apply_refuses_dirty_tree` | No cross-session mixing |
| `test_apply_only_touches_verdict_review` | Minimal, auditable writes |
| `test_rerun_is_idempotent` | Crash-safe resume |

**Acceptance check before trusting the pipeline:** re-run it on the 94 rows adjudicated
2026-08-23 and compare decisions. Agreement is the evidence; every divergence is read by
hand and recorded.

## Out of scope (YAGNI)

- Claude API / Agent SDK reviewer backend (user has a $10 credit; subagents cost $0).
  Add behind the same packet/answer files if automation is needed later.
- Auto-apply of any kind.
- New books beyond HTJAH-I/II and NH until the 94-row acceptance check passes.
