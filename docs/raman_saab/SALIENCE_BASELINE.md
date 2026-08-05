# Salience baseline — the engine's attention vs Raman's own

*Measured 2026-08-05, before any salience code existed. This is the number the "instinct and
intuition" programme has to beat, and it is recorded here so it cannot drift.*

## What was measured

For each of Raman's worked charts in *Notable Horoscopes*, the houses he actually **emphasised**
in prose are the ground truth. The engine's ranked digest is scored on whether it surfaces those
same houses first. Target is **expert attention, never life outcomes** — this sits clear of the
astrobank firewall and relitigates nothing in `REAL_OUTCOME_GENERALIZATION.md`.

Benchmark: `tests/fixtures/notable_attention.json` (31 admitted charts, frozen tune/holdout
split written before any model existed). Admission required the engine's cast to reproduce
Raman's printed planetary longitudes (median **0.01–0.02°**) and, where he states one, his
Lagna (**9 stated, 9 matched, 0 mismatches**).

Rankings are compared **paired** on the same charts, with a 10,000-sample paired bootstrap.
Unpaired proportions at n≈14 carry a ±21pp CI and would be unreadable.

## The result

**Today's fixed-order digest is significantly WORSE than a constant ranking.**

Holdout (n=14):

| metric | digest | trivial | difference | 95% CI |
|---|---|---|---|---|
| p@1 | 0.286 | 0.643 | −0.357 | [−0.714, +0.071] |
| p@3 | 0.357 | 0.500 | **−0.143** | [−0.238, −0.024] |
| r@3 | 0.452 | 0.714 | **−0.262** | [−0.464, −0.083] |
| MRR | 0.507 | 0.810 | **−0.302** | [−0.503, −0.083] |

All admitted charts (n=28) — same direction, all four significant:

| metric | digest | trivial | difference | 95% CI |
|---|---|---|---|---|
| p@1 | 0.321 | 0.643 | **−0.321** | [−0.571, −0.036] |
| p@3 | 0.310 | 0.464 | **−0.155** | [−0.250, −0.048] |
| r@3 | 0.411 | 0.655 | **−0.244** | [−0.411, −0.083] |
| MRR | 0.510 | 0.776 | **−0.266** | [−0.432, −0.088] |

"Trivial" is the constant order **1, 10, 7, 9, 2, 4, 5, 8, 11, 3, 6, 12** — always name the
Lagna, then the 10th, then the 7th, regardless of chart. It is **twice as good** as the engine
at putting the right house first.

## Why

`build_insight_digest` is a fixed 9-slot template, identical for every chart:

1. most-corroborated favourable house 2. most-corroborated afflicted house 3. the running
period 4–6. top cross-feature insights 7. the sharpest tension 8–10. **what most distinguishes
this chart**

It leads with **corroboration** — which is population-typical by construction, since the median
chart carries 19 afflicted and 31 favourable significations — and buries **distinctiveness**,
the only genuinely information-bearing item, in the last slots. Raman does the opposite: he
opens on the Lagna (HTJAH-I:16001) and goes to what is unusual about the chart in front of him.

So the ranking is not merely arbitrary. It is **anti-correlated with expert attention**, because
the quantity it sorts by (agreement) is the quantity the population study proved is
non-differential.

## What this licenses

- Real headroom exists, and it is measurable. Simply *reaching* the trivial baseline would be
  an improvement; beating it is the target for `salience.py`.
- The engine already computes the right raw material — `band_share` (surprisal against 16,450
  charts), judgment-graph centrality, dignity and strength — and sorts by none of it.
- Any future claim of improvement must be reported **paired, with intervals, on the holdout
  split**, against **both** the digest and the trivial ranking. A gain over the digest alone is
  not a gain: the digest is the weaker of the two baselines.

## Honest limits

- n is small (14 holdout, 28 total). Intervals are wide and stated everywhere.
- Ground truth is Raman's *emphasis markers*, extracted from OCR'd prose. Two extraction
  defects were found and fixed (frame references such as "the 5th **from Lagna**" — 30% of all
  Moon mentions; and date/age ordinals such as "the 6th day"). Others may remain.
- Charts are read at **age 35**, not 2026: the Vimshottari sequence is generated for 120 years
  from birth, so pre-1906 births have no "currently running" period and `synthesize()` raises.
  This is a real engine limitation, worth its own fix independent of this programme.
- 3 admitted charts carry no emphasised house and are unscorable on this target.

## Reproduce

```powershell
py -3.12 tools/raman_saab/measure_salience.py --split holdout
py -3.12 tools/raman_saab/measure_salience.py --split all
```
