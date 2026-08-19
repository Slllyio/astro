# RUN 3 PRE-REGISTRATION — the Triple Lock

**Committed BEFORE the confirmatory evaluation.** Code SHA at freeze:
`faea72d9e9773f977101806a8363ade7f0c06e98`. Only the null-side base rates
below were computed before this commit (no observed death-moment was
evaluated). Seeds: corpus/order `20260702` (run-2 convention), evaluation
`20260703` (`triple_lock._SEED`). Any test not listed here is exploratory and
barred from the VERDICT's results tables.

**Ethical guardrail** (kundli spec §11): everything here measures
population-level statistical association. Nothing in this run or its VERDICT
may be phrased as predicting an individual's death. The unit of claim is
base-rate lift across a cohort, never individual fate.

---

## 1. Claim under test

B. V. Raman's death-timing doctrine, in its **conjunctional** form — the form
practitioners actually assert: *death comes when (1) a **maraka dasha**
operates (the Vimshottari MD or AD lord is a lord of the 2nd or 7th from the
lagna), (2) a **gochara trigger** is live (Saturn/Jupiter transits touching
the mortality axis), and (3) the native's age lies in the chart's promised
**ayurdaya band** (Alpayu/Madhyayu/Purnayu).* ⚑ Raman, *How to Judge a
Horoscope* (maraka adhyaya); BPHS Ch.44 (maraka lords), Ch.31 semantics for
the double transit; three-pairs ayurdaya per Jaimini/Raman (P1).

**Why this is a new hypothesis** (kill-criterion accounting,
DOCTRINE_RATCHET_PLAN.md §1): run 1 refuted the house-independent *marginals*
(fixed karaka lord sets, no ascendant); run 2 refuted the house-based maraka
*marginals*. Neither tested the conjunction, the gochara leg, or the ayurdaya
leg — all three require the timed ascendant and are tested here for the first
time. A refutation here therefore refutes a distinct, previously untested
claim (and famously the doctrinal defense of the marginal nulls is exactly
"the factors must CONCUR").

## 2. Corpus (frozen)

`data/raman_saab/death_corpus_run3.parquet` — sha256 `45c7cd38fb7d6737…`,
**N = 2,091** (1,836 Rodden AA + 255 A), built by
`app/medini/ml/raman_saab/build_run3_corpus.py` from the ASTROCRM files
(MANIFEST sha256: holos_clean `3b1a0a79fee0cab5…`, astro_people
`b3ce21407a3346ff…`). Join: normalized name; dup-name and
conflicting-death-date drops; own-death roots only (`Death*` but not
`Death of *`); |lat| ≤ 60 (P9); age 1–120. Exclusion accounting in
`data/raman_saab/exclusions.json` (joined 2,109 → final 2,091).

