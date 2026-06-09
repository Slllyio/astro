# LunarAstro real-data run — dasha→event findings

**Date**: 2026-06-09
**Source**: LunarAstro research export (`kundlis.jsonl`, 35,931 rows).
**Cohort**: the 4,590 `category=event` records carry dated Astro-Databank-
style life events in their `description`. Pipeline:
`app.medini.etl.lunarastro_kundli_pipeline`.

## Corpus built

| quantity | value |
|---|---|
| charts built (sidereal D1 + Vimshottari windows) | 3,779 |
| dated events parsed | 18,007 |
| events joined to active MD/AD window | **17,912** |
| dropped (implausible age ≤0 or >105) | 95 |
| unmatched to a dasha window | 0 |

### Known data caveats (carried into every claim below)
- `time_zone` is a constant garbage value in the source; UTC offset is
  derived from longitude as Local Mean Time. Birth place/time are noisy
  (some records show a wrong city; a few birth *years* are mis-scraped).
  Vimshottari dashas key off the Moon's nakshatra and are robust to hours
  of time error and to place; **dignity-by-sign** is place-independent.
  **Functional (house-lordship) nature is the noisiest** derived feature.
- These are **descriptive tilts, not deconfounded causal effects**. Lift
  is normalised against measured person-time exposure (so it is *not*
  biased by unequal dasha lengths), but it does **not** remove the age
  confound: a lord's dasha tends to fall in particular life decades, and
  events cluster by age. See `round11_triple_test_synthesis` for what a
  permutation control does to effects of this size.

---

## Finding 1 — *which* lord runs maps to *which* event, classically

Normalised lift (observed share ÷ person-time exposure), MD lord:

| event_class | top MD lords (lift, p) | classical reading |
|---|---|---|
| **career** | Jupiter 1.28 (3e-18), Rahu 1.23 (2e-14); **Ketu 0.69**, Venus 0.84, Mercury 0.84 | Jupiter = status/wisdom, Rahu = worldly ambition; Ketu (detachment) **suppresses** career — the predicted direction |
| **marriage** | Rahu 1.43 (1e-12), Jupiter 1.22; **Ketu 0.70**, Mercury 0.83, Venus 0.86 | Jupiter is the classic marriage karaka; Ketu again lowest |
| **relationship** | Jupiter 1.52, Rahu 1.46 | — |
| **education** | Rahu 1.53 | — |
| **family** | Sun 1.57, Jupiter 1.28 | — |

Top MD/AD **pair** for career: **Jupiter/Saturn 1.56 (p=3e-10)** — the two
karma/career grahas together. The effects are modest (lift ~1.2–1.6) but
the *pattern* is the one a Parashari astrologer would predict, and Ketu
sitting at the bottom of both career and marriage is a clean negative
control. **Confound**: Jupiter/Rahu dashas also span typical career/
marriage ages, so part of each lift is age, not chart.

---

## Finding 2 — life stage dominates outcome valence (a recording effect)

Base beneficial-event rate by life stage (this is the *age confound*, not
a dignity effect):

| stage | benefit base rate |
|---|---|
| childhood (0–14) | 28% |
| youth (14–25) | 82% |
| prime (25–42) | 75% |
| maturity (42–60) | 60% |
| elder (60+) | 39% |

Beneficial events (marriage, new job, prize) are logged in youth/prime;
adverse ones (deaths of kin, diagnoses) in childhood and old age. The
dignity analysis **normalises this out** by lifting each cell against its
own life-stage base rate.

---

## Finding 3 — the dignity effect, net of age, is small; sharpest as the
MD+AD **pair** in the **prime** years

Dignity gradient = strong-quality benefit share − weak-quality benefit
share, per life stage (positive = a well-disposed lord helps):

| life stage | MD | AD | **MD+AD pair** |
|---|---:|---:|---:|
| youth | +0.02 | +0.03 | +0.05 |
| **prime** | +0.06 | +0.05 | **+0.21** |
| maturity | −0.03 | −0.00 | −0.05 |
| elder | −0.07 | +0.09 | −0.08 |

In the prime years, when **both** MD and AD lords are well-disposed, 84%
of events are beneficial (lift 1.12 over the 75% base); when both are
ill-disposed, 62% (lift 0.83). That **+0.21 pair gradient is the cleanest
signal in the run** and points exactly where the doctrine predicts —
strong lords + productive years = beneficial manifestation, and the pair
is a sharper filter than either lord alone (MD +0.06, AD +0.05 → pair
+0.21).

**But**: it is modest (n=235 strong-pair events in prime), it does not
hold in maturity/elder (mildly reverses), and it has **not** been
permutation-tested. On the evidence of `round11_triple_test_synthesis`,
an effect this size is exactly the kind that can shrink toward the null
under chart-shuffle. Treat Finding 3 as a **directionally-correct hint at
modest effect size**, not a confirmed law.

---

## Honest verdict

Real data, real charts, real dasha math — and the results rhyme with both
the classics and this project's own prior conclusion: **strong, sensible
associations between which lord runs and which event occurs** (Finding 1),
a **large age/recording effect on outcome valence** (Finding 2), and a
**small, directionally-correct dignity×life-stage interaction that is
sharpest for the MD+AD pair in the prime years** (Finding 3). The next
step to know whether Finding 3 is real is the permutation control
(shuffle natal charts, recompute the pair gradient, K≥100).

## Files
- `lifestage_dignity.md` — full MD / AD / pair tables + MD×AD grid
- `dasha_event_associations.md` — per-class MD/AD/pair lift tables
- Pipeline: `app/medini/etl/lunarastro_kundli_pipeline.py`
- Analyzers: `app/medini/ml/dasha_lifestage_dignity.py`,
  `app/medini/ml/dasha_event_associations.py`
