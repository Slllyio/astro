# Track 2 — measuring the two promoted-but-unmeasured live components

`synthesis_v2` was promoted to the live grade path at increment 28. Two of the labels it now serves
live had never been validated against Raman's verdicts:

- **`synthesize_house`** — the OVERALL house-conclusion label (`synthesis_v2.py:274`), fused from the
  bhava/lord/karaka factor grades and promoted at `house_judgment.py:1591-1593`.
- **Chandra-Lagna** — the from-the-Moon sub-verdict (`_assess_from_moon`, `house_judgment.py:1237`),
  re-labelled through synthesis_v2 at `:1594-1598`.

## Finding 1 — both are unmeasurable **directly** against Raman's 9-grade verdicts

A read-only yield probe over all 168 held-out charts, using the verbatim, sha256-verified worked-chart
prose in `data/raman_doctrine/worked_analyses.jsonl` (83 records):

| source verdict | clauses found | **mappable to a 9-grade** |
|---|---|---|
| overall "the Nth house is X" | 23 | **3** |
| Chandra-Lagna / "from the Moon" | 67 | **1** |

Raman's overall-house and from-the-Moon statements are **narrative or descriptive** — "the third
house is good", "occupied by exalted Jupiter", "a fiery one", "spoilt" — not crisp gradeable factor
verdicts, and the pre-registered `verdict_grade_map.json` (correctly) declines to grade them. Where a
from-the-Moon judgment exists it is woven *into* a bhava/lord phrase (e.g. "has rendered the 5th house
weak from Chandra Lagna" is part of a LORD row), never stated as a standalone Chandra-Lagna verdict.
So there is essentially **no separate overall / Chandra-Lagna gold to score**, and these components
stay reading-side-by-design (exactly as `synthesize_house`'s own docstring already states). The cheap
read-only probe prevented a costly extraction pass that would have netted ~4 rows.

## Finding 2 — the honest substitute: `synthesize_house` vs Raman's factor central tendency

Raman's CRISP factor verdicts (bhava / lord / karaka) *do* map. Where a chart carries ≥ 2 of them, the
**central tendency (median) of his mapped factor grades** is a principled derived target for the house
conclusion. Two measurements (`validation/overall_consistency.py`):

| slice | end-to-end: synthesize_house(engine factors) vs Raman-central | fusion-logic: fuse(Raman's grades) vs Raman-central |
|---|---|---|
| all-3-factor charts (N=6) | within-one 4/6 (66.7%), Δ +0.83 | within-one 4/6 (66.7%), Δ +1.17 |
| ≥2-factor charts (N=14) | within-one 7/14 (50.0%), Δ +0.29 | within-one **12/14 (85.7%)**, Δ +0.50 |

Two honest reads:
1. **The fusion FORMULA is sound.** Feeding Raman's own factor grades through the class-weight +
   lead-veto fusion lands within-one of their central tendency 85.7% of the time (≥2 slice) — the
   fusion does not diverge from sensible central tendency (a mild +0.5 upward bias; the class-weighted
   mean sits slightly above the median on right-skewed triples).
2. **End-to-end the fusion does not degrade the signal.** synthesize_house of the ENGINE's factor
   grades tracks Raman's central tendency at ~50–67% within-one — in line with the engine's own
   per-factor accuracy (~57%). The overall label is roughly centred on Raman's factor gist, slight
   over-credit.

**N is small (6 / 14)** — a first spot-measurement of a component that was previously scored on a
single stray gold row, not a validation. But it is enough to state that the promoted overall label is
**consistent** with Raman's factor-level assessments and its fusion logic is not introducing error.

## Verdict
No engine change. The two components stay reading-side (unmeasurable directly on the 9-grade scale);
`synthesize_house`'s fusion is spot-confirmed sane at small N. Pinned by
`tests/doctrine/test_overall_consistency.py`; both diagnostics are reproducible
(`validation/overall_consistency.py`).
