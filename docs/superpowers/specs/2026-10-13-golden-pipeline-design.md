# Golden-corpus pipeline — design

**Date:** 2026-10-13 · **Status:** approved design, revised after spec review, not yet implemented
**Goal:** turn the 2026-08-23 one-off adjudication (94 DRAFT rows, four blind
`bphs-doctrine-reviewer` agents) into a repeatable, auditable pipeline that grows the
golden corpus — CLAUDE.md North Star Playbook rule 7: *"The accuracy lever now is the
GOLDEN CORPUS, not the judge."*

## Non-negotiables (from CLAUDE.md)

1. **Confirm what Raman CONCLUDED, regardless of whether the engine agrees.** Never
   confirm to pad, never withhold to protect the number.
2. **Conclusion, not observation.** A factor Raman is still weighing is never a verdict.
3. **A contested label never enters the scored pool.** The pipeline uses only the states
   that already exist in `tests/raman_saab/test_goldens.py:53-58`:
   `{DRAFT, CONFIRMED, DUPLICATE, CONTESTED}`. No new states.
4. **Blind review.** Reviewers never see engine output.
5. **Re-base deliberately, with lineage, user-signed.** The pipeline PROPOSES; only the
   user's explicit `apply` changes the scored pool or the baseline.

## Architecture — staged CLI over a file queue

```
tools/raman_saab/golden_pipeline/
  __main__.py      CLI: extract | packets | ingest | propose | apply | status
  extract.py       calls the existing deterministic extractors; gemma fallback
  splice_check.py  imports the existing splice guards from extract_htjah_goldens.py
  packets.py       writes one self-contained reviewer packet per row per reviewer
  ingest.py        validates answers: schema, normalised quote match, then reconcile
  reconcile.py     pure function: answers -> CONFIRMED | REVISE | DRAFT(rejected) | tiebreak | CONTESTED
  propose.py       ONLY stage that runs the engine; writes proposal.md + projected ratchet
  apply.py         line-level writes of approved changes + snapshots + baseline lineage
.claude/agents/golden-reviewer.md   Read-only reviewer subagent
data/pipeline_runs/<run_id>/         manifest.json + one JSONL/dir per stage (gitignored)
```

Each stage reads the previous stage's file and writes its own; every stage is idempotent
per row id, so a crashed run resumes by re-running the stage.

### Flow

```
extract ($0) -> splice_check -> packets
  -> [Claude Code session: 2 blind golden-reviewer subagents per packet, $0 API]
  -> ingest (quote check + reconcile) -> [tiebreak packets if split] -> propose (engine)
  -> USER SIGN-OFF -> apply
```

## Extraction (deterministic first, local gemma as fallback, $0)

- **Primary:** the existing extractors `tools/raman_saab/extract_htjah_goldens.py` and
  `extract_nh_goldens.py` already chunk per chart and emit DRAFT verdicts deterministically
  via `classify_prose`. The pipeline calls them; it does not replace them.
- **Fallback only:** gemma4:12b handles prose `classify_prose` cannot classify, and books
  with no extractor yet. Output is always `verdict_review: "DRAFT"`, schema-validated, and
  `stated_positions` cross-checked against a deterministic re-parse of the printed planet
  table. Requires `REPORT_LLM_THINK=false`, `REPORT_LLM_NUM_CTX=8192` (without them gemma
  returns empty output — CLAUDE.md). Ollama unavailable → the stage fails loudly, writes
  nothing.
