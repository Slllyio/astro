# Round 9 Plan — Honest Foundation + 16-Yoga Statistical Wedge (revision 2)

**Plan date**: 2026-05-21 (post-audit revision 2, post-review)
**Supersedes**: `C:\Users\S.C.C\.claude\plans\first-litsen-to-me-warm-fern.md` (original single-yoga wedge plan)
**Reason for this revision**: incorporates the structural-review findings (phase renumbering, explicit baseline + glossary, behavioral-first classical gate, event corpus before catalog, tightened statistical gate with replication, decision-point gates on later phases).

---

## Glossary

Terms used throughout this plan, in order of first appearance:

| Term | Definition |
|---|---|
| `screening_career.parquet` | Per-person binary cohort (`app/medini/data/screening_career.parquet`). 951 rows, 542 cols. `is_event_X=1` if the person has ≥1 career-class biographical event in Astro-Databank, 0 if era-matched random negative. Built by Round-8.5 `build_screening_cohort.py`. **Cannot test timing yogas** — no `event_date` for negatives. |
| `event_corpus_career.parquet` | **Does not exist yet** — Phase 3A builds it. Per-(person, event_date) rows for career-class events. Carries `active_md_lord`, `active_ad_lord`, `active_pd_lord`, `event_jd`. The only substrate that can fairly test timing yogas like Vipareeta Harsha (whose mechanism is "fires under 6L's dasha"). |
| `baseline` (for ML eval) | The exact column set in `screening_<class>.parquet` (Round-8.5 honest substrate), with all yoga-derived columns excluded. Concretely: `_coerce_features(df, lean=False)` in `app/medini/ml/round8_screening_eval.py` MINUS any column starting with `yoga_`, `harsha_`, `raja_`, `dhana_`, `gajakesari_`, etc. **All Δ AUC measurements are vs this baseline.** |
| `yoga_strength` | Float ∈ [0, 1] computed by `app/core/yoga_strength.py`. For non-Vipareeta yogas: `sthana_bala_total / max_ceiling[planet]`. For Vipareeta yogas: `1 − (sthana_bala_total / max_ceiling[planet])` (inverted per BPHS 36). Multiplied by drishti enhancement/affliction modifier. |
| `noise floor` | σ_Δ measured by running the baseline-vs-(baseline + 1 column of N(0,1) noise) eval across 20 seeds per substrate. Sets the minimum detectable effect. Measured BEFORE any wedge eval runs. |
| `bootstrap 95% CI` | 1000-resample bootstrap on the holdout indices, yielding lower/upper bounds on the AUC delta. The Phase-0 wedge audit used this; revisited in `wedge_eval_v2.py`. |
| `BPHS-compliance test` | A test that declares: (a) BPHS sloka reference, (b) canonical example chart from a published source, (c) expected behavior (hit/miss + strength rank, NOT raw virupa). Lives in `tests/bphs_compliance.py`. |
| `reference chart` | One of 5 charts pinned against Jagannatha Hora outputs (Bangalore baseline + Ramana Maharshi + J. Krishnamurti + Indira Gandhi + Mother Teresa). The pinning is *behavioral first* (presence/absence + ordering), with numeric ±5% as a secondary check. |
| `YSH-CM` | Yoga-Slot Hierarchical Causal Model. PyTorch model whose forward pass IS the astrologer's reasoning chain: `signal_s = present_s × strength_s × dasha_gate_s × transit_gate_s × V[event_class, s]`. Defined in original plan §4; unchanged here. |
| `Gate` | A named falsifiable checkpoint. Numbered (Gate 0, Gate 1, ...). The plan does not continue past a failed gate without explicit re-planning. |

---

## Context — what the audit changed

The original plan made five assumptions that proved unsafe in practice:

1. **"+0.02 from a single yoga = signal."** Bootstrap on the actual eval gave a 95% CI of [−0.0122, +0.0329] on the AUC delta — the gate was set below the noise floor. With a test set of n=191 (67 positives), single-yoga effects under ~0.05 AUC are statistically undetectable.
2. **"Natal yoga strength is a fair test."** Vipareeta Harsha is fundamentally a *timing* yoga (its BPHS mechanism is "fires under the 6L's dasha"). A natal-only column is constant per person — degenerate for the structural hypothesis. The screening cohort, by construction, cannot test timing yogas.
3. **"Classical rules are obvious."** The BPHS reviewer found three independent classical-fidelity errors in one detector (over-permissive rule, wrong strength sign, mis-calibrated virupa table). Empirical confirmation: low-strength yoga-havers had 39% career-event rate, high-strength had 29.8% — the strength was monotonically inverted from classical.
4. **"Single-seed eval is enough."** Multi-seed (0..9) showed mean Δ = −0.0072 and only 1/10 seeds with positive Δ. Seed 42 was the best-of-10 outlier; the original result was a lucky-seed artifact.
5. **"Strength = monotonic with Sthana-bala."** For Vipareeta yogas, classically weaker lord = stronger yoga. Our formula reversed this. Also the Sthana-bala formula itself had calibration errors (exalted=45 should be 20; no Moolatrikona; Mercury/Saturn missing Oja-Yugma; wrong ceiling for neuter planets).

