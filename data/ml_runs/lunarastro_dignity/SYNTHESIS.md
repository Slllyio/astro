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

### Finding 3 — RESOLVED by the permutation control ✅

Unlike Round-11's RR=2.31 (which collapsed to z=1.07 under chart-shuffle),
this gradient **survives**. Holding every event's (md_lord, ad_lord,
age, valence) fixed and re-scoring the running lords' dignity from a
*random other person's chart*, K=500 times:

| quantity | value |
|---|---|
| real prime pair gradient | **+0.215** |
| chart-shuffle null mean / max | +0.004 / +0.120 |
| shuffled ≥ real | **0 / 500** |
| z-score | **4.49** |
| empirical p | **0.002** |

Stable across seeds (z≈4.7–4.9). **Decomposition** shows the signal is
anchored in **dignity-by-sign** (exaltation/own/debilitation — z=2.16
alone), the *place-independent* feature robust to this source's noisy
birth coordinates, while the place-dependent **functional** component is a
pure null (z=0.40). A bad-birth-data artifact would show the opposite, so
the decomposition argues *for* a genuine chart-structural effect.

See `permutation_test.md`. **Caveats that remain**: one corpus (~3.8k
people), event valence comes from a label→polarity map, and famous-person
recording bias is not controlled by the chart shuffle (it controls only
the person↔chart link). This is the strongest positive result in the
project's history of this question — worth replication on an independent
corpus before it is called a law.

---

### Finding 4 — anatomy of the gradient: small, planet-specific, Sun reverses

Dissecting *how* the effect is produced (`dignity_anatomy.md`) tempers the
headline:

- **Single-MD dignity ladder is monotonic but tiny**: exalted 1.05 → own
  1.02 → … → debilitated 0.94. The direction is right (better dignity →
  more beneficial) but no single rung is significant; well-vs-ill contrast
  is only **+0.024**.
- **Within-lord (lord-identity controlled) is heterogeneous, not a law**.
  For a *fixed* planet, benefit share when well- vs ill-dignified:
  - **Jupiter +0.08 (p=3e-5)** and **Mercury +0.10 (p=0.002)** — the
    predicted positive dignity→benefit, well powered.
  - Rahu/Venus/Moon/Ketu/Saturn/Mars ≈ 0.
  - **Sun −0.10 (p=0.0009) — REVERSED**: a well-dignified Sun runs with
    *fewer* events coded beneficial (Sun = authority/separation/ego; may
    also be a valence-coding boundary case).

**Reconciliation**: the large +0.21 composite *pair* gradient is mostly
**natural-benefic selection** — "strong pair" overwhelmingly means two
natural-benefic, well-placed lords (Jupiter/Venus/Mercury) running
together — riding on a **small but permutation-real by-sign core** that is
concentrated in Jupiter and Mercury. The honest one-line version: *dignity
matters, but modestly and chiefly for the benefic lords; it is not a
uniform "good planet strong → good life" dial, and for the Sun it points
the other way.*

### Finding 5 — robustness battery & split-half replication

Two threats to Finding 3 remained: confounds/label-noise, and the fact
that 17912 events cluster into only 3779 people (non-independence).
`dasha_dignity_robustness.py` re-runs the full chart-shuffle permutation
under each stress (`robustness.md`):

- **Label noise** — restrict to events whose class polarity agrees with the
  Beneficial/Adverse label: z **3.91** (vs 4.09 baseline). Not a coding
  artifact.
- **Soft classes** — drop personal/family/relationship/other: z **4.00**.
- **Independence** — one *random* event per native (¼ the sample): real
  gradient holds at ~+0.2, **median z = 2.41, significant in 5/6 random
  draws**. The full-sample significance is *not* inflated by repeated events
  per person. (An earlier "earliest-event" version of this filter gave a
  false collapse — it cherry-picked late-bloomers; the random pick is the
  correct test.)
- **Split-half replication** — disjoint 50/50 person halves, each with its
  own events and donor chart pool: **all 6 halves positive, z 2.6–3.9, every
  p ≤ 0.01**. The effect reproduces, not a one-partition fluke.

**Remaining caveat (the headline one)**: this is *internal* replication on a
single corpus. A truly independent second dataset is the gold standard and
is **not yet available in this repo** — confirmed by surveying the data
dirs. That, not a statistical gap, is the next real step.

