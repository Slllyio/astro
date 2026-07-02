---
date: 2026-07-02
type: methodology / findings (findings tables empty until first run)
status: DRAFT — pre-review (awaiting sign-off before any code is written)
project: raman_saab population validation — longevity / maraka family
companion_to: docs/raman_saab/DOCTRINE_RATCHET_PLAN.md
---

# Death-Timing Methodology & Findings

> **DRAFT, reverse-inferred from the existing medini code to fit repo
> conventions.** This is the *methodology* half of the `raman_saab` work; the
> *governance* half is `docs/raman_saab/DOCTRINE_RATCHET_PLAN.md`. The
> findings tables in §7 are **empty templates** — they get populated by the
> first harness run, not by this draft. Classical specifics marked ⚑ need a
> `bphs-doctrine-reviewer` audit before they are treated as authoritative.
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

## 7. Findings (EMPTY — populated by the first run)

> These tables are the render target of the first `raman_saab` longevity run.
> Left empty deliberately; filling them from this draft would fabricate results.

### 7a. Enrichment (pooled MH RR)
| rule_id | N deaths | RR ADB | RR WD | RR LA | RR pooled | p (Bonf.) | Cochran Q p | Gate G1/G2 | Status |
|---|---|---|---|---|---|---|---|---|---|
| _(pending first run)_ | | | | | | | | | |

### 7b. Timing concordance (survival)
| rule_id | C-index rule | C age-alone | C duration-alone | Δ vs max(baseline) | 3σ noise floor | Gate G3 | Status |
|---|---|---|---|---|---|---|---|
| _(pending first run)_ | | | | | | | |

### 7c. Ayurdaya-band accuracy
| method | band accuracy | κ vs base-rate null | N | Status |
|---|---|---|---|---|
| _(pending first run)_ | | | | |

### 7d. Shuffled-chart null (G4)
| rule_id | real RR | null mean | null σ | z | empirical p | Gate G4 |
|---|---|---|---|---|---|---|
| _(pending first run)_ | | | | | | |

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