- **Source text:** `data/knowledge_library/sources/<book>/chapter_001_full-text-unsplit.md`
  (gitignored; present only in the main checkout's `data/`). The CLI takes `--sources-root`
  and fails loudly if the file is missing. Citation line numbers resolve against it.
- Rows whose `review_note` begins `REJECTED` are skipped — already adjudicated, never
  re-queued.

## Splice checks

Reuse, not rewrite: `_SECTION_HEADING`, `_FOOTNOTE` and `_conclusion()` in
`extract_htjah_goldens.py:448-490` already guard the known classes. `splice_check.py`
imports them and adds a two-passage check only if not already covered.

| Class | Known instance (test fixture = pre-fix prose from git history) |
|---|---|
| Footnote | NH.chart_5 (inverted polarity; since re-extracted) |
| Section heading | HTJAH-I.x75 (since CONFIRMED) |
| Two-passage | NH.chart_41 H10 (dropped hedge) |

Flagged rows go to review **with the flag attached** (reviewer may REJECT as `splice`);
they are never silently dropped.

## Reviewer contract

**Packet contents** (built by Python, which does not import the judge at this stage):
candidate `{book, citation (a line OR a range such as HTJAH-I:1177-1195), signification,
proposed verdict, verdict_prose}`, the printed source passage (the cited span ± 40 lines),
the ordinal scale `afflicted < mixed < favourable`, and the single question:

> Is this Raman's CONCLUSION about the matter, or an OBSERVATION about one contributing
> factor he is still weighing?

**Never in a packet:** engine output, any other reviewer's answer, any fidelity figure.
Reviewers A, B (and C for tiebreak) get differently-worded prompts with the identical
question and schema.

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
per packet. The dispatching session saves each reply to `answers/<row_id>.<A|B|C>.json`.

## Ingest and reconcile (pure Python)

1. Schema-invalid answer → treated as missing (re-dispatch).
2. `decisive_quote` not found in the source near `quote_line` → row stays DRAFT
   (`kind: not_found`). Matching is on **normalised** text — case-folded, whitespace and
   line breaks collapsed, de-hyphenated across wraps — because the source is OCR with hard
   wraps. This keeps every claim falsifiable by string search.
3. Both REJECT → stays DRAFT with `review_note: "REJECTED by engine-blind review (run <id>) …"`
   so it is never re-queued. **Exception (pilot 2026-10-13):** when every agreeing (or
   2-of-3 majority) REJECT has `kind: not_found`, the outcome is `NOT_FOUND` — the reviewers
   saw no conclusion *in the window*, which indicts the window, not the label. NOT_FOUND is
   non-writable: no note, row stays a live DRAFT, re-queued once its window is fixed.
   REJECT with kind observation/splice stays REJECTED.
4. Identical outcome — both accept (CONFIRM or REVISE) with the same verdict and signification (case-insensitive), and every accepting answer must have kind = conclusion → that outcome.
5. Any split (including a single REJECT) → `packets --tiebreak` writes a third packet
   (reviewer C). 2-of-3 agreement decides, per the NH.chart_38 H9 precedent (2026-08-29).
   No 2-of-3 majority → `CONTESTED`.
6. Missing answer → listed by `packets --missing` for re-dispatch.

**Invariant:** every failure path ends in DRAFT or CONTESTED, never CONFIRMED.

**HTJAH packet windows (pilot 2026-10-13).** In *How to Judge a Horoscope* Raman discusses a
chart BEFORE its `Chart No. N.—Born …` line, so a `chart_header` window runs from just after
the previous presentation header, through the record's own header, to the next presentation
header (≤ 200 lines before the header, ≤ 250 in total, own header always inside). A
presentation needs "Born" (OCR "Bom", "Male born") directly after its number; a mention such
as "In Chart No. 98, the native was born" is not one. When a verbatim opening repeats inside
the wider window, the whole prose decides first. NH windows and verbatim locates are unchanged.

## Propose

The only stage that runs the engine. Writes `proposal.md`: per row, Raman's decisive quote
and line, the reconciled verdict, the engine's verdict, and the projected ratchet movement
on **both** axes side by side (exact and within-1) — never averaged.

## Apply (user-signed)

- Refuses unless the git tree is clean (prevents mixing with another session's edits).
- Changes only `verdict_review`, `review_note` (the adjudication record), and REVISE'd
  verdict/signification, for the approved ids in `tests/fixtures/raman_goldens.jsonl`.
- **CONFIRMED rows store Raman's quoted conclusion (user decision 2026-10-13):**
  `verdict_prose` becomes the longest source-verified `decisive_quote` among the agreeing
  answers, and the appended `review_note` ends `prior extracted prose: "<old>"`. A CONFIRMED
  decision without a verified quote is refused.
- Refuses every non-writable outcome (INCOMPLETE, UNVERIFIED, TIEBREAK, NOT_FOUND,
  NOT_LOCATED); acceptance scoring reports NOT_FOUND as itself, never as REJECT.
  Edits are **line-level** — the file contains `#` comment blocks that a load-and-dump
  would destroy.
- Writes snapshots for newly confirmed rows (`UPDATE_RAMAN_SNAPSHOTS=1`) into
  `tests/fixtures/golden_snapshots/`; otherwise the snapshot test silently skips them.
- Runs `test_goldens.py` and `test_golden_verdict_uniqueness.py` (one verdict per
  nativity × matter; DUPLICATE handling), and checks `rule_liveness_baseline.json`.
- Updates **both** floors in `tests/fixtures/golden_accuracy_baseline.json` (`track_b` and
  `track_b_ordinal`), **appending** to `_comment` / `_comment_ordinal` lineage (run id,
  date, "user-signed") — never replacing it.
- Appends a `docs/raman_saab/DOCTRINE_BACKLOG.md` entry with **per-row** CONFIRM / REVISE /
  REJECT / CONTESTED tables (the 2026-08-23 entry recorded only aggregates; this fixes that).

## Testing (`tests/raman_saab/test_golden_pipeline.py`, no live model)

Tests use **committed source excerpts** as fixtures (the full books are gitignored).

| Test | Proves |
|---|---|
| `test_packet_contains_no_engine_output` | Blindness by construction |
| `test_quote_not_in_source_stays_draft` | A fabricated quote cannot confirm |
| `test_quote_match_survives_ocr_wraps` | A true quote across a hard wrap still matches |
| `test_split_triggers_tiebreak` | Disagreement never scores directly |
| `test_tiebreak_two_of_three` | Third reviewer resolves; no majority → CONTESTED |
| `test_rejected_rows_not_requeued` | Prior REJECTED notes are honoured |
| `test_splice_footnote/heading/two_passage` | Fixtures: pre-fix NH.chart_5, HTJAH-I.x75, NH.chart_41 |
| `test_apply_refuses_dirty_tree` | No cross-session mixing |
| `test_apply_edits_are_line_level` | `#` comments and untouched rows survive byte-for-byte |
| `test_apply_only_touches_review_fields` | Only verdict_review / review_note / REVISE'd fields change |
| `test_apply_updates_both_floors_appending_lineage` | Two-axis baseline, lineage preserved |
| `test_rerun_is_idempotent` | Crash-safe resume |

**Acceptance check before trusting the pipeline:** re-run it on the 94 rows adjudicated
2026-08-23 and compare decisions. The backlog records only aggregates (59/17/18), so the
answer key is rebuilt from `git diff 6517390^ 6517390 -- tests/fixtures/raman_goldens.jsonl`
(a verdict/signification change ⇒ REVISE), and pipeline inputs are the
**pre-adjudication** DRAFT rows at `6517390^` — later commits re-extracted NH.chart_5,
overturned HTJAH-II.chart_01 H7, and changed CONTESTED/DUPLICATE on 2026-08-29. Only 15
rows carry a REJECTED note versus the reported 18; the 3 unaccounted rejects are traced
before the check is scored. Agreement is the evidence; every divergence is read by hand and
recorded.

Also in scope: update the stale `docs/raman_saab/golden_schema.md`, which still lists only
DRAFT/CONFIRMED.

## Out of scope (YAGNI)

- Claude API / Agent SDK reviewer backend (user has a $10 credit; subagents cost $0).
  Can be added later behind the same packet/answer files.
- Auto-apply of any kind.
- New books beyond HTJAH-I/II and NH until the 94-row acceptance check passes.
