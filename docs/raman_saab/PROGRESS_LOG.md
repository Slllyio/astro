# Raman Saab — Progress Log (durable, append-only)

**Purpose:** chronological build ledger that survives session limits / context compaction. Append
a dated entry at **every commit or milestone**. Complements the other durable artifacts:
- **Execution plan:** `C:\Users\S.C.C\.claude\plans\compressed-mixing-trinket.md` (v3, the full
  staged plan with per-possibility contingencies).
- **Resume anchor:** `docs/raman_saab/BUILD_STATUS.md` (structured current-state + resume pointers).
- **Spec:** `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md`.
- **Golden validation:** `docs/raman_saab/golden_validation_worksheet.md` (user DRAFT→CONFIRMED).
- **The ratchet:** `tests/fixtures/golden_accuracy_baseline.json` (accuracy floor, human-bumped).

**Convention:** never lose a decision. Review findings (which otherwise live only in ephemeral
`tasks/*.output` temp files) get archived here. Commits are on branch `round8-unification`,
surgical staging, no Co-Authored-By.

---

## ▶▶ RESUME HERE (2026-06-13, post H3 affliction rules) ◀◀

**HEAD `3a12ea1`** · suite **1744 passed, 8 skipped, 3 xfailed** · **ratchet 11/24** (H1 7/12 +
H3 4/12) · pushed to GitHub `origin/round8-unification`.

**The execution plan is now IN the repo:** `docs/raman_saab/EXECUTION_PLAN.md` (v3, all stages +
per-possibility contingencies G1-G16). The validation worksheets:
`docs/raman_saab/golden_validation_worksheet.md` (H1, done) +
`..._worksheet_h3.md` (H3, done). Goldens: `tests/fixtures/raman_goldens.jsonl` (24 CONFIRMED:
H1 charts 9-35, H3 charts 52-63). Ratchet test + scoreboard: `tests/raman_saab/test_goldens.py`
(`track_b_scoreboard()`). Tuner: `tools/raman_saab/tune_thresholds.py`.

**EXACT next steps, in order:**
1. **REVIEW + TUNE the pillar-preponderance mechanism** (commit `d46f4e7`, currently no-op,
   review+tune were cut off by a session limit). It replaced the count-based contradiction-weigh
   in `house_template._decide` clause-2 with a PILLAR weigh (Raman three-factors: count weak/strong
   of lord/karaka/bhava_bala; knobs `CONTRA_PILLAR_AFFLICT`/`CONTRA_PILLAR_FAVOUR` in
   `shadbala/total.py`, default 99 = no-op). (a) Adversarial-review it (no-op default proof +
   doctrine fidelity: weak>=2 → afflicted must match Raman, and the count-version's over-favour
   artifact must be GONE). (b) Run `py -3.12 -m tools.raman_saab.tune_thresholds
   --max-iterations=50 --holdout-lock`; inspect the candidate's TUNED confusion matrix — apply
   `CONTRA_PILLAR_*` to `total.py` ONLY if it gains fit AND holdout WITHOUT a class-swap artifact
   (an afflicted-golden flipping to favourable = overfit, reject). On apply: re-measure, regen
   Tier-3 snapshots under review, BUMP baseline in the earning commit, push.
2. **Judge clause-8 policy refinement** — chart_56 fires 3 malefic ear_throat rules correctly but
   `_decide` clause-8 (strong pillars + only-malefic, no benefic contradiction → mixed) blocks the
   afflicted verdict. When ONLY malefic fires and no benefic contradicts, the engine should still
   read afflicted. Affects chart_56 directly; may unblock other "strong but afflicted" patterns.
3. **Continue breadth** house-by-house per EXECUTION_PLAN Stage 4 (richest next: H7 marriage or
   H10 career → best tuner signal) + Stage-6 longevity interleave after H8/H2.