### Finding 6 — native-kundli deep dive: benefic/malefic is flat, dignity is the only signal

We widened the per-event feature set from one dignity axis to 45 native-kundli
features of the running MD & AD lords — natural nature (benefic/malefic),
functional nature (yogakaraka / dusthana-lord off the lagna), bhava placement
(kendra/trikona/dusthana/lagna), pair relations, and chart-level auspiciousness
counts — and tabled the benefit rate by each (`event_features_deepdive.md`,
module `dasha_event_features.py`). Across **57 feature-levels** (Bonferroni
bar p < 0.0009):

- **Natural benefic/malefic is FLAT** — a running natural benefic and a running
  natural malefic carry the *same* benefit rate (75% vs 75%). `pair_both_benefic`
  is null too. The textbook "benefic dasha = good period" does **not** hold at
  the single-feature level on this corpus.
- **Functional nature** is weak: functional-neutral MD lords underperform
  (72%, raw p=0.01) but don't survive correction.
- **Bhava placement** mostly flat; the two largest raw cells — AD lord in the
  1st house (81%, raw p=0.003) and `chart_kendra_net=2` (81%, p=0.0035) —
  are **suggestive but do NOT survive** the family-wise bar. Honest status:
  candidate hypotheses, not findings.
- **Dignity remains the one validated axis** — not because it's individually
  huge, but because it was a *single pre-registered hypothesis* that passed a
  chart-shuffle permutation (Findings 3–5), whereas everything here is
  multiple-comparison-exposed.

Net: enriching events with the full chart does **not** surface a stronger or
simpler predictor than the dignity gradient already found; if anything it
shows how little the coarse benefic/malefic dichotomy buys you.

### Finding 7 — promise vs timing, and what the dignity signal really is

Testing the doctrine *"the dasha only times a result the natal chart already
promises"* (`dasha_event_promise.py`, `promise_analysis.md`). For each event we
scored the native chart's **domain-matched promise** — the strength of the bhava
the event belongs to (marriage→7, career→10, death→8, …): house-lord dignity +
placement, karaka dignity, benefic/malefic occupancy and aspect — and flagged
whether the running dasha **activates** that domain (MD/AD = house-lord or
karaka).

- **Promise → valence: NULL.** Strong / medium / weak promise all ~74–75%
  beneficial; the chart-shuffle permutation on the promise gradient gives
  z=0.59, p=0.28. The chart's domain promise does not predict outcome here.
- **Marginal timing effect looks huge** — activated 82% vs non-activated 63% —
  **but it is Simpson's paradox.** Within every event class the timing gap is
  ≈0 (career 0.97 vs 0.98, marriage 1.00 vs 1.00, death 0.00 vs 0.00). Beneficial
  classes (career, marriage) just get activated more often than adverse ones.

**The deep reason — and a reinterpretation of Findings 3–6.** In this corpus
**event valence is essentially a relabeling of `event_class`** (career 97%
beneficial, marriage 100%, education 100%; death/health/divorce 0%). So
"predicting benefit" ≈ "predicting which *class* of event occurs", and almost no
within-class outcome variation exists for any natal feature to move. Re-examining
the validated dignity gradient under this lens: strong-dignity MD+AD buckets
contain **more career (59% vs 43%) and marriage (19% vs 13%)** and **fewer death
(10% vs 18%), health and divorce** than weak buckets, while *within* a class
dignity barely moves valence (career 0.986 vs 0.955). 

So the real, permutation-validated, replicated signal is best stated as:
**well-disposed MD+AD dasha periods coincide with beneficial-*class* life events
(career, marriage); ill-disposed periods coincide with adverse-*class* events
(death, disease, divorce)** — a classical idea (benefic periods bring auspicious
matters) — *not* "a given event resolves better when the lords are dignified."
The promise layer adds no predictive lift on top of that, and the coarse
benefic/malefic dichotomy adds none at all (Finding 6).

### Finding 8 — escaping circularity: non-circular targets, and the 7th house lights up

Findings 3–7 used "benefit valence", which is ~a relabel of `event_class` →
near-circular. Two reframed questions use targets **independent of the chart and
of the class label**, so a signal is real and a null is real.

**A. Significator timing** (`significator_timing.md`,
`dasha_significator_timing.py`) — do events fall in the dasha of the native's own
significators? We separate the **chart-specific house-lord** (the 7th lord is a
different planet per ascendant) from the **universal karaka** (Venus for marriage,
same for everyone), and test the house-lord with a chart-shuffle null (reassign
donor ascendants; the running lord is held fixed, so Vimshottari exposure is
absorbed).

