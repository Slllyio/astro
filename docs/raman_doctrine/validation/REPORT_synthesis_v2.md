# synthesis_v2 — a doctrine-derived non-linear scorer breaks the strength ceiling

**Status: landed (2026-07-12).** A standalone, parallel strength scorer (`app/medini/doctrine/domains/
synthesis_v2.py`) that replaces the live engine's additive `_combine`/`_THRESH` with Raman's own
structural OVERRIDES. **The live engine is byte-untouched** — synthesis_v2 consumes the exact same
`Finding` lists the assessors already emit, so this is pure additive measurement with zero drift risk.

## Headline — the two-axis breakthrough

| Axis | live engine | **synthesis_v2 (A+B)** | Δ |
|---|---|---|---|
| pooled HTJAH held-out (N=53) | 54.7% within-one | **64.2%** (exact 37.7%) | **+9.5** |
| NH degree pool (N=32) | 53.1% | **62.5%** (exact 31.2%) | **+9.4** |
| ch. IV live anchor (N=8) | 1/8 (12.5%) | **1/8** (12.5%) | parity |

Reproduce: `PYTHONPATH=. python3 -m app.medini.doctrine.validation.synthesis_v2_validate`.

This **replicates the A2 learned decision tree's in-distribution gain (63.5% LOCO)** — but from PURE
doctrine, nothing fit to labels, and **without the anchor collapse** that made the fitted model
unlandable (A2 dropped the anchor to 0/8). synthesis_v2 holds the anchor at parity.

## Mechanism — engine base + doctrinal override gates

Per factor (bhava/lord/karaka): the **base grade is the live engine's own grade** (so with no gate
firing, v2 == engine). Then Raman's structural conditions apply as overrides, in hierarchy:

- **A — besiegement veto:** a factor hemmed between malefics (papakartari) is capped at "weak"
  regardless of positive testimony. *Raman: a besieged planet is helpless.*
- **B — deep-affliction gate:** summed Rāśi negatives ≤ −2.45 → "afflicted"; ≤ −1.22 → "weak". These
  two thresholds are the **load-bearing split of the A2 tree** (`ml_research/a2_tree_rules.json`),
  declared as the only two data-read constants; they encode Raman's "stacked affliction breaks the
  gear," doctrinally consistent with papakartari.
- **collinearity guard:** combustion is the tight-orb case of Sun-proximity — counted once, not
  stacked with a Sun-conjunction penalty. (Prevents the double-count from spuriously tripping Gate B.)

## The ablation (what earns its place, and what doesn't)

`GATE_A/B/P/C` toggles; each row is full three-axis within-one:

| config | held-out | NH | anchor |
|---|---|---|---|
| base (= live engine) | 54.7 | 53.1 | 1/8 |
| A besiegement | 56.6 | 53.1 | 1/8 |
| B deep-affliction | 64.2 | 62.5 | 1/8 |
| **A + B (landed)** | **64.2** | **62.5** | **1/8** |
| P strong-promise floor | 54.7 | 53.1 | 1/8 |
| C dignity floor | 47.2 | 28.1 | 2/8 |
| A + B + C | 47.2 | 31.2 | 2/8 |

- **B is the powerhouse** (+9.5 / +9.4). **A** adds a clean held-out point and is neutral elsewhere.
- **P (strong-promise floor / "D9 is sequence not cancellation") is inert** on sign-reconstructed
  charts — factors rarely reach a strong Rāśi grade there, so the floor never binds. It is retained
  (off) for a future degree corpus, where D9-cancellation is the House-11-class failure it targets.
- **C (dignity floor) is a documented negative:** it lifts the anchor 1→2 but costs ~17 pts of
  held-out and ~25 of NH. Diagnosis: on the sign feature space the anchor's *strong* verdicts are
  **not separable** from held-out's *weak* verdicts — both show "dignity + affliction." Raman's
  distinction there rests on yogas/degrees/dispositor strength that the sign chart does not carry.
  This is the **same feature-space ceiling** the additive engine hits (increments 8/12/13/18); the
  gates cannot repair a signal that is absent from the features. So C stays off.

