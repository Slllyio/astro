# Claude as the Raman reader: pre-registration addendum (2026-11-03)

Written and committed before any Claude call. The user chose "Try Claude as the writer" after the
14B result (201/262 vs count 171, but chart-blind matter rule 197; see the main prereg's
2026-11-02 addendum). Code: tools/raman_llm/claude_reader.py.

## Set-up (fixed now)
- Rows: the same 262 hold-out conclusions (H1-H5), same prompts as the 14B saw (the clause judge's
  verdict still left out).
- Model claude-opus-5-5, adaptive thinking, effort high, JSON output (verdict, reasons,
  conclusion), Message Batches API, one pass, no retries on content.
- 16 worked examples per row: 6 on the same matter, 10 others, seeded (20261103), drawn only from
  other folds AND never from the same nativity (lagna + nine planet signs). This removes the
  nativity leak the 14B run had.
- No training, no prompt tuning on any score. requests.jsonl is written before submission and
  committed with the results.
- A refusal, error or unparsable answer counts as wrong.

## Bar
Primary: exact verdicts on the 262 rows against the chart-blind matter rule (most common verdict
for the matter in the other folds), exact two-sided McNemar.
- SIGNAL: Claude > matter rule, p < 0.05. Only this would show reading the chart beyond the
  per-matter base rate.
- WORSE: Claude < matter rule, p < 0.05.
- otherwise NULL.
Secondary, always reported: vs count B3 (171), vs Qwen3-14B (201), H4+H5, nativity-clean rows,
real errors.

Expected (written now): NULL. Same input, same limits; the matter rule already gets 197.

## Known caveat
Claude may have read Raman's books in pre-training. The prompt carries no names, ids or dates, and
Claude is told not to identify natives or use remembered charts, but recognition from planet
positions cannot be ruled out. A gain over the matter rule would need that caveat beside it.

## Prose
Reported: distinct conclusions, median length, and a blind packet (Raman's words vs Claude's)
for a human reader. No one has judged it blind at the time of writing.
