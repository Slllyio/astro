---
title: "Raman Saab — Detailed Execution Plan to the Truest Engine (v3, 2026-06-12)"
kind: plan
topic: process
measured: false
updated: 2026-06-12
words: 5415
tags: [raman-saab, plan, process]
---
# Raman Saab — Detailed Execution Plan to the Truest Engine (v3, 2026-06-12)

## Context

`app/raman_saab/` is the deterministic replica of **B.V. Raman's *How to Judge a Horoscope***.
The architecture is built and validated; what remains is the **accuracy climb**: encoding the
remaining doctrine and proving every step against Raman's own verdicts via the live ratchet.
This plan details every remaining stage **with explicit contingency branches** (each possibility
→ the prescribed action), so execution never stalls on an unanticipated outcome.

**State as of `a90414d` (all committed, suite 1212 passed / 5 skipped / 3 xfailed):**
- Phases A + B + A-deps + wiring COMPLETE: per-signification judge (3 frames, §6.3 rule,
  veto/salvage/bhava-rescue, navamsa+yoga modulation, H5 fertility gate, lookup metadata,
  chart_overview), golden harness (Track A sign-gate, Track B ratchet, Tier-3 snapshots,
  DRAFT-gate), 16 cited yogas, 3 sphuta engines, 93 lookup rows, kemadruma bhanga corrected
  to 3HC, 12 **user-CONFIRMED** H1 goldens, **ratchet floor 7/12** (Sakata corrected chart_33).
- Rule corpus: 255 placement rules + 15 H7 extras + 16 yogas. Combinations layer unencoded.
- 5 open H1 mismatches: charts 09, 10, 17, 20, 31 (diagnosed below, each with its fix).

**Locked decisions carried forward (do NOT relitigate):** Raman ayanamsa; Bhava/Chalita results
+ whole-sign lordship/aspects/Kartari; nodes 7th-only, mean node; 7-karaka AK; no `app/core`
imports; every rule cites a real on-disk corpus line; ordinal verdicts; user validates goldens
(DRAFT→CONFIRMED); ratchet floor only rises, human-bumped in the earning commit; corrected
harana order (Chakrapatha → Satrukshetra [Mars+retro exempt] → Astangata [Venus/Saturn fully
exempt] → Krurodaya [absolute, Pindayu-only]); Vipareeta = Raman's narrow form; maraka
tie-break = Chart-35 unit-counting; spans 8-32/33-75/75-120; §6.3 numbers = golden-tuned
heuristics never cited to Raman; 3 Shadbala xfails stay.

**Standing execution protocol (every batch, no exceptions):**
implement (subagent/workflow, TDD) → adversarial review (doctrine + code lenses; **the doctrine
reviewer content-verifies a random ≥10% sample of NEW citations against the corpus text** —
`verify()` is range-only and cannot catch wrong-but-in-range lines) → fix CRITICAL/HIGH
(MEDIUMs at orchestrator discretion, doctrinal MEDIUMs always) → full suite green →
**Tier-3 snapshot regeneration, REVIEWED**: the reviewer diffs the snapshot delta and classifies
every change as evidence-addition (expected) vs verdict-change (must match the batch's intended
flips); regenerated snapshots commit WITH the earning batch (never reflexively) → ratchet
measured → surgical commit on `round8-unification` (simple one-line `-m`, no `git add -A`, no
Co-Authored-By) → BUILD_STATUS.md updated at milestones.

**Single-writer rule for ratchet artifacts:** `raman_goldens.jsonl`,
`golden_accuracy_baseline.json`, and `golden_snapshots/` are ORCHESTRATOR-owned. Confirmations/
re-bases land only BETWEEN encoding batches, never mid-flight. Every commit touching the
baseline re-runs `track_b_scoreboard()` at HEAD immediately pre-commit and records old/new
`correct/total` in the JSON `_comment` (prevents stale-denominator bumps when stages interleave).

---

## GLOBAL CONTINGENCY TABLE (applies to every stage)