## What this settles

- **Synthesis, not features, was the strength ceiling** — confirmed a third time (ceiling diagnostic
  → A2 → here), now with an *interpretable, doctrine-derived* mechanism, not a fitted model.
- **The two big held-out axes move together, +~9.5 each, with the anchor held** — a result no linear
  weight-surgery trade achieved (every prior trade spent one axis for another) and the fitted model
  could not land (it sacrificed the anchor).
- **The anchor's residual under-credit is a feature-space limit, not a synthesis failure** — provable
  because the only override that moves it (C) is the one that wrecks the held-out it should preserve.

## Honest scope

- `synthesize_house` (the factor→house conclusion) is UNMEASURED — no corpus carries an `overall` gold
  verdict — so it is kept deliberately simple (class-weighted mean + lead-veto, no fit) and is not
  part of the headline.
- synthesis_v2 is a **parallel** scorer; the production `judge_house_doctrine` grades are unchanged.
  Promoting it to the live path is a separate decision (it would require re-pinning the anchor ledger
  and the drift-guard), deliberately not taken here.
- Pinned by `tests/doctrine/test_synthesis_v2.py` (7 unit gates + a three-axis ratchet at
  ≥62% / ≥60% / ≥1-of-8).

---

## Degree corpus grow2 — the P/C floors tested where they can finally bind (2026-07-12)

The increment-24 diagnosis said the strong-promise floor (P) was untestable on sign charts (factors
rarely reach a strong Rāśi grade) and predicted the floors' real test needed degrees. So the degree
pool was grown: **all 27 unmined degree-usable NH nativities** sectioned from the clean full text,
**62 raw candidates → 19 after mechanical triage** (unmappable stems / Navāṁśa-frame / bare / no-house
culled; the pre-registered verdict map UNCHANGED) **→ 18 after a unanimous 3-agent adversarial
attribution audit** (1 refuted 3/3 — a truncated "so far as military operations are concerned" scope
qualifier). Extraction frozen before any scoring. Shipped: `corpora/nh_strength_grow2.json` — 18 rows,
13 fresh nativities → **degree pool 32 → 50 rows, 36 nativities**. The pinned N=32 numbers and every
drift guard are untouched (grow2 lives only in `synthesis_v2_validate._NH_ALL`).

### The lead generalizes to fully unseen data

| pool | live engine | synthesis_v2 (A+B) | lead |
|---|---|---|---|
| N=32 pinned | 53.1% | 62.5% | +9.4 |
| **N=50 enlarged** | **44.0%** | **52.0%** | **+8.0** |
| grow2-only slice (N=18) | 5/18 | 6/18 | +1 row |

The fresh rows are hard for both scorers (the live baseline drops to 44%), but the doctrine gates'
lead is stable (+8.0 vs +9.4) on data neither scorer nor its thresholds ever saw. That is the
generalization the fitted A2 model failed.

### The floors: tested and refuted (documented negative)

P/C ablation on the enlarged pool (A+B always on): **A+B 52.0% · +P 50.0% · +C 28.0% · +P+C 26.0%.**
The bind-rate diagnostic shows this is a REAL test now: **13/50 factors reach a strong Rāśi grade**
on degree charts (vs almost none on sign reconstructions), so Gate P fires — and it *costs* 2 points.
The pool contains strong-Rāśi factors that Raman himself grades down; flooring them at "fairly good"
is doctrine the data rejects. C remains catastrophic on degrees (28%), consistent with the sign-chart
result. **Both floors stay off; A+B stands as the validated configuration** — no longer just "P never
fires," but "P fires and hurts," which closes the question.

Pinned by `test_grow2_corpus_integrity` (18 rows, keys degree-usable, phrases map) and
`test_synthesis_v2_enlarged_degree_pool` (N=50, ≥50% within-one, ≥4-pt lead over the live engine on
the same rows).

---