The hypothesis — that astrologer-mimetic structural ML can outperform flat-feature XGBoost — **is not refuted**. What was refuted is *this particular implementation* and *this evaluation protocol*. The revised plan addresses both layers explicitly.

Intended outcome (unchanged): clear ≥ 0.65 AUC on career/fame OR ≥ 0.55 on a previously-noise class, with per-yoga interpretable predictions. But now with statistically-grounded gates and classical-fidelity infrastructure.

---

## The five structural changes from the audit

### Change 1 — Classical-fidelity becomes a hard prerequisite (Phase 0)

A new front-loaded phase. **No new yoga ships without passing this.** Gate is *behavioral-first*: correct dignity/yoga presence-absence + strength ordering, with numeric ±5% virupa match as a secondary check.

### Change 2 — Foundation block (Phase 1 + 2) is now properly scoped (~2 weeks)

The original "Sthana-bala only" Phase 0 was too narrow; some BPHS components (Naisargika-bala, full Saptavargaja with compound relation) are needed for the wedge to be a fair test.

### Change 3 — Replace single-yoga wedge with **16-yoga catalog wedge on dual substrate** (Phase 3)

Effectively merges the original Phase 0 wedge with early Phase 2. Tests the hypothesis with enough statistical power to be falsifiable. **Event corpus is built BEFORE the catalog** (Phase 3A precedes 3B) so the catalog can be evaluated on the right substrate as soon as it exists.

### Change 4 — Statistically-grounded gates everywhere (no more arbitrary thresholds)

Every wedge / eval gate has a measured noise floor and a statistical pass criterion (95% CI lower-bound > 0). Replication required if the gate passes by a tight margin (< 1.5σ above threshold).

### Change 5 — Explicit decision gates on later phases (4 / 6 / 7)

Phase 4 (full catalog), Phase 6 (YSH-CM), and Phase 7 (transformer) are **conditional on Phase 3C passing with robust, reproducible signal**. The fallback at each gate is documented, not assumed.

---

## Phases

### Phase 0 — Classical-fidelity infrastructure (1 week) — **HARD GATE**

**Goal**: build the substrate that prevents the recurring "we coded the wrong rule" failure mode.

**Files to add**:
- `docs/bphs_reference.md` — per-computation BPHS sloka citations. For each function in `app/core/dignity.py`, `shadbala.py`, `planet_state.py`, `yogas.py`, document: (a) BPHS adhyaya/sloka, (b) the rule as quoted, (c) any tradition we chose between when sources differ, (d) the chosen convention with rationale.
- `tests/bphs_compliance.py` — base test class with this contract per yoga / dignity / strength rule:
  ```python
  class BPHSComplianceTest:
      bphs_sloka_reference: str           # e.g. "BPHS 36.12-15"
      published_example_chart: str        # canonical chart for the case
      expected_behavior: dict             # presence/absence; strength ordering
      acceptable_numeric_tolerance_pct: float = 5.0   # secondary check only
  ```
- `tests/test_reference_charts.py` — 5 canonical charts pinned against Jagannatha Hora outputs:
  - Bangalore baseline 1990-07-15 12:00 IST (existing project anchor)
  - Ramana Maharshi 1879-12-30 01:00 IST Tiruchuli
  - J. Krishnamurti 1895-05-12 00:30 IST Madanapalli
  - Indira Gandhi 1917-11-19 23:11 IST Allahabad
  - Mother Teresa 1910-08-26 13:25 LMT Skopje (known Vipareeta case)

**Behavioral-first gate** (Tier 1 — must pass for every reference chart):
1. **Dignity correctness**: own/exalted/debilitated states match the canonical reading for each planet. Friend/neutral/enemy via compound relation matches Jagannatha Hora ordering.
2. **Yoga presence**: each yoga the canonical chart is known to carry is detected; each yoga it is known NOT to carry is NOT detected.
3. **Strength ordering**: across the 5 reference charts, the per-yoga strength ranking matches the canonical "stronger-than" relation (e.g., Indira Gandhi's Raja-Yoga set must rank above Ramana's).

