# Phase 4.3 results: whole-chart blind matching

Per `docs/validation/PHASE4_3_MATCHING_PREREG.md` (PHASE4_3_MATCHING_PREREG@39dfc2ce). Parashara engine. 5406 people (A+B), 16571 verdict-axis labels. Chance hit rate 0.20, mean rank 3.0.

| arm | n | hit rate | effect (−0.20) | 95% CI | mean rank of true chart | MDE80 | p_TOST | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL planted (profile drawn from the true chart) | 5406 | 0.3118 | +0.1118 | +0.1032..+0.1209 | 2.484 | nan | nan | pass |
| CONTROL sham (decoy posing as true) | 5406 | 0.2054 | +0.0054 | -0.0027..+0.0134 | 2.994 | nan | nan | pass |
| **PRIMARY regime S** (decoys ±3 days) | 5406 | 0.1999 | -0.0001 | -0.0080..+0.0073 | 2.989 | 0.015 | 0.000 | BOUNDED_NULL |
| secondary regime Y (decoys same year) | 5406 | 0.1961 | -0.0039 | -0.0116..+0.0042 | 3.004 | 0.015 | 0.000 | BOUNDED_NULL |
