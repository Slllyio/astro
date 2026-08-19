# Held-out validation of the doctrine engine

Every accuracy figure from the calibration corpora (audit within-one ~78%) is on data
the engine was **tuned against**. This directory measures the engine on **worked charts
it has never seen**, against B. V. Raman's own printed verdicts in *How to Judge a
Horoscope* — the only honest feedback.

## What it validates
The **strength verdict** (bhāva / lord / kāraka on the 9-grade scale) reconstructed from
Raman's printed **Rāśi + Navāṁśa sign diagrams**. This isolates *our doctrine*: it needs
no degrees and no daśā (daśā drives timing, not strength), so there is no ephemeris or
timezone confound — the chart is rebuilt from exactly the positions Raman saw.

## Pipeline
1. **Extract** — `.claude/agents/raman-chart-extractor.md` (reusable subagent) parses a
   chapter's noisy OCR into `{rasi, navamsa, lagna, house_judged, verdicts:[{factor,phrase}]}`
   — **raw positions + raw verdict phrases only**, never engine features (independence).
2. **Reconstruct** — `app/medini/doctrine/validation/reconstruct.py`:
   `chart_from_raman` parks each planet at its printed Rāśi sign and back-solves the one
   navāṁśa **pada** whose D9 (the engine's own `calculate_divisional_longitude`) equals
   its printed Navāṁśa sign. Reproduces Raman's Navāṁśa **exactly**. A (rāśi, navāṁśa)
   pair that is impossible (only 9 of 12 navāṁśa signs are reachable from a rāśi sign)
   flags a mis-extraction and is dropped.
3. **Score** — `worked_chart_validate.py` runs `judge_house_doctrine`, maps Raman's
   phrase to a grade via the **pre-registered** `verdict_grade_map.json` (committed before
   any scoring so it can't be tuned), and reports exact / within-one / per-factor plus a
   full divergence list. Unmappable phrases are excluded, not guessed.

```
PYTHONPATH=. python3 -m app.medini.doctrine.validation.worked_chart_validate \
    docs/raman_doctrine/validation/corpora/heldout_ch07_4th.json
```

## Credibility safeguards
- Extractor emits raw positions + raw verdict phrases only.
- The verdict→grade map is pre-registered and committed **before** scoring.
- The (rāśi, navāṁśa) consistency gate drops mis-extractions automatically.
- The report lists **every** divergence and every exclusion (no cherry-picking), and
  qualifies the accuracy figure with the extractor's measured error rate (gold set).

## Scaling (fan-out)
The pilot proves the pipeline on one chapter (Vol 1 Ch. VII, 4th house). To scale, run
`raman-chart-extractor` per held-out chapter (a Workflow fanning the extractor in
parallel), merge the `charts` arrays, and run the harness over the union. Largest
untapped pools: Vol 2 10th-house (~70), 8th (~50), 12th (~40), Vol 1 houses 3–6.
De-duplicate nativities by (date, time, place) — the same chart recurs across chapters.

## Phase B — ML weight-fitting
Each scored row is a `(feature-vector, Raman-grade)` example. `fit_weights.py` (Phase B)
fits the scheme's parameters (`_DIGNITY_W`, `_W`, cap/blend/thresholds) to Raman's grades
with a constrained optimizer — fit on the tuned corpora, **validate on this held-out
set** (disjoint). Adopting any fitted weight into the engine is a separate, gate-guarded
step. See the plan; `FIT_REPORT.md` will record the outcome.
