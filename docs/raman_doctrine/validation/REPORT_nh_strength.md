# Fresh, degree-accurate strength held-out — Notable Horoscopes

Every prior strength score is on charts **sign-reconstructed** from Raman's diagrams — the
intra-sign degree is a pada midpoint. *Notable Horoscopes* prints **full degree positions**, so
its charts reconstruct **exactly** (`raman_chart.from_printed_positions`, Raman's ayanāṁśa, no
vision, no sign back-solve). The doctrine strength engine was never tuned on NH. This is the
strongest strength test the project can build: a **different book**, judged on **true degrees**.

## Method
From the 50 positioned golden cases, extract Raman's verbatim **"the Nth house/lord is [grade]"**
verdicts, **hand-verify each against the full text**, and drop mis-attributions (an "afflicted"
that describes an *adjacent* planet, or a "from the Moon" frame the Lagna-based engine doesn't
judge). 15 clean rows survive (`nh_strength.json`). Each: reconstruct from degrees →
`judge_house_doctrine(chart, house)` → compare the factor label to the mapped verdict, reusing
`worked_chart_validate`'s grade lattice + pre-registered map.

## Result

| metric | value |
|---|---|
| exact | 5/15 (33.3%) |
| **within-one** | **7/15 (46.7%)** |
| **mean Δ** | **+1.13** |

The result is dominated by one clean, consistent signal: **the engine systematically
over-credits.** Every large miss is Raman-"afflicted" read by the engine as fairly-good /
moderate / *fairly powerful*:

| chart | house/factor | Raman | engine | Δ |
|---|---|---|---|---|
| John Milton | 7th house | afflicted | fairly powerful | **+6** |
| Sri Gautama Buddha | 7th lord | afflicted | fairly good | +4 |
| Alexander the Great | 5th house | afflicted | fairly good | +4 |
| Sri Adi Śankarāchārya | 8th house | afflicted | moderately good | +3 |
| Omar Khayyam | 9th house | afflicted | moderate | +2 |
| Swami Sivananda | 5th house | afflicted | moderate | +2 |

## Interpretation
- **The over-credit is real, not a reconstruction artifact.** Because these are Raman's own
  printed **degrees**, the chart is faithful — so the engine grading an afflicted house "fairly
  powerful" is a genuine engine gap, the same **benefic-aspect over-credit / holistic
  negative-weighing** ceiling documented in increments 8 and 12 and seen on the HTJAH grow set.
  A blanket down-shift can't fix it (Phase-2 recalibration proved it breaks the anchor).
- **The 46.7% is honestly *lower* than the ~54% HTJAH pooled number, and the corpus explains
  why:** it is deliberately afflicted-heavy (12 of 15 rows), so it stresses exactly the engine's
  weakest axis — recognising affliction against positive placement/dignity. It is not a
  like-for-like re-baseline; it is a **targeted stress test** of the over-credit, and the engine
  fails it in one direction (+1.13 mean).
- Combined with Track B (balance 28/30) and the timing result (MD 47/50), NH now validates the
  engine across **three** axes: the daśā start-balance and MD arithmetic hold; the sign-only
  *strength* scorer, run on true degrees, over-credits afflicted factors by ~1 grade.

## Honesty guardrails
- Every scored verdict is hand-verified against the `.mht`; mis-attributed / wrong-frame verdicts
  are dropped, not force-fit. The corpus is afflicted-skewed by NH's nature (it discusses
  afflictions at hardship/death), stated up front.
- Measurement only — no engine change; anchor + tuned floor + HTJAH held-out untouched. Guarded
  by `tests/doctrine/test_nh_strength.py`. `nh_strength_validate.py` reproduces the table.
- Follow-on (separately gated) only if a *fixable*, anchor-safe mechanism emerges; the observed
  over-credit is the known non-separable ceiling, so none is proposed here.
