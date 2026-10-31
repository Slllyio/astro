# Ceiling check: results (2026-10-30)

Pre-registration: `CEILING_CHECK_PREREG_2026-10-30.md` (commit b61b1d9c, Addendum 1 before any
agreement number). No engine code changed. Hold-outs 4 and 5 not read.
Reproduce: `python -m tools.raman_saab.ceiling_check` and `python tools/raman_saab/ceiling_agreement.py`.

## Part A. The engine against trivial baselines

| Set | n | Engine exact | Always favourable | Rule polarity (B2) | Polarity, ties favourable (B3) | Engine real errors | B3 real errors |
|---|---|---|---|---|---|---|---|
| Pool (tuned on) | 389 | **263** | 183 | 240 | 253 | 35 | 98 |
| Hold-out 1 | 36 | 23 | 23 | 24 | 26 | 5 | 10 |
| Hold-out 2 | 134 | 55 | **94** | 85 | 88 | 34 | 39 |
| Hold-out 3 | 28 | 9 | 9 | 17 | 17 | 9 | 11 |
| **Hold-outs 1-3** | 198 | **87** | 126 | 126 | **131** | **48** | 60 |

Macro recall (mean recall over the three classes) on hold-outs 1-3: engine 0.347, B2 0.465,
B3 0.433, always-favourable 0.333.

**Pre-registered verdict: engine below baseline out of sample.** Exact, engine minus B3: -44,
chart-clustered 95% interval -61 to -28. Real errors, engine minus B3: -12 (-23 to -1), so the
engine makes fewer two-step inversions, mostly because it answers "mixed" instead.

Why: out of sample the engine says "mixed" 58 times where Raman says mixed 7 times; its largest
single loss is Raman-favourable read as mixed (41 rows). On the pool, the clause cascade adds 23
exact over plain rule polarity (240 -> 263); out of sample it loses 39 (126 -> 87). That is the
signature of logic fitted to the pool.

## Part B. Label agreement (is the target itself reliable?)

80 random pool rows, two fresh engine-blind labellers (C, D) reading only Raman's passages.

| | Labeller C vs gold | Labeller D vs gold | C vs D | Engine vs gold (same rows) |
|---|---|---|---|---|
| **Primary (all 80, "none" = disagreement)** | 0.762 (kappa 0.64) | 0.750 (0.63) | 0.938 (0.91) | 0.675 |
| Not pre-registered: drop the 13 rows both called "none" (n 67) | 0.910 (0.85) | 0.896 (0.83) | 0.925 | 0.687 |

**Pre-registered reading:** A = 0.756 (95% 0.66-0.84). Engine pool exact 0.676 >= A - 0.10, so by
the committed rule the engine is **"near the label ceiling"**.

**But that reading is driven by the passage windows, not by the labels.** Most "none" rows are
items whose window still did not reach the chart (labellers name charts 65, 69, 73 as absent),
and 10 of the 13 are gold "afflicted". Where the text reached the matter, the two blind
labellers agree with the gold label about 90% of the time (kappa about 0.85) and with each
other 93-95%. Only 4 rows have both labellers agreeing against gold (HTJAH-II.h11_04 H11,
NH.chart_43 H9, NH.chart_47 H9, NH.chart_63 H10); these are candidate label fixes for a
reviewer, not changes made here.

## Part C. Raman against himself

Only two natives recur across the sets with the same matter judged twice; both agree. Too few
to measure.

## What this means

1. **The labels are not the problem.** Raman's conclusions can be read back reliably (about 90%).
   The true ceiling is far above 68%; the committed rule's "near ceiling" reading is an artefact
   of short passages and should not be quoted on its own.
2. **The judge logic is the problem.** On unseen charts it loses to "always favourable" and to
   a plain count of benefic vs malefic rules. The single-rule tweak cycle is retired: it tunes
   the pool and does not carry over.
3. **Next step (user decision: rebuild).** The rebuilt judge must beat B3 (131/198 exact, 60 real
   errors, macro recall 0.43) on fresh data before it replaces anything. Hold-out 5 (sealed,
   unspent) is the natural test; hold-outs 1-3 are now development data.

## Addendum (2026-10-31): the same comparison on fresh data

Hold-outs 4 and 5 (64 never-seen conclusions) were scored once by the philosophy thread
(FIDELITY_FIXES_PREREG Addendum 38, commit 155ed516 on claude/project-thread-1ztlhb, pool figures there on pre-re-review labels; V0 with the audit thread's RS1 repair gives identical verdicts on all 64 rows), with the
two no-fit baselines included at this thread's request:

| | exact | within one | real errors | macro recall |
|---|---|---|---|---|
| Engine (clause judge) | 29 | **50** | **14** | 0.369 |
| B3 (plain rule count) | **40** | 45 | 19 | **0.408** |
| Always favourable | 38 | 43 | 21 | 0.333 |

The pattern of hold-outs 1-3 repeats on fresh data: the plain count beats the clause judge on
exact matches (40 vs 29) and macro recall, while the clause judge makes fewer outright
reversals because it answers "mixed" more often. No unspent Raman hold-out remains.
