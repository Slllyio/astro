---
date: 2026-07-02
type: methodology / findings
status: IMPLEMENTED — first run complete (Wikidata N=82,589); dasha family refuted
project: raman_saab population validation — longevity / maraka family
companion_to: docs/raman_saab/DOCTRINE_RATCHET_PLAN.md
verdict: docs/ml_runs/raman_saab_death_timing_VERDICT.md
---

# Death-Timing Methodology & Findings

> **STATUS: implemented and run.** §7 below now holds real results from the
> first run (Wikidata death corpus, N=82,589). The dasha-timing rule family is
> **refuted** under the confound-controlled permutation null; full write-up in
> `docs/ml_runs/raman_saab_death_timing_VERDICT.md`. House/lord maraka rules
> remain untested (need birth times). Classical specifics marked ⚑ still need a
> `bphs-doctrine-reviewer` audit before promotion.
>
> **Ethical guardrail (non-negotiable, from kundli spec §11 and the
> `ramana_maharshi.json` "structural_notes"):** everything here measures
> *population-level statistical association*. Nothing in this methodology, and
> nothing in any `VERDICT.md` it produces, may be phrased as predicting an
> individual's death. The unit of claim is "base-rate lift across a cohort,"
> never "this chart foretold this person's death."

---

## 1. The question

> Do B. V. Raman's longevity/maraka rules — the classical apparatus for
> *when and whether* death is indicated — show, across the medini population of
> biographied people, a **death-event rate above base rate** in the charts /
> dasha windows the rules flag, and does that signal **survive the project's
> standard confound controls and 3-corpus replication**?

This is the death-timing instance of the general population-validation loop.
It is deliberately the **first** family because (a) death is a well-recorded,
unambiguous event with the largest clean N, and (b) it is the family most
vulnerable to the age confound, so it forces the confound machinery to work
before we trust it on softer families (marriage, career).

---

## 2. Data — what a "death event" is here

| Concern | Answer | Source |
|---|---|---|
| Is death a first-class event class? | Yes. Harmonized `death_cause_unspecified`, taxonomy `category = 'death'`, `is_death_subclass = True`. | `build_event_class_taxonomy.py` |
| Own death vs. death of a relative? | **Separated.** `death_of_child/father/mother/mate/sibling/…` harmonize to `relationships` (`category = 'family_loss'`), *not* to own death. **For longevity you MUST filter `category = 'death'`, not `is_death_subclass`** (the latter also catches family loss). | taxonomy `_TAXONOMY` |
| Granular own-death classes | `death`, `death_by_accident`, `death_by_disease`, `death_by_execution`, `death_by_heart_attack`, `death_by_homicide`, `death_by_suicide`, `death_by_war_or_terrorism`, `death_mysterious`, `other_death`, `death_cause_unspecified`. | taxonomy |
| How many death events? | ≈ **11,285** own-death events reach the framework validation (`framework_validation_v1_VERDICT.md` "Death → 8H" row, N=11,285). Ample for population RR. | prior VERDICT |
| Event date field | `events.event_date` (ISO) + `event_date_precision ∈ {day, approx_window_midpoint}`. | `build_person_event_tables.py` |
| Death-date → JD → dasha | `events_with_dasha.parquet`: `event_jd`, `birth_jd`, `age_at_event_years`, `md_lord_at_event`, `ad_lord_at_event`, `md_seq/ad_seq`, `md_elapsed_years`. | `build_event_dasha_join.py` |
| Survival-ready view | `v_event_survival` with `time_to_event_days = event_jd − birth_jd`. | `build_duckdb_catalog.py` |

**Existing regression targets to reuse** (`derive_event_targets.py`):
`age_at_death` (own-death mask `event_root.startswith("death")`, age clamped
10–120, `max` per person), `event_died_young` (< 50), `event_lived_long`
(≥ 80; comment cites classical *poorna-ayur = 80*). Note the reconciliation
issue in §4.

---

## 3. Raman maraka / longevity rules to validate (candidate catalogue)

Seeded from the **existing cited rule library** — re-cited to Raman ⚑ in
`raman_saab/rules.py`. These enter the ratchet as `candidate`.

