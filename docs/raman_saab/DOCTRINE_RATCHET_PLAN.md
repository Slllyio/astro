---
date: 2026-07-02
type: design / plan
status: DRAFT — pre-review (awaiting sign-off before any code is written)
project: raman_saab population validation
author: drafted by agent from existing medini validation machinery
companion_to: docs/death_timing_findings.md
supersedes: nothing (new subsystem)
---

# raman_saab — Doctrine Ratchet Plan

> **This is a DRAFT specification, reverse-inferred from the existing medini
> validation code so that it fits the repo's conventions.** The task that
> spawned it referenced this file and `docs/death_timing_findings.md` as if
> they already existed; they did not. Nothing here has been implemented.
> **Open questions for the requester are collected in §10 — please resolve
> those before implementation begins.** Classical-doctrine specifics marked
> ⚑ must be pinned by the `bphs-doctrine-reviewer` subagent (per the
> `docs/doctrine-decisions.md` amendment process) before they can be treated
> as authoritative.

---

## 0. What "raman_saab" is

`raman_saab` is the working name for a **named doctrine set attributed to
B. V. Raman** — the 20th-century astrologer whose *Hindu Predictive
Astrology*, *How to Judge a Horoscope*, and *Three Hundred Important
Combinations* are among the most-cited English-language Parashari sources.
The repo already references a "BV Raman variant" as a distinct doctrinal
lineage — see `docs/doctrine-decisions.md` **D-7** (functional-nature table),
which explicitly lists *"BV Raman variant (Raman's Hindu Predictive
Astrology offers a partially different table, particularly for nodes)"* as an
alternative that the production engine did **not** lock.

The point of the `raman_saab` subsystem is to take Raman's rule set —
especially his **longevity / maraka (death-timing) doctrine**, which is the
first tranche and the subject of the companion `death_timing_findings.md` —
and **validate it as a population**, against the medini catalog of biographied
people, using the same statistical machinery the project already built for
Round-9/11 doctrine testing.

"Validate as a population" (a.k.a. *population validation*) means: rather than
asking "does this rule fit Gandhi's chart?" (the Stack-A canonical-chart
scaffold in `validate_framework_readings.py`), we ask **"across all ~75k
people with recorded life events, does a chart carrying Raman's rule show the
predicted event at a rate meaningfully above the base rate, and does that
survive the project's standard confound controls and cross-corpus
replication?"**

---

## 1. What "Doctrine Ratchet" means

The **ratchet** is the governance mechanism, not a statistic. It is a
**monotonic promotion ladder** for individual doctrine rules. A rule only ever
moves *up* the ladder when it clears a gate; it is never silently loosened
(exactly the discipline `docs/doctrine-decisions.md` already enforces for the
production lockfile, and the antidote to the "one more test" trap catalogued in
`docs/round9_lessons_learned.md` §12).

Each Raman rule (see the catalogue seed in `death_timing_findings.md` §3)
carries a **status** field:

| Status        | Meaning                                                                 | Entry condition |
|---------------|-------------------------------------------------------------------------|-----------------|
| `candidate`   | Transcribed from Raman's text, cited, not yet tested.                   | Citation pinned ⚑ |
| `provisional` | Shows lift/RR in the predicted direction on ≥1 corpus.                  | Passes G1 on any corpus |
| `validated`   | Survives the full gate on the **pooled** estimate + replicates.         | Passes G1–G4 (§4) |
| `locked`      | Promoted into a real doctrine decision (a `D-nn` in the lockfile).      | Human sign-off + `bphs-doctrine-reviewer` audit |
| `refuted`     | Fails in the predicted direction, or inverts, after full power.         | Fails G1 at target power, terminal |

**Ratchet invariants** (enforced by the harness, not by convention):