**Numeric gate** (Tier 2 — secondary):
- Shadbala virupa totals within ±5% of Jagannatha Hora per planet
- If a chart fails Tier 2 but passes Tier 1, document the deviation in `docs/bphs_reference.md` (often a tradition difference, not a bug) and continue.
- If a chart fails Tier 1, **STOP** — there is a real classical-fidelity error.

**Gate to Phase 1**: all 5 reference charts pass Tier 1 (behavioral); ≥ 4/5 pass Tier 2 (numeric ±5%).

**Effort**: 1 week.

---

### Phase 1 — Audit-fix patch (3 days) — depends on Phase 0

Apply all 5 audit findings to the existing primitives. **Each fix paired with a BPHS-compliance test**.

| Fix | File:line | Change | Test |
|---|---|---|---|
| **Saptavargaja virupa table** | `app/core/shadbala.py:53-60` | Add `moolatrikona`=45, change `exalted` from 45 to 20, use compound (not naisargika) for friend/neutral/enemy distinction. Add `is_moolatrikona(planet, longitude)` helper in `app/core/dignity.py` with BPHS 3.20 ranges. | Pin against Jagannatha Hora |
| **Oja-Yugma for Mercury/Saturn** | `app/core/shadbala.py:_MALE_PLANETS` | Move Mercury and Saturn into `_MALE_PLANETS` (BPHS 27.28-30 treats them as masculine for parity). | Sun/Mars/Jupiter/Mercury/Saturn all get +15 in odd D1 |
| **Neuter-planet strength ceiling** | `app/core/yogas.py:_MAX_STHANA_BALA_PHASE_0` | Replace constant with `_max_sthana_bala_for_planet(planet)` returning 180 for Mercury/Saturn (no oja-yugma achievable), 210 for male/female. | Mercury in own 6th Virgo gets strength near 1.0, not 0.75 |
| **Vipareeta strength inversion** | `app/core/yogas.py:detect_vipareeta_harsha` | Add `invert_for_vipareeta=True` to the strength formula. Vipareeta strength = `1 − (sthana_total / ceiling[planet])` when present. Document BPHS 36 + Phaladeepika 6.39 inversion principle. | Debilitated 6L in 12th gets strength ≈ 1.0; exalted 6L in own 6th gets strength ≈ 0.1 |
| **"Alone in dusthana" gate** | `app/core/yogas.py:detect_vipareeta_harsha` | After confirming 6L in 6/8/12, check the 6L is NOT conjunct any kendra/trikona lord. If conjunct a benefic (Jupiter, Venus, well-disposed Mercury), return `None`. | Mercury in 12th conjunct Jupiter → yoga NOT detected |

**Gate to Phase 2**: all 5 fixes shipped, BPHS-compliance suite green, no regression in 201 existing tests.

**Effort**: 3 days.

---

### Phase 2 — Complete primitives (1 week)

Fill in everything Phase 1 left stubbed.