### 3a. House / karaka rules already encoded in the repo
| rule_id (proposed) | Antecedent | Consequent | Existing code |
|---|---|---|---|
| `raman.maraka.saturn_in_8th` | Saturn in 8th house | death / longevity issue | `bayesian_rule_validation.py:227` `saturn_in_8th_longevity` |
| `raman.maraka.mars_in_8th` | Mars in 8th | sudden/violent end | `:237` `mars_in_8th_violence` |
| `raman.maraka.ketu_in_8th` | Ketu in 8th | spiritual/sudden death | `:246` `ketu_in_8th_spiritual_end` |
| `raman.maraka.rahu_in_8th` | Rahu in 8th | unusual/sudden death | `:523` `rahu_in_8th_unusual_death` |
| `raman.maraka.lord8_in_dusthana` | 8th lord in 6/8/12 | longevity issues | `:512` `lord_of_8th_in_dusthana` |
| `raman.maraka.sun_afflicted_cardiac` | Sun afflicted by Saturn/Mars | cardiac death | `:401` (→ `death_by_heart_attack`) |
| `raman.longevity.8th_functional` | 8th house = longevity axis | death timing | `survival_analysis.EVENT_FUNCTIONAL_HOUSES["death…"]=(8,)` |
| `raman.longevity.disease_6_8` | 6th+8th axis | death by disease | `…["death by disease"]=(6,8)` |
| `raman.karaka.saturn_death` | Saturn as death karaka | death-timing dasha | `survival_analysis.EVENT_KARAKAS["death…"]=(Saturn,)` |

### 3b. Raman-specific doctrine to transcribe (net-new, ⚑ must be pinned)
These are the pieces Raman's system adds beyond the generic BPHS set. They are
**placeholders pending citation** — do not implement predicates until the
`bphs-doctrine-reviewer` confirms the exact classical statement and the repo
has a computation for each input:
- **Maraka lords.** Lords of the **2nd and 7th** houses as primary marakas;
  their dasha/antardasha periods as death-timing windows. ⚑ (Raman, *How to
  Judge a Horoscope* Vol. II.) — requires functional-lordship of 2H/7H, which
  the dasha-tree / dossier tables already expose.
- **Marana Karaka Sthana overlay.** The production MKS table is already locked
  as **D-9** in `docs/doctrine-decisions.md` (Sun-12, Moon-8, Mars-7, Merc-7,
  Jup-3, Ven-6, Sat-1, Rahu-9, Ketu-NA). Test whether a planet in its MKS at a
  death event is enriched. Reuses `computations/marana_karaka_sthana.py`.
- **Longevity-span (ayurdaya) bands.** Alpayu / Madhyayu / Purnayu via the
  classical three-pair method (⚑ exact pairs to be pinned — commonly lagna &
  its lord / Moon & Saturn / lagna & Hora-lagna, movable-fixed-dual count).
  Validate whether the predicted band matches observed `age_at_death`. See §4.
- **8th-from-lagna and 3rd (the 8th-from-8th) axis** for longevity. ⚑

---

## 4. Longevity-band reconciliation (an open decision)

There is a **conflict** between the repo's operational thresholds and Raman's
classical bands. This must be resolved before the ayurdaya rules can be scored:

| Scheme | Short | Middle | Full |
|---|---|---|---|
| **Repo** (`derive_event_targets.py`) | died_young `< 50` | (implicit) | lived_long `≥ 80` |
| **Raman / classical ayurdaya** ⚑ | Alpayu (short) | Madhyayu (middle) | Purnayu (full) — cutoffs commonly ~32 / ~70 / ~100 |

**Decision needed** (also raised in the plan §10 Q6): does the ratchet score
the ayurdaya rules against Raman's bands (requires new cutoffs) or against the
repo's existing binary targets (loses the three-way structure)? Recommendation:
score against **Raman's three bands** (that's the doctrine under test) and keep
the repo's binary targets only as a coarse cross-check.

---

## 5. Metrics & baselines — the confound gauntlet

Death is the **age-confound worst case** (`round9_lessons_learned.md` §4 notes
age-alone C-index for death ≈ 0.75 — "obvious"). So a death-timing rule must
clear a higher bar than mere enrichment.

**Three metrics, matched to three claim types:**

1. **Enrichment (base-rate lift / RR).** *Claim:* charts carrying rule R have
   death events at a rate above base rate.
   - Stack-A lift: P(8H verdict = afflicted | death event) / baseline, bands
     from `framework_event_validation.py` (>1.20 / 0.85–1.20 / <0.85). **Add a
     permutation p** (harness gap, plan §8.4).
   - Stack-B: **exposure-adjusted Poisson RR** on person-days, pooled
     Mantel-Haenszel across ADB/WD/LA + Cochran Q (`dasha_doctrine_pooled.py`).
