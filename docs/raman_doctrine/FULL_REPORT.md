---
title: The Medini Doctrine Engine — Full Report (premise → present)
tags: [moc, raman-doctrine, report]
updated: 2026-07-13
---

# The Medini Doctrine Engine — A Full Report

*From the first honest-measurement question to the present position. This is the narrative that
ties together the per-increment ledger ([`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md)), the
results table ([`VALIDATION_SUMMARY.md`](VALIDATION_SUMMARY.md)), and the ~20 focused reports under
[`validation/`](validation/). Where a number appears here it is reproduced live by a validator and
pinned by a test; where a lever failed, the failure is reproducible and pinned too.*

---

## 0. Executive summary

The goal was never "make astrology work." It was narrower and testable: **build an engine that
reproduces what B. V. Raman actually wrote in *How to Judge a Horoscope* (HTJAH), and measure it
honestly — on charts it was never tuned against, against his own printed verdicts.**

Where that admits a crisp verdict, the engine does well and the numbers are held-out:

| Axis | Result | N |
|---|---|---|
| **Timing** — mahādaśā lord (real births) | **94%** exact (47/50) | 50 |
| **Daśā balance** — starting lord (real births) | **93%** exact (28/30) | 30 |
| **Longevity** — 8th-bhāva strength vs Raman's order | **ρ +0.50** | 14 |
| **Strength** — pooled HTJAH held-out | **56.9%** within-one | 58 |
| **Strength** — NH degree-accurate pooled | **63.0%** within-one | 27 |

The one axis with a genuine **ceiling** is 9-grade *strength*. It sat at ~53% within-one for
fourteen increments. Two things then happened, and both are the real story of this project:

1. **Wiring the encoded doctrine into the grades** (the 1,913 hand-encoded sūtras had never fed the
   strength scores) and then **a doctrine-derived non-linear scorer** (`synthesis_v2`) lifted it to
   **56.9% held-out / 63.0% NH** and put those grades on the live path.
2. **Every remaining attempt to close the last gap — hand-gates, structural features, and a fitted
   ML model — hit the same wall**, and each was turned into a *documented, reproducible negative*.
   The residual is a **holistic judgment** (Raman weighing debilitation against placement against
   association) that no aggregate feature over the sign/degree chart representation can separate.

The honest end state: the doctrine is faithfully encoded and validated on every axis that admits a
crisp verdict; the strength ceiling is *characterized*, not hand-waved; and the last open lever (a
learned model) was tested to a definitive refusal. Closing the final gap would need a fundamentally
richer representation, not another model over the same features.

---

## Part I — The premise and the honest-measurement problem

Early accuracy numbers (audit within-one ~78%) were all measured on corpora the engine had been
*tuned against* — optimistic by construction. The only trustworthy measure is **held-out**: run the
engine on worked charts it has never seen and compare to Raman's own printed verdicts.

Two feasibility findings shaped everything that followed:

- **Raman prints Rāśi + Navāṁśa *sign* diagrams, birth data, a daśā balance, and a verdict phrase —
  never planetary longitudes.** ~150+ distinct nativities exist outside the tuned corpora.
- **The strength verdict needs neither degrees nor daśā.** Bhāva/lord/kāraka strength is a function
  of Rāśi signs + Navāṁśa signs only (daśā drives *timing*, not strength). So a faithful chart can
  be reconstructed from Raman's two diagrams alone: park each planet at its printed Rāśi sign, and
  **back-solve the one navāṁśa pada whose D9 matches his printed Navāṁśa sign** — a deterministic
  lookup, no ephemeris, no timezone parsing.

That insight is what made held-out validation *at scale* possible: the engine's own doctrine could
be isolated from ephemeris/timezone error and tested against Raman directly.

---

## Part II — The validation infrastructure

Built once, reused everywhere. Every piece was designed so the test stays *independent* of the
thing it measures.

- **Reconstruction harness** (`validation/reconstruct.py`) — the sign→chart bridge and the
  **(Rāśi, Navāṁśa) reachability gate**: only 9 of 12 navāṁśa signs are reachable from a given rāśi
  sign, so an unreachable pair is a mis-extraction and is dropped. A free extraction-error detector.
- **Pre-registered verdict→grade map** (`validation/verdict_grade_map.json`) — Raman's phrase
  lattice mapped onto the 9-grade scale, **committed before any scoring** so it can never be tuned
  to flatter the engine. Unmappable phrases are logged and excluded, never guessed. Word-boundary
  matched, most-specific-first.
- **The extractor** (`.claude/agents/raman-chart-extractor.md`) — emits **raw positions + Raman's
  raw verdict phrase only**, never "features the engine would see." This is what keeps the test
  honest.
- **The validators** — `worked_chart_validate` (strength, sign), `nh_strength_validate` (strength,
  degree), `timing_validate` (daśā), `balance_validate` (start balance), `longevity_validate`,
  `anchor_live_validate` (the live calibration anchor). Each exposes a `run()` and is pinned.
- **The blind pipeline** for every corpus expansion: extract raw phrases → mechanical triage →
  **3-agent adversarial attribution audit** (each agent tries to *refute* a candidate: wrong
  nativity? wrong planet? not Lagna-frame? paraphrase not verbatim?) → the frozen verdict-map gate →
  ship. Per-row gold pins prevent silent re-grading.

---

## Part III — The corpora

The engine's data was grown deliberately and kept scrupulously separated:

- **Tuned** (never counted as held-out): houses 2/7/9/11 chapters + the **ch. IV anchor
  (Charts 12–14)**.
- **Held-out (HTJAH)**: the *non-tuned* houses 3/4/5/6/8/10/12, extracted chapter by chapter with a
  vision agent + the reachability gate as an automated quality filter.
- **Blind** (built *after* the engine was frozen): `unseen_scoreable` + `unseen_grow`, disjoint from
  everything by (volume, chart_no).
- **Degree-accurate (real births)**: the *Notable Horoscopes* (NH) set — true printed longitudes, no
  sign reconstruction. Grown 32 → **73 rows** across four expansions (grow, grow2, grow3, grow4),
  each through the full blind pipeline. The attribution audit here caught **5 pre-existing bad gold
  rows** (frame errors and section-bleed misattributions) and removing them *widened* the engine's
  measured lead — the corpus was noisier than the engine.

An honest yield finding recurred throughout: **extraction gives many charts but few scoreable rows.**
Most of Raman's prose is soft/narrative ("good", "ordinary") that the 9-grade map correctly won't
grade. The crisp-verdict houses were the exception; the softest (10th/profession) yield almost
nothing gradeable.

---

## Part IV — The four validated axes

### Timing (daśā) — strong
Seeding the Vimśottarī timeline from Raman's printed balance line and placing each stated event by
age reproduces his **mahādaśā lord exactly 94% of the time on 50 real-birth NH events** (100% on the
8 HTJAH events), and the antara within-one ~93%. This validates the period arithmetic against
ground truth end-to-end.

### Daśā balance — strong
Computing the start balance from the Moon's longitude matches Raman's printed "Balance of X Dasa at
birth: Y-M-D" line on **28/30 NH charts** for the lord and duration — the first *direct* check of
the balance-from-Moon computation.

### Longevity — a discriminating result
8th-bhāva strength predicts Raman's longevity ordering at **Spearman ρ +0.50**, while general
benefic-strength *anti*-predicts it (ρ −0.35). The sign of that contrast matters: it means the engine
is picking up the *right* signal (bhāva condition), not a generic "strong chart = long life" artifact.

### Strength — the axis with a ceiling
The rest of this report is mostly about this one.

---

## Part V — The strength engine and its ~53% ceiling

The strength scorer reads each factor's `Finding`s (dignity, placement, lordship, aspect,
conjunction, kartari, vargottama, combustion, ashtakavarga) and combined them additively:
`score = blend(cap⁺(Σ wᵢ·featureᵢ)_rasi, …_navamsa)` → thresholds → 9-grade. Across every held-out
cut it long sat at **~53% within-one, ~26% exact, with a positive bias (Δ ≈ +0.4 to +0.5 — the
engine over-credits).**

A forensic, per-row diagnosis established the ceiling was **structural, not parametric**:

- **Re-weighting is exhausted.** A full ML weight-fit (`fit_weights.py`, constrained ordinal
  regression over all parameters jointly) and a LOCO-CV recalibration confirmed no re-weighting of
  the existing features closes it.
- **The dominant misses are holistic.** The [ceiling diagnostic](validation/REPORT_ceiling_diagnostic.md)
  showed the kāraka/lord over-credit lives in whole-sign aspects + positive offsets, not
  orb-attackable conjunctions — so even sub-degree resolution can't separate it.
- **Documented negatives, each reproduced:** kāraka over-credit not threshold-separable (increment
  8); ashtakavarga bindus inert (9); neechabhāṅga sub-threshold (12); true-degree affliction
  (combustion + aspect-orb) reduces but does not *separate* the over-credit (13); bhāva-chalita
  placement *hurts* because Raman grades by whole-sign rāśi, not Sripati cusps (14b); degree-graded
  dignity inert within a sign (14c).

The one degree feature that *did* land: **orb-graded combustion** (NH pooled 40.6 → 43.8%), a
phenomenon the sign engine is blind to. It is on by default, gated to real-longitude charts.

---

## Part VI — Encoding the doctrine, and the root cause

A three-agent survey found the deepest problem was not the weights at all:

> **The 1,359 (later 1,913) encoded sūtras never fed the strength grades.** The validators scored a
> path produced *entirely* by ~15 hand-decoded weights; the fired compendium rules went to a
> parallel, unscored path consumed only by the prose reader. The engine encoded the doctrine and
> then didn't use it to judge.

Two increments fixed this:

- **Increment 17 — wire the sūtras into scoring.** A novelty classifier (`sutra_strength.py`) routes
  each *fired, novel* rule to the right factor as a `Finding` with a doctrine-derived weight,
  clamped per factor. This was **the largest single gain**: held-out 52.8 → **54.7%**, NH pooled
  43.8 → **53.1%** — the first *content* change to move the ceiling.
- **Completing the encoding (increment 19).** The compendium was finished — HPA's ~20 pending
  chapters swept and merged under a strict quote-sha/antecedent-compile gate — to **1,913 rules
  across 10 source books**. Most new rules are method/definition/electional/prasna/transit (outside
  the admitted strength types), so they were grade-neutral by policy.
- **Firing coverage (increment 21).** A diagnostic on the Mainpuri kundli found 60 applicable natal
  rules never fired because two orphan compendium domains mapped to no house. Widening candidate
  selection surfaced them for *reading*; the grade path stayed on the increment-17 discipline.

---

## Part VII — The ML research track

With the hand-coded engine at its structural ceiling, the question became: is the residual
*learnable*, even if it isn't hand-codable?

- **A1 — a blinded LLM-as-scorer.** A frontier model graded anonymized positions (no names/dates)
  against the pre-registered map, each real row paired with a **perturbed twin** (identical
  engine-finding multiset, historical identity broken) as a contamination probe. Result: **47.1%
  within-one, with zero real-vs-twin gap** — no better than the engine, and no memorization. The
  holistic read did not beat the structural one.
- **A2 — a learned combine.** A small interpretable model (constrained ordinal logistic + a depth-3
  decision tree) over the engine's *own* Finding tokens scored **63.5% within-one under LOCO-CV vs
  the engine's 51.9% on identical rows** — a real in-distribution gain. Its single robust discovery
  was a **gate**: `sum_neg_rasi ≤ −1.22 → afflicted` regardless of positional credit — the
  "besieged factor is broken" override a linear checklist cannot express.
- **But A2 failed the anchor gate**, and the investigation (A2′) found the failure was *substantive*:
  the model's LOCO training folds are the dusthāna-heavy held-out chapters, skewed toward afflicted
  verdicts; it learned "dense negatives → afflicted" and **collapsed out-of-distribution on the
  house-1 anchor** (strong lagnas with mixed testimony it never saw). The pre-registered gate did its
  job — it caught an overfit model. So the residual is **learnable where there is training signal,
  not a universal replacement.**

The A2 gate discovery, however, was doctrine-consistent and transferable — which is what the next
part is built on.

---

## Part VIII — `synthesis_v2`: the doctrine-derived gated scorer

The A2 experiment said the bottleneck is **synthesis, not resolution**: Raman applies *gate-like
overrides* where the engine applies a blended checklist. `synthesis_v2` encodes exactly that, from
pure doctrine — no fitting:

- **Base** = the additive engine's own grade (so with no gate firing, it reproduces the engine).
- **Gate A — besiegement veto.** Papakartari (hemmed between malefics) caps the factor at "weak".
- **Gate B — deep-affliction gate.** Stacked Rāśi negatives break the factor (the A2 tree's
  `−1.22 / −2.45` split, declared as the only two data-read constants; everything else is cited to
  Raman's decoded weights).
- **Collinearity guard.** Combustion is the tight-orb case of Sun-proximity — counted once, not as
  two independent penalties.

Because the gates only *reduce* from an engine-grade floor, `synthesis_v2` reproduces the A2 tree's
gain **without** its out-of-distribution collapse. Measured, then **promoted to the live grade path
(increment 28)**:

| axis | additive baseline | **synthesis_v2 (live)** |
|---|---|---|
| pooled HTJAH held-out (N=58) | 50.0% | **56.9%** |
| max HTJAH expansion (N=81) | 51.9% | **61.7%** |
| fresh blind (N=14) | 71.4% | **71.4%** |
| NH degree-accurate (N=12) | 41.7% | **58.3%** |
| NH degree pooled (N=27) | 51.9% | **63.0%** |
| NH full degree pool (N=73) | 39.7% | **46.6%** |
| ch. IV live anchor (N=8) | 1/8 | **1/8** (parity) |

Every axis improves or holds; nothing regresses. The additive baseline stays reproducible forever
(scores untouched; the harness recomputes it), so the v2-vs-additive comparison can never be lost.

---

## Part IX — Closing the strong side: four documented negatives

`synthesis_v2`'s two live gates only ever *reduce* a grade. That left one clean failure regime: the
**strong-graded slice** — the factors Raman grades ≥ *fairly strong* — stayed floored (5/29
within-one, pooled). These are fortified-but-badly-placed factors Raman credits despite the
placement (Sankara's Moon "in the 12th though … highly fortified by the combined aspects of Saturn,
Jupiter and Mars-yogakāraka"). Four separate attempts to lift them all failed, each reproducibly:

- **Gate P (strong-promise floor)** and **Gate C (dignity floor)** — retained as documented
  negatives from the start: on sign data, P is inert; C lifts the anchor 1→2 but costs ~17 points of
  held-out, because the same dignity+affliction pattern is Raman-weak on held-out yet Raman-strong on
  the anchor.
- **Gate F (fortification floor, increment 29)** — the positive mirror of Gate B: a fortification
  tally over the same findings (yogakāraka › exalted › vargottama › own › kendra › benefic) that
  floors strong factors *up*. Ablation over 7 threshold + 2 gentle-floor configs: **every one
  regresses held-out (−3..−7) and NH (−11..−33)** to buy the strong-slice lift. Why: the corpora
  carry 68 afflicted-graded rows (A+B scores 82.4% of them within-one) that bear the *same*
  fortifier tags, so a tag-level floor over-fires on them (the afflicted slice collapses 56→41).
- **Structural feature tokens (increment 30)** — the deepest test. New features *absent* from the
  Finding vocabulary but computable from the chart: **yoga-participation, dispositor-strength,
  benefic-cluster**. A read-only separability diagnostic (the inert-token design — engine untouched)
  showed they **anti-separate**: each signal is at least as common on the afflicted slice as the
  strong slice (dispositor-strength and cluster *never* fire on the strong slice at all). A gate on
  them would lift the afflicted rows *more* than the strong ones.

**The conclusion these four force:** Raman's discriminator between "fortification that overrides the
affliction" (his strong verdict) and "fortification that fails to" (his afflicted verdict) is **not
in the feature space** — sign *or* degree. It is holistic and configuration-specific. No gate or
aggregate feature recovers it.

---

## Part X — The two side tracks

### Track 2 — the two promoted-but-unmeasured live components
`synthesize_house` (the overall house verdict) and the Chandra-Lagna (from-the-Moon) sub-verdict
were both promoted live yet scored against ≈0 gold. A read-only yield probe over 168 charts found
Raman's overall-house verdicts map to a 9-grade in **3/168** cases and Chandra-Lagna in **1/67** —
his overall and from-the-Moon statements are narrative or woven into bhāva/lord phrases, so both
stay reading-side-by-design. Against the honest substitute (the central tendency of Raman's crisp
factor verdicts), `synthesize_house`'s **fusion formula is sound** — 12/14 (85.7%) within-one on the
≥2-factor slice — and end-to-end it tracks Raman's central tendency in line with per-factor accuracy.
A first measurement of a component that was previously scored on one stray row.

### Track 3 — transit / gochara: not pursued
A feasibility probe found the transit dimension has thin substrate: Raman's *stated* transit-at-event
prose is near-nil in the available sources, and the 50 dated deaths are daśā-timed, not
transit-annotated. The only computable path (gochara doctrine-satisfaction at the dated deaths) tests
satisfaction rather than agreement and overlaps prior null ML death-timing work. A full gochara
engine exists but is disconnected from the doctrine grade path. Decision: **conclude rather than
build a large validator on weak ground** — scoped for a future session if the death-chapter transit
prose is extracted.

---

## Part XI — The learned-combine landing test (the last lever, resolved)

The one un-landed opportunity was the A2 learned model's in-distribution gain. Its documented landing
path was "house-1 / kendra-strong training rows + a grid-backed anchor re-baselined through the live
engine." Both were supplied and the test run (`learned_combine_landing.py`):

- the anchor scored in **live engine representation** (grid-backed ch. IV casts, judged live — the
  re-derivation the path named), and
- the model trained under three regimes, one injecting the **strong-heavy full NH pool** (73 rows,
  15 strong-graded) — the missing training signal.

**Result: 0/8 within-one on the live anchor in every regime** (ordinal and depth-3 tree; the tree
predicts "afflicted" for all 8 house-1 rows). Adding strong training signal does **not** cure the
collapse — the anchor's strong-lagna verdicts are not feature-separable from afflicted ones, the
*same* holistic gap increments 29–30 proved. The model is strictly worse on the anchor than the live
engine (0/8 vs 2/8) because it lacks the engine-base floor `synthesis_v2` uses. And `synthesis_v2`
already landed the model's one transferable discovery (Gate B) *with* that floor, holding anchor
parity.

So the ceiling residual is **learnable in-distribution but not landable**, and the pre-registered
anchor gate is vindicated at the model level.

---

## Part XII — The honest final position

**What landed:**
- The doctrine *wired into the grades* (increment 17) — the biggest single gain, fixing the root
  cause that the 1,913 encoded sūtras never fed the scores.
- `synthesis_v2`, a doctrine-derived gated scorer, **promoted live**: held-out **56.9%**, NH
  **63.0%**, every axis up or level.
- Orb-graded combustion (the one degree feature that separates).
- Timing (94%), balance (93%), longevity (ρ +0.50) — validated and wired into the reading output.

**What is a documented negative (each reproducible + pinned):**
- Re-weighting / recalibration; ashtakavarga; neechabhāṅga; bhāva-chalita; degree-dignity;
  true-degree affliction (reduces, doesn't separate).
- The four strong-side attempts: Gate P, Gate C, Gate F, structural tokens.
- The learned combine's landing (0/8 on the live anchor even with strong training data).

**What is left:** the strong-side residual is a *holistic* gap no sign-or-degree feature closes.
Closing it needs a fundamentally richer representation — a full configuration-level model, or the
real-birth degree engine's deeper resolution applied to features that don't yet exist — not another
model over the same features. Track 3 (transit) is scoped but deferred as low-expected-value.

**The through-line:** every path to beating the strength ceiling — hand-gates, structural features,
and a fitted ML model — hits the identical wall, and each rejection is characterized and
reproducible. That is the result. The engine is faithful where a crisp Raman verdict exists, and the
one place it plateaus is understood, not hidden.

---

## Part XIII — Integrity and reproducibility

- **Held-out is held-out.** No corpus in the held-out/blind tables was used to fit any weight or map
  entry; blind corpora are (vol, chart_no)-disjoint from everything else.
- **Verdicts are pre-registered.** Phrases → grades once, committed before scoring; per-row gold
  pins prevent silent re-grading.
- **Grids are prose-cross-checked** and pass the Navāṁśa reachability gate before they score.
- **Two anchors, two scopes.** The frozen ch. IV anchor pins the *harness* representation (8/8); the
  **live** anchor (faithfulness-gated casts) records the honest live state (1/8) so frozen-vs-live
  drift can never hide.
- **Every headline number is a tested contract.** `tests/doctrine/test_validation_summary.py` re-runs
  each validator and asserts the numbers still hold; each negative has its own drift-guard.

**Reproduce the headline axes:**
```
PYTHONPATH=. python3 -m app.medini.doctrine.validation.synthesis_v2_validate       # strength, 3 axes
PYTHONPATH=. python3 -m app.medini.doctrine.validation.timing_validate             # daśā timing
PYTHONPATH=. python3 -m app.medini.doctrine.validation.balance_validate            # start balance
PYTHONPATH=. python3 -m app.medini.doctrine.validation.longevity_validate          # longevity ρ
```
**Reproduce the negatives:**
```
PYTHONPATH=. python3 -m app.medini.doctrine.validation.structural_separability     # incr 30
PYTHONPATH=. python3 -m app.medini.doctrine.validation.learned_combine_landing     # A2 landing
PYTHONPATH=. python3 -m app.medini.doctrine.validation.overall_consistency         # Track 2
```

**Report index:** [`VALIDATION_SUMMARY.md`](VALIDATION_SUMMARY.md) (results ledger) ·
[`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md) (per-increment history) ·
[`ML_RESEARCH.md`](ML_RESEARCH.md) (A1/A2 + roadmap) ·
[`validation/REPORT_synthesis_v2.md`](validation/REPORT_synthesis_v2.md) (increments 24–30) ·
[`validation/REPORT_house_moon.md`](validation/REPORT_house_moon.md) (Track 2) · plus the focused
`validation/REPORT_*.md` per axis.

---

*Last updated 2026-07-13. Full doctrine suite: 322 tests green. Every figure above is live-reproduced
and pinned.*
