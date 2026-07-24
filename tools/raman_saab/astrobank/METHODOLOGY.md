# AstroDatabank Real-Outcome Validation Program — methodology & governance

> The Prime Directive commands: *"Measure honestly. Distinguish textbook fidelity from real-outcome
> generalization; report both; overfitting to worked examples is not accuracy."* The golden ratchet
> measures textbook fidelity (261/293). This program measures the second axis — does the engine
> predict **real lives** — at scale (~65k celebrity charts, ~31k dated events), meticulously.

## Governance (locked)

1. **Golden-ratchet sovereignty.** Astrobank results are a *monitoring axis only*. No engine
   constant, threshold, or rule may be tuned from these results directly. Any engine change they
   motivate goes cite → bphs-doctrine-reviewer → zero-golden-regression (261/293 remains supreme).
2. **Pre-registration.** `mapping/category_house_map.csv` is the pre-registration: directions,
   strengths, min-n, contrasts, and confound notes are locked (with BPHS/Raman citations) BEFORE any
   verdict is scored. Post-hoc edits require a new `mapping_version` and archive the old results.
   Only `status=locked` rows are scorable; `rejected` rows document why a tempting mapping is unsound.
3. **Anti-peeking order.** The sham mapping + permutation-uniformity checks run and PASS before any
   Tier-1 result is read. Tier-2 is scored only after the pilot's negative controls behave.
4. **Privacy/size.** All data (source CSVs, parquets, results JSON) stays under gitignored `data/`.
   Committed: code, this doc, the mapping tables, the baseline JSON, the ratchet test.

## Corpus decisions (Stage 0, evidence-logged)

- **Sources.** `raw_holos_full.csv` (61.6k, ALL AA/A — the master taxonomy corpus) + `raw_wayback.csv`
  (snapshot-deduped by richest categories) form the `celebrity_databank` population.
  `raw_lunarastro_aa.csv` people are `population='app_user'` — **excluded from all cohorts and
  controls** (different selection process/base rates; flattened categories).
  `raw_lapaas.csv`/`raw.csv` are excluded entirely (no ratings, no usable labels).
- **Lunarastro supplies NOTHING to celebrity records** — not the chosen record, not time upgrades.
  Evidence (Stage-0 spot-check): its times can be flatly wrong while claiming AA with matching
  coords (Einstein 09:23 vs the canonical 11:30). The pre-registered time-upgrade rule is DISABLED;
  the build counts would-fire upgrades (1,725) as a no-op for the record.
- **Quality tiers (pre-registered):** A = AA ∧ minute-precision; B = {AA,A} ∧ ≤ quarter;
  C = {AA,A,B} ∧ any non-noon time. Noon-default/unknown times are excluded outright (cusps
  meaningless). Celebrity tiers: A=15,007, B=24,701 (A+B=39,708), C=21,766.
- **Gate outcome:** 9/10 cohorts ≥60% tier-B survival. **H8_LONGLIFE = 52.3% — consciously
  accepted** (documented relaxation): the shortfall is era-bias (long-lived ⇒ born earlier ⇒
  round-hour records), the cohort retains n≈3,855 at tier A+B (ample), and the decade
  stratification addresses the era confound directly.
- **Person identity:** `pid = sha1(normalized_name | birth_date)`; namesakes with different dates
  separate; events join ONLY on corpus-unique normalized names; 40 longevity
  category-vs-event contradictions quarantined.

## Statistical protocol (Stage 3)

- Unit: person × mapped signification; outcome = verdict ordinal (afflicted=0 mixed=1 favourable=2).
- **Primary:** one-sided Mann-Whitney U, case vs labeled contrast, in the pre-registered direction;
  reported as AUC + bootstrap 95% CI (1,000 resamples). **Secondary:** continuous `degree`.
  Tertiary: χ² on afflicted-rate. Corpus-control comparisons are SECONDARY by design (unlabeled ≠
  negative — catalog absence is not outcome absence); H12_PRISON is flagged the weakest design.
- **Confounds:** celebrity population only; stratified birth-decade × latitude-band; per-stratum U
  combined by inverse-variance; permutation null within strata.
- **Multiplicity:** Benjamini-Hochberg FDR q=0.10 per family (static / timing). Exploratory tier
  reported descriptively, never as claims.
- **Minimum effect of interest:** AUC ≥ 0.55 → "supported"; 0.50–0.55 with q<0.10 → "weak signal";
  else null. Min-n: 100 core / 30 supporting (wide-CI flagged).
- **Ayurdaya axis:** AUC of predicted `total_years` separating SHORTLIFE vs LONGLIFE; class-match;
  Spearman vs actual `age_at_death` where events give it.

## Timing protocol (Stage 4)

- `active_houses` is NOT used (proven saturated: ~10.5/12 houses active). Windows come from
  `timer_set`/`significator_dasha_windows` + maraka periods, materialized in the Stage-2 store.
- **Within-chart control-date null:** each real event vs K=min(20, span−1) control dates uniform in
  [age 15, min(death−1yr, age 75)], ±1yr blackout around same-root events; paired lift;
  person-clustered bootstrap (2,000). Coverage fraction reported per test; gate: coverage <0.6 else
  the test is redesigned, not reported.
- **Precision rule:** full-date events → AD-level windows, point-in-interval. Year-only events →
  MD-level, ≥0.5-overlap of the event year. Never mixed in one test.
- **Death timing:** real death date vs controls against maraka windows; controls capped at
  death−1yr; no leakage (predicted-span windows only).

## Ratchet (Stage 5)

`real_outcome_baseline.json` records mapping/person-master/engine hashes + per-core-test floors
(observed − 1.5·bootstrap-SE). `tests/raman_saab/test_astrobank_ratchet.py` skips when data absent
(CI-safe), skips LOUDLY on hash mismatch, else asserts floors. Bumps only via
`update_baseline.py --confirm` with a reasoned commit message.
