# Raman Saab — Doctrine Ratchet Plan (89/130 → higher)

**Status:** proposed · **Branch:** `round8-unification` (PR #6) · **Current ratchet:** 89/130 (68.5%)
CONFIRMED Track-B verdicts · **Governing rule:** every change is *doctrine-first, cited,
zero-regression, and non-overfitting* — faithful to B.V. Raman's printed method, not curve-fit
to the golden charts.

## Context & intent
`app/raman_saab/` is a deterministic re-implementation of **B.V. Raman's *How to Judge a
Horoscope*** (HTJAH I/II), judging each bhāva by his three-factor method and scoring the output
against Raman's own worked verdicts (`tests/fixtures/raman_goldens.jsonl`). The ratchet
(`tests/fixtures/golden_accuracy_baseline.json`) only rises, human-bumped in the earning commit.
This plan sequences the next increments to raise fidelity **without violating any classical
principle and without overfitting** — the two hardest misses (chart_60, chart_08) are left failing
*on purpose* because forcing them would be unfaithful, and this plan preserves that discipline.

## The astrological charter (every rule must honour these)
These are Raman's principles as the engine encodes them; a proposed rule that breaks one is rejected.
1. **Three-factor triad, weighed *comparatively*.** Each matter is judged by its **bhāva, its
   lord, and its kāraka**; the *strongest single factor dominates*, two-of-three strong assures the
   matter, and a **weak/combust dominant factor denies it even when another factor is strong**
   (HTJAH-I:3713/3788/3815). This is the core dictum — see WP1.
2. **Kāraka reconciliation per signification.** A house has several sub-matters, each routed to its
   own kāraka (e.g. 4th → mother=Moon, property=Mars, education=Jupiter/Mercury); judged from the
   kāraka-as-lagna frame (`significations.py`).
3. **Strongest-frame reckoning + bhāvat-bhāvam.** Read from the stronger of Lagna/Moon (Sun where
   Raman does); derived houses count from their origin (3rd = younger, 11th = elder siblings;
   HTJAH-I:3444).
4. **Dusthāna affliction & Vipareeta inversion.** 6/8/12 destroy indications; Śaḍbala is
   *directional* — strength aids a benefic matter but **strengthens the evil** for a dusthāna matter.
5. **Papakartari / subhakartari, graded combustion, functional benefic/malefic, cancellations
   (neechabhanga, parivartana, Vipareeta, Bhāvārtha-Ratnākara).** All already primitives; new rules
   compose them, never bypass them.
6. **Verdict vocabulary is ordinal, not numeric:** `favourable | mixed | afflicted |
   insufficient-evidence`; absent testimony = `insufficient-evidence`, explicit negative =
   `afflicted`, explicit positive = `favourable`.

## Gap analysis — the 41 current misses
Worst clusters (engine → Raman): **H9 father (7), H1 self (6), H5 children (6), H11 (5), H2 (4),
H12 (4), H3 (3), H10 (3), H4/H6/H7 (1)**. The **dominant failure mode** (documented since the
53/130 snapshot and still the majority pattern) is *engine = `mixed` where Raman committed to
`afflicted`/`favourable`* — i.e. the judge counts the three pillars as independent booleans
("any benefic + any malefic → mixed") instead of **weighing them comparatively**. Fixing that one
mechanism is therefore both the most doctrinally central and the highest-leverage move.

## Work plan (priority order)

### WP1 — Comparative three-factor weighing  ★ doctrinal core, highest leverage
- **Principle:** Raman weighs {bhāva, lord, kāraka} *against each other* — strongest dominates; a
  weak/combust *dominant* factor drags the matter down (HTJAH-I:3788 combust lord denies despite a
  strong kāraka; HTJAH-I:3815 house+kāraka afflicted denies despite a good lord).
- **Gap:** `judges/house_template.py::_decide` clause-2 does a preponderance *count*
  (`CONTRA_PILLAR_*` knobs) — never a *comparison of effective factor strengths*.
- **Mechanism (doctrine, not tuning):** give each of the three factors an **effective strength**
  that folds in combustion + dusthāna placement (not raw Śaḍbala alone), then let the strongest
  factor's polarity lead, with two-of-three as the tie-break. Keep the ledger→ordinal thresholds
  honestly labelled "golden-tuned heuristic" (spec §6.3) — the *comparison logic* is the cited part,
  the cut-points are not dressed as scripture.
- **Targets:** the `mixed`-bias cluster spanning **H1 (chart_12,18), H2 (chart_43,45,48), H9
  (h9_07,09,12), H12 (h12_01,04,08)** and the chart_60-class holistic judgments.
- **Risk:** high — it touches the shared judge. Mitigation: implement behind the existing clause
  ordering, measure every house, accept only a **net rise with zero individual regression**; if any
  committed golden flips the wrong way, reject per **G5**.

### WP2 — H5 children: putra-affliction, comparative not softened
- **Principle:** 5th matter denied when the **5th, its lord, and Jupiter (putrakāraka)** are
  afflicted, or the **Beeja/Kshetra sphuṭas both barren** (already a gate) — Raman calls these
  `afflicted`, but the engine's strong lagna pillar out-votes to `favourable`.
- **Gap:** 5 of 6 H5 misses are `favourable → afflicted` — the fertility gate only *softens to
  mixed*; comparative weighing (WP1) plus one or two **cited putra-denial combinations** (5th-lord
  in dusthāna with malefic on 5th; afflicted/combust Jupiter as dominant factor) are needed.
- **Method:** read each h5 golden's Raman prose, encode the *specific testimony he cites* as an
  `HN.C.*` clause, flag decisive only if lord==kāraka collapse or explicit denial. **h5_16
  (afflicted→favourable) is the reverse** — do NOT force it if it would be an overfit class-swap
  (per the chart_08 precedent).

### WP3 — Dusthāna nuance: H12 (and H6) over-harshness
- **Principle:** the 12th is a natural dusthāna, but Raman reads *expenditure/moksha* nuancedly —
  benefic testimony yields `mixed`, not blanket `afflicted`. Four H12 misses are `afflicted → mixed`
  (engine too harsh).
- **Mechanism:** a **Vipareeta / benefic-relief modulator** for non-loss 12th significations that
  lifts a lone-malefic `afflicted` to `mixed` when a benefic aspects/occupies — mirroring the
  existing `_dhana_floor`/`_blemishless_venus_floor` house-modulator pattern; cited to Raman's 12th
  treatment. Same shape helps H6 dusthāna-inversion.

### WP4 — Cited yoga & house-rule mining (B5/B6) for H1/H2/H9/H11
- **Principle:** the engine cites only 3 of 13 Raman books; **HPA's 16 named yogas and ~290 unused
  3HC combinations** are cited-but-unencoded fidelity, and the H11/H2/H9 `mixed`-bias misses often
  need a *named positive yoga* (Dhana/Rāja/virtue) to tip to `favourable`.
- **Method (from B5's discipline):** add a yoga **only when a golden exercises it**, in its
  *faithful* form (e.g. Lakshmi #72 needs Śaḍbala — geometry-only over-fires 17/130 and is therefore
  *rejected*), each golden-validated and doctrine-reviewed. Concretely: 3HC Dhana floor already lifts
  H11; extend to the H11 `elder_siblings` misses (11th-from-lagna = elder, bhāvat-bhāvam) and the H9
  bhāgya yogas.

### WP5 — Golden expansion (scale the evidence, don't fit it)
- **Principle:** more of Raman's *own* worked charts = more faithful coverage. *Notable Horoscopes*
  is only 2 of ~50 chapters present (~48 fully-worked goldens missing) — an **acquisition gap** to
  flag to the user (sourcing the text), then run the DRAFT→worksheet→CONFIRMED pipeline.
- This *lowers* the ratchet percentage temporarily (more `total`) but raises true fidelity; it is the
  honest way to grow, and it stress-tests WP1–WP4 against unseen charts (guards overfit).

### Explicitly out of scope (principled non-fixes)
- **chart_60** (Raman calls a Śaḍbala-weak lord "more powerful" — a holistic relative-strength call
  the deterministic engine cannot reproduce without regressing chart_54) and **chart_08** (Venus not
  blemishless — has Mars on it) stay failing. Forcing either is overfit, forbidden by G14.

## Methodology — the per-increment loop (mandatory for every WP above)
1. **Map the exact gap** for the target chart(s): run
   `python -c "from tests.raman_saab.test_goldens import track_b_scoreboard; c,t,m=track_b_scoreboard(); print(c,'/',t); print(chr(10).join(m))"` and read the failing charts' Raman prose in
   `data/knowledge_library/sources/how_to_judge_a_horoscope_raman/…`.
2. **Find the real citation** (`doctrine/sources.py` line resolvers; verify the passage exists — **G7:
   never invent a line; if it isn't there, the rule was hallucinated → delete**).
3. **Author** a `RuleRecord` in the right `rule_sets/house_NN_*/combinations.py` (or a judge modulator
   for WP1/WP3), composing shared predicates from `doctrine/conditions.py`; define a local
   `class _Foo(C.Condition)` if needed — **G13: never fake a predicate** (ship `kind="descriptive"`
   with `TODO(predicate)` if the algebra can't express it).
4. **Doctrine-review** the clause (the `bphs-doctrine-reviewer` pattern): verify it encodes Raman's
   *stated grounds*, not a coincidence (**G14: check fired-rule evidence vs Raman's prose on every
   flipped chart**; a class-swap afflicted↔favourable is treated as overfit and rejected).
5. **Validate zero-regression:** `pytest tests/raman_saab/test_goldens.py -q`. Accept only a net rise
   with **no committed golden regressed** (G5). On a rise, bump `golden_accuracy_baseline.json` in the
   **same commit**, recording chart ids + mechanism in its `_comment` (G6), and refresh Tier-3
   snapshots with `UPDATE_RAMAN_SNAPSHOTS=1`.

## Sequencing & effort
1. **WP1** (judge-mechanism, high effort/med risk) — do first; it is the doctrinal core and should
   clear the largest `mixed`-bias cluster across H1/H2/H9/H12 in one principled change.
2. **WP2 + WP3** (targeted cited clauses/modulators, low–med each) — clean up the H5 and H12/H6
   residue that WP1 doesn't fully resolve.
3. **WP4** (cited yoga/house-rule mining, low–med each, golden-gated) — incremental H11/H2/H9 gains.
4. **WP5** (golden expansion) — ongoing; needs the user to source *Notable Horoscopes*.

## Verification (end-to-end)
- Ratchet: `pytest tests/raman_saab/test_goldens.py::test_track_b_accuracy_ratchet -q` stays green and
  the baseline rises only in earning commits.
- Full suite: `pytest tests/raman_saab/test_goldens.py -q` (Track-A astronomy + Tier-3 snapshots +
  schema + DRAFT/CONFIRMED report) green.
- Live score + misses: the `track_b_scoreboard()` one-liner above.
- Citation integrity: `doctrine/sources.py::verify()` plus a ≥10% manual content-check of new
  citations against the corpus text.
- Single-writer discipline on `raman_goldens.jsonl` / `golden_accuracy_baseline.json` /
  `golden_snapshots/`; every baseline-touching commit re-runs the scoreboard pre-commit.