4. Cleanup later: Stage 1c (fine re-tag, aggregate bridge — doesn't move ratchet), Stage 1d
   (chart_17 bhava-frame), chart_33 Capricorn-vs-Aquarius lagna re-validation.

**Standing protocol (terminal):** TDD; per batch: implement → adversarial review (doctrine
content-audits ≥10% of new citations) → fix CRITICAL/HIGH → full suite green → reviewed Tier-3
snapshot regen → ratchet measured (G5/G6/G16) → surgical commit on `round8-unification` (simple
`-m`, no `git add -A`, no Co-Authored-By) → **`git push origin round8-unification`** (user wants
continuous GitHub backup) → update this log + BUILD_STATUS. Run `py -3.12 -m pytest
tests/raman_saab/ -q` (currently 1734 passed). Locked decisions: see EXECUTION_PLAN.md + below.

---

## Where we are (history — superseded by RESUME HERE above)

- Phases A+B+deps+wiring + Stage 1 (H1) + preponderance mechanism + tuner-fix + House 3 +
  pillar-preponderance refinement — all COMMITTED + pushed.
- **AT THE PLATEAU CHECKPOINT (plan F13).** Stage 1 added 106 H1 rules + 6 predicates; the rules
  WORK (chart_10 now correctly `afflicted` on real malefic evidence) but the **§6.3 judge
  synthesis caps accuracy** — diagnosed as a systematic **mixed-bias** (clause-2 contradiction →
  mixed without weighing preponderance) + **navamsa/lead-frame over-aggression**. Next decision:
  refine the judge policy (WITH the user) vs continue breadth. NOT a rule-coverage problem.
- Open H1 mismatches (5): 09(mixed/insuff), 15(mixed/fav — regressed by mind-rule pollution),
  17(afflicted/fav — needs Stage-1d bhava-frame + lead-frame), 20+31(mixed/afflicted — the
  preponderance cap).

---

## Commit ledger

### Phase 0–2 (pre-accuracy-first; the working vertical slice)
| sha | what | state |
|---|---|---|
| (earlier) | Phase 0/1: chart adapter, all primitives, full 6-fold **Shadbala** reconciled to GBB to the decimal; `app/core` import-guarded out | — |
| `6d622ee`,`6673978` | lord-in-12 layer, all 12 houses (147 cited rules) | — |
| `485cd6a` | rule-firing bridge (Shadbala picks fortified/afflicted branch) | engine produces cited readings |
| `e0b3938`,`036906c`,`e26cd35` | planets-in-house layer, all 12 houses (108 rules) → **255 cited rules** | — |
| `f11e8ae` | Phase-3 house-level judge (ordinal verdict from rules + pillars) | — |
| `7e3519e`,`b71abf9` | proforma + render + CLI `--format reading` | **full vertical slice**: birth data → cited worksheet (706 tests) |

### Accuracy-first rebuild (the current architecture)
| sha | what | ratchet / tests |
|---|---|---|
| `924d7b6` | **A1** `significations.py` — 42 routings, mandatory frames (H4/H7/H9/H10); doctrine PASS | — |
| `60c7664` | **A2/A3** lazy `EvalContext` cache + `functional_nature()` accessor | 731 |
| `f81d051` | **A4-A6** per-signification judge: 3-frame immutable ledgers, §6.3 `_decide`, veto/salvage/identity/parivartana | 753 |
| `ff96590` | **A judge fixes** (adversarial review caught: citation misattribution, inert longevity guard, lord/strength frame mismatch — see Findings) | 764 |
| `780ac15` | **B framework** golden harness (Track A/B/Tier-3 + DRAFT-gate + condition-solver + tuner skeleton) | 770 |
| `2506ad2` | **B** first 19 DRAFT goldens (DOB/TOB/POB charts + 3 longevity) | 827 |
| `0eb5af8` | **B review fixes** (chart_33 IST tz; Aquarius Lagna per HTJAH-II:4253; Lincoln Western lon; Track-A lagna assertion; schema guard #11; tuner Final removed) | 855 |
| `c053eaf` | **user-CONFIRMED 12 H1 verdicts** + **Track-B accuracy ratchet armed** | **baseline 6/12** |
| `3dbd4dc` | yoga catalogue — 16 cited (3HC corpus found on disk) + **kemadruma bhanga corrected to 3HC:2182-2185** | 826 (doctrine) |
| `db84a35` | sphuta engines — Beeja/Kshetra (mirrored odd/odd vs even/even), Special-Dhana-Lagna, Sahams (arc-minute pins) | 1063 |
| `4d18430` | special-grid lookups — 93 cited rows (decanate/source-of-gains/Bhavartha/confinement/disease) | 1150 |
| `a90414d` | wire deps into judge — H5 fertility gate, yoga modulation (never-overturn-decisive), lookup metadata, chart_overview | 1212 · **ratchet 6/12→7/12** (Sakata corrects chart_33) |

---

## Locked corrections (caught by review against the corpus — do NOT regress)

1. **Harana order (longevity)** — Chakrapatha → Satrukshetra (Mars+retro exempt) → Astangata
   (Venus/Saturn **fully** exempt, not ½) → Krurodaya (**absolute**, Pindayu-only). The earlier
   draft (Krurodaya-first, ½ exemptions, "no double jeopardy") **contradicted `HTJAH-II:4006-4101`**
   and was corrected. Corpus is authority.
2. **Vipareeta** = Raman's narrow form (dusthana lords conjoined in a dusthana, `HTJAH-I:6302`);
   the Phaladeepika isolation clauses were stripped (NOVEL-tagged if ever re-added).
3. **§6.3 heuristics provenance** — the 5-step rule, Rupa thresholds, 1-Rupa canceller gate are
   **golden-tuned engine heuristics, NOT cited to Raman**. The salvage/rescue *principle* is real:
   bhava-rescue = `HTJAH-I:503-505` (the HOUSE's good aspects, not karaka strength — the original
   miscitation); strong-karaka demotion = three-pillar doctrine `HTJAH-II:221`/`HTJAH-I:985`.
4. **Kemadruma bhanga** must include **kendra-from-Moon** + **Moon-conjunction** cancellations
   (`3HC:2182-2185`) — the Phase-1b primitive had only kendra-from-Lagna; the benefic-drishti
   branch is labeled EXTENDED (not from 3HC).
5. **Beeja/Kshetra** strength is **mirrored**: Beeja odd-sign/odd-navamsa, **Kshetra even/even**
   (`HTJAH-I:5521/5523`).
6. **chart_33's affliction** is driven by **Y.SAKATA** (Moon 12th from Jupiter, `3HC:2984`), NOT
   Kemadruma (which doesn't form there) — pinned by `test_chart33_h1_drop_is_sakata_not_kemadruma`
   (right-for-the-right-reason guard).
7. **Maraka tie-break** = Chart-35 unit-counting (`HTJAH-II:4733-4791`), not a fixed ladder.
8. **Span bands** 8-32 / 33-75 / 75-120; Raman rejects 32-70/100.

---

## Adversarial review findings archive (substantive only; temp outputs are ephemeral)

- **Phase-A judge (`ff96590`):** karaka-salvage cited the wrong verse (`:503-505` is the house
  rescue, not karaka); longevity guard was inert (flag set, never read → maraka still drove H8
  afflicted); `as_house_verdict` reported Lagna lord's name with the lead (Moon) frame's strength.
  All fixed + pinned.
- **Phase-A deps (`3dbd4dc`):** kemadruma bhanga incomplete vs its cited 3HC line; `Y.RAJA.910X`
  dropped a printed disjunct. Fixed.
- **Wiring (`a90414d`):** arishta drop could act on a contradiction-mixed (hiding benefic
  testimony) — guarded; chart_33 right-for-wrong-stated-reason (Sakata not Kemadruma) — pinned;
  Beeja metadata over-claimed "strong" → renamed `numeric_strong`; LONGEVITY_GUARD arishta
  suppression is dead-code-but-defensive (documented).
- **Plan v3 deep review (17 findings):** F1 tuner-holdout excludes all book charts → empty fit
  set (real defect; fix = id-list + crc32 slice + holdout SCORING code); F2 fine-tag ordering
  would inert Groups 4/5 before re-tag (fix = encode coarse `self`, re-tag AFTER measure); F3
  chart_33 crutch-removal most-likely-failure is contradiction-mixed not non-firing; F4 missing
  `LordsConjunct`/`LORD_OF` predicate shapes; F5 no Tier-3 snapshot-churn protocol; F7 H8
  LONGEVITY_GUARD mutes Stage-4-H8 measurement (interleave Stage 6); F8 no longevity assertion
  track in harness yet; F9 golden-key invariant needed; F13 intermediate accuracy gates +
  plateau checkpoint + abstain ceiling. All folded into plan v3.

---

## Decisions owned by the USER (domain authority)

- Validated the 12 H1 verdicts (some stronger than the reviewer: chart_10 & chart_31 →
  **afflicted** not mixed; "weak constitution is purely negative H1 testimony", "career is H10").
- Validation method: agents draft → user confirms (DRAFT→CONFIRMED). Pending: batches A2..G.
- Fresh-cast from DOB/TOB/POB where given (computed degrees must match Raman's print — this caught
  the Capricorn-vs-Aquarius methodology error on chart_10/33).

---

## Append new entries below this line

### 2026-06-13 — pillar-preponderance refinement (committed `d46f4e7`, review+tune PENDING)
- House 3 goldens user-CONFIRMED (all 12 drafts kept; chart_58 time→5:30pm/Aquarius per user's
  structural-reality call). Baseline re-based 7/12 → **9/24** (`727d0d2`).
- Tuner run #1 (count-based, 2 houses): suggested `CONTRA_FAVOUR_MARGIN 99→1`, +0.158 fit but the
  confusion matrix showed it over-favours (6 afflicted→favourable) = **overfit artifact REJECTED**.
- Diagnosis: count-based net is the wrong signal; Raman weighs the **three pillars** (chart_20
  "all three factors afflicted → afflicted" is literal). Pillar-aware weigh would fix 6 of 7
  contradiction misses (20/31/59/61 weak-pillars→afflicted; 53/54 strong-pillars→favourable).
- **Mechanism refined to PILLAR-based** (`d46f4e7`): `_decide` clause-2 counts weak/strong of
  {lord, karaka, bhava_bala}; knobs `CONTRA_PILLAR_AFFLICT/FAVOUR` (default 99 no-op); tuner sweep
  {2,3,99}; tests rewritten. Suite 1734 passed, ratchet 9/24 unchanged (no-op verified). **The
  adversarial review + the real tuner run were CUT OFF by a session limit** — they are step 1 of
  RESUME HERE. (Committed no-op because it's verdict-unchanged + green + leaves a clean tree for
  the terminal switch; the tune APPLICATION is the gated next step, not done.)
- Plan copied into repo: `docs/raman_saab/EXECUTION_PLAN.md`.

### 2026-06-12 — Plateau resolution path + House 3 developed
- **User decision (plateau):** TUNER-DRIVEN cutoffs (data-calibrated preponderance, not hand-set).
- **Preponderance mechanism + tuner-fix COMMITTED (`e07418b`):** `_decide` clause-2 gains a
  tunable net malefic-benefic margin (`CONTRA_AFFLICT_MARGIN`/`CONTRA_FAVOUR_MARGIN` in total.py,
  default 99 = no-op, verified byte-identical at e59fc2e). Tuner holdout fixed (F1: id-list
  {chart_73/74/75/78} + crc32%5 slice + separate fit/holdout scoring + cast cache); CONTRA knobs
  in the sweep. Advisory run (single-house, NOT applied per F11): the H1 margins trade off
  (lowering AFFLICT fixes 09 but breaks 35) — confirms multi-house goldens are needed.
- **House 3 COMMITTED (`7d6d1af`):** 30 cited combinations (26 evaluable + 4 descriptive-deferred
  for unbuilt D9-count machinery), house_03_sahaja subpackage split, **new `ear_throat`
  signification** (HTJAH-I:3325 — deafness charts 55/56/57 were mis-bucketed; #28/#29 re-tagged,
  goldens re-keyed), 12 DRAFT goldens (charts 52-63, 11 fresh-cast). Reviews: only MEDIUM/LOW
  (ear_throat gap — FIXED; contestable 52/53/54 sibling-loss ordinals → user worksheet). H1
  ratchet 7/12 unchanged (H3 isolated). Suite 1732 passed.
- **Repeating loop established:** develop house (combinations+goldens) → USER validates goldens →
  re-run tuner as combination-rich houses accumulate → apply CONTRA when >=2 houses give clean
  fit+holdout → repeat. Longevity (Stage 6) interleaves after H8/H2.

### 2026-06-12 — GitHub backup enabled
- User reversed the earlier "local only": pushed `round8-unification` to `origin`
  (`github.com/Slllyio/astro`), upstream set. **Standing: push after every commit** for
  continuous off-machine backup. No secrets pushed (`.env` gitignored; only `.env.example`).

### 2026-06-12 — Stage 1 (H1 deep encoding) — ENCODE DONE, DEFECTS FOUND, FIX IN FLIGHT
Workflow `wf_4cbd3be9-afb` (foundations + 6 group encoders + adversarial verify; fix stage died
on session limit). **NOT YET COMMITTED** — the batch regressed the ratchet, so per G5 it cannot
ship until fixed.
- **Foundations (clean, in working tree):** 6 new predicates in `conditions.py` —
  `InVargaHouseFrom` (D9, both endpoints in varga), `VargaDignity`, `PlanetPairIn2_12` +
  `AllPlanetsInDwirdwadasha`, `SignIsSushka`/`SignIsWatery`, `LordsConjunct`, and the
  **`LORD_OF:n` origin** in shared `_origin_house`. `house_01_lagna.py` split into the
  `house_01_lagna/` subpackage (21 original rules moved verbatim, verified field-by-field). 36
  new predicate tests. (A 3rd registration point surfaced: `test_significations.py` globs flat
  `house_*.py` — fixed to recurse into subpackages.)
- **Encode:** ~97 new H1 rules across 6 group modules (combinations_core 14, combinations_misc
  22, navamsa_qualifiers 30, constitution 7, moon_mind 15, sign_afflictions 9). Many
  descriptive-deferred for absent predicates (Tara #35/36, Shadbala aggregates).
- **Reviews (both ISSUES_FOUND) — the batch REGRESSED ratchet 7/12 → 5/12 (charts 20/31/33
  flipped afflicted→mixed).** Root causes: (CRITICAL) duplicate ids H1.C.32/33/34 in core AND
  misc (fire twice → benefic flood — the G12 overlapping-span hazard); (HIGH) #13-19 / #38-39 /
  #67 double-encoded across modules; rule #15 self-conjunction tautology; wrong whole-sign
  drishti proxy in H1.M.G2; **inverted fortified-text** on affliction-condition rules (positive
  text surfaced as benefic); (verdict-MED) `~AllPlanetsInDwirdwadasha` fires on ~every chart;
  constitution physique polarity (stout=benefic). Fix workflow `wf_034b34b3-2c5` in flight.
- **OPEN QUESTION (user/golden territory — DEFERRED):** doctrine review flags **HTJAH-I.chart_33
  may be CAPRICORN, not Aquarius** — the book files it under "Makara/Capricorn" and Raman's
  stated grounds (6-planet stellium "in the 10th") only reproduce from Capricorn (Libra = 10th
  from Capricorn). The earlier `0eb5af8` "Aquarius 9°42' per HTJAH-II:4253" fix was for the
  **HTJAH-II chart_33** (a DIFFERENT chart — the longevity one); the two were conflated. The H1
  personality chart_33's lagna needs re-validation against the printed diagram. The verdict
  (afflicted) is likely correct either way; only WHICH rules fire depends on it. NOT changed
  pending user/Phase-B re-check.
- **Lesson for Stage 4+:** parallel encoders must get DISJOINT corpus line-ranges (not just
  disjoint files) + a unique-id guard test must exist BEFORE encoding (now being added). The
  overlapping-span instruction was an orchestrator error.

### 2026-06-12 — Stage 1 COMMITTED (`e59fc2e`) + PLATEAU CHECKPOINT reached
Fix workflow `wf_034b34b3-2c5` applied all 7 review fixes (dedup + unique-id guard, inverted-text
→ fortified=None, rule-#15 tautology, true-drishti in H1.M.G2, Dwirdwadasha "almost-all"
threshold, constitution physique → neutral, W33 → descriptive). Ratchet recovered 5/12 → 7/12.
Committed: conditions.py (6 predicates + LORD_OF origin), the `house_01_lagna/` subpackage (10
modules, 106 rules), 14 reviewed Tier-3 snapshot regenerations, 4 new test files. Suite 1623
passed. Baseline stays 7/12 (count flat — composition +chart_10 / −chart_15).
- **Verdict audit of the snapshot regen (all changes intended):** chart_10 fav→**afflicted**
  (WIN, grounded); 09/20/31 fav→mixed (closer, capped); chart_15 fav→mixed (regression from
  mind-rule pollution); 12/17/18/24/29/33/35 verdict-stable.
- **THE PLATEAU DIAGNOSIS (measure agent, cross-referenced to memory obs 1611/1657):** remaining
  misses are JUDGE-POLICY, not rules:
  1. **Clause-2 mixed-bias** — "any benefic + any malefic → mixed" ignores preponderance; chart_09
     (4 malefic vs 1 benefic) and chart_20/31 ("all three factors afflicted" per Raman) read mixed
     where Raman reads afflicted. Caps 09/20/31.
  2. **Navamsa-weakens + lone-malefic over-aggression + Moon-lead-frame** — chart_17 reads
     afflicted (opposite of golden favourable) despite 5 benefic rules; also needs Stage-1d
     bhava-frame (Ketu → 12th bhava, not afflicting H1).
  3. **chart_33** afflicted RIGHT-FOR-THIN-REASONS (zero malefic house rules; rides on Y.SAKATA
     overlay — the known crutch).
- Aligns with the USER's own calls (chart_10/31 "afflicted not mixed; career is H10"). The §6.3
  numbers are golden-tuned heuristics → the refinement is a doctrine-shaping decision for the user.

### 2026-06-13 — H3 affliction rules completed (`3a12ea1`), ratchet 9/24 → 11/24
- **Step 2 of RESUME-HERE executed (plan step 2).** 5 new rules + 2 condition fixes + 1 golden fix:
  - **C.31** (ear_throat malefic): 3rd lord in dusthana (6/8/12) → fires on charts 55 (Venus h12),
    56 (Mars h6). Citation HTJAH-I:3465.
  - **C.32** (ear_throat malefic): Saturn aspects 3rd house → fires on charts 55, 56. New local leaf
    `_SaturnAspects3rd`. Citation HTJAH-I:3467.
  - **C.33** (ear_throat malefic): 3rd lord debilitated → fires on chart 56 (Mars debil in Cancer).
    Citation HTJAH-I:3467.
  - **C.34** (siblings malefic): 3rd lord in dusthana → fires on charts 56, 62. Citation HTJAH-I:3436.
  - **C.35** (siblings malefic): natural malefic aspects 3rd → new leaf `_MaleficAspects3rd` (inverse
    of C.7). Fires on charts 58, 60. Citation HTJAH-I:3430.
  - **C.9 fix**: exempt exalted/own malefic 3rd lord via `Not(_ThirdLordHasDignity({"exalt","own"}))`.
    Chart 63's Saturn (malefic, exalted in Libra) no longer triggers C.9. Citation HTJAH-I:4087.
  - **C.30 fix**: new leaf `_LordsIdentical(h1, h2)` recognises same-planet lordship as "connection"
    (LordsConjunct returns False for identity by design). Chart 63 Sagittarius: Saturn lords both
    h2 (Capricorn) and h3 (Aquarius) → identity fires as benefic.
  - **chart_63**: added stated_positions `Mars sign:9 bhava:1`, `Saturn sign:7 bhava:11`.
- **Gains:** chart_55 favourable→**afflicted** (C.31 fires, no benefic ear_throat contradicts →
  clause-3 Track-B fallback → afflicted). chart_63 afflicted→**favourable** (C.9 exempted + C.30
  identity + C.1 lord-in-11th + C.8 exalted → only benefic fires → clause-3 → favourable).
- **NOT gained (expected):** chart_56 favourable→mixed (closer, 3 malefic rules fire correctly but
  judge clause-8 — strong pillars + only-malefic, no benefic contradiction — falls through to
  "mixed" instead of "afflicted"). This is a judge-policy gap, not a rule-coverage gap. Charts
  53/54/58-62 deferred per plan (pillar tuning, navamsa-override, papakartari).
- **H1 7/12 unchanged** (no regression). **H3 2/12 → 4/12.** Baseline bumped 9→11/24.
- `Not` condition already existed in `conditions.py` (line 188) — no addition needed.
- All 12 H3 Tier-3 snapshots regenerated. Suite 1744 passed.

### 2026-06-13 — Stage-4 H8 (Ayur/Randhra) combination layer encoded (breadth start)
**Directive:** complete ALL houses' combination layers first, then polish. Stage-4 order
H8 → H7 → H10 → H4 → H5 → H6 → H9 → H11 → H12 (H1/H2/H3 done). H8 first per plan
(longevity-adjacent, feeds Phase E).
- **Subpackage split:** flat `house_08_ayur.py` → `house_08_ayur/` (lord_in_12 [12] +
  planets_in_8th [9], moved verbatim, + new `combinations.py` [50]). Aggregator __init__
  mirrors H2/H3 (relative import). Registration unchanged (explicit import resolves to pkg).
- **50 combination rules** (60 evaluable / 11 descriptive across the subpackage):
  nature-of-death (C.1-3), specific killers (C.12,13,15-18), 23 killer-yogas (K.1-30 subset),
  place-of-death by 8th-sign modality (C.24-26), chronic disease (D.1). New local leaves:
  `_LagnaInSign`, `_EighthSignModality`, `_PlanetInWaterySign`, `_ConjunctAnyMalefic`,
  `_AspectedByClass`, `_PlanetWithHouseLord`, `_LordsRelated`, `_all_in_house`
  (conditions.py untouched — local-leaf convention).
- **LONGEVITY_GUARD handling:** death/manner/cause/place/disease → `signification="death"`
  (guarded, deferred to Phase-E). **Re-tagged `legacies`/`sudden_gains` significations off the
  "longevity" bridge** (`("longevity",)` → `("legacies",)`/`("sudden_gains",)`) so the
  NON-death, measurable matters are no longer guard-clamped — H8.C.28/30/31 (legacies) +
  C.29/32 (sudden_gains) can move them. HTJAH-II:2886 / 3068 cite these as distinct matters.
- **Honest deferral (G13):** 11 descriptive `TODO(predicate)` for 22nd-drekkana/D3, 64th-navamsa,
  Mandi-in-navamsa, planet-strength gates, affliction-grade — Stage-5 picks them up.
- **Adversarial review (both lenses): SHIP.** Doctrine reviewer content-verified 24/50 citations
  (48%, > 30% floor) — no wrong-but-in-range found after 3 pre-fixes (C.29 3490→3491, C.30
  3524→3525, C.25 3901→3902). Fixed K.20 (documented the deliberate de-dup of its Moon+Mercury-6th
  branch vs C.17, same `death` sig) and C.31 (noted Ketu branch sourced 3574). Code reviewer:
  SHIP (1 style nit fixed — relative import).
- **Ratchet 18/37 UNCHANGED** (H8 has no confirmed Track-B goldens — DRAFT longevity charts only;
  baseline untouched per single-writer rule). 5 H8 Tier-3 snapshots regenerated (reviewed):
  death/longevity verdicts unchanged (guard holds), legacies/sudden_gains mixed/afflicted→favourable
  (intended re-tag effect), +2 grounded evidence-additions (chart_35 C.28, chart_75 C.30).
  **Full suite 2025 passed, 21 skipped, 3 xfailed.**