The Wayback re-scrape (run-2's corpus source) is running as an optional
N-booster; **it is NOT part of this pre-registration.** If it completes, any
run on the union corpus is a pre-declared *replication extension* using the
same pins and thresholds, reported separately — never pooled post hoc.

Ephemeris: Lahiri sidereal throughout. Kundali casting via the production
engine (`calculate_all_charts`); transits/sunrise/HL via `FLG_MOSEPH`
(sign-level agreement; both are Moshier-backed in this environment).

## 3. Doctrine pins

### Leg 1 — maraka dasha
- **L1-a** Lord set: lords of the 2nd and 7th from the lagna
  (`functional_roles.maraka_planets`; Rahu/Ketu never members — repo lock).
  ⚑ BPHS Ch.44; Raman HJH.
- **L1-b** Level: **md_or_ad primary** (either period lord in the set);
  md-only and ad-only are secondary rows. ⚑ Raman treats both period levels
  as maraka-operative.

### Leg 2 — gochara trigger (frozen menu; nothing may be added after this commit)
- **T1** Sade Sati: transit Saturn in 12/1/2 from the natal Moon sign
  (engine semantics `gochara_engine._check_sade_sati`). ⚑ Saturn on the
  janma-rashi axis.
- **T2** Saturn transiting the natal 8th (whole-sign from lagna). ⚑ Saturn
  (ayushkaraka) in the ayus-sthana.
- **T3** Jupiter–Saturn double transit touching the 8th bhava (occupancy or
  drishti — Saturn 3/7/10, Jupiter 5/7/9; `is_double_transit_bhava`
  semantics pinned by a 200-case parity test). ⚑ BPHS Ch.31 activation.
- **Primary leg-2 indicator = T1 | T2 | T3.**
- **T4** Jupiter absent from all kendras from the Moon: **aggravator only**
  (secondary conjunction row `triple_plus_t4`); its ~2/3 base rate would
  trivialize the OR. ⚑ protective-Jupiter doctrine.

### Leg 3 — ayurdaya (three-pairs method; pins P1–P12)
- **P1** Method: Jaimini/Raman three-pairs majority. Full BPHS Ch.43
  Pindayu/Amsayu/Nisargayu + haranas **out of scope** for run 3 (needs
  Shadbala at scale + ~a dozen further pins; emits years, not the band the
  indicator consumes). ⚑ Raman HPA longevity ch.; Jaimini via Rath.
- **P2** Pairs: (lagna & lagna-lord), (Moon & Saturn), (lagna & Hora-Lagna).
  ⚑ The "lagna-lord & 8th-lord" variant for pair 1 is explicitly rejected
  for v1 (reviewer may relitigate before any future run).
- **P3** Modality→band: chara+chara | sthira+dual → Purnayu; dual+dual |
  chara+sthira → Madhyayu; sthira+sthira | chara+dual → Alpayu. ⚑ Jataka
  Parijata; Rath.
- **P4** Same-sign pair = the degenerate same-modality cell of P3; no
  special rule; `same_sign` recorded.
- **P5** Samasaptaka (mutual-7th) reversal: recorded on the PairVerdict,
  **never applied** in v1; sensitivity-only.
- **P6** Band cutoffs: Alpayu < 32; Madhyayu 32–<70; Purnayu 70–120
  (closed-left, half-open right). Variants 32/64/100 and 32/75/120 noted and
  rejected ⚑. The repo's <50/≥80 binary targets are a secondary cross-check
  only.
- **P7** Three-way split: the **lagna & Hora-Lagna pair prevails**;
  `tie_broken` recorded; pre-declared sensitivity rerun with
  Madhyayu-fallback.
- **P8** Hora Lagna: `sun_sidereal_lon(sunrise) + 30° × hours since
  sunrise`, sunrise-anchored; the `special_lagnas.py` mid-sign stub is NOT
  used. ⚑ Rath; PVR Rao.
- **P9** Sunrise: `swe.rise_trans`, disc-center, default refraction,
  Moshier; the rise immediately preceding birth; |lat| > 60° excluded.
- **P10** Sign rulers: classical single rulers (`SIGN_RULER`); no modern
  co-rulers.
- **P11** Classical exceptions NOT applied in v1 (each a named future pin):
  Saturn-in-lagna ayus modification; benefics-in-kendra promotion;
  Balarishta childhood overrides; kakshya hrasa/vriddhi; mrityu-bhaga.
- **P12** Lahiri + Moshier + `DAYS_PER_VEDIC_YEAR = 365.2425` for age→band.

## 4. Statistics (frozen)

- **Null (primary and only):** permutation / shuffled-age. One fixed-seed
  (`20260703`) sample of 1,000 ages from the corpus's empirical age-at-death
  distribution, shared across persons and legs; all three legs evaluated at
  the SAME sampled ages, so the joint p_i inherits the full between-leg
  dependence. Counts are Poisson-binomial → exact z, one-sided p. The
  exposure null is not computed (run 1 proved it length-biased).
- **Primary tests: 4.** Bonferroni α = 0.01/4 = **0.0025**.

| test | threshold | direction | null base rate | E | √var | power at threshold |
|---|---|---|---|---|---|---|
| leg1_maraka (md_or_ad) | RR ≥ 1.20 | enrich | 0.4040 | 844.7 | 21.24 | ≈ 1.0000 |
| leg2_gochara (T1\|T2\|T3) | RR ≥ 1.20 | enrich | 0.3752 | 784.5 | 21.69 | ≈ 1.0000 |
| leg3_ayurdaya (band match) | RR ≥ 1.20 | enrich | 0.3270 | 683.7 | 18.57 | ≈ 1.0000 |
| **triple_lock (1∧2∧3)** | **RR ≥ 1.50** | enrich | 0.0492 | 102.9 | 9.55 | **0.9951** |

  (Base rates computed null-side only, before this commit; the joint base
  rate 4.9% lands inside the anticipated 3–10% power window. The joint
  threshold is 1.50 because the conjunctional claim is strong — at
  E ≈ 103, RR 1.2 would be a ~2σ coin-flip, unfalsifiable; RR 1.5 is a
  lenient floor for "when all three lock, death follows".)
- **Refutable-power rule** (`run3_gate.toml`, replaces the blanket
  N ≥ 5000): a failed test is `refuted` only if
  `power = Φ((RR_thr−1)·E/√var − z_α) ≥ 0.90` for that test; else
  `candidate`. All four tests are refutable at this corpus (table above).
  A pass is capped at `provisional` (single corpus; G2 unmet).
- **E < 30 fallback**: if any primary E dropped below 30 (none does), the
  normal approximation would be replaced by a 100k-draw Monte-Carlo p,
  fixed seed.
- **Secondary rows (10, descriptive only):** leg1_md, leg1_ad, T1, T2, T3
  singles, triple_plus_t4, the three pairwise conjunctions, and the ayurdaya
  confusion matrix + Cohen's κ.

## 5. Preflight & robustness (pre-declared)

- **Preflight hard gate:** shuffled person↔death-age pairing must collapse
  every primary RR to within ±0.08 of 1.0; the run aborts robustness and the
  VERDICT reports the failure otherwise.
- **Birth-time jitter:** ±15 min uniform (Rodden-A precision), 2 fixed
  seeds; report primary RRs + fraction of persons whose ascendant, maraka
  set, or ayurdaya band flips.
- **Degenerate fixed-hour sweep** (00/06/12/18h, all persons): bridges run
  1's no-birth-time regime; primary RRs only.
- **Strata:** Rodden AA vs A; hemisphere. Descriptive; no gate action.
- Robustness may explain but can never overturn a primary verdict.

## 6. Verdict mapping

Gate outcome → ledger status (`RATCHET_LEDGER.json`, append-only, run block
`run3-triple-lock`): G1 pass → `provisional` (ceiling; single corpus);
G1 fail at power ≥ 0.90 → `refuted`; else `candidate`. The VERDICT
(`docs/ml_runs/raman_saab_triple_lock_VERDICT.md`) uses the standard
Question → Methodology → Results → Verdict shape and updates
`docs/death_timing_findings.md` §7.

## 7. Reviewer sign-off

⚑ items require a `bphs-doctrine-reviewer` audit before any rule promoted
past `provisional`/`refuted` enters `docs/doctrine-decisions.md`. Checkbox
ledger:

- [ ] L1-a, L1-b (maraka lord set + level)
- [ ] T1–T4 citations
- [ ] P1–P12 (ayurdaya)