1. **Monotonic.** A rule may move `candidate → provisional → validated →
   locked`, or to `refuted`. It may **never** move back down to hide a
   failure. A previously-`validated` rule that fails a later, larger run is
   re-labelled `contested` and frozen — its prior verdict JSON is retained,
   never overwritten (mirrors the lockfile's "never silently edit" rule).
2. **Pre-registered gate.** The gate thresholds (§4) are fixed in
   `raman_ratchet.toml` **before** the run. This is the pre-registration
   discipline from `round9_lessons_learned.md` §"next-time checklist".
3. **Kill criterion.** Per lessons-learned §12: **3 consecutive `refuted`
   verdicts in a doctrine family halts that family** — no more tests without a
   new hypothesis. The ratchet records the halt; it does not keep grinding.
4. **Ledger, not prose.** The authoritative state of every rule lives in a
   machine-readable ledger (`docs/raman_saab/RATCHET_LEDGER.json`), append-only,
   one row per (rule_id, run_id, status-transition). The `VERDICT.md` files are
   human-readable renders of the ledger, never the source of truth.

The ratchet is deliberately **decoupled from `docs/doctrine-decisions.md`**:
a rule reaching `validated` does **not** auto-edit the production lockfile.
Promotion to `locked` is a separate, human-gated step (§7) precisely because
the lockfile feeds `Meta.doctrine_config` in every shipped reading.

---

## 2. Design constraints inherited from prior rounds

These are non-negotiable, taken straight from `docs/round9_lessons_learned.md`.
The whole reason to reuse the existing machinery is that it already encodes
these hard-won lessons.

| Constraint | Source | How the ratchet honours it |
|---|---|---|
| **3-corpus replication is the MINIMUM, not optional** | lessons §2 | Every gate evaluates the Mantel-Haenszel **pooled** RR across ADB+WD+LA, plus Cochran's Q heterogeneity. No single-corpus promotions past `provisional`. |
| **Birth-date-proxy confound** (chart features = birthdate in disguise) | lessons §"meta-insight" | Every model carries `birth_jd` (day precision) as a control, never `birth_year` alone. |
| **Exposure-time confound** (longer dasha ⇒ more events) | lessons §1 | Rate ratios are **exposure-adjusted Poisson** on person-days, not raw event counts. |
| **Selection / documentation bias** | lessons §2 | Cross-corpus pooling + per-corpus heterogeneity flag; within-person controls where applicable. |
| **Age-pattern confound** (death clusters in old age) | lessons §4 | Survival tests run **age-alone and duration-alone baselines simultaneously**; a rule must beat both. See `death_timing_findings.md` §5. |
| **"Looks like signal, controls reveal confound" fires late** | lessons §1 | Confound checks are a **pre-flight gate** (§6), run before the headline metric, not after. |
| **Prediction-trap ban** | kundli spec §11; `tests/reading/famous_charts/ramana_maharshi.json` "structural_notes" | Outputs report *statistical association only*. No `VERDICT.md` may phrase a result as "this chart predicts this person's death." Framing is population base-rate lift, never individual fate. |

---

## 3. Architecture — reuse, don't reinvent

The project already has **two** validation stacks (mapped below). `raman_saab`
is a thin orchestration layer that drives **both** and writes ledger entries.

### Stack A — Framework Reading validation (the astrologer's-lens engine)
- `app/core/reading_composer.compose_reading(chart, ctx, *, transit_signs=…, vimshottari_md_lord=…) -> Reading`
  → `Reading.bhava_claims[bhava].verdict_label ∈ {strong, medium, weak, afflicted}`.
- `app/medini/ml/framework_event_validation.py` — the **lift** harness
  (P(label|event) / P(label|baseline)), interpretation bands `>1.20` signal /
  `0.85–1.20` null / `<0.85` inverted.
- `app/medini/ml/validate_framework_readings.py` — canonical-chart scaffold
  (Gandhi/Indira/Nehru vs expert-expectation tables). `raman_saab` extends the
  expert table with Raman's own published readings (⚑ cite per chart).

### Stack B — Dasha-doctrine statistical validation (rate-ratio / survival)
- `app/medini/ml/dasha_doctrine_pooled.py` — Mantel-Haenszel pooled RR +
  Cochran's Q across ADB/WD/LA, with cross-corpus dedup by `birth_jd`,
  Bonferroni on pooled estimates.
- `app/medini/ml/dasha_doctrine_structural.py` — karaka-stripped scorer +
  **20-permutation shuffled-chart null** (z-score + empirical p).
- `app/medini/ml/stage_d_*` — survival pipeline (Cox / DeepHit), the
  **G1–G4 gate** (`stage_d_evaluate.evaluate_gate`), the noise-floor bootstrap
  (`scratch_bootstrap_noise_floor.py`), and the anti-leakage pre-flight
  (`stage_d_preflight.py`).

### New code (the only net-new surface)
```
app/medini/ml/raman_saab/
  __init__.py
  rules.py          # the Raman rule catalogue as data (id, family, citation ⚑,
                    #   antecedent predicate over a natal/dossier row,
                    #   consequent event_class, predicted direction, status)
  predicates.py     # pure functions: does a chart satisfy rule R? (reuse
                    #   bayesian_rule_validation.py predicates where they exist)
  ratchet.py        # the promotion engine: reads rules.py + run outputs,
                    #   applies gate (§4), writes RATCHET_LEDGER.json
  population_validate.py  # orchestrator: for each rule, dispatch to Stack A
                    #   (lift) and/or Stack B (pooled RR / survival), collect
                    #   verdicts, hand to ratchet.py
  cli.py            # python -m app.medini.ml.raman_saab.cli --family longevity
```
Config: `docs/raman_saab/raman_ratchet.toml` (pre-registered gate thresholds).
Output: `docs/raman_saab/RATCHET_LEDGER.json` + per-run
`data/ml_runs/raman_saab/<run_id>/VERDICT.md`.

**The doctrine rule library already exists** and should be the seed, not a
rewrite: `app/medini/ml/bayesian_rule_validation.py` contains ~40 cited rules
including the maraka/longevity set (`saturn_in_8th_longevity`,
`mars_in_8th_violence`, `ketu_in_8th_spiritual_end`, `rahu_in_8th_unusual_death`,
`lord_of_8th_in_dusthana`, cardiac `sun_afflicted`), and
`app/medini/ml/survival_analysis.py` encodes `EVENT_FUNCTIONAL_HOUSES`
(death → 8th; death-by-disease → 6th+8th) and `EVENT_KARAKAS`
(death → Saturn). `raman_saab/rules.py` should **wrap and re-cite** these
against Raman's texts, adding only what Raman's doctrine contributes beyond
the generic BPHS set.

---

## 4. The gate (pre-registered)

A rule is promoted to `validated` only if it clears **all four** gates on the
**pooled** estimate. Thresholds are the pre-registered defaults; overridable
only in `raman_ratchet.toml` **before** a run, never after seeing results.

- **G1 — Effect present, correct direction.** Pooled MH rate ratio
  `RR_pooled ≥ 1.20` (or `≤ 0.83` for a depletion rule) with one-sided
  `p < α`, **α = 0.01 Bonferroni-corrected** across the rules tested in the
  run (matches `dasha_doctrine_pooled` default). For Stack-A lift rules, the
  equivalent is `lift ≥ 1.20` **plus** a permutation p (the current lift
  harness lacks a significance test — see §8 gap #1; `raman_saab` must add it).
- **G2 — Homogeneous across corpora.** Cochran's Q heterogeneity
  `p_Q > 0.05` (the 3 corpora are estimating the same effect, not
  averaging a real effect in one with noise in others).
- **G3 — Beats the null model.** For survival/timing rules, the rule's
  concordance improvement over the **simultaneous** age-alone and
  duration-alone baselines must exceed **3× the bootstrap noise floor**
  (`stage_d_evaluate` G-logic; noise floor per `scratch_bootstrap_noise_floor`,
  with its documented "conservative-for-FAIL / invalid-for-PASS" caveat
  respected — a PASS requires a *real* 20-seed noise floor, not the bootstrap).
- **G4 — Survives shuffled-chart null.** Real effect must exceed the
  20-permutation shuffled-natal-chart null (`dasha_doctrine_structural`
  z-score, empirical `p < 0.05`).

`provisional` requires only G1 on **any one** corpus. `refuted` = fails G1 in
the predicted direction at the pre-registered target power (§ power note below).

**Power / stop rule.** Per lessons §11, if the stdev across 5 subsample seeds
is `< 0.25 × |mean|`, the verdict is locked — do not buy more seeds. The
ratchet records "power-sufficient FAIL" vs "underpowered" distinctly; only the
former can drive a rule to `refuted`.

---

## 5. Verdict output schema

Two artifacts per run, both rendered from the ledger:

1. **`RATCHET_LEDGER.json`** (append-only, source of truth). One row per
   status transition:
   ```json
   {
     "rule_id": "raman.maraka.saturn_in_8th",
     "family": "longevity",
     "run_id": "2026-07-02T…",
     "from_status": "candidate", "to_status": "provisional",
     "gate": {"G1": true, "G2": null, "G3": null, "G4": null},
     "stats": {"rr_pooled": 1.31, "p": 0.004, "q_p": 0.21,
               "per_corpus": {"ADB": 1.4, "WD": 1.2, "LA": 1.1}, "n": 11285},
     "citation": "Raman, How to Judge a Horoscope, Vol. II, ch. …",  // ⚑
     "confounds_checked": ["birth_jd", "exposure_days", "age_baseline"],
     "notes": "…"
   }
   ```
2. **`VERDICT.md`** — human render, in the exact shape of
   `docs/ml_runs/framework_validation_v1_VERDICT.md`: Question → Methodology →
   Results table → Verdict → confirms/overturns → caveats → next steps →
   Status. This keeps the family's outputs comparable with the 12 prior rounds.

---

## 6. Pre-flight (runs before any headline metric)

Reuse `stage_d_preflight.py` guards, adapted:
- **Chart-shuffle collapse**: shuffling event labels must drive the metric to
  its null (lift → 1.0 / C-index → 0.5). If it doesn't, the pipeline leaks.
- **No JD/`death*` columns in features** (leakage guard).
- **Person-leak assertion** (a person's own future event can't be a feature).
- **Class qualification**: each rule's consequent event class needs enough
  positives (death class currently has N≈11.3k in `event_dossier` — ample).
- **Confound presence**: assert `birth_jd` and exposure-days columns are
  actually joined before the RR is computed (not silently dropped).

---

## 7. Promotion to `locked` (the only path that touches production)

`validated → locked` is **out of scope for the automated harness**. It
requires, in order (mirroring `docs/doctrine-decisions.md` "Amendment
process"):
1. A human decision to adopt the rule.
2. A `bphs-doctrine-reviewer` subagent audit confirming the classical citation.
3. A new `D-nn` entry appended to `docs/doctrine-decisions.md` (or an
   amendment to an existing one, e.g. D-7's Raman variant).
4. The rule's ledger row updated to `locked` with a back-reference to the
   `D-nn`.

The harness stops at `validated` and *proposes* the lockfile diff; it never
writes it.

---

## 8. Known prerequisites & risks (discovered while drafting)

**These are blockers or hazards a code-writing session will hit immediately.**

1. **⛔ Stack B is import-fragile — scorer modules are missing.**
   `dasha_doctrine_pooled.py`, `dasha_doctrine_structural.py`,
   `stage_d_features.py` all import `app/medini/ml/dasha_doctrine_score.py`,
   `…_score_mix.py`, `…_score_strength.py` — **none of which exist in the
   repo** (`ModuleNotFoundError` on import; only `tests/test_dasha_doctrine_scorers.py`
   and docstrings reference them). The scorer *contract* is reconstructable
   from the test file (`doctrine_relevance = HR + KR + func_mod`, `_HOUSE_MAP`,
   `_KARAKA_MAP`, `dignity_strength`, `_scorer_for`). **Building `raman_saab`
   on Stack B requires first restoring or re-deriving these three modules.**
   This is the single largest hidden cost and needs a decision (§10 Q3).
2. **⛔ The catalog parquets/duckdb are not committed.**
   `app/medini/data/` contains only `README.md` + `__init__.py`. Every table
   this plan relies on (`persons`, `events`, `event_dossier`,
   `dasha_windows`, `events_with_dasha`, `v_event_survival`, …) is a
   **generated artifact** produced by the `app/medini/etl/build_*.py`
   pipeline. A build session must first run the ETL (rebuild sequence in
   `docs/data_dictionary.md`) or obtain the artifacts. Same for the
   per-corpus files Stack B expects (`*_dasha_corpus.parquet`,
   `*_natal_lord_houses.parquet`) and `readings.parquet` (Stack A lift).
3. **Corpus data-quality limits** (affect which rules are testable — detailed
   in `death_timing_findings.md` §6):
   - **WD** persons have `birth_jd = NaN` (day precision) → noon-UTC ascendant
     fallback → **house-based maraka rules are unreliable for the WD cohort**.
   - **LA** event dates are dasha-window **midpoints**
     (`approx_window_midpoint`) → **unusable for fine death-timing**; LA can
     contribute to base-rate/enrichment but not to timing-precision claims.
4. **Lift harness has no significance test** (`framework_event_validation.py`
   computes lift only; VERDICT v1 flags this). `raman_saab` must attach a
   permutation p to any Stack-A lift before G1 can pass on it.
5. **Smoke-test inflation trap** (VERDICT v1 §"smoke-test inflation"):
   sequential `head(N)` sampling of a corpus is stratified, not random, and
   inflated smoke lifts to 1.6–1.74. All `raman_saab` sub-N runs must sample
   randomly; report dropped/sampled counts explicitly (no silent truncation).

---

## 9. Phased build order (once §10 is resolved)

1. **Phase 0 — unblock data.** Restore/re-derive the three `dasha_doctrine_score*`
   modules (Q3); run the ETL to materialize the catalog (Q4). Gate: `import`
   of `dasha_doctrine_pooled` succeeds; `catalog.duckdb` builds.
2. **Phase 1 — rule catalogue.** `rules.py` + `predicates.py` for the
   **longevity/maraka family only** (the death-timing tranche), seeded from
   `bayesian_rule_validation.py` + `survival_analysis.py`, re-cited to Raman ⚑.
3. **Phase 2 — harness.** `population_validate.py` wiring rules → Stack A lift
   (with new permutation p) and Stack B pooled RR + survival; `ratchet.py`
   ledger + gate. Pre-flight wired first (§6).
4. **Phase 3 — first run + VERDICT.** Longevity family end-to-end; write
   `RATCHET_LEDGER.json` + `VERDICT.md`; populate the findings tables in
   `death_timing_findings.md` §7.
5. **Phase 4 — expand families** (marriage/7th, career/10th, …) only after the
   longevity family validates the harness end-to-end.

---

## 10. Open questions — must be answered before implementation

1. **Scope of first tranche.** The task says "population validation"; this plan
   assumes the **longevity/maraka (death-timing) family first** (matching the
   `death_timing_findings.md` companion). Confirm, or name a different family.
2. **`raman_saab` = B. V. Raman?** Confirm the honorific resolves to B. V.
   Raman and that his texts are the citation authority. If it's a different
   "Raman" (e.g. Ramana Maharshi, who *is* a chart fixture in the repo but is
   not a doctrine author), the entire doctrine-source basis changes.
3. **Missing scorer modules (risk §8.1).** Restore from history/backup,
   re-derive from the test contract, or **avoid Stack B** and validate on
   Stack A (framework lift) only? This is the biggest fork in cost.
4. **Data availability (risk §8.2).** Do the generated parquets/duckdb exist
   somewhere (they're gitignored), or must a build session run the full ETL?
   The latter needs ephemeris inputs and is a multi-step job of its own.
5. **Do you have Raman's actual published chart readings** to seed the
   Stack-A expert-expectation tables (`validate_framework_readings.py` style),
   or should that scaffold stay generic-BPHS for v1?
6. **Longevity-band reconciliation.** The repo hard-codes died-young `< 50` /
   long-life `≥ 80` (`derive_event_targets.py`). Raman's classical bands are
   Alpayu / Madhyayu / Purnayu with different cutoffs ⚑. Which governs? (See
   `death_timing_findings.md` §4.)

---

## Files referenced

- `docs/doctrine-decisions.md` — production doctrine lockfile (D-1…D-18; D-7 names the Raman variant; D-9 the Marana Karaka Sthana table)
- `docs/round9_lessons_learned.md` — the 5-null retrospective and confound/gate discipline this plan inherits
- `docs/ml_runs/framework_validation_v1_VERDICT.md` — the verdict format to mirror
- `docs/death_timing_findings.md` — the death-timing methodology (companion)
- `app/medini/ml/framework_event_validation.py` — Stack-A lift harness
- `app/medini/ml/validate_framework_readings.py` — Stack-A canonical-chart scaffold
- `app/medini/ml/dasha_doctrine_pooled.py` — Stack-B Mantel-Haenszel pooled RR + Cochran Q
- `app/medini/ml/dasha_doctrine_structural.py` — Stack-B shuffled-chart permutation null
- `app/medini/ml/stage_d_evaluate.py` / `stage_d_preflight.py` — G1–G4 gate + anti-leakage pre-flight
- `app/medini/ml/bayesian_rule_validation.py`, `survival_analysis.py` — the existing cited maraka/longevity rule library to seed from
- `scratch_bootstrap_noise_floor.py` — noise-floor bootstrap (with its PASS/FAIL caveat)
- `docs/data_dictionary.md` — catalog schema + ETL rebuild sequence