- **Marriage under the native's own 7th-lord: 14% vs 12% shuffled, lift 1.16,
  z=2.28, p=0.01** — a genuine *chart-specific* timing signal (borderline under
  Bonferroni over 9 classes, but the most pre-registered classical rule).
- The discrimination is the insight: for marriage the **universal Venus karaka
  is under-represented** (lift 0.86 — Venus's 20-yr dasha does *not* attract
  marriages), while the **chart-specific 7th-lord is significant**. It is
  house-lordship, not the universal karaka, that times marriage.
- Career/death house-lord timing is directionally positive but not significant
  (z≈1.1–1.2); death's universal Saturn-karaka shows lift 1.18.

**B. Event age** (`event_age.md`, `dasha_event_age.py`) — continuous targets.
- **Longevity (age at death) vs lagna+8th strength: NULL** (ρ=−0.011, z=−0.48,
  p=0.63). A coarse promise index does not predict age at death here (classical
  Ayurdaya is more elaborate; sample is died-already/notable-biased).
- **Marriage age vs 7th-house strength: ρ=−0.060, z=−2.08, p=0.04** — stronger
  7th house → **earlier** marriage (29.1 vs 30.4 yrs, −1.35 yr), exactly the
  classical direction.

**The convergence (the real headline).** Two independent non-circular methods,
two different targets, both light up the **7th house for marriage**: A says the
native's 7th-*lord* dasha *times* the wedding (z=2.28); B says 7th-house
*strength* sets the *age* (z=−2.08). Marriage is the domain where this corpus
carries genuine, mutually-corroborating chart signal — modest in size but real
and non-circular, unlike the valence findings. Longevity, the other classical
flagship, is a clean null with this index.

### Finding 9 — drilling the marriage signal, and the multiclass ceiling

**Marriage deep dive** (`marriage_deepdive.md`, `dasha_marriage_deepdive.py`)
sharpens Finding 8A into a precise rule:
- It is specifically the **7th-lord in the Mahadasha** that times marriage
  (lift 1.15, z=2.18, p=0.018). The **antardasha is null** (0.99), and the
  **2nd and 11th lords do not time marriage** (lift 0.87, 0.89) — the textbook
  "2/7/11 signify marriage" does *not* hold; pooling them only dilutes the 7th.
- **Double activation sharpens it**: MD∩AD both = 7th-lord lifts to 1.25
  (highest), directionally consistent with doctrine though underpowered (~2% of
  marriages).
- **Replication**: the 7th-lord MD lift is positive in **all 6 disjoint person
  halves** (mean lift 1.15, mean z 1.60). Per-half significance is weak only
  because a ~1.15 lift needs the full sample to resolve — direction and
  magnitude reproduce everywhere (the Finding-5 discipline).

**Multiclass ceiling** (`houselord_class.md`, `dasha_houselord_class.py`) — the
formal "does the running lord's house-lordship predict which CLASS of event the
period brings", as a 12×N lift matrix with a chart-shuffle null. The three major
life domains all lean the classically-correct way — marriage/7th lift 1.09
(z=1.53), career/10th 1.05 (z=1.38), death/8th 1.06 (z=1.30) — but **none clears
p<0.05 in the class-prediction direction and the aggregate diagonal is null**
(lift 1.03, z=0.78, p=0.21); health/education are flat. So house-lordship →
event-class is **directionally classical but too weak to confirm** on this
corpus. Marriage remains the single domain with a real, replicated, non-circular
signal — and it lives in the *timing* direction (which dasha), strongest for the
7th-lord Mahadasha.

### Finding 10 — the Navamsa (D9) does not sharpen marriage *timing*

D9 is the classical marriage varga, so we tested whether D9-derived significators
time marriage better than the D1 7th-lord. `charts.parquet` stored only D1 signs,
but `birth_jd_used` lets us recompute each graha's longitude from the ephemeris
and fold it to Navamsa (`build_d9_charts.py` → `charts_d9.parquet`; recomputed D1
signs reproduce the stored parquet exactly; Venus vargottama rate 0.109 ≈ 1/9).
The D9 *ascendant* is unrecoverable (birth lat/long were not persisted), so we
test the strongest **planet-based** D9 significators (`dasha_marriage_d9.py`,
K=5000):

