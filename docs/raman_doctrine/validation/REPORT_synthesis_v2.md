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
