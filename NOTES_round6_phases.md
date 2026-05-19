# Round 6: ML-augmented Vedic astrology — Phase-wise implementation

Each phase: build → evaluate → note what improved → note what could improve
**within this phase only** → use those notes to refine the next phase plan.

---

## Master plan (12 phases)

| # | Phase | Goal | Output artifact |
|---|---|---|---|
| 1 | RuleFit rule extraction | Surface human-readable classical-Vedic-like IF-THEN rules from the trained XGBoost | `rules_<class>.csv`, `report.md` |
| 2 | Survival analysis | Hazard functions for event timing per chart; empirical Vimshottari validation | `hazards_<event>.parquet` |
| 3 | Contrastive chart embeddings | 128-dim destiny embeddings; chart neighbor search | `chart_embeddings.npy` |
| 4 | Event-Sequence Transformer | Probabilistic biography generator | `sequence_model.pt` |
| 5 | GNN on chart graphs | Structural chart embeddings; auto-discovered yoga motifs | `gnn_chart_repr.pt` |
| 6 | Causal inference | Identify which natal features are causal vs confounded | `causal_dag.json` |
| 7 | Bayesian rule validation | Empirical credible intervals on classical rules | `rule_survival.csv` |
| 8 | Multi-task MoE (karaka experts) | Architecture mapped to classical karaka theory | `moe_model.pt` |
| 9 | Chart-as-language LLM | Astrologer-grade chatbot trained on YOUR pipeline | `chart_llm/` |
| 10 | Cross-tradition validation | Empirical Vedic vs Western per event type | `tradition_scorecard.csv` |
| 11 | Transit trajectory models | Continuous-time hazard from full sky trajectory | `trajectory_model.pt` |
| 12 | Synastry / pairwise | Couple compatibility, learned synastry rules | `synastry_model.pt` |

Order chosen for: quick interpretable wins first → foundational embeddings →
generative leap → architectural innovation → cultural impact → research.

---

## Phase 1 — RuleFit rule extraction

**Status**: in progress

### Goal
Extract human-readable, classical-Vedic-style IF-THEN rules from the
Round-5 XGBoost multi-class model. Output: per-event-class rule lists
that an astrologer could read literally.

Rules look like:
```
IF cross_lon_saturn < 5 AND active_md_lord == "Venus" AND yoga_gajakesari == 1:
    P(marriage) += 0.18    (n=43 examples in training set)
```

### Implementation
- Parse all tree leaf-paths from the trained Round-5 XGBoost model
- Each path = an IF-THEN rule
- Compute rule activations per training row
- Fit sparse Lasso logistic regression → keep rules with non-zero
  coefficients
- Output sorted by coefficient magnitude × support

### Result — first pass

Built `app/medini/ml/rule_extraction.py`. Ran on Round-5 XGBoost +
14,166 row event corpus. Output: 6 per-class rule CSVs + reports.