**Files**:
- `app/core/dignity.py` — extend with `is_moolatrikona(planet, longitude)`, `dignity_state_compound(planet, sign, chart)` returning the 5-tier compound state (adhi_mitra / mitra / sama / shatru / adhi_shatru), full dispositor chain helper.
- `app/core/shadbala.py` — complete six components:
  - Dig-bala (directional strength, kendra-aware)
  - Kala-bala (temporal: divama / nakta / paksha / triyamsha / abda / masa / vara / hora)
  - Cheshta-bala (motional: retrograde, fast/slow, vakra)
  - Naisargika-bala (constant per planet: Sun 60, Moon 51.43, Venus 42.85, Jupiter 34.28, Mercury 25.7, Mars 17.14, Saturn 8.57)
  - Drik-bala (aspectual strength from benefic vs malefic aspects on the planet's natal degree)
- `app/core/bhava_bala.py` — Bhavadhipati / Bhavadigbala / Bhavadrishti bala per house.
- `app/core/saptavargaja.py` — extract from `shadbala.py`, expand to all 7 vargas (D1, D2, D3, D7, D9, D12, D30) using `dignity_state_compound`. Phase-1 D1-only becomes a thin wrapper.

**Verification**: pin Shadbala totals against Jagannatha Hora on the 5 reference charts. **Behavioral first** (correct sign + ordering across charts); **numeric ±5% second**. Add ~50 new unit tests.

**Gate to Phase 3**: reference-chart pinning passes Tier 1 for ALL 5 charts and Tier 2 for ≥ 4/5.

**Effort**: 1 week.

---

### Phase 3 — Wedge block (event corpus → catalog → eval)

The Phase 2C from the previous revision, expanded to 3 sub-phases with the corpus built FIRST so the catalog never has to be tested only on the wrong substrate.

#### Phase 3A — Build `event_corpus_career.parquet` (3 days) — **runs FIRST in Phase 3**

The screening cohort cannot test timing yogas. The event corpus (per-(person, event_date) rows) can. Building this first means the catalog work in 3B can be incrementally evaluated against it as detectors come online.

**Action**:
- Extend `app/medini/etl/event_corpus.py` to confirm `active_pd_lord` is emitted alongside MD and AD (audit noted MD+AD only currently).
- Run:
  ```
  python -m app.medini.etl.event_corpus \
      --features app/medini/data/ml_astro_tier_a_dasha_kinematic.parquet \
      --events   data/astro_databank/events_all.csv \
      --raw      data/astro_databank/raw.csv \
      --event-root "career" \
      --output   app/medini/data/event_corpus_career.parquet
  ```
- Expected: ~656 positive rows + matched negatives (1:1 balanced lifespan sample). Each row carries `active_md_lord`, `active_ad_lord`, `active_pd_lord`, `event_jd`.

**Gate to 3B**: `event_corpus_career.parquet` exists with ≥ 1300 rows. All three dasha-lord cols non-null on ≥ 95% of rows. Name-group-split feasibility check passes (≥ 80% of test names not in train).

**Effort**: 3 days.

#### Phase 3B — Tier-1 yoga catalog (3-4 weeks)

Build **16 yogas** with YogaInstance type. Each yoga must pass BPHS-compliance tests before merging.

| Yoga family | Detectors | BPHS reference |
|---|---|---|
| Pancha Mahapurusha (UPGRADE existing) | Ruchaka, Bhadra, Hamsa, Malavya, Sasa (5) — convert from Yoga TypedDict to YogaInstance with strength | BPHS 36 |
| Vipareeta Raja | Harsha (fixed), Sarala (8L in 6/8/12), Vimala (12L in 6/8/12) (3) | BPHS 36 |
| Raja Yoga | Kendra-trikona lord conjunction (1 generic detector, ascendant-conditioned) | BPHS 36 |
| Dhana Yoga | 2nd + 11th lord interaction; 5th + 9th lord interaction (2) | BPHS 41 |
| Moon-based | Gajakesari (UPGRADE existing), Sunapha, Anapha, Durudhura, Kemadruma w/ cancellation (4) | BPHS 73-74 |
| Solar | Budha-Aditya (UPGRADE existing) (1) | BPHS 36 |

Total: 16 detectors. Phase 3B delivers the wedge cohort.

**Files**:
- `app/core/yogas/` — refactor flat `yogas.py` into package. Subfiles per family.
- `app/core/yoga_strength.py` — central scoring with `invert_for_vipareeta` flag. Strength formula:
  ```
  if vipareeta:
      strength = 1.0 − (sthana_total / max_ceiling[planet])
  else:
      strength = sthana_total / max_ceiling[planet]
  ```
  Plus drishti enhancement/affliction multiplier.

**Verification (per-yoga)**:
- BPHS-compliance test: declare sloka, published example chart, **expected behavior** (presence + strength rank — not raw virupa).
- Run on 50 charts from `data/astro_databank/raw.csv`: detector hit-rate matches classical prevalence estimates within ±50%.
- Each detector's tests inherit from `BPHSComplianceTest` (Phase 0 infrastructure).

**Gate to 3C**: 16 detectors complete, all BPHS-compliance tests green, hit-rate sanity checks pass.

**Effort**: 3-4 weeks.

#### Phase 3C — Wedge eval on dual substrate (1 week) — **THE FALSIFIABLE GATE**

Run all 16 yogas through eval on BOTH `screening_career.parquet` (natal component) AND `event_corpus_career.parquet` (timing component).

**Step 1 — Measure noise floor** (must run first, per substrate):
- For each substrate: run 20 seeds of baseline-vs-(baseline + one column of N(0, 1) Gaussian noise).
- Compute σ_Δ_holdout_AUC across the 20 seeds. **This is the noise floor.**
- Expected: σ ≈ 0.01-0.02 on screening (n=191 test), σ ≈ 0.005-0.01 on event corpus.

**Step 2 — Inject all 16 yogas**:
- For each yoga, two columns per substrate where applicable:
  - `<yoga>_natal_strength` (Phase-3B YogaInstance.strength)
  - `<yoga>_dasha_gated_strength` (only meaningful on event corpus; = natal × dasha_activation per yoga)
- One large `app/medini/etl/add_yoga_features.py` script processes the full catalog at once.

**Step 3 — Eval**:
- Per-substrate, run 10-seed holdout AUC measurement of baseline vs (baseline + 16-yoga columns).
- **Model-stability check (new)**: compute σ_model = std-dev of the 16-yoga-augmented model's holdout AUC across the 10 seeds. If σ_model > the measured holdout-AUC Δ_mean, the model is unstable — fail the gate regardless of point estimate.
- Per-yoga: bootstrap 95% CI on its marginal contribution (SHAP / leave-one-out).
- Per-yoga: XGBoost gain importance ranking.

**Tightened gate criteria** (ALL of the following must hold):
- (A) Mean holdout AUC Δ across 10 seeds ≥ 3σ_noise on at least one substrate, OR at least 3 individual yogas have bootstrap 95% CI lower-bound > 0 on at least one substrate.
- (B) σ_model ≤ Δ_mean (model is stable across seeds).
- (C) At least 5 yogas rank in top-50 by XGBoost gain importance.
- (D) **Replication clause**: if the gate passes by < 1.5× the threshold margin (i.e., within 1.5σ of failing), require a fresh 20-seed run on a different GroupShuffleSplit configuration (e.g., test_size=0.25 instead of 0.20) and rerun all three criteria. Counts as PASS only if both runs satisfy A/B/C.

**Decision point — what happens after the gate**:

| Outcome | Action |
|---|---|
| **PASS strong** (Δ_mean ≥ 2× noise floor; ≥ 3 yogas with CI > 0; replication confirms) | Proceed to Phase 4 (full catalog) |
| **PASS weak** (passes A/B/C but within 1.5× threshold; replication clause fires and confirms) | Proceed to Phase 4, but with the explicit caveat that the per-yoga effect sizes are modest — expect Phase 6 model AUC to land at the lower end of the acceptance window |
| **PASS weak; replication fails** | Treat as FAIL with partial signal (see below) |
| **FAIL with partial signal** (1-2 yogas have CI > 0, but cumulative doesn't clear noise floor) | Document non-passing yogas as "inconclusive". Re-plan Phase 4 to focus on the 1-2 yogas that did pass + expand corpus. Do NOT proceed to Phase 6 yet. |
| **FAIL with no signal** (no yoga has CI > 0; cumulative effect within noise) | **STOP.** Do not proceed to Phase 4/5/6/7/8. Pivot options: (a) build a larger corpus (Astro-Databank scrape expansion), (b) try a non-structural neural architecture (EGNN from astrov2/) on the honest substrate, (c) close the project as a defensible null result. |

**Effort**: 1 week (assuming Phase 3B delivered 16 working detectors).

---

### Phase 4 — Full ~80 yoga catalog (6-8 weeks) — **CONDITIONAL on Phase 3C PASS**

Only entered if Phase 3C passes. Expand from 16 to ~80 yogas using the same BPHS-compliance gate per yoga.

| Tier-2 family | New detectors |
|---|---|
| More Raja Yogas | Sun-Moon-Mercury, Dharma-Karmadhipati variants by ascendant, Adhi Yoga, Chamara |
| More Dhana Yogas | Lakshmi, Saraswati, Sankha, Akhanda Samrajya, Mahabhagya |
| Parivartana | Mutual sign exchange (closed-form, 66 pairs reducible to categories) |
| Kal Sarpa | Kal Sarpa Dosha + Kal Amrita variants |
| Neech Bhanga | 4 deterministic cancellation rules per BPHS 9 |
| Aristas | Pitra Dosha, Guru Chandala, Visha Yoga, Daridra, Nasha, Pravajya |
| Nabhasa | 32 Nabhasa Yogas (Akriti / Sankhya / Ashraya — closed-form) |

**Verification per yoga**: BPHS-compliance test (behavioral) + 50-chart hit-rate sanity.

**Gate to Phase 5**: full ~80-yoga catalog passes BPHS-compliance suite. Phase 3C wedge eval re-run with the full catalog still satisfies criteria A/B/C.

**Effort**: 6-8 weeks.

---

### Phase 5 — Causal feature schema (1 week)

Unchanged from original plan. `app/medini/etl/causal_features.py` produces per-(person, event_date) `CausalRecord` with yoga list + dasha activation per yoga + transit modulation per yoga.

**Gate to Phase 6**: `CausalRecord` emits non-zero `dasha_activation_per_yoga` for at least 30% of event-positive rows. Sanity inspection (Phase 3 hypothesis: dasha-activated yogas should plausibly tie to event class) passes on a 200-row sample.

**Effort**: 1 week.

---

### Phase 6 — YSH-CM model (2 weeks) — **CONDITIONAL on Phase 3C PASS + Phase 5 GATE**

The model whose forward pass IS the astrologer's reasoning chain. PyTorch model. Classical priors initialise V[event_class, slot].

**Gate to Phase 7**:
- Mean AUC ≥ 0.58 (vs 0.5240 baseline)
- AND at least one of {career, fame} ≥ 0.65
- AND at least one previously-noise class ≥ 0.55

**Phase 6b — Falsification fallback (3 days)** — runs only if Phase 6 gate fails. Two experiments documented in original plan (no learned gate; shuffled dasha-gate).

**Effort**: 2 weeks (+ 3 days for 6b if triggered).

---

### Phase 7 — Yoga-attention transformer (2 weeks, optional) — **CONDITIONAL on Phase 6 PASS**

Cloud-trained transformer attending over yoga slots, conditioned on event class + active dasha lord. Only if Phase 6 cleared its gate and there's headroom.

**Gate**: ≥ 0.05 AUC lift over Phase 6 model; otherwise keep Phase 6 model.

**Effort**: 2 weeks.

---

### Phase 8 — Interpretability layer (1 week) — **CONDITIONAL on Phase 6 PASS**

Per-prediction Vedic-astrologer report. Extends `chart_verbalizer.py` and `report_writer.py`.

**Effort**: 1 week.

---

## Revised timeline

| Phase | Effort | Cumulative | Conditional? |
|---|---|---|---|
| 0 — Classical-fidelity infrastructure | 1 wk | 1 wk | — |
| 1 — Audit-fix patch | 3 days | ~1.5 wk | gated by 0 |
| 2 — Complete primitives | 1 wk | ~2.5 wk | gated by 1 |
| 3A — Build event corpus | 3 days | ~3 wk | gated by 2 |
| 3B — Tier-1 yoga catalog (16 yogas) | 3-4 wk | 6-7 wk | gated by 3A |
| 3C — Wedge eval (dual substrate, bootstrap, replication) | 1 wk | 7-8 wk | gated by 3B |
| **GATE 1 (Phase 3C decision point)** | — | — | — |
| 4 — Tier-2+3 expansion to ~80 yogas | 6-8 wk | 13-16 wk | **CONDITIONAL on 3C PASS** |
| 5 — Causal feature schema | 1 wk | 14-17 wk | gated by 4 |
| 6 — YSH-CM | 2 wk | 16-19 wk | **CONDITIONAL on 3C + 5** |
| 6b — Falsification (if needed) | 3 days | +3 days | only if 6 fails |
| 7 — Transformer (optional) | 2 wk | 18-21 wk | **CONDITIONAL on 6 PASS** |
| 8 — Interpretability | 1 wk | 19-22 wk | **CONDITIONAL on 6 PASS** |

**Total**: 19-22 weeks (vs original 16). The +3-6 weeks goes into Phase 0 fidelity infrastructure, broader Phase 3 wedge, and the explicit conditional structure on 4/6/7/8.

---

## What stays the same as the original plan

- The 5-axis structural formula (PROMISE × STRENGTH × MODULATION × TIMING).
- The Round-8.5 honest substrate (career=0.61, fame=0.60, 6/10 noise) as the honest measuring stick.
- Locked decisions: Lahiri ayanamsa, `DAYS_PER_VEDIC_YEAR=365.2425`, whole-sign drishti, JD arithmetic.
- The YSH-CM architecture for Phase 6.
- The acceptance criterion for the whole plan (career or fame ≥ 0.65, OR any noise class ≥ 0.55).

---

## Critical files to modify / create

### Modify (extend, don't rewrite):
- `app/core/dignity.py` — add `is_moolatrikona`, `dignity_state_compound`
- `app/core/shadbala.py` — apply Phase-1 fixes; complete in Phase 2
- `app/core/yogas.py` → refactor to package `app/core/yogas/` in Phase 3B
- `app/medini/etl/event_corpus.py` — ensure `active_pd_lord` emitted

### Create:
- `docs/bphs_reference.md`
- `tests/test_reference_charts.py`
- `tests/bphs_compliance.py`
- `app/core/yoga_strength.py`
- `app/core/saptavargaja.py`
- `app/core/bhava_bala.py`
- `app/core/yogas/{mahapurusha,raja,dhana,vipareeta,moon,solar}.py`
- `app/medini/data/event_corpus_career.parquet`
- `app/medini/etl/add_yoga_features.py` (replaces single-yoga `add_harsha_feature.py`)
- `app/medini/ml/wedge_eval_v2.py` (replaces `phase0_wedge_eval.py` with proper bootstrap CIs + multi-seed + replication clause)

### Deprecate (after Phase 1 fixes):
- `app/medini/etl/add_harsha_feature.py` — superseded by add_yoga_features.py
- `app/medini/ml/phase0_wedge_eval.py` — superseded by wedge_eval_v2.py
- `data/ml_runs/phase0_wedge/` — keep as historical record, mark superseded

### Reuse unchanged:
- `app/core/ashtakavarga.py`, `avastha.py`, `antardasha.py`, `pratyantar.py`, `ephemeris_engine.py`, `shodashavarga.py`, `nadi_rules.py`
- `data/ml_runs/round8_master_eval/baseline_holdout_indices.parquet` — locked holdout, never regenerate
- `app/medini/data/screening_*.parquet` — honest substrate, used for natal-component eval

---

## Risks specific to the revised plan

1. **Phase 0 reference-chart pinning fails Tier 2 (numeric ±5%) on multiple charts.** Likely cause: Shadbala formula has further bugs, OR Jagannatha Hora uses a different convention (e.g., Mercury combustion orb 12 vs 14, recension difference). Mitigation: Tier-1 behavioral-first design accepts this; document each numeric deviation in `docs/bphs_reference.md` with the convention rationale.
2. **Phase 3C noise floor is higher than the per-yoga lift.** This is the "honest result" case — the 16 yogas individually contribute less than the eval can detect. Mitigation: the cumulative-effect criterion (A) handles this case explicitly; if even cumulative effect doesn't clear 3σ, the FAIL-with-no-signal decision is documented.
3. **`event_corpus_career.parquet` build fails** because `event_corpus.py` has implicit dependencies on intermediate files. Mitigation: Phase 3A runs first (3 days) precisely so this failure mode surfaces BEFORE the 3-4-week catalog work.
4. **Yoga catalog falsifies the classical literature.** If 5+ of the 16 Tier-1 yogas have empirical effect direction OPPOSITE to BPHS prediction (e.g., Lakshmi Yoga lowers wealth in our cohort), it's evidence of corpus bias or cultural mismatch. Mitigation: flag any such reversal explicitly in the report; treat as data finding, not just code bug.
5. **Classical-fidelity test suite becomes a bottleneck.** If every new yoga requires 1-2 days of BPHS-citation research, Phase 4 (80 yogas) balloons to 16+ weeks. Mitigation: template the compliance test in Phase 0; reference chart can be re-used across yoga families.
6. **Phase 3C passes weakly, replication clause fires, replication fails.** Documented in the decision-point table as "FAIL with partial signal" — do NOT proceed to Phase 6 yet; replan Phase 4 to focus on the passing yogas + corpus expansion.

---

## Verification — end-to-end test of the changes

After each phase, run:

```powershell
# Phase 0 gate:
pytest tests/test_reference_charts.py tests/bphs_compliance.py -v
# Must pass Tier 1 for all 5 charts; Tier 2 for ≥ 4/5

# Phase 1 gate (audit fixes):
pytest tests/test_dignity.py tests/test_shadbala.py tests/test_vipareeta_harsha.py tests/test_reference_charts.py -v
# Plus: 201 existing tests still pass (no regression)

# Phase 2 gate:
pytest tests/test_shadbala.py tests/test_bhava_bala.py tests/test_saptavargaja.py tests/test_reference_charts.py -v

# Phase 3A gate:
test -f app/medini/data/event_corpus_career.parquet
python -c "import pandas as pd; df = pd.read_parquet('app/medini/data/event_corpus_career.parquet'); assert len(df) >= 1300; assert df['active_md_lord'].notna().mean() > 0.95"

# Phase 3B gate:
pytest tests/test_yogas/ -v  # 16 detectors green + BPHS compliance

# Phase 3C gate (the falsifiable wedge):
python -m app.medini.ml.wedge_eval_v2 \
    --substrates screening,event_corpus \
    --seeds 0..9 \
    --bootstrap 1000 \
    --measure-noise-floor \
    --replication-on-weak-pass \
    --report data/ml_runs/round9_wedge/

# Gate pass criteria (must satisfy A, B, C; D fires if borderline):
# (A) mean Δ ≥ 3σ_noise on at least one substrate OR ≥ 3 yogas with bootstrap CI lower-bound > 0
# (B) σ_model ≤ Δ_mean (model stable across seeds)
# (C) ≥ 5 yogas in top-50 XGBoost gain importance
# (D) if pass margin < 1.5× threshold, rerun with different split config
```

**Acceptance for the whole plan** (unchanged):
- Mean holdout AUC ≥ 0.58 (vs 0.5240) → publishable result
- career or fame ≥ 0.65 → real architectural improvement validated
- Any noise class ≥ 0.55 → structural signal exists where flat features couldn't find it
- Predictions are human-readable per-yoga (Phase 8) → meets user's "model reasons like an astrologer" requirement

---

## Appendix A — Audit findings preserved for reference

The Round-9 wedge audit (this session) produced four parallel reviews. The findings:

**BPHS reviewer (8 findings)**: Vipareeta strength inverted (CRITICAL), detector too permissive (CRITICAL), Saptavargaja virupa miscalibrated (HIGH), Oja-Yugma Mercury/Saturn missing (MEDIUM), Drekkana boundary convention (LOW), Combustion orb minor (MEDIUM), Naisargika friendship CORRECT, houses_activated semantic (LOW).

**ML methodology reviewer**: Bootstrap 95% CI on Δ = [−0.0122, +0.0329]; multi-seed mean = −0.0072; paired CV t-test p=0.486; XGBoost importance rank 272/530; pos vs neg non-zero rates and means **identical** (73.2%/74.5%, 0.361/0.362).

**Feature engineering reviewer**: Within yoga-havers, low-strength → 39.0% event rate, high-strength → 29.8% (empirical confirmation of inversion). `house_<6th_lord>` ∈ {6,8,12} is a PERFECT proxy (r=1.0 binary) — XGBoost already knew the yoga was present; only marginal info added was the (wrong-signed) strength magnitude.

**Code reviewer**: Wrong strength ceiling for neuter planets (CRITICAL — 180 vs 210), silent fallback masks data quality issues (WARNING), test coverage gap on Saturn-ruled ascendants (SUGGESTION).

These findings are the basis for the Phase 1 fix list.

---

## Appendix B — Why Phase 0 is non-negotiable

The audit found three sign-coherent bugs in a single yoga that all suppressed signal toward zero. If we proceed to Phase 3B's 16 yogas WITHOUT classical-fidelity infrastructure first, we risk shipping 16× the same kind of bug — each appearing to "work" in isolation but collectively dragging the signal back below noise. The 1-week investment in `docs/bphs_reference.md` + `tests/test_reference_charts.py` + `tests/bphs_compliance.py` is the cheapest possible insurance against repeating the wedge failure mode 16 more times.

The behavioral-first gate design is deliberate: numeric ±5% matching is too brittle (different software packages disagree on convention by larger margins than that for several BPHS sub-rules), so we accept tradition-difference deviations on numeric values BUT require correct presence/absence + correct ordering. This catches the kind of bug the audit found (sign-inverted Vipareeta strength) while not failing on harmless convention differences (Jagannatha Hora's 14° Mercury combustion vs Santhanam's 13°).

---

## Appendix C — Changes from revision 1 to revision 2 (this revision)

Triggered by user review of revision 1. Summary of changes:

| Item | Revision 1 | Revision 2 |
|---|---|---|
| Phase numbering | Phase 0.5, 0, 1, 2A, 2B, 2C, 3, 4, 5, 5b, 6, 7 | Phase 0, 1, 2, 3A, 3B, 3C, 4, 5, 6, 6b, 7, 8 |
| Glossary | none | added at top with 10 terms |
| Baseline definition | implicit | explicit in glossary |
| Classical gate | "±5% match" (numeric-first) | behavioral-first (Tier 1 must pass; Tier 2 numeric secondary, ≥ 4/5 charts) |
| Event corpus position | "parallel to 2A" | Phase 3A — runs FIRST in Phase 3 block |
| Wedge gate criteria | A OR B AND C | (A) AND (B model stability) AND (C); (D) replication if pass < 1.5× margin |
| Decision point after wedge | implicit | explicit 5-row decision table with documented fallback |
| Phase 4/6/7/8 conditionality | "if 3C passes" prose | flagged **CONDITIONAL** in title + timeline column |
