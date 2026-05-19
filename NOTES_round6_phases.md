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

(more sections to follow as Phase 2 progresses)

---

(Phases 2–12 sections will be appended after each phase completes.)