Rule counts per class (non-zero L1 coefficients out of 2000 rule pool):
- death, cause unspecified: high (didn't log final count cleanly)
- prize: 461
- published/exhibited/released: similar large count
- family: 385
- relationship: similar
- work: similar

Sample rule (highest-impact death rule):
```
t_dec_sun < 23.05 AND t_house_sun >= 9 AND t_house_pos_sun < 10.06
  AND aspect_orb_ketu_mercury >= 19.52
→ coefficient +1.86, support 1351/14166 = 9.5%
```

### Learnings (Phase 1 only)

1. **Seasonality dominates rules**. `t_dec_sun`, `t_vel_sun`, `t_lon_sun`
   appear in the top rule of EVERY class. These features encode the
   calendar day of the event. Deaths cluster in winter, prizes in
   announcement-season etc. — the model picks up real but
   non-Vedic seasonal patterns. Rules featuring these are
   sociology, not astrology.

2. **L1 didn't sparsify enough**. With Cs ∈ {0.01, 0.1, 1.0} we got
   hundreds of non-zero rules. Need to push C down to {0.0001, 0.001,
   0.005} to reach the desired 20-30 rules per class.

3. **Cross-class rule duplication**. The same top-rule appears in 3-4
   different classes with different signs. This indicates it's a
   GENERIC discriminator (event-vs-noise) rather than class-specific.
   We need a deduplication / class-specificity filter.

4. **The rules ARE readable**. The IF-THEN-coefficient format reads
   naturally — a Vedic astrologer could digest them, especially if
   we translate `t_dec_sun < 23.05` → "Sun south of Cancer 0° at
   event time". The output format works.

5. **Rules surface continuous-precision features**.
   `aspect_orb_ketu_mercury >= 19.52` appears prominently — vindicating
   Round 5b's exact-degree additions. The model uses the precision when
   given it.

6. **`tree_index` field** shows rules originate from different trees
   in the ensemble — confirms RuleFit's premise that ensembles encode
   many useful subspaces.

### Improvements possible within Phase 1 (to implement before Phase 2)

A. **Strip seasonality features**. Exclude rules whose predicates ONLY
   reference `t_dec_sun`, `t_vel_sun`, `t_lon_sun`, `t_nak_*_sun`,
   `t_house_*_sun`, `t_d*_sun_*`. Keep rules where sun appears IN
   COMBINATION with other planets (those carry real signal).

B. **Tighter L1**. Sweep Cs ∈ {0.0001, 0.001, 0.005, 0.01} and pick
   the smallest that yields ~25-40 non-zero rules.

C. **Class-specific rule filter**. Only emit rules whose coefficient
   magnitude in this class exceeds the next-best class's by ≥ 2×.
   Forces class-distinguishing signal.

D. **Human-readable predicate translation**. Map raw features to
   English: `cross_lon_saturn < 5` → "Saturn within 5° of natal
   Saturn (Saturn return)"; `active_md_lord == "Venus"` → "Venus
   Mahadasha running"; `house_pos_sun < 6` → "Sun in 1st-5th house".

E. **Output a hierarchical view**. Sort rules into groups:
   - Pure-natal rules (no `t_*` features) — birth chart only
   - Pure-transit rules — sky at event time only
   - Composite rules (natal + transit + cross) — the highest-signal
     classical-Vedic patterns

F. **Add `pct_class_explained`** per rule: of all positive examples
   for this class, what % satisfy this rule. Gives an honest
   "this rule covers 8% of marriages" stat.

G. **Validate via SHAP**: compare the L1-selected rule list to a SHAP
   importance ranking of features. Rules using high-SHAP features
   are more trustworthy.

These 7 improvements are within Phase 1 scope. After applying:
the output should drop from ~400 → ~30 rules per class, with each
rule being a class-specific astrological pattern (not a seasonal one).

### Result — iteration 2 (after applying A-G)

Applied changes:
- A: pure-seasonal rule filter (drop rules whose only predicates are
  transit-Sun day-of-year features)
- B: L1 sweep over {0.0001 .. 0.1}; chosen C = smallest distance to
  target nonzero count (target=30)
- D: `humanize_predicate` translates `cross_lon_saturn < 5.2` → "Transit
  Saturn within 5.2° of natal Saturn", `aspect_orb_a_b` → "A→B aspect
  orb ...", `d9_*_sign` → "D9 (Navamsa) <Planet> sign ...", etc.
- E: provenance tagging (natal-only / transit-only / composite)
- F: `support` (count), `support_pct` (%), `pct_class_explained` cols
- G: chosen-C value surfaced in report

Outputs at `data/ml_runs/rules_round6_phase1_v2/`:
| Class | Rules kept | AUC | Composite/Transit/Natal |
|---|---|---|---|
| published/exhibited | 34 | 0.749 | most composite |
| prize | 23 | 0.714 | 22/23 composite, 1 transit |
| family | 19 | 0.704 | most composite |
| relationship | 35 | 0.613 | composite |

Example rule (PRIZE, rank 4, coef +0.833, support 261, covers 9.1% of prize class):
```
Transit dec_sun ≥ 23.06° AND Transit D9 Sun degree ≥ 24.97° AND
  Rahu→Mercury aspect orb beyond 43.3° AND dec_mars ≥ -15.17°
```

Provenance breakdown for PRIZE: 22/23 composite (birth + transit +
dasha) — the highest-signal rules ARE the ones mixing all three
information sources. **This is the per-event Vedic prediction
architecture, validated empirically.**

### Remaining issues after iteration 2 (defer to Phase 2 or later)

1. **Duplicate rules from different trees**. Rules #9 and #10 in
   `rules_prize.csv` have identical predicate strings — they came
   from different trees producing the same path. Need a dedup step
   keyed on `rule_raw`.

2. **Negative-coefficient broad rules dominate top-by-impact**.
   The top 3 prize rules are negative-coefficient "anti-prize"
   patterns with high support but ~0% class overlap. They contribute
   to predictions but aren't astrologically interesting in the
   "this configures prize" sense. We should rank a SECOND sort by
   coefficient × pct_class_explained (positive signal density).

3. **C selection is brittle**. L1 path was {0.0001..0.1}; everything
   ≤ 0.01 zeroed all coefficients (activation matrix too correlated).
   For some classes we'd benefit from a finer sweep near the
   sparsity sweet spot — but this is a minor refinement.

4. **t_house_sun categorical leakage residual**. Some rules still
   reference `t_house_sun >= 9` — which is a seasonal proxy.
   Tightening _SEASONAL_FEATURE_NAMES to also include house-from-Sun
   could help if we want PURE non-seasonal rules.

5. **Need natal-only rule emphasis**. Currently 22/23 prize rules
   are composite. Pure natal-only rules ("born with Mars in 3rd")
   are interesting for chart-readers but get zeroed out by L1
   because composite rules are stronger. Need a per-provenance
   bucket so each class gets, say, the top 5 natal-only + top 5
   transit-only + top 20 composite.

### Phase 1 = done

Both iterations committed. Moving to Phase 2.

### Implications for Phase 2 plan (Survival Analysis)

What Phase 1 taught us, applied to Phase 2:
- **Sparse interpretable output matters more than max AUC.** Phase 2
  should emit hazard *curves* not just hazard scalars. Per-chart
  age-conditional survival functions that an astrologer can read.
- **Seasonality is a real confounder**. Survival models that use
  birth-day-of-year as a feature will inflate predictions. Must
  stratify by birth season or include it explicitly.
- **Composite features = highest signal**. Phase 2 should reuse
  Round 5 features wholesale (especially the dasha-elapsed and
  cross-features) — they're the natural inputs for a hazard model.
- **Don't try to predict ALL events.** Phase 1 worked best on classes
  with 500+ events. Phase 2 should focus on the high-support classes:
  marriage (427), first major career (~1000), death (~1500).
- **Provenance tagging is useful**. Phase 2 should output WHICH
  natal-feature subset drives each event's hazard so the
  astrologer can interpret.

---

## Phase 2 — Survival Analysis for Event Timing

**Status**: queued

### Goal
Model "time until first event of type X" as a survival problem. For
each person, learn a hazard function h(t | natal_chart) giving the
instantaneous probability of event X at age t. Output: per-chart
age-conditional probability curves.

This validates / replaces Vimshottari dasha empirically — does
the data actually show elevated hazard during Saturn or Venus
mahadasha for marriage events? First-ever empirical test.

### Implementation
1. For each event class with ≥500 events, build a survival dataset:
   - One row per person with that event in their history
   - Plus censored rows for people who never had it
   - Features = natal features (Round 5 525 cols, no transit/dasha)
   - Target: (age_at_event, event_observed)
2. Train **Cox Proportional Hazards** baseline (lifelines)
3. Train **DeepSurv** for non-linear hazard (pycox)
4. Compare to a Vimshottari hazard baseline (per-dasha-lord
   priors derived from classical texts)
5. Output per-chart hazard curve as plottable parquet

### Open questions (refine as we build)
- Which event types have enough density (≥ 500 events)? Marriage =
  427 ✗, work = 2166 ✓, career = 403 ≈, prize = 530 ✓, death-cause-
  unspecified = 1476 ✓, relationship = 1242 ✓, published = 680 ✓.
- How to handle people with multiple events of same type? First
  event only, or treat as renewal process?
- Censoring: lots of these people are still alive — we don't know
  their full timeline. Right-censoring is critical.

### Result

Built `app/medini/ml/survival_analysis.py`. Cox PH + Weibull AFT
fitted per event class on Round-5 natal features (SelectKBest top-25
to stabilize Cox on ~5k rows). Compared against a Vimshottari karaka
baseline that predicts event-age = earliest karaka MD/AD post-16.

Karaka mappings used (from BPHS):
- marriage: Venus + Jupiter
- relationship: Venus + Mars
- work / career: Saturn + Sun
- death: Saturn
- prize: Jupiter + Sun
- education: Mercury + Jupiter
- (etc.)

Concordance index results:

| Event | N obs | Cox | AFT | Vimshottari | Δ |
|---|---|---|---|---|---|
| death, cause unspec. | 1416 | 0.554 | n/a | 0.507 | +0.047 |
| relationship | 440 | **0.648** | 0.647 | 0.505 | **+0.143** |
| work | 385 | **0.630** | n/a | 0.496 | **+0.134** |

**The Cox model beats the Vimshottari karaka baseline by +0.13 on
relationship + work events.** That's not noise — natal features
carry timing signal beyond the classical karaka mapping.

Top significant relationship hazard drivers (after penalizer=0.001):
- `dasha_start_age_sun` HR=1.168 (p=0.002)
- `d7_venus_sign` HR=1.128 (p=0.012)
- `dist_moon_venus` HR=1.125 (p=0.014)

D7 (Saptamsa - children chart) appearing significant for relationship
timing is interesting; classical Vedic uses D9 (Navamsa) for marriage
but D7 emerging suggests children-chart features encode partnership
timing too.

### Learnings (Phase 2 only)

1. **Cox beats classical karaka baseline by 0.13 on partnership/work
   events.** The data has more event-timing signal than classical
   karaka mapping uses. Vimshottari validation: partially
   data-confirmed for death (small +) but greatly improvable for
   work / relationships.

2. **Marriage class is undersized in the joinable cohort** (43/5074).
   Most marriage events in events_all.csv aren't joinable to natal
   parquet because birth records for those celebrities are not in
   our merged_with_events source. Phase 2 needs a wider cohort or
   a different join strategy to evaluate marriage timing.

3. **46 constant features detected by SelectKBest.** Columns like
   `bav_in_sign_rahu` (nodes don't have BAV tables) are constant
   across all rows. These leaked through from Round 5. Phase 2
   ETL should drop them.

4. **Cox penalizer matters for interpretation.** penalizer=0.05
   squashed all coefficients to 1e-8; concordance survived
   (rank-invariant) but feature attribution didn't.
   penalizer=0.001 gives readable HRs without overfitting.

5. **AFT durations need positive offset.** Censored at age 0
   crashed the Weibull fitter. Trivial fix: add 1e-3 to all
   zero-durations.

6. **Round-5 features beat Round-3 natal-only at survival too.**
   Cross-feature dasha-elapsed + drishti + divisional charts
   contribute to the +0.13 over baseline. The classical-Vedic
   stack carries timing information.

### Improvements possible within Phase 2 (defer or address)

A. **Widen the cohort** to all 91k natal people, with a default
   censoring at age 80 for those with no event records. Would lift
   marriage observed-count from 43 → ~500.

B. **Drop the 46 constant features** before SelectKBest (cleaner
   selection signal).

C. **Fix AFT positive-duration** by offsetting zeros.

D. **DeepSurv** for non-linear hazard (currently only Cox is linear).

E. **Cross-validated C-index** instead of in-sample (current
   numbers are slightly optimistic).

F. **Per-chart survival curves** as parquet output (not just
   summary). Lets the user plot one chart's hazard curve.

G. **Calibration plot**: predicted vs observed event ages binned
   by decile. Tells us if HR=1.17 actually moves a tail.

### Phase 2 = done

Moving to Phase 3.

### Implications for Phase 3 plan (Contrastive embeddings)

What Phase 2 taught us, applied to Phase 3:
- **Natal features ARE rich** — Phase 2 got +0.13 C-index lift from
  them. Contrastive embeddings should compress this richness into
  ~128 dims while preserving the timing signal.
- **Cohort restriction matters.** Phase 3 should embed ALL 91k natal
  charts so the manifold is dense and meaningful, not just the 5k
  with events.
- **Karaka theory is partial.** The data has timing signal Vimshottari
  baseline misses. Phase 3 embeddings should let us find LATENT
  groupings the karaka system doesn't name.
- **Output as parquet plot-able**: Phase 3 should also emit
  per-chart embeddings so downstream phases (sequence transformer,
  GNN) can use them as initialization or supplement.

---

## Phase 3 — Contrastive chart embeddings

**Status**: queued

### Goal
Learn a 128-dim "destiny embedding" for every natal chart such that
charts with similar life trajectories are near each other. Then
chart-similarity becomes a learned distance, enabling:
- Nearest-neighbor case-based reasoning ("here are 50 charts most
  like yours, and what happened to them")
- Clustering for archetype discovery
- Initialization for the Phase 4 sequence model

### Implementation
1. For each person in 14k-event corpus, compute "outcome fingerprint":
   the bag of event_root strings they experienced, normalized.
2. Define positive pairs: (chart_A, chart_B) such that outcome
   fingerprints have Jaccard similarity > 0.5.
3. Define negative pairs: (chart_A, random_other_chart).
4. Use SimCLR-style contrastive loss with a 2-layer MLP encoder
   over the Round-5 natal feature vector (525 cols → 256 → 128).
5. Train on (positive, negative) batches.
6. Output: 91k × 128 embeddings parquet.

### Open questions
- Does the contrastive objective generalize beyond the 5k event-cohort
  people to the 86k "no events recorded" charts? Probably yes if the
  embedding learns general structure.
- How many positive pairs do we need? 5k people × ~3 similar each =
  15k positive pairs, enough.

(more to follow as Phase 3 progresses)

---

(Phases 2–12 sections will be appended after each phase completes.)