## grow3 + the attribution audit — mining the remaining, and cleaning the gold (2026-07-12)

**grow3 (second-verdict sweep).** All 23 already-mined nativities re-swept for verdicts the earlier
passes missed, with a hard dedup rule (no candidate whose (key, house, factor) matches a shipped row):
**45 raw candidates → 12 after mechanical triage → 11 after the 3-agent adversarial audit** (1 refuted
3/3: a daśā-scoped nizam grade). Shipped: `corpora/nh_strength_grow3.json` — 11 rows, 9 nativities.

**The attribution audit (the sweep's real find).** A batch-0 extractor noticed the shipped gandhi row's
source sentence sits in the anonymous **"No. 73 — An Example for Poverty"** chapter, not Gandhi's. That
triggered a mechanical + agent audit of ALL 50 previously-shipped rows (phrase located in the full
text; chapter attribution and Rāśi/Lagna frame checked). Verdict: 45 sound (verbatim-modulo-OCR or
subject/grade-correct paraphrases), **5 bad gold removed** (recorded in `nh_strength_removed.json`):

| row | defect |
|---|---|
| gandhi H1 bhava (grow) | misattributed — anonymous "Example for Poverty" chart |
| einstein H9 kāraka (grow) | misattributed — Ramana-chapter section bleed |
| milton H5 bhava (base) | frame error — "In the Navamsa again, the 5th house is…" |
| sankara H8 bhava (base) | frame error — "In the Navamsa again, the 8th house is…" |
| nehru H4 bhava (base) | frame error — "In the Navamsa also, the 4th house is…" |

Corrected pools (drift guards re-pinned at increment 26): base N=15→12 (41.7%), default pooled
N=32→**27** (live 51.9%, Δ+0.11), full pool N=**56**.

### Results on the corrected pools

| pool | live engine | synthesis_v2 (A+B) | lead |
|---|---|---|---|
| default (N=27, corrected) | 51.9% | **63.0%** | **+11.1** |
| **full (N=56)** | **44.6%** | **53.6%** | **+9.0** |
| grow3-only slice (N=11) | 6/11 | 7/11 | +1 row |

Removing the bad gold *widened* v2's lead on the default pool (+9.4 → +11.1) — the removed rows were
noise, not signal. The full-pool lead is stable at +9.0 across 56 rows spanning 38 nativities. Pinned
by `test_grow3_corpus_integrity` (11 rows; no (key,house,factor) duplicate across all four corpora;
total 56) and the re-pinned `test_synthesis_v2_enlarged_degree_pool` (N=56, ≥50%, ≥4-pt lead).

**Honest note on the pre-registered map.** 25 of the 45 grow3 raw candidates fell to unmappable stems
("well fortified", "free from affliction", "null and void") — the frozen map is conservative by
design; extending it is possible future work but must happen before any extraction round that uses it.

---

## Increment 27 — verdict map v2 + grow4: the culled stems recovered, and the under-credit regime exposed

**Map v2.** The pre-registered verdict map was extended (BLIND — assignments derived from the map's own
intensity ladder before any re-scoring; rationale per family in the map's notes): the fortified /
affliction-freedom / placement / power / destruction families, plus a **negation-bug fix** — "not well
disposed" matched the positive `well disposed` pattern, so two shipped rows (omar H7, hyderali H5)
re-grade fairly good → **weak** (the only deliberate re-grades; every other shipped phrase grades
identically, now pinned per-row by `nh_gold_grade_pins.json` + `test_verdict_map_gold_pins` so gold
can never drift silently again).

**grow4.** The 46 map-v1 culls re-triaged under v2: 18 newly-mappable (gandhi's dropped — its phrase
verified absent from Gandhi's true chapter) → **17 shipped** after the 3-agent adversarial audit
(1 refuted 3/3: nero's Sun graded qua daśā lord). `corpora/nh_strength_grow4.json` — 17 rows,
12 nativities, and a finally strong-heavy spread (1 very powerful, 5 very strong, 3 fairly strong).
**Full degree pool: 56 → 73 rows.**

### Results — the strong-graded gold exposes the under-credit regime

| pool | additive baseline | synthesis_v2 (A+B) | lead |
|---|---|---|---|
| default (N=27) | 51.9% | **63.0%** | +11.1 |
| **full (N=73)** | 39.7% (Δ −0.10) | **46.6%** (Δ −0.59) | **+6.9** |
| grow4-only slice (N=17) | 2/17 | 2/17 | 0 |

The recovered rows are mostly STRONG-graded gold — and **both scorers fail them almost completely
(2/17)**. This is the ch. IV anchor's all-under-credit signature, now visible in held-out gold at
scale: on factors Raman grades *very strong/fortified*, the engine's features (and the gates, which
only cap downward) systematically under-credit. Both pool-level mean-Δs turn negative for the first
time. v2's lead holds (+6.9) because the A+B gates keep winning on the afflicted/weak side — but the
strong side is a feature gap no synthesis can bridge (consistent with the increment-24/25 diagnosis:
the strength signal lives in yogas/dispositor chains the Finding vocabulary doesn't carry).

**What this buys:** the corpus now has real statistical power on BOTH tails (afflicted-heavy AND
strong-heavy rows), the map covers Raman's full verdict vocabulary, and the under-credit regime is a
measured, reproducible target for the next feature-side increment. Pinned by
`test_grow4_corpus_integrity`, the re-pinned full-pool ratchet (N=73, ≥44%, ≥4-pt lead), and the
73-triple cross-corpus dedup check.

---

## Increment 28 — synthesis_v2 PROMOTED to the live grade path

Lever 2 of "implement both levers." `SYNTHESIS_V2_LIVE = True` in `house_judgment.py`:
`judge_house_doctrine` now re-labels the three factor verdicts through `synthesis_v2` BEFORE the
conclusion is built (so the synthesis prose embeds the promoted labels), grades the conclusion via
`synthesize_house`, and re-labels the Chandra-Lagna view on the same scale. The additive SCORES are
untouched — `label == _verdict_label(score)` no longer holds by design: the score is the raw additive
testimony, the label is the doctrine grade. The additive baseline stays reproducible from scores
(`apply_synthesis_v2` helper; `fit_weights.heldout()` forces the flag off; `synthesis_v2_validate`'s
baseline is recomputed from `.score`, so the v2-vs-additive comparison is preserved forever).

### The promoted ledger (all measured, `_TOL`-pinned)

| axis | additive baseline | **promoted (live)** |
|---|---|---|
| pooled HTJAH held-out (N=58) | 50.0% | **56.9%** (exact 34.5%) |
| max HTJAH expansion (N=81) | 51.9% | **61.7%** |
| fresh blind (N=14) | 71.4% | **71.4%** |
| NH degree-accurate (N=12) | 41.7% | **58.3%** |
| NH degree pooled (N=27) | 51.9% | **63.0%** |
| NH full pool (N=73) | 39.7% | **46.6%** |
| ch. IV anchor (N=8) | 1/8 | **1/8** (two intra-band ledger shifts) |

Every axis improves or holds; nothing regresses. The anchor ledger moved on two rows
(12-karaka weak→afflicted, 13-bhava moderate→weak — the deep-affliction gate reading down testimony
Raman overrides on those charts; the documented feature-space limit, within-one unchanged).

### Consumer notes
- The reading path (`interpret.build_grounding`) now serves doctrine grades as `verdict` beside the
  raw additive `score` fields (documented in `_verdict`).
- `worked_chart_validate`'s rāśi-only and named-karaka paths route through the same promoted helper —
  no mixed-scheme scoring within a corpus.
- The vargottama-lagna sentinel ("very powerful") is unchanged by construction.

---

## Increment 29 — Gate F (fortification floor): a third documented negative

### Motivation
Increments 24–28 built only *reducing* gates (A besiegement, B deep-affliction), so the
**strong-graded held-out slice stayed floored**: pooled across held-out + NH-enlarged + anchor,
only **5/29 (17.2%)** of the factors Raman grades ≥ *fairly strong* land within-one. Increment 27
had already localised the cause — those misses are **fortified-but-badly-placed** factors Raman
credits despite the placement (Sankara's Moon "in the 12th though … rendered highly fortified by
the combined aspects of Saturn (7th), Jupiter (9th) and Mars (yogakāraka)"). Gate F is the positive
mirror of Gate B: it reads a **fortification tally** over the *same* findings and floors the grade
**up**, where B floors it down.

### Mechanism
`FrameState.fort` sums the Rāśi-frame positive testimony, ranked by Raman's own hierarchy
(each fortifier counted once, in its strongest category):

| fortifier | weight | rationale |
|---|---|---|
| yogakāraka contact (aspect/conjunction) | 2.0 | the strongest single fortifier in the doctrine |
| exaltation (dignity ≥ 1.6) | 1.6 | decisive dignity (`_DIGNITY_W["exalted"]`) |
| vargottama | 1.2 | cross-varga confirmation |
| own-sign / moolatrikōṇa / neechabhāṅga | 0.8 | own dignity / cancelled debilitation |
| kendra placement | 0.5 | angular strength |
| benefic aspect/conjunction | 0.4 | the weakest incremental fortifier |

Gate F: *if NOT besieged AND fort ≥ F1 → floor at "fairly strong"; fort ≥ F2 → floor at "very
strong".* Besiegement (Gate A) still vetoes — a hemmed graha is broken regardless of incoming aid.
F1/F2 were swept; a gentler floor variant (fairly-good / fairly-strong) was also tested.

### Ablation — every config regresses the drift-guards
Pooled slices: **strong** = Raman ≥ fairly strong (N=29, Gate F's target); **aff** = Raman ≤ weak
(N=68, the guard). Baseline is A+B (Gate F off).

| config | held-out | NH default | NH enlarged | anchor | strong slice | aff slice |
|---|---|---|---|---|---|---|
| **A+B baseline** | **56.9%** | **63.0%** | **46.6%** | **1/8** | 5/29 (17%) | 56/68 (82%) |
| F1=1.6 F2=2.8 | 51.7 | 29.6 | 32.9 | 2/8 | 12/29 | — |
| F1=1.6 F2=3.0 | 50.0 | 29.6 | 32.9 | 2/8 | 11/29 | — |
| F1=2.0 F2=3.0 | 51.7 | 40.7 | 37.0 | 1/8 | 10/29 | — |
| F1=2.4 F2=3.2 | 48.3 | 48.1 | 42.5 | 1/8 | 6/29 | — |
| F1=2.0 F2=3.0 min_neg=−2.45 | 53.4 | 51.9 | 42.5 | 1/8 | 8/29 | — |
| gentle floors (4,5) F1=2.0 F2=3.0 | 55.2 | 40.7 | 35.6 | 2/8 | 9/29 | 41/68 |

**Not one config clears the gate** (held-out ≥ baseline AND NH not regressing). The trade is
structural, not a threshold-tuning artifact: the corpora carry **68 afflicted-graded rows that A+B
scores 82.4% within-one**, and those rows carry the *same* fortifier tags (exaltation, kendra,
benefic aspects) as the strong-graded misses — so any tag-level floor over-fires on them. The
gentle-floor run makes the mechanism explicit: the afflicted slice collapses **56 → 41 within-one
(−15 rows over-lifted)** to buy 4 strong-slice rows, and mean Δ swings from −0.59 to +0.41 (the
over-credit that A+B fixed comes straight back).

### Verdict — documented negative (joins P and C)
The strong-side under-credit is a **feature gap, not a synthesis gap**: Raman's discriminator
between "fortification that overrides the affliction" (his strong verdict) and "fortification that
fails to override it" (his afflicted verdict) is **not present in the Finding vocabulary** —
it lives in yoga/dispositor structure the assessors never emit. No floor over the existing tags can
separate the two, exactly as Gate C (dignity floor) could not. `GATE_F = False` by default; the
mechanism is retained as a reproducible ablation switch (`synthesis_v2_validate.run_slices` prints
the strong/mid/afflicted slices; `test_gate_F_when_enabled_floors_a_fortified_factor` pins the
switch). Closing the strong side requires **new features** (yoga/dispositor/fortification-chain
tokens fed into the assessors), the next feature-side increment — not another synthesis gate.

---

## Increment 30 — structural feature tokens: a fourth documented negative (feature-side)

### Motivation
Increment 29 (Gate F) proved the strong-side under-credit is a **feature gap**: synthesis_v2's gates
read Finding *tags*, and the tags marking Raman's strong-graded-yet-afflicted factors (exaltation,
kendra, benefic aspect) are identical to those on his afflicted-graded factors — no gate over the
current vocabulary separates them. Increment 30 tests the natural successor: do **new structural
features**, absent from the Finding vocabulary but computable from the same chart, separate the two?

### Design — inert tokens, fail-fast (no engine change)
Rather than wire new findings into the live scorer (an engine change with a full re-pin cascade),
the increment first runs a **read-only separability diagnostic**
(`app/medini/doctrine/validation/structural_separability.py`) on three candidate features, each
targeting a documented strong-side miss:

| feature | definition | targets |
|---|---|---|
| yoga-participation | the factor's planet (house LORD for a bhava) participates in a POSITIVE yoga (`detect_yogas`, true participants) | Sankara's Moon "highly fortified", raja/dhana yogas |
| dispositor-strength | the factor planet's dispositor (`SIGN_RULERS`) itself grades ≥ fairly strong under synthesis_v2 | "the lord is in the sign of a strong planet" |
| benefic-cluster | ≥3 benefic/yogakāraka grahas aspect or conjoin the factor's house | the "combined aspect of Saturn, Jupiter, Mars-yogakāraka" structure |

The go/no-go is a single question: do the tokens appear on the **strong** slice (raman ≥ fairly
strong) and **not** the **afflicted** slice (raman ≤ weak)? If they anti-separate, a gate on them
cannot help, and the negative is established with the live engine untouched.

### Result — the features ANTI-separate
Pooled across held-out + NH-enlarged + anchor (N strong = 30, mid = 42, afflicted = 68):

| signal | strong | mid | afflicted |
|---|---|---|---|
| yoga-participation | 11/30 (37%) | 15/42 (36%) | **29/68 (43%)** |
| dispositor ≥ fairly strong | **0/30 (0%)** | 7/42 (17%) | 8/68 (12%) |
| benefic-cluster ≥3 | **0/30 (0%)** | 1/42 (2%) | 1/68 (1%) |
| any signal | 11/30 (37%) | 20/42 (48%) | **33/68 (49%)** |

Every signal is at least as common on Raman's afflicted-graded factors as on his strong-graded ones
— dispositor-strength and benefic-cluster **never fire on the strong slice at all**. A gate keyed on
any of them would lift the afflicted slice *more* than the strong slice, re-introducing the exact
over-credit A+B fixed. This is stronger than the increment-29 finding: it is not merely that the
*current* tags fail to separate — *new* structural tags computable from the sign+navāṁśa feature
space fail too, and in the wrong direction.

### Verdict — documented negative (feature-side)
The discriminator Raman uses to credit a strong-but-afflicted factor is **not recoverable** from
yoga-participation, dispositor-strength, or benefic-cluster structure over this representation. It is
genuinely holistic — weighing the specific configuration in a way no aggregate feature over the
sign/degree chart captures. synthesis_v2 and house_judgment are **unchanged** (the inert-token design
delivered the negative read-only, at near-zero cost — no wiring, no ablation compute). Pinned by
`test_structural_separability.py`. The remaining lever for the strong side is not feature engineering
over the current chart representation but a richer representation (e.g. an LLM-judge over the full
configuration, or the real-birth degree engine's deeper resolution) — a separate, larger effort.