2. **Timing concordance (survival).** *Claim:* rule R's flagged dasha window
   coincides with the death window better than chance.
   - Cox / DeepHit C-index on `v_event_survival`, **compared simultaneously to
     the age-alone AND duration-alone baselines** (lessons §4). A rule passes
     G3 only if it beats **both** by > 3× the (real 20-seed) noise floor.
3. **Ayurdaya-band accuracy.** *Claim:* predicted longevity band matches
   observed `age_at_death` band above chance (confusion matrix + Cohen's κ
   against a base-rate-matched null).

**Mandatory confound controls on every metric** (all from lessons-learned):
- **Age:** age-alone baseline run *simultaneously* (not post-hoc).
- **Exposure:** person-days denominator, never raw counts (longer dashas ⇒ more
  events).
- **Birth-date proxy:** `birth_jd` (day precision) as a control feature always.
- **Selection/documentation:** 3-corpus pooling; per-corpus heterogeneity flag.
- **Own-death filter:** `category = 'death'` (never `is_death_subclass`).

---

## 6. Data-coverage caveats specific to death timing

1. **WD cohort has no birth time** (`birth_jd = NaN`, day precision) → ascendant
   is a noon-UTC fallback → **house-based maraka rules (8th-house occupancy,
   8th-lord placement) are unreliable for WD**. House rules should be scored on
   **ADB only**, or ADB+LA where LA has a time; WD contributes to
   sign/karaka-level (house-independent) rules and to base rates.
2. **LA event dates are dasha-window midpoints** (`approx_window_midpoint`) —
   **do not use LA for timing-precision (survival) claims.** LA may contribute
   to enrichment/base-rate but is barred from metric #2.
3. **Right-censoring.** Persons with no recorded death are alive/unknown, not
   "did not die." The survival framing (`v_event_survival`) already models this
   as censoring; do not treat missing death as a negative label.
4. **Death-cause coverage is uneven.** `death_cause_unspecified` dominates;
   cause-specific rules (cardiac, violent) have much smaller N — check class
   qualification (pre-flight §6 of the plan) before scoring them.

---

## 7. Findings (first run — Wikidata, N=82,589, 2026-07-02)

Full write-up: `docs/ml_runs/raman_saab_death_timing_VERDICT.md`. Result JSON:
`data/ml_runs/raman_saab/population_validation.json`. Ledger:
`docs/raman_saab/RATCHET_LEDGER.json`.