| significator | lift | z | p |
|---|---:|---:|---:|
| **d1_7th_lord** (baseline) | **1.15** | 2.24 | 0.016 |
| venus_d9_disp (Venus's navamsa dispositor) | 1.03 | 0.45 | 0.34 (null) |
| d1_7L_d9_disp (7th-lord's navamsa dispositor) | 1.13 | 1.84 | 0.037 |
| d1_7L or venus_d9 (union) | 1.09 | 1.96 | 0.029 |

- **D9 does not beat D1.** The plain D1 7th-lord (lift 1.15) stays the strongest
  single marriage-timing significator. The 7th-lord's navamsa dispositor is also
  significant (1.13) but is a *correlated* refinement, not an improvement; Venus's
  navamsa dispositor is null; the union dilutes.
- **Caveat:** the most classical D9 marriage significator — the Navamsa 7th-lord
  reckoned from the D9 *lagna* — could not be tested (no birth lat/long → no D9
  ascendant). So this rules out the D9 *dispositors* sharpening timing, not the
  full Navamsa. D9 may still matter for marriage *quality/promise*, which this
  corpus (valence ≈ class) can't probe.

Net: across D1 and the testable parts of D9, **marriage timing lives in one place
— the D1 7th-lord Mahadasha.** Adding vargas does not help on this data.

## Honest verdict

Real data, real charts, real dasha math — and the results rhyme with both
the classics and this project's own prior conclusion: **strong, sensible
associations between which lord runs and which event occurs** (Finding 1),
a **large age/recording effect on outcome valence** (Finding 2), and a
**small, directionally-correct dignity×life-stage interaction, sharpest for
the MD+AD pair in the prime years** (Finding 3) that **survives a
chart-shuffle permutation** (z≈2.9–4.1, p≈0.003), is **carried chiefly by
Jupiter/Mercury and reverses for the Sun** (Finding 4), and is **robust to
label noise, event clustering, and disjoint-subsample replication**
(Finding 5). Net: a genuine but modest (~+0.2) chart→event signal on this
corpus. The one honest gap left is **external replication** — a second,
independent dataset — which the repo does not currently contain.

## Files
- `lifestage_dignity.md` — full MD / AD / pair tables + MD×AD grid
- `dasha_event_associations.md` — per-class MD/AD/pair lift tables
- Pipeline: `app/medini/etl/lunarastro_kundli_pipeline.py`
- `dignity_anatomy.md` — dignity ladder + within-lord contrast (Finding 4)
- `robustness.md` — robustness battery + split-half replication (Finding 5)
- `event_features_deepdive.md` — 45 native-kundli features per event (Finding 6)
- `events_enriched.parquet` — events + all native-kundli features (reusable)
- `promise_analysis.md` — domain promise vs dasha timing + within-class control (Finding 7)
- `events_promise.parquet` — events + domain promise score + timing-activation flag
- `significator_timing.md` — chart-specific house-lord vs universal karaka timing (Finding 8A)
- `event_age.md` — chart strength → longevity / marriage age (Finding 8B)
- `marriage_deepdive.md` — 7th-lord MD/AD/MD∩AD + secondary significators + split-half (Finding 9)
- `houselord_class.md` — house-lordship → event-class lift matrix, chart-shuffle (Finding 9)
- `marriage_d9.md` — D9 Navamsa marriage significators vs D1 7th-lord (Finding 10)
- `charts_d9.parquet` (run dir) — recomputed Navamsa signs per graha (reusable)
- Analyzers: `app/medini/ml/dasha_lifestage_dignity.py`,
  `app/medini/ml/dasha_event_associations.py`,
  `app/medini/ml/dasha_dignity_permutation.py`,
  `app/medini/ml/dasha_dignity_characterize.py`,
  `app/medini/ml/dasha_dignity_robustness.py`,
  `app/medini/ml/dasha_event_features.py`,
  `app/medini/ml/dasha_event_promise.py`,
  `app/medini/ml/dasha_significator_timing.py`,
  `app/medini/ml/dasha_event_age.py`,
  `app/medini/ml/dasha_marriage_deepdive.py`,
  `app/medini/ml/dasha_houselord_class.py`,
  `app/medini/etl/build_d9_charts.py`,
  `app/medini/ml/dasha_marriage_d9.py`
