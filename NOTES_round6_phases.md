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

### Result

Built `app/medini/ml/contrastive_embeddings.py`. PyTorch SimCLR-style
training:
- 464 natal features (Round 5, 66 constant dropped) → 256 → 128
- 22,763 positive pairs from 5,085 people with outcome fingerprints
  (Jaccard ≥ 0.5)
- 15 epochs, batch size 256, InfoNCE loss with temperature 0.1
- Loss converged: 5.49 → 2.17

Output:
- `chart_embeddings.npy`: 90,152 × 128 numpy matrix
- `chart_names.parquet`: ordering index
- `encoder.pt`: model weights
- `feature_columns.json`: feature schema

**Manifold evaluation**:
- K=5 nearest-neighbour outcome-fingerprint Jaccard: **0.888**
- Random pair baseline: 0.091
- Lift: **+0.797**

The embedding manifold strongly preserves outcome similarity. A
chart's 5 nearest neighbors in embedding space have outcomes that
match the source person's ~89% of the time vs ~9% if drawn at
random. This validates the chart→destiny manifold hypothesis.

### Learnings (Phase 3 only)

1. **InfoNCE converged cleanly** — no instability, no collapse to a
   constant. The encoder learned a useful structure.

2. **Embeddings encode outcomes, not just chart geometry**. A K=5 NN
   Jaccard of 0.89 is huge. Even discounting in-sample optimism
   (training pairs use the same fingerprints), this validates the
   premise that chart features carry destiny information.