The corpus has no birth times, so the metric run was **enrichment of the
dasha-lord-at-death** (not the survival C-index or ayurdaya bands, which need an
ascendant). The primary null is the **permutation / shuffled-age null** (§5
metric #1, adapted): it controls both the dasha-length endpoint-bias and the
age-at-death confound simultaneously. RR = observed / expected; O is
Poisson-binomial → exact z, one-sided p.

### 7a. Enrichment — dasha-lord-at-death (permutation null, PRIMARY)
| rule_id | best level | RR | z | p (1-sided) | Gate G1 | Status |
|---|---|---:|---:|---:|---|---|
| raman.karaka.saturn_dasha | AD | 1.007 | 0.90 | 0.18 | ✗ | refuted |
| raman.karaka.mars_saturn_dasha | AD | 0.997 | −0.50 | 0.69 | ✗ | refuted |
| raman.malefic_dasha | AD | 0.997 | −0.72 | 0.77 | ✗ | refuted |
| raman.benefic_dasha_protective (deplete) | MD-or-AD | 1.002 | +1.16 | 0.88 | ✗ | refuted |
| raman.karaka.rahu_ketu_dasha | MD | 1.004 | 0.57 | 0.28 | ✗ | refuted |

All within RR ∈ [0.97, 1.01] = null. None clears G1 (RR ≥ 1.20 enrich / ≤ 0.83
deplete). N=82,589 ≫ power threshold → **refuted**, not underpowered.

### 7b. The length-bias confound (exposure null vs permutation null)
| rule / lord | level | exposure-null RR | permutation-null RR |
|---|---|---:|---:|
| Saturn (19y MD) | MD | **1.090** (z 12.1, p 9e-34) | **0.973** (z −4.0) |
| malefic group | MD | 0.923 | 0.989 |
| benefic group | MD | 1.075 | 1.010 |

The exposure null's apparent Saturn "signal" is entirely the endpoint
length-bias (long dashas over-catch deaths); it collapses under the
length-and-age-controlled permutation null. **Do not cite the exposure column.**

### 7c. Robustness
| check | Saturn MD RR | note |
|---|---:|---|
| birth-time sweep 00h | 0.977 | z −3.39 |
| birth-time sweep 06h | 0.975 | z −3.64 |
| birth-time sweep 12h (primary) | 0.973 | z −4.03 |
| birth-time sweep 18h | 0.982 | z −2.70 |
| age-stratified 55–85 (N=55,000) | 0.960 | z −4.88; not an age artifact |

### 7d. Run 2 — house-based maraka rules on TIMED births (2026-07-03)

Corpus: **N = 4,586 Rodden AA/A/B timed charts** (Astro-Databank via Wayback;
real birth times + ADB tz offsets incl. LMT; death dates from each page's own
Events section). Built by `app/medini/etl/adb_wayback_death_corpus.py`;
validated by `app/medini/ml/raman_saab/maraka_validate.py`. Permutation
(shuffled-age) null throughout. Results:
`data/ml_runs/raman_saab/maraka_validation.json`.

| rule (chart-dependent lords) | RR MD | RR AD | RR MD-or-AD | Gate G1 | status |
|---|---:|---:|---:|---|---|
| raman.maraka.lords_2_7 (2H+7H lords) | 0.989 | 0.960 | 0.974 | ✗ | candidate¹ |
| raman.maraka.lord_8 | 0.987 | 0.964 | 0.982 | ✗ | candidate¹ |
| raman.maraka.lords_2_7_8 (union) | 0.992 | 0.968 | 0.980 | ✗ | candidate¹ |
| raman.maraka.saturn_as_maraka (n=1,625) | 0.943 | 0.947 | 0.958 | ✗ | candidate¹ |

¹ `candidate (underpowered)` by the letter of the pre-registered gate
(N = 4,586 < 5,000 power bar); every point estimate is at-or-below 1.0 vs the
G1 threshold of ≥ 1.20, and the corpus tail is still growing — statuses move
to `refuted` when N ≥ 5,000.

**Natal 8H longevity** (births ≤ 1900, two-sided, N≈115 per placement): all
null — Saturn +2.4y (p=0.10), Mars +0.2y, Rahu +0.3y, Ketu −0.4y, Jupiter
−1.2y, Venus +1.3y. The Rahu/Venus p≈0.06–0.08 trends at the N≈2,100
checkpoint regressed to null at full N (multiple-comparison noise, as
expected). Note the Saturn direction (longer life) matches classical BPHS
"Saturn in ayus-sthana" rather than the repo library's "longevity issues"
phrasing ⚑ — but it is not significant.

**G2 replication completed:** run 1's fixed-lord rules re-run on this
independent corpus land at RR 0.98–1.03 (all null) — the Wikidata null
replicates on ADB. Two corpora, one conclusion.

Still not run: survival C-index vs age/duration baselines; ayurdaya-band
accuracy (§4). These stay `candidate` (unimplemented, not refuted).
**Update (run 3):** ayurdaya-band accuracy is now tested — see §7e (null,
κ = 0.016). The survival C-index remains untested.

### 7e. Run 3 — the Triple Lock (conjunctional claim, 2026-07-03)

**Pre-registered** (`docs/raman_saab/RUN3_PREREG.md`, committed before the
evaluation; pins P1–P12, T1–T4, thresholds, seeds, hashes). Corpus:
**N = 2,091** Rodden AA/A timed births with full-date own-deaths
(ASTROCRM/ADB; `build_run3_corpus.py`). Full write-up:
`docs/ml_runs/raman_saab_triple_lock_VERDICT.md`. Result JSON:
`data/ml_runs/raman_saab/run3/triple_lock_validation.json`.

This is the test of the doctrine's *conjunctional* form — the standing defense
of the marginal nulls ("the factors must concur") — plus the two never-tested
legs (gochara triggers; ayurdaya bands via the three-pairs method with true
sunrise-anchored Hora Lagna).

| test (permutation null) | RR | z | p | threshold | power | status |
|---|---:|---:|---:|---|---:|---|
| leg1 maraka dasha (md_or_ad) | 0.978 | −0.88 | 0.81 | ≥1.20 | 1.000 | **refuted** |
| leg2 gochara (SadeSati\|Sat-8H\|DoubleTransit-8H) | 1.020 | +0.72 | 0.24 | ≥1.20 | 1.000 | **refuted** |
| leg3 ayurdaya band match | 1.033 | +1.20 | 0.12 | ≥1.20 | 1.000 | **refuted** |
| **Triple Lock (1∧2∧3)** | **0.992** | **−0.09** | **0.54** | ≥1.50 | 0.995 | **refuted** |

Observed 442 joint-lock deaths vs 445.8 expected — chance to the third
decimal. Ayurdaya confusion: accuracy 33.8% vs 33.3% chance, **Cohen's
κ = 0.016** (the three-pairs method mis-bands its own author: it votes ALPAYU
for B. V. Raman, who died at 86). Robustness: ±15-min birth-time jitter flips
13–14% of ascendants/bands yet joint RR stays 0.95–0.96; fixed-hour sweep
0.93–1.05; Rodden strata 0.96–1.00. Preflight shuffled-pairing collapse
passed (all primary |z| ≤ 3).

**Family verdict after runs 1–3:** house-independent marginals (N=82,589),
house-based marginals (N=4,586), and the conjunction (N=2,091) are all null
across three independently assembled corpora. The longevity family **halts**
per the ratchet kill criterion absent a genuinely new mechanism; the
remaining pinned variants (P5/P7 sensitivities, BPHS Ch.43 Pindayu family,
survival C-index) are catalogued `candidate`, not scheduled.

### 7f. Run 4 — "Raman as practiced" (fidelity-gated composite, 2026-07-03)

The genuinely-new-mechanism run the §7e halt allowed for: encode Raman's
**practiced** method (not textbook marginals) from his own worked cases in
*Notable Horoscopes*, verify the encoder against his published verdicts
BEFORE touching the population, freeze weights, run in **his ayanamsa**.
Prereg: `docs/raman_saab/RUN4_PREREG.md`; full write-up:
`docs/ml_runs/raman_saab_run4_VERDICT.md`.

**Fidelity gate** (`docs/raman_saab/FIDELITY_REPORT.md`): his printed
positions reproduce his stated death dashas 4/4 (Lahiri: 2/5 — the frame
matters); named killers in encoder top-4 for 3/4 Tier-A charts; band correct
where he states one (Shaw). But death-window potency concentrated only
modestly even on his own showcase charts (median 21st pctile vs 50% chance).
**FIDELITY: PARTIAL — calibration closed after four cited rounds.**

| Primary (α = 0.01/3, N = 2,091) | result | threshold | verdict |
|---|---|---|---|
| P1 death potency > own 90th-pct null | RR **1.0045** (p 0.47) | ≥ 1.25 | null |
| P2 mean percentile of death potency | **0.5062** (p 0.16) | ≥ 0.53 | null |
| P3 longevity-band κ | **0.0145** (p 0.23) | ≥ 0.05 | null |

Preflight shuffled-pairing collapsed cleanly (|z| ≤ 1.2). The golden-set
concentration did NOT generalize (population deaths sit at the 50.6th
percentile of each person's own potency distribution — chance). Ledger:
`raman.composite.as_practiced_v1 → refuted`.

**Family verdict after run 4: HALTED, hard.** Four escalating
operationalizations — marginals, house lords, conjunction, and a
fidelity-verified reconstruction of the practitioner's own composite in his
own zodiac — are all null. No further death-timing runs without BOTH a
qualitatively new hypothesis AND a new data modality (Wayback replication
corpus for G2, or rectified birth times). The unfalsifiable residue
("intuition beyond the encodable") is acknowledged in the prereg, not
litigated.

### 7g. Run 5 — audit-corrected encoder, held-out fidelity design (2026-07-03)

A three-agent audit of run 4's encoder found defects that made it an unfair
test of its own hypothesis (degenerate band veto, navamsa conjunctions in
radix houses, dead combustion/Shadbala wiring, band edges HPA explicitly
rejects), and the full *Notable Horoscopes* sweep supplied a new data
modality: 48 OCR-validated golden cases with Raman's printed positions
(run 4 had 6). Both re-run conditions of the §7f halt met; owner-directed.
Prereg: `docs/raman_saab/RUN5_PREREG.md`; full write-up:
`docs/ml_runs/raman_saab_run5_VERDICT.md`.

**Held-out fidelity gate** (the design element run 4 lacked): weights
calibrated on a seeded half of the casebook only (median death-window
percentile 0.184 → 0.090), sha-frozen, then the unseen half scored ONCE:
**HG1 median 0.123 — PASS** (16/24 unseen charts below the 20th
percentile). The encoder verifiably reproduces Raman out of book-sample.
Transit terms excluded by the pre-registered calibration rule (−0.006 gain).

| Primary (α = 0.01/3, N = 2,091) | result | threshold | verdict |
|---|---|---|---|
| P1 death potency > own 90th-pct null | RR **0.9675** (p 0.68) | ≥ 1.25 | null |
| P2 mean percentile of death potency | **0.4950** (p 0.78) | ≥ 0.53 | null |
| P3 longevity-band κ (v2 bands, non-degenerate) | **−0.0234** (p 0.96) | ≥ 0.05 | null |

Preflight collapsed cleanly (|z| ≤ 1.1). Ledger:
`raman.composite.as_practiced_v2 → refuted`.

**The dissociation is the finding**: an encoder that passes an honest
out-of-sample fidelity test on the practitioner's own casebook (12th
percentile median on unseen charts) lands at exactly chance (49.5th
percentile) on 2,091 independently-timed real deaths. The coherence is a
property of the literature, not of the population. Run 4's most charitable
escape hatch — "the fidelity signal was overfitting to six charts" — is
closed; the signal survives a held-out half of the book and vanishes only
when the charts stop coming from the book.

**Family verdict after run 5: re-HALTED.** Five operationalizations, the
last carrying an out-of-sample fidelity certificate — all null. Remaining
outs: the Wayback/ADB replication corpus (one pre-declared read-out with
the frozen pipeline if it yields ≥ 1,000 timed persons) and the
unfalsifiable intuition residue, which shrinks with every mechanism
encoded and is acknowledged, not litigated.

---

## 8. Prior expectation (for calibration, NOT a result)

Twelve prior rounds set a strong prior that **death-timing enrichment will be
null or near-null** at population scale:
- `framework_validation_v1_VERDICT.md`: **Death → 8H lift = 1.00** (dead null),
  vs the one positive in the whole project (Career → 10H, lift 1.37).
- `round9_lessons_learned.md`: "Death events cluster in older age" is filed
  under *"empirically real but uninteresting for prediction"* — i.e. the age
  confound is expected to eat most apparent signal.

So the **realistic success criterion** for this family is not "prove Raman's
maraka doctrine predicts death." It is: **run the doctrine through the same
rigorous gauntlet, ratchet each rule to its honest status (most likely
`refuted` or `contested`), and produce a defensible, cited `VERDICT.md`** — the
"uniquely rigorous null evidence" asset that lessons-learned §"assets that
survive" values. A single rule reaching `validated` would be genuinely novel;
the methodology is built to make that claim only if it is real.

---

## Files referenced

- `docs/raman_saab/DOCTRINE_RATCHET_PLAN.md` — governance/architecture companion
- `docs/doctrine-decisions.md` — D-9 Marana Karaka Sthana table (locked)
- `docs/round9_lessons_learned.md` — confound discipline, age-baseline rule, kill criterion
- `docs/ml_runs/framework_validation_v1_VERDICT.md` — Death→8H null baseline + verdict format
- `app/medini/etl/build_event_class_taxonomy.py` — own-death vs family-loss split
- `app/medini/etl/derive_event_targets.py` — `age_at_death`, died_young/lived_long targets
- `app/medini/etl/build_event_dasha_join.py` — `events_with_dasha` timing join
- `app/medini/etl/build_duckdb_catalog.py` — `v_event_survival` (`time_to_event_days`)
- `app/medini/ml/bayesian_rule_validation.py` — cited maraka/longevity rule library
- `app/medini/ml/survival_analysis.py` — `EVENT_FUNCTIONAL_HOUSES`, `EVENT_KARAKAS`
- `app/medini/ml/dasha_doctrine_pooled.py` — pooled MH RR + Cochran Q
- `app/medini/ml/stage_d_evaluate.py` — G1–G4 survival gate