| # | Possibility | Action |
|---|---|---|
| G1 | Subagent dies on **session limit** mid-workflow | Work is journaled: resume via `Workflow({scriptPath, resumeFromRunId})` — builds cache-hit, only dead agents re-run. If resume also fails, fall back to direct `Agent` calls one at a time; if still limited, orchestrator does the review itself in-session (read-only) and defers heavy builds. NEVER commit unreviewed verdict-affecting code. |
| G2 | **Corpus line OCR-garbled** at the citation target | Encode only what is legible; SKIP the garbled row/rule and log it in the module docstring + report (precedent: named-drekkana grid). Never guess content. If the methodology file has a clean transcription with a different line ref, cite BOTH lines with a note. |
| G3 | **Book self-contradiction** (printed rule ≠ worked example) | Worked examples win when ≥2 agree (precedent: Saham "+Lagna-lord"); single conflicting example → follow the stated rule and `xfail(strict)` the example cell with the quantified delta (precedent: Mars/Venus Ayana). Document in the module docstring; never silently average. |
| G4 | **Suite goes red** after a merge of parallel work | Re-run to rule out mid-edit race; if persistent, `git stash`/isolate per-file to find the breaking file; fix forward if trivial, otherwise revert the offending uncommitted file and re-dispatch its builder with the failure attached. Never commit red. |
| G5 | **Ratchet drops** below baseline after a change | The change is rejected by default. Diagnose via `track_b_scoreboard()` mismatch lines: (a) rule mis-encoded → fix the rule; (b) rule correct but polarity/tag wrong → fix metadata; (c) rule correct and the PREVIOUS pass was right-for-wrong-reasons (a crutch removed) → present evidence; only with explicit justification may the baseline re-base, in its own commit, with the reason in the JSON `_comment`. |
| G6 | **Ratchet rises** | Bump `golden_accuracy_baseline.json` in the SAME earning commit, recording chart ids + mechanism in `_comment`. |
| G7 | **Citation guard fails** (a rule cites a non-resolving line) | The encoding agent must fix before handoff (re-locate the passage). If the passage truly doesn't exist → the rule was hallucinated → DELETE it and log; never invent a line. |
| G8 | **Ambiguous verdict prose** during golden extraction | Emit DRAFT with `confidence ≤ 0.5` + the ambiguity note; surface in the user worksheet with the reviewer's alternative readings. NEVER auto-confirm. |
| G9 | **User validation pending** for a DRAFT batch | Non-blocking: DRAFTs are inert (gate skips them). Continue encoding/building; the ratchet simply measures over the confirmed subset. Re-surface the worksheet at the next natural pause. |
| G10 | **Lagna/planet near a sandhi** in a fresh-cast golden | Track A logs to the audit list (never hard-fails within ±2°); keep Raman's printed value in `lagna_sign`. If >1 sign off AWAY from a cusp → birth-data decode is wrong → re-read the corpus header (tz/LMT decode, precedent chart_33 IST). |
| G11 | A fix requires touching a **committed Phase-1/2 primitive** | Allowed when the corpus demands it (precedent: kemadruma bhanga), but: cite the line, keep the old behavior available/labeled if existing tests pin it (extended/NOVEL tag), rebuild affected fixtures honestly, full suite green. |
| G12 | **Parallel builders** would touch the same file | Don't parallelize that batch — sequence it, or split the file first (the rule_sets house-split). File ownership is per-builder, orchestrator commits. |
| G13 | An encoding requires a **missing predicate** mid-batch | If trivial (pure function of existing chart data) → the builder adds it to `conditions.py` with tests in the same change. If non-trivial (varga overlay, nakshatra math, new chart state) → rule goes in as `kind="descriptive"` with a `TODO(predicate)` marker + the batch report flags it; Stage-D picks it up. Never fake a condition. |
| G14 | **Engine right-for-wrong-reasons** suspicion (a golden passes but the fired evidence looks off) | The adversarial reviewer checks fired-rule evidence vs Raman's stated grounds on every flipped chart (precedent: chart_33 Sakata-not-Kemadruma). If confirmed: pin the true mechanism with a test, log the "crutch" as a known issue, and add the genuine doctrine to the next batch so the verdict stands without the crutch. |
| G15 | **Tier-3 snapshot drift** after a rule batch (every batch WILL drift the snapshots of goldens in that house) | Follow the standing snapshot protocol: reviewed regeneration, evidence-additions expected, verdict-changes must match intended flips; commit with the batch. Red snapshots are never "fixed" by blind `UPDATE_RAMAN_SNAPSHOTS=1`. |
| G16 | **User confirmation contradicts a currently-PASSING engine verdict** (a confirmation makes accuracy drop) | Legitimate measured drop, same deliberate re-base path as new-territory drops (G5-c wording): re-base in the confirmation commit, `_comment` records the contradicting chart ids; the chart joins the next batch's mismatch-target list. |

---

## STAGE 1 — Phase C-0: H1 deep encoding, mismatch-targeted

**Goal:** flip charts 10, 20, 31 (and ideally 17) to Raman's confirmed verdicts by encoding the
H1 affliction layer they actually need; raise ratchet from 7/12 toward 10-11/12.