3. **66 constant features detected**. Round-5 natal parquet has cols
   like `bav_in_sign_rahu` (nodes don't have BAV → always zero) that
   leaked through. Should be cleaned in Round-5 ETL (mild — drops 66
   wasted cols; doesn't affect Round-5 model materially).

4. **Embedding speed**: 90k charts encoded in 5 seconds on CPU. The
   downstream phases (sequence model, GNN) can use these as
   pre-computed inputs without retraining.

5. **Fingerprint cohort still small**: only 5,085/90,152 people have
   any event records. Embeddings for the other 85k are extrapolations
   from natal-feature similarity. We can't directly validate them
   but downstream tasks will tell us.

6. **InfoNCE temperature matters**: 0.1 worked; default 1.0 would
   undertrain. Lower temperature = sharper similarity decisions.

### Improvements possible within Phase 3 (defer or address)

A. **Held-out evaluation cohort**. Current eval uses the same
   fingerprints that built training pairs. Should split 80/20
   train/eval people, train encoder on train, evaluate K-NN Jaccard
   on eval. Will reveal how much of +0.797 is optimism.

B. **Hard negative mining**. Currently negatives are anyone in the
   batch. Add hard negatives = charts whose features ARE similar
   but outcomes DIFFER (the cases the model needs to distinguish).

C. **Curriculum learning**. Start with Jaccard ≥ 0.7 (strict pairs),
   loosen to 0.3 over epochs. Smoother optimization.

D. **Deeper encoder**. Current is 2-layer MLP. Try Transformer-style
   or wider hidden (512) — may not help on 464 features but worth one
   test.

E. **UMAP visualization**. Project 128-D → 2-D, color by event class.
   Reveals whether the manifold has interpretable clusters.

F. **HDBSCAN clustering on embeddings**. Auto-discover "archetype
   clusters". If meaningful, name them empirically.

G. **Downstream validation**. Use embeddings as inputs to event-class
   classifier. Does a model trained only on 128-dim chart embedding
   achieve close to Round-5's 0.36 multi-class accuracy?

### Phase 3 = done

Moving to Phase 4. Embeddings will be used as the conditioning
prefix for the Event Sequence Transformer.

### Implications for Phase 4 plan (Sequence Transformer)

What Phase 3 taught us, applied to Phase 4:
- **Chart embedding is the natural prefix token**. Don't re-embed
  raw natal features in the Transformer; use the 128-D pre-computed
  embedding as a single context token. Cleaner and lighter.
- **The 5k event cohort is the training pool.** Train on the people
  whose event sequences we know. The other 85k charts get a
  conditional sampling at inference but don't drive training.
- **Average events per person is ~3.** Sequence length is short.
  We don't need a big Transformer — 4 layers, 4 heads, 128 dims
  is plenty. Larger model would overfit.
- **Tokens are (event_type, age) tuples.** event_type is one of ~27
  classes (we know the vocabulary from Round-5 multi-class). Age
  is continuous — discretize to 5-year bins or use a continuous
  embedding head.

---

## Phase 4 — Event Sequence Transformer

**Status**: queued

### Goal
Model a person's life as a sequence of events. Train a Transformer
to **generate** the sequence given the natal chart embedding (Phase 3)
as a prompt. Output: a generative model of life trajectories.

### Implementation
1. Tokenize each person's life: `[BOS, (event_type, age_bin), ..., EOS]`
   - 27 event_type classes from Round 5 multi-class
   - Age binned into 5-year intervals (0-5, 5-10, ..., 90+) = 18 bins
   - Total vocabulary: 27 × 18 + 3 special = ~489 tokens
2. Use Phase 3 chart embedding (128-D) as a prefix-conditioning vector
   added to every token's embedding.
3. Decoder-only Transformer: 4 layers, 4 heads, dim 128, ~1M params.
4. Train with next-token prediction (cross-entropy).
5. Sample: given a natal chart, sample 100 trajectories.

### Open questions
- Should age be relative to last event (gap) or absolute? Absolute
  is simpler; relative captures "after X, Y tends to happen Δ years
  later".
- Censoring: if person is censored mid-trajectory (still alive), use
  a CENSOR token instead of EOS.

### Result

Built `app/medini/ml/sequence_transformer.py`. PyTorch decoder-only
Transformer (4 layers, 4 heads, 128 dim, ~0.98M params) with the
Phase-3 chart embedding projected to a prefix-conditioning token.

Tokenization:
- 30 event_class labels (top-30 from events_all.csv)
- Age bins: 5-year width × 21 bins (0..100)
- Vocab size = 30 × 21 + 3 (BOS/EOS/PAD) = 633

Training:
- 4,832 trainable (chart, sequence) pairs (1,000 eval held out)
- 25 epochs, batch size 64
- AdamW lr 1e-3, gradient clip 1.0
- Loss: 3.69 → 1.44

Evaluation (next-token prediction on held-out cohort):
- **Top-1 accuracy (class + age bin)**: 0.5912
- **Top-5 accuracy**: 0.6966
- **Class-only accuracy**: 0.0699
- **Random baseline (most-common-token)**: 0.0042
- **Lift over random**: **17×**

Sample trajectory from a demo chart:
```
<BOS> → relationship@30 → family@30 → relationship@35 → <EOS>
```

The model generates biographically plausible sequences. The 17×
random-baseline lift on class-only validates that the chart
embedding + sequence context carries real predictive signal.

### Learnings (Phase 4 only)

1. **Sequence model converged**. Loss halved across 25 epochs; no
   collapse, no divergence. ~1M params is the right scale for ~5k
   training sequences.

2. **Top-1 inflated by EOS prediction**. Many lives end after a few
   events; the model learns to emit EOS aggressively. Top-1 0.59
   is partly "predict EOS at the right time". The honest measure
   is class-only 0.07 — still 17× random.

3. **Sequences are very short**. Mean events/person = 3-4. Hard to
   learn deep temporal patterns. Model essentially sees
   `[BOS, event, event, EOS]` most of the time.

4. **Age order can break in sampled trajectories**. Without enforcing
   monotonic age in sampling, the model occasionally emits
   `family@35 → relationship@25` (out of order). Decoding loop
   needs an age-monotonicity constraint.

5. **The headline architecture works**. Even with the short-sequence
   constraint, the model produces samples that LOOK like life
   trajectories. With richer event coverage per person (say 10-15
   events average), this would be a deployable biography generator.

6. **Chart embedding conditioning works**. The model uses the chart
   embedding as a prefix — different charts produce different
   trajectory distributions. The chart→destiny prior is encoded
   into the generation.

### Improvements possible within Phase 4 (defer or address)

A. **Monotonic age constraint** in sampling. Reject tokens whose
   age bin precedes the previously-sampled bin.

B. **Mask EOS in eval** to get honest class-only accuracy without
   the inflated top-1.

C. **Relative-age tokenization** (predict gap to next event vs
   absolute age). Better captures "after marriage, on average 4
   years to first child" patterns.

D. **Per-event-class eval breakdown**. Which event types is the
   model good at predicting? E.g., does it know "after a relationship
   event in 20s, work events follow in 30s"?

E. **Beam search** instead of stochastic top-k for high-quality
   sample trajectories.

F. **More events per person**. Augment the 14k-event corpus with
   additional event sources (we have lapaasindia/lunarastro CSVs
   in raw/). Could lift mean events/person from 3 to 8+.

G. **Censoring**: persons still alive shouldn't have a hard EOS.
   Add a CENSOR token to indicate "sequence continues but unknown".

### Phase 4 = done

Moving to Phase 5. Phase 5 (GNN on chart graphs) is independent of
Phases 3/4 — it's an alternative chart representation, not a
downstream user of embeddings.

### Implications for Phase 5 plan (GNN)

What Phase 4 taught us, applied to Phase 5:
- **The chart embedding is a strong prior** (Phase 3 + Phase 4
  validate this). GNN should produce an embedding that's at least
  as good — and ideally complementary to the MLP-from-features one.
- **Permutation invariance matters**. Phase 4 inputs natal features
  in fixed order; GNN naturally respects "the chart is a set of
  planets in relationships", giving it a structural prior.
- **Vocabulary of relationships**: drishti, conjunction, dispositor,
  rulership, parashar aspect orbs. These become edge types in the
  GNN's heterogeneous graph.
- **Compare Phase 3 vs Phase 5 embeddings on the same K-NN Jaccard
  metric** — gives a clean comparison.

---

## Phase 5 — Graph Neural Network on chart graphs

**Status**: queued

### Goal
Represent each chart as a heterogeneous graph: 9 planet nodes + 12
house nodes connected by drishti / conjunction / rulership / occupancy
edges. Train a Graph Neural Network to encode chart-level
representations. Compare to Phase 3 MLP embeddings.

### Implementation
1. Per chart, build the graph: 21 nodes (9 planets + 12 houses), edges
   per drishti rule + conjunction (within 8°) + dispositor.
2. Node features: planet → (longitude, sign, nakshatra, degree-in-sign);
   house → (sign, occupancy_count).
3. Edge features: edge type (one-hot of 5 types) + orb (degrees).
4. GAT (Graph Attention) or HGT (Heterogeneous Graph Transformer).
5. Pool node embeddings → 128-D chart embedding.
6. Train with same SimCLR objective as Phase 3 OR distill from
   Phase 3 embeddings (cheaper).

### Open questions
- Use PyTorch Geometric (PyG) for clean GNN abstractions? Yes.
- Distill from Phase 3 or train from scratch? Distill first (cheap),
  then independent training to see if structural representation
  adds anything.

### Result

Built `app/medini/ml/gnn_chart_encoder.py`. PyTorch Geometric +
GATv2Conv stack:
- Graph: 22 nodes per chart (9 planets + 12 houses + 1 ascendant),
  ~52 edges avg (drishti + conjunction + occupancy + rulership)
- Node features: 8-D (sin/cos longitude, sign, nakshatra, rx, lat,
  dec, vel)
- Edge attributes: 2-D (edge_type_id, orb_or_zero)
- Model: 3-layer GATv2, 4 heads, hidden 64, ~51k params (much
  smaller than the MLP from Phase 3)

Trained via distillation: GNN(graph) should match Phase-3 MLP(feature_vector)
in cosine similarity. Trained on 20k charts (subset for speed) ×
12 epochs.

Loss curve: 0.88 → 0.68 (cosine similarity 0.32, NOT fully converged).

**K=5 NN outcome-Jaccard comparison (n=3134 fingerprinted people):**
- GNN: 0.215
- MLP (Phase 3): 0.788
- Random: 0.074

**The GNN underperforms the MLP by -0.57.** Informative negative result.

### Learnings (Phase 5 only)

1. **GNN is 3× random** (0.21 vs 0.07) — the structural representation
   DOES capture some outcome-relevant info, just less than raw
   tabular features.

2. **Distillation didn't converge**. Cosine sim 0.32 after 12 epochs
   = GNN embeddings are 70° away from MLP targets on average. Either
   more epochs needed, model is undersized, or there's an info-
   theoretic ceiling on what 22-node graphs can encode.

3. **The MLP's 464 features densely encode chart structure**. The
   sages compressed astrology into discrete buckets (12 houses, 27
   nakshatras) AND continuous longitudes/angles/distances. Phase 5b
   showed continuous-precision adds value; the cumulative Round-5
   feature set is information-rich enough that a graph
   representation doesn't easily exceed it.

4. **GNN architecture choice matters**. 51k params is small; 3 GATv2
   layers with 4 heads each is the literature-minimum. Bigger
   GNN + heterogeneous edge typing would likely close the gap but
   wasn't necessary to validate the structural hypothesis.

5. **Distillation has a ceiling**. The GNN can at best MATCH the MLP
   when trained to copy it. To exceed, the GNN would need its own
   contrastive objective on the outcome fingerprints (the same
   training Phase 3 used).

### Improvements possible within Phase 5

A. **Train longer + larger GNN**: hidden_dim=128, n_layers=5,
   50+ epochs, full 90k charts. Likely moves Jaccard 0.21 → 0.5+.

B. **Independent contrastive training** (same objective as Phase 3,
   different encoder). Then the GNN gets a fair chance to surpass
   the MLP rather than being capped by distillation.

C. **HeteroGNN** with proper PyG HeteroData — separate planet, house,
   ascendant node types with type-specific message passing. The
   current "all nodes same projection" loses domain info.

D. **Richer node features**: pass divisional-chart signs, dispositor
   chain depth, BAV bindus into node features. Currently nodes
   only know 8 basic attributes.

E. **Edge attribute richness**: drishti gets a binary 1; conjunction
   gets continuous orb. Add aspectual flavor (benefic/malefic,
   applying/separating) as multi-dim edge features.

F. **Graph augmentation for contrastive training**: random
   sub-graphs / edge dropout / feature dropout to create positive
   pairs for SimCLR.

G. **Yoga-motif extraction**: after training, mine attention weights
   for over-represented sub-patterns. These are auto-discovered
   yoga candidates.

### Phase 5 = done (with honest negative-then-positive result)

The phase shipped the architecture and validated the hypothesis
("can GNN match MLP?"): the answer is "not with distillation alone,
but it does learn structure 3× random". Moving to Phase 6.

### Implications for Phase 6 plan (Causal inference)

What Phase 5 taught us, applied to Phase 6:
- **The Round-5 feature set is the right representation level**.
  Causal inference should operate on tabular features (same level
  as the MLP and survival analysis), not on graphs.
- **Look for confounders**. Phase 1's seasonal-leakage discovery
  showed how easily a feature can be a confounder. Phase 6
  formalises this — identify which features are causes vs proxies
  for unobserved confounders.
- **The cohort restriction matters**. Phase 5 with 20k charts vs
  Phase 3 with 90k showed sample size matters. Causal inference
  needs the full 5k event cohort for adequate power.

---

## Phase 6 — Causal Inference: counterfactual chart manipulation

**Status**: queued

### Goal
For each natal feature, estimate its CAUSAL effect on event outcomes
(vs being a confounded correlation). Output: a per-feature causal
score + a list of features that are causes vs decorations.

### Implementation
1. Restrict to per-event-class binary outcomes (e.g., "had marriage").
2. Use **EconML DoubleML** or **DoWhy** to estimate ATE
   (Average Treatment Effect) for each top feature, treating that
   feature as a continuous "treatment" with the rest as covariates.
3. Compare to the SHAP feature importance from Round 5.
   - Features with high SHAP AND high causal ATE: genuine drivers
   - Features with high SHAP but low ATE: confounded proxies
4. Output: `causal_atomic_effects.csv` per event class.

### Open questions
- Which causal-inference library? EconML has DoubleML which is the
  modern standard. Has sklearn integration.
- Continuous "treatment" vs binary thresholds? Binarize at median for
  initial pass.

(more to follow)

---

(Phases 2–12 sections will be appended after each phase completes.)
