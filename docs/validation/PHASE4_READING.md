# Phase 4: how to read the results (hand-written)

## 4.3 Whole-chart blind matching: the third core question (`PHASE4_3_RESULTS.md`)
5,406 people (A+B), 16,571 known life facts with a direction (divorced, childless, prison, early loss
of a parent, wealthy, ...). The engine must pick the true chart out of 5. The 4 decoys are born at
the same place within ±3 days, at random times, so the season, era and slow planets are identical.
- **Hit rate 0.1999 vs chance 0.2000** (effect −0.0001, CI −0.008..+0.007): **BOUNDED_NULL**.
  The mean rank of the true chart is 2.989 vs chance 3.0. Same-year decoys: 0.196, also bounded.
- The machinery works. When the profile is generated from the true chart's own verdicts (75%
  faithful), the hit rate is 0.312. The decoy-as-true sham gives 0.205.
- Meaning: what is known about a person's life does not identify their chart better than a die roll.

## 4.2 Rule-level effects (`PHASE4_2_RESULTS.md`)
- **Q1, the 91 published rule × outcome tests pooled:** RR **1.007** (CI 0.996–1.019), τ² = 0:
  **BOUNDED_NULL**, and no rule family stands out. Only **35%** of rules lean in Raman's predicted
  direction (sign test p = 0.006). More rules point the wrong way than the right way.
- **Q2, dose-response** ("more testimonies, stronger result"): OR **0.984 per extra rule fired**
  (CI 0.942–1.028): **BOUNDED_NULL**. People with more of Raman's affliction rules for a matter are
  not more likely to have that outcome.
- Deviations, recorded: the dose-response decade adjustment moved from dummy-logit (5/9 fits failed by
  separation) to conditional logit, with a dummy fallback on informative decades for the three large
  universes. The slopes seen before the fix are printed in the results file.
- This closes Phase 1's open point. Houses were not individually excluded at AUC 0.53, but the
  rule-level form, which is the doctrine's actual claim, is excluded on average and shows no
  heterogeneity.

## Stopping rule: TRIGGERED
All three core questions are BOUNDED_NULL, each with its machinery shown to see an effect of that size:
1. Static house verdicts (Phase 1 pool; Phase 4.2 rule-level pool and dose-response).
2. Dasha-activation timing (Phase 3: AD and MD, placebo, tiers, ayanamsa, double transit).
3. Whole-chart identification (Phase 4.3).

Per the plan, **no new outcome questions are opened.** All four holdouts (C1, C2, Gauquelin, Wikidata)
stay unread. Nothing reached SIGNAL, so there is nothing to confirm. Spending them would only add
power to bound a null that is already bounded. Remaining Phase 4 items: 4.1 (Gauquelin positive
control, already registered and running) finishes as the machinery check it is. 4.4–4.7 and Phase 5
(the composite score, ML) are **not opened**, because the stopping rule exists precisely so that the
project does not keep testing until something turns up by chance.