### 1a. Prerequisite predicates (small, build first — `doctrine/conditions.py` + tests)
Per the mismatch diagnosis, these four unlock the H1 combinations (G13 applies to any other):
1. **`InVargaHouseFrom(p, origin, houses, varga="D9")`** — the Navamsa 6/8/12 overlay (rules
   #40-#67; also chart_10's "Saturn debilitated in Navamsa" via D9 dignity). Reuse
   `chart/varga.py` navamsa math; origin semantics mirror `InHouseFrom`.
2. **`VargaDignity(p, varga, states)`** — dignity computed on the D9 (or other varga) sign
   (chart_10, chart_31 Navamsa weakness). Reuse `primitives/dignity` tables on `navamsa_sign`.
3. **`Dwirdwadasha()` / `PlanetPairIn2_12(p1,p2)`** — the 2/12 mutual-scatter test (rule #34;
   charts 09, 31). Pure rasi-house arithmetic.
4. **`SignClass(sign)` helpers** (`SignIsSushka`, `SignIsWatery`) — constitution rules #13-#19.
   Data + accessor in `chart/constants.py` or `doctrine/lookups`.
5. **`LordsConjunct(h1, h2)`** (lord-of-house-A conjunct lord-of-house-B) — review fix F4: rule
   #1 ("lord of birth with lord of 6/8/12", the chart_10 killer) and the #40-#65 lord-with-lord
   family have NO existing predicate shape (`Conjunct` takes planet names, `LordIn` places one
   lord). Build + test BEFORE group builders dispatch.
6. **`LORD_OF(n)` origin** in `_origin_house` (shared by `InHouseFrom`/`ClassInHouseFrom`/the
   new `InVargaHouseFrom`) — the #41-style D9 rules count "from the sign held by the 2nd lord";
   no such origin exists. Because `_origin_house` is shared infrastructure, it is built HERE,
   once, by one builder — never mid-batch in parallel (G12).
   (Defer `TaraOf` to Stage 5: rules #35/#36 go in as `kind="descriptive"` + `TODO(predicate:
   TaraOf)` per G13 — `InStarOf` checks a star's lord, NOT the 3rd/5th/7th-star-from-Janma
   count, so it does NOT suffice.)

| Possibility | Action |
|---|---|
| D9-dignity tables differ from D1 (moolatrikona N/A in varga) | Encode dignity-in-varga as own/exalt/debil/friendly only; document that moolatrikona is a D1-degree concept (corpus-check first). |
| `InVargaHouseFrom` semantics ambiguous (house counted in D9 from D9-position of origin?) | YES — both endpoints in the varga chart (that is Raman's usage, HTJAH-I:1709-1789 block). Pin with a worked-example test from those lines. |

### 1b. Encode the H1 combination groups (~67 atoms + S1-S9 + constitution + Moon-mind)
**Step 0 (unconditional — review fix F10):** split `rule_sets/house_01_lagna.py` (193 lines
today; the batch far exceeds the 600-line threshold, so splitting mid-batch is inevitable —
do it FIRST) into a `house_01_lagna/` subpackage, one module per group. The ORCHESTRATOR owns
the two shared registration files (`rule_sets/__init__._MODULES` and
`test_rule_sets.ALL_RULE_SETS`) — builders never touch them; alternatively land pkgutil
auto-discovery once here, before Stage 4 makes registration a 12× problem.
**Tagging policy (review fix F2):** ALL 1b rules ship with the existing coarse
`signification="self"` tag (plus `group=` markers) so they route immediately — fine re-tagging
is 1c, AFTER measurement. One builder per group-module (disjoint files, G12):
- **Group 1 (the mismatch killers, encode first):** #26/#27 hemming rules (Papakartari on Lagna
  and on the lord, with the #27 positional note as effect-text), #28 many-malefics-in-Lagna,
  #1 lord-with-6/8/12-lord health rule (chart_10), #20 all-three-pillars context rules, the
  functional-malefic-in-Lagna readings (Sun/Mercury as 2nd/3rd lords — chart_20; predicate
  `FunctionalNature` exists), neecha-lord-conjunct-node (chart_33's true grounds — removes the
  Sakata crutch, G14).
- **Group 2:** remaining Important Combinations #13-#39 (existing predicates suffice per
  inventory).
- **Group 3:** Navamsa qualifiers #40-#67 (needs 1a-1/1a-2).
- **Group 4:** constitution/Sushka #13-#19 (needs 1a-4) — tag `body`.
- **Group 5:** Moon-mind rules (frame="MOON", `InHouseFrom(..., "MOON", ...)` exists) — tag `mind`*.
- **Group 6:** per-sign afflictions S1-S9 — condition = `And(LagnaInSign(s), ...)` (add trivial
  `LagnaInSign` if absent; per-sign auto-filter is just a conjunct, no new machinery).

*`mind` requires adding a `Signification(key="mind", ...)` row to `significations.py` H1 (cited).

### 1c. Re-tag H1 + routing — runs AFTER 1e measurement (review fix F2: order is 1a → 1b → 1e → 1c)
Split `signification="self"` into fine tags: `self`, `body`, `health`, `mind` — in ONE commit
under a **scoreboard-invariance guard** (per-chart verdicts unchanged, total stays 12).
**Golden-to-signification policy (decided now, not left to agents):** the H1 `self`
signification keeps an AGGREGATE bridge — `rule_tags=("self","health","body","mind")` — because
Raman's H1 worked-chart judgments (and the user's confirmed verdicts) are whole-house readings;
the fine rows (`body`/`health`/`mind`) get `(key,)` for targeted sub-verdicts. This means the
mismatch-killer rules (e.g. the #1 health rule for chart_10) feed BOTH their fine matter AND
the `self` verdict the goldens assert — no orphaned testimony.

| Possibility | Action |
|---|---|
| Re-tag changes per-chart verdicts despite the bridge | The invariance guard fails the commit; the tag assignment that moved testimony out of `self` is re-examined per the corpus, not per the test. |
| The 12 CONFIRMED goldens' `signification` key is `self` — fine tags could orphan them | Covered by the aggregate-bridge policy above + the GLOBAL golden-key invariant (review fix F9): a schema-guard test asserts every CONFIRMED golden's signification key exists in `significations_of(house)`; any future house re-key ships a mechanical golden key-migration in the same commit. |

### 1d. Bhava-frame audit (chart_17's mechanism)
Chart_17 needs Ketu-in-Lagna-rashi recognized as **12th-bhava** occupant (HTJAH-I:1945, the
locked Bhava-for-results rule). Audit: H1 planet-in-house rules use `InRashiHouse(p,1)`;
Raman's occupancy *results* are bhava-based. Action: for H1 (pilot), add bhava-variant
conditions where Raman's text is occupancy-result language — encode as
`C.InHouse(p, 1)` (Chalita) for the result-rules while keeping rasi-house rules where the text
is sign-language. **Burden flipped (review fix F12): Chalita `InHouse` is the DEFAULT for
occupancy-result rules per the locked Bhava-for-results decision; a rasi-frame encoding
requires a cited sign-language justification flagged for the doctrine reviewer** (not a free
per-rule call). The interim cross-house asymmetry (H1 bhava-framed before H2-12's Stage-4
passes) is a KNOWN STATE — record it in BUILD_STATUS so it doesn't generate spurious bug reports.

| Possibility | Action |
|---|---|
| Bhava-frame switch flips OTHER confirmed charts (rasi≠bhava placements elsewhere) | Scoreboard per-chart diff before/after; any newly-mismatched confirmed chart → that rule reverts to rasi-frame pending corpus re-read (the frame call was wrong for that rule). |
| Track-B charts (`from_stated_positions`) carry `bhava` from the stated dict — sparse charts may lack it | `InHouse` predicates are already None-safe; verify with the sparse-chart tests. |

### 1e. Measure + per-chart contingencies (the heart of this stage)

Run `track_b_scoreboard()` after each group lands. Expected per chart:

| Chart | Expected flip | If it flips | If it does NOT flip | If it overshoots |
|---|---|---|---|---|
| 10 (favourable→afflicted) | Group 1 (#1 health rule + D9 debility) | bump baseline (G6) | check the #1 rule actually fires (lord-with-6th-lord conjunction present? functional table says Moon=6th lord for Aquarius? verify); if fires but verdict still favourable → the strength pillars outvote; inspect ledger: malefic fired + weak pillar should hit clause 6 | afflicted is the target; n/a |
| 20 (favourable→afflicted) | Group 1 (#28 + functional-malefic + hemming-on-lord) | G6 | verify `FunctionalNature` returns malefic for Sun/Mercury @ Cancer lagna (table check); verify HemmedBy("Moon") fires (whole-sign adjacency satisfied?) | n/a |
| 31 (favourable→afflicted) | Group 1 hemming ×2 + Group 3 D9-weakness | G6 | hemming on lord requires Ketu/Saturn flanks — verify node handling in `HemmedBy` (nodes count as malefics per `NATURAL_MALEFICS` in `primitives/functional_nature.py` — NOT `_HOUSE_CLASS`, which is the kendra/trikona dict); if verdict lands mixed not afflicted → acceptable interim (closer); record | n/a |
| 17 (afflicted→favourable) | 1d bhava-frame (Ketu out of H1) + Jupiter-aspect-fortifies rule | G6 | if still afflicted: ledger shows WHICH malefic fired — if `H1.P.Ketu` (rasi) persists, the 1d frame call for that rule needs the doctrine reviewer's ruling | if it becomes mixed: acceptable interim, record |
| 09 (favourable→insufficient) | HARDEST — "ordinary" ≈ canceled testimony | unlikely to flip cleanly | **Accept as known-mismatch** if Groups 1-6 leave it favourable/mixed: document that `insufficient-evidence` requires near-zero net testimony which the engine only reaches with no fired rules; do NOT hack a per-chart rule (forbidden); optionally re-surface to user: is `mixed` a tolerable re-read of "ordinary"? (user decides; if yes, golden edited in a user-attributed commit) | n/a |

**Stage-1 exit:** ratchet ≥ 9/12 expected (10/12 good case). ANY result is recorded in
BUILD_STATUS + the baseline moves per G5/G6. The Sakata crutch on chart_33 must be replaced by
the true grounds (G14) with the pin-test updated. **chart_33 crutch-removal contingencies
(review fix F3 — the most likely failure is NOT "rule doesn't fire"):**
- New malefic rule doesn't fire → fix the rule (condition/predicate), before commit.
- New rule FIRES but the verdict lands **contradiction-mixed** (the ledger still carries
  benefic testimony, e.g. H1.L.3, so clause-2 fires and the arishta drop is correctly blocked
  by its own contradiction guard) → the doctrine reviewer adjudicates the benefic testimony
  on chart_33's H1 against the corpus: is H1.L.3's benefic reading genuine for a debilitated
  Saturn-with-Rahu, or itself a crutch (a placement rule firing fortified for an afflicted
  lord)? If the benefic testimony is bogus → fix THAT rule's branch selection (corpus-cited).
  If BOTH testimonies are genuine → the malefic-preponderance question goes to the USER —
  never resolved by weakening the contradiction guard or re-tagging to dodge it.
- Removing the crutch is not urgent enough to block the batch: if unresolved, keep the Sakata
  pin AND the new rule, document the open adjudication, proceed.

---

## STAGE 2 — Golden corpus expansion (continuous, parallel to all stages)

**Inventory (from corpus survey):** ~374 worked charts; ~250 fresh-cast eligible. Batches:

| Batch | Houses | ~Charts | Priority | Notes |
|---|---|---|---|---|
| A2 | H1 remaining | 18 | P0 | richest prose; extends the existing confirmed set |
| B | H2+H3 | 14 | P1 | sibling-count forensics need D9 count predicates (Stage 5) |
| E | H8+H9 | 35 | P1 | longevity-critical; feeds Phase E directly |
| C | H4+H5 | ~40 | P2 | mixed DOB quality — careful tier routing (full vs sign-only) |
| D | H6+H7 | ~55 | P2 | many sign-only → Track-B-only tier |
| F | H10+H11 | ~55 | P2 | career/gains; H11 elder-sibling counts |
| G | H12 | ~22 | P3 | last |

Per batch: extractor agent drafts (lexicon ordinal + verbatim prose + confidence + citations;
fresh-cast where DOB/TOB/POB, else stated-positions tier; rule-level/doctrine_statement tiers
for partials per schema) → doctrine reviewer pre-screens (flags alternate readings) → **user
worksheet** (same xlsx-able format as pass #1) → user calls applied verbatim → CONFIRMED →
ratchet total grows → baseline re-based deliberately in that commit (G5-c path, documented).

| Possibility | Action |
|---|---|
| New confirmations DROP the accuracy fraction (new territory measured) | This is a legitimate re-base (not a regression): set the new floor at the measured value in the same commit applying the confirmations; `_comment` records old/new and why. |
| A batch's house has NO encoded combination rules yet | Expected: those goldens will largely mismatch → they become that house's Stage-4 target list. Confirm them anyway (the measure is the point). |
| User edits a verdict later (changes mind) | Goldens are data: user-attributed commit editing the JSONL; ratchet re-measured; baseline re-based with the reason. |
| Birth-data decode ambiguous (LMT vs IST, E/W) | Decode convention is documented in the extractor; ambiguous → flag in worksheet + confidence ≤0.5 + provenance note (precedents: chart_29, Lincoln). |

---

## STAGE 3 — Threshold tuning, first REAL run (after Stage 1 + batch A2 confirmed)

**Known defect to fix first (corrected per deep review F1 — the original fix was itself
unimplementable):** the tuner's holdout `_HOLDOUT_PREFIXES = ("HTJAH-I.chart_",
"HTJAH-II.chart_")` excludes **every existing golden** → empty fit set, zero signal (verified).
Note the death charts are stored AS `HTJAH-II.chart_73/74/75/78` (no "named" id form exists)
and carry ZERO confirmed Track-B verdicts — they measure longevity (Stage 6/7), not Track-B
accuracy. The implementable fix (a CODE task, not a constant edit):
1. **Holdout membership** = explicit id list `{HTJAH-II.chart_73,74,75,78}` (excluded from fit
   regardless) **+ a stable hash slice of confirmed worked examples**: `zlib.crc32(id) % 5 == 0`
   (~20%, membership NEVER churns as the corpus grows — "every 5th of the sorted list" would
   leak previously-fitted charts into the holdout).
2. **Holdout SCORING**: extend `run()` to score fit and holdout separately and print both —
   `_filter_holdout` currently just discards records, so "improves fit, drops holdout" is not
   currently a computable branch. Add the (chart-cast cache keyed by golden id) in the same
   commit (pure function of birth data; Track A/B/Tier-3 re-cast the same charts today).

Run `py -3.12 -m tools.raman_saab.tune_thresholds --max-iterations=50 --holdout-lock` once
≥25-30 fresh-cast CONFIRMED verdicts exist. **First APPLIED diff additionally requires
confirmations from ≥2 houses (review fix F11)** — tuning global thresholds on H1-only
phenomenology is advisory-only (the report must break accuracy per house; single-house
improvements are recorded, not applied).

| Possibility | Action |
|---|---|
| Tuner finds a setting that improves fit AND holdout | Human applies the diff to `total.py` in a dedicated commit citing both numbers; Tier-3 snapshots regenerate (reviewed); baseline bumps. |
| Improves fit, DROPS holdout | Overfit → reject; record the attempt in the tuner report archive. |
| Suggests a value at its GBB bound | Red flag per plan: do not apply; investigate whether the misses it chases are rule-gaps (usually) — feed Stage 4 instead. |
| No improvement at any step | Thresholds already optimal for current corpus → record and move on; re-run after each major confirmation batch. |
| Tuner runtime explodes (full judge × goldens × steps) | Cache chart casts per golden id (pure function of birth data); cap with --max-iterations; acceptable up to minutes. |

---

## STAGE 4 — Phase C breadth: combinations house-by-house (the long middle)

Order: **H8+H2 (maraka-adjacent, feeds Phase E) → H7 (incl. Kuja-Dosha grid wiring, encoding
home `primitives/kuja_dosha.py`) → H10 → H4 → H5 (fertility rules around the gate) → H6
(dusthana-inversion meta-modifier) → H9 → H11 → H12 (Bhavartha inversion flag) → H3.**
Rationale: longevity path first, then the highest-worked-chart houses.

**H8 measurement caveat (review fix F7):** the LONGEVITY_GUARD clamps afflicted on
longevity/death matters until Phase E — so Stage-4-H8's ratchet expectation is scoped to
NON-guarded H8 matters (legacies, sudden_gains); the guarded batch-E cohort is pre-declared a
tracked known-mismatch block in the baseline `_comment`, resolved at Stage 6. **Therefore
INTERLEAVE: run Stage 6 (longevity engine) immediately after the H8+H2 encoding pass** — its
prerequisites are already DONE — so the guard lifts and H8's goldens become measurable before
the H7/H10 batches proceed.

**Stage-4 entry tasks (review fix F17 — certain, not contingent):** add the
(chart,house)-keyed `fire_house` cache inside a judge pass (EvalContext) and the session-scoped
chart-cast cache (shared by Track A/B/Tier-3) BEFORE the rule corpus scales — at ~900 rules ×
150+ goldens the >10s suite trigger fires with certainty.

Per house (the repeating unit — same as Stage 1 pattern):
1. If goldens for the house exist+confirmed: list its mismatches → encode mismatch-killers first.
2. Encode the house's Important Combinations groups (parallel builders on disjoint groups, G12;
   split file at 600 lines).
3. Re-tag that house's rules to fine significations; collapse its `rule_tags` bridge.
4. Special-grid wiring where the house owns one (H7 Kuja-Dosha 3-point grid as sub-verdict;
   H6 dusthana polarity inversion as proforma meta-modifier — NOT a condition; H12 Bhavartha
   `inverted` flag; H2 Special-Dhana parallel verdict surfacing).
5. Adversarial review (doctrine lens mandatory — it has caught a real error in EVERY round so
   far) → fix → measure ratchet → commit (+baseline per G5/G6).

| Possibility | Action |
|---|---|
| A house's combinations are dominated by missing predicates | Encode the encodable now; descriptive-tag the rest with TODO(predicate) (G13); schedule the predicate in Stage 5 ordered by how many rules it unblocks. |
| Dusthana-inversion (H6) flips confirmed non-H6 verdicts via shared planets | The inversion is signification-scoped metadata/polarity at the H6 judge only — guard-test that no other house's verdict changes when it lands. |
| Kuja-Dosha synastry requests creep in | OUT OF SCOPE v1 (locked) — single-chart grid only. |
| Rule count makes the suite slow (>10s) | Profile; cache `fire_house` per (chart,house) within a judge pass (EvalContext); only optimize after measurement. |

---

## STAGE 5 — Phase D: remaining predicates + sub-engines (demand-ordered)

Build when a Stage-4 house demands them, ordered by rules-unblocked: `TaraOf` (H1 timing, H4
mother-death, H8) · `AspectStrengthGreater` (graded Drik from `shadbala/drik.py`) ·
exact-degree/orb gates (Charts 14/30 conjunction exceptions) · `STRONGEST_OF`/`KARAKAMSA`
origins (H10 Atmakaraka routing) · `Strongest/Weakest` aggregates · D9 child/co-born counts
(H3/H5/H11) · `Gender`/`Age`/`MaritalStatus` from BirthData (consideration #7; H5 sex-of-child,
H7 chart-sex rule flips) · `MoonPhase`/`Eclipsed`/`BhavaSandhi` · **conditional benefic
classification** (review fix F16: `NATURAL_BENEFICS` treats Moon/Mercury as unconditional
benefics, but Raman's waning-Moon and Mercury-by-association rules make them conditional —
this static set drives `HemmedBy`/`ClassInHouseFrom`/`CountInHouse`, the backbone of the
hemming and many-malefics rules, and a waning Moon counted benefic can be the hidden cause of
fires/doesn't-fire surprises in 1e; either add the conditional predicate here or explicitly
lock the static classification as v1 doctrine with a cited docstring note) ·
`ShashtiamsaClass`/`VaiseshikamsaGrade` (only if a golden needs them).
Each predicate: unit tests pinned to a worked example + at least one golden that moves.

| Possibility | Action |
|---|---|
| A predicate needs chart state not yet computed (e.g. D3 drekkana chart) | Extend `chart/varga.py` with the divisional first (cited formula), then the predicate; never approximate a varga. |
| BirthData lacks sex/marital status (it does today) | Add optional fields defaulting None; rules gated on them go `insufficient` when absent (honest absence), goldens may carry them in `birth`. |

---

## STAGE 6 — Phase E: longevity (the corrected sub-engine)

**Readiness confirmed:** `maraka_points` (tiers+units+22nd-drekkana+64th-navamsa) and
`balarishta` (gates+antidotes, Shadbala-aware) are DONE. Base-term tables + worked computations
located: overview §8.3-8.4 + HTJAH-II Charts 33 (Pindayu, ~:4100-4260), 34 (Amsayu,
:4332-4441), 35 (maraka units, :4661-4855).

Build `doctrine/ayus_tables.py` + `judges/longevity.py`:
1. **Span pipeline:** Balarishta gate → span class two ways (maraka banks primary;
   mathematical Pindayu/Amsayu/Nisargayu by strongest-of Sun/Moon/Lagna) → reconcile (lead
   maraka, attach math, `agreement` flag — never average).
2. **Math:** base terms (full/debilitated halves; proportional by exaltation distance per
   corpus); **Vakra-as-exalted scaling BEFORE reductions** (pin the GBB/HTJAH-II line for the
   factor — do not guess); haranas in the corrected order with the corrected exemptions;
   Krurodaya absolute, Pindayu-only; Amsayu bharanas (×3 exalt/retro, ×2 vargottama/own,
   stronger-factor-once).
3. **Maraka timing:** tie-break by Chart-35 unit-counting (`maraka_tie_breaker` in
   `primitives/maraka.py`), node delegation (Sanivad Rahu / Kujavad Ketu).
4. **Wire LIVE:** `chart.longevity` via `EvalContext.get_or_compute`; the LONGEVITY_GUARD
   clamp lifts for charts where longevity IS computed; span-conditional rules read the band;
   H8 DRAFT goldens (3 longevity + 4 deaths) get their assertions activated.
5. **Harness extension (review fix F8 — new code, scheduled HERE):** `test_goldens.py` has NO
   assertion path for `expected_longevity` today (schema-only). Add a **longevity assertion
   track**: exact y/m/d for the Pindayu/Amsayu pins; killer-planet-only partial assertions for
   the death charts pre-Stage-7; death-window assertions post-Stage-7; its own DRAFT→CONFIRMED
   gating for the 3 DRAFT H8 records. Update `docs/raman_saab/golden_schema.md` in the same
   commit (schema doc and guard move together — same rule applies to Stage 7's
   `stated_dasha_balance`).

**Verification — non-negotiable pins:** Chart 33 → **86y 2m 20d** (Pindayu); Chart 34 →
**68y 10m 5d** (Amsayu); Chart 35 → **death 1966-02-07** path (Poornayu + Rahu-dasa Sun-bhukti
once Stage 7 provides dasha; until then assert span class + killer identification).

| Possibility | Action |
|---|---|
| Chart 33 doesn't hit to-the-day | Diff the per-planet term table against Raman's printed intermediate rows (:4150-4260 prints each planet's term + each harana) — the corpus shows EVERY intermediate; binary-search the divergent planet/harana; fix the formula, never fudge the constant. |
| Printed intermediates themselves inconsistent (it happens) | G3: follow the stated rule, xfail the cell with delta, keep the FINAL total pinned if Raman's total follows his own arithmetic (it did in Shadbala). |
| Pindayu hits but Amsayu (Chart 34) doesn't | Bharana stacking order is the usual culprit (×3 vs ×2, once, stronger factor) — re-read :4380-4435 sequence; also Krurodaya must be absent for Amsayu. |
| Balarishta fires on a confirmed adult chart | Antidote set incomplete → re-check HPA-14 list (locked: real antidotes only, no upachaya invention); if genuinely uncancelled per text, the chart is child-track — surface, don't suppress. |
| Spans disagree (maraka band vs math) on a golden | By design: lead with maraka, `agreement=False`; the golden asserts Raman's stated class. |
| The 4 assassination charts need dasha to assert death timing | Their `expected_longevity.death_date` asserts only the DATE-window once Stage 7 lands; in Stage 6 assert killer-planet identification only (partial activation, documented). |

---

## STAGE 7 — Phase F: timing (Vimshottari from scratch — confirmed unbuilt)

Build `app/raman_saab/timing/vimshottari.py` (no app/core import — re-derive):
nakshatra→lord, balance from Moon longitude with **`DAYS_PER_VEDIC_YEAR=365.2425` + JD
arithmetic** (CLAUDE.md locks), MD/AD (bhukti) ladders; `judges/timing.py`: two-level
activation (both lords related → par-excellence / one → limited / AD-only → feeble) over the 7
governing factors; Tara + Gochara modifiers; per-matter `TimingWindow[]`. Golden schema gains
optional **`stated_dasha_balance`**: when Raman printed the balance, force-initialise (drift
guard); fresh-cast charts with trusted TOB compute it.

| Possibility | Action |
|---|---|
| Computed balance ≠ Raman's printed (Moon-longitude drift) | Use `stated_dasha_balance` for that golden (the guard's purpose); log the delta in the audit list; do NOT tune the ayanamsa to force it. |
| Death-date falls in the right MD but wrong AD | Check AD ladder arithmetic (proportional sub-periods) before doctrine; then the maraka-AD selection rule (Chart 35's Sun-bhukti reasoning :4844-4855). |
| Gochara (transit) confirmation needs ephemeris-at-date | `cast positions at the event date via the existing adapter (allowed — astronomy, not doctrine); keep it a CONFIRMING modifier, never the driver. |

---

## STAGE 8 — Phase G: surfaces + cutover

1. `PHASE_G_CUTOVER` flag: proforma/render consume `HouseProforma` natively (per-signification
   blocks + metadata + chart_overview + longevity + timeline); legacy `HouseVerdict` shim
   retired; Tier-3 snapshots regenerate under review (the safety net for the cutover).
2. `app/api/raman_routes.py` `POST /raman/reading` (FastAPI, rate-limited per repo conventions)
   + contract test; portal tab (safe-DOM, caching per person+ayanamsa).
3. Lunar-kind yogas surface `:noted` (the documented Phase-G promise); H2 Special-Dhana
   parallel verdict + all metadata rendered.

| Possibility | Action |
|---|---|
| Snapshot diff explosion at cutover | Expected once: review the diff for verdict-changes (must be NONE — rendering only), then `UPDATE_RAMAN_SNAPSHOTS=1` regenerate in the cutover commit. Any verdict change = bug, fix first. |
| Legacy CLI consumers break | CLI keeps `--format reading|markdown` outputs stable in content commitments (tests pin); JSON format gains fields additively only. |

---

## STAGE 9 — Completion criteria (the definition of done for v1) + intermediate milestones

**Intermediate gates (review fix F13 — quantified bars between Stage 1 and done):**
- After Stage 1: **≥9/12** (≥75% on the H1 set).
- After Stage 4's first four houses (H8/H2/H7/H10) + Stage 6: **≥75% over ≥60 confirmed
  verdicts** spanning ≥4 houses. **PLATEAU CHECKPOINT:** if accuracy is <75% here, PAUSE
  breadth encoding and review the §6.3 decision heuristics WITH THE USER (the misses' confusion
  matrix decides: rule-gaps → keep encoding; systematic ordinal-shape misses → judge revision).
- After all Stage-4 houses: **≥85% over ≥120 verdicts**, all 12 houses represented.

**Done (v1):**
- Ratchet: **≥90% Track-B accuracy over ≥150 user-CONFIRMED verdicts**, with a **per-house
  minimum of ≥8 confirmed verdicts per house** (no H1-stuffing), an **abstain ceiling**
  (engine `insufficient-evidence` on ≤10% of decisive goldens — abstention can neither inflate
  accuracy nor hide gaps), and the holdout reported separately, **within 10 points of fit
  accuracy, gated on holdout size ≥20 confirmed verdicts** (until then: report-only).
- The 3 longevity goldens exact to the day; the 4 assassination charts' death windows hit
  (MD+AD level).
- Rule corpus ≥ ~900 evaluable cited rules; zero citation-guard failures **+ the per-batch 10%
  citation content-audits on file** (the guard is range-only — the audits are the real
  fidelity check); all 12 houses fine-tagged; all special grids surfacing.
- Suite green incl. import guard, shim-equivalence retired at cutover; CLI/API/portal serving
  the per-signification proforma.
- Every remaining mismatch documented with its doctrinal reason (no silent gaps).

## Verification commands (run at every stage gate)
```powershell
py -3.12 -m pytest tests/raman_saab/ -q                       # full suite
py -3.12 -m pytest tests/raman_saab/test_goldens.py -q -s     # tiers + reporter line
py -3.12 -m pytest tests/raman_saab/test_goldens.py -k track_a --tb=short  # astronomy isolation
py -3.12 -m tools.raman_saab.tune_thresholds --max-iterations=50 --holdout-lock
py -3.12 -m app.raman_saab --name X --date 1990-07-15 --time 12:00 --tz 5.5 --lat 12.97 --lon 77.59 --format reading
```

## Critical files by stage
| Stage | New | Modified |
|---|---|---|
| 1 | — | `doctrine/conditions.py` (+4 predicates), `rule_sets/house_01_lagna.py` (→ split), `doctrine/significations.py` (H1 mind row + rule_tags), tests |
| 2 | per-batch goldens | `tests/fixtures/raman_goldens.jsonl`, `golden_accuracy_baseline.json`, validation worksheets (docs/) |
| 3 | — | `tools/raman_saab/tune_thresholds.py` (holdout id-list + crc32 slice + holdout SCORING + cast cache — code, not constants), `primitives/shadbala/total.py` (only via applied diffs) |
| 4 | `rule_sets/house_NN_*/` splits | each house module, `significations.py` rule_tags, `proforma` meta-modifiers (H6/H12) |
| 5 | — | `doctrine/conditions.py`, `chart/varga.py` (D3 etc.), `chart/model.py` (BirthData optional fields) |
| 6 | `doctrine/ayus_tables.py`, `judges/longevity.py` | `primitives/maraka.py` (tie-breaker), `judges/house_template.py` (guard lift), `tests/raman_saab/test_goldens.py` (NEW longevity assertion track), `docs/raman_saab/golden_schema.md`, goldens (H8 activation) |
| 7 | `timing/vimshottari.py`, `judges/timing.py` | golden schema (+`stated_dasha_balance`), `test_goldens.py` |
| 8 | `app/api/raman_routes.py`, portal tab | `proforma.py`, `render.py`, `cli.py` (cutover), snapshots |
