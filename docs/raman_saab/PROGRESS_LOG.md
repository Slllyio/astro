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

### 2026-06-13 — Stage-4 H7 (Kalatra/Yuvati) combination layer encoded
- **Subpackage split:** flat `house_07_kalatra.py` (24 rules) → `house_07_kalatra/` (from_karaka [3] +
  lord_in_12 [12] + planets_in_7th [9] + new `combinations.py` [43]). 67 rules total.
- **43 combination rules** across sections A-F: marriage-happiness (→marital_happiness),
  character/chastity + marriage-count (→spouse), impotency (→virility), loss/death/widowhood
  (→coverture), wealth-loss-via-women (→wealth_through_marriage). New local leaves: parity
  (odd/even sign + Lagna), `_SeventhSignIn`, `_LordIsPlanet`, `_HouseHemmedBy` (papakartari on a
  HOUSE), `_KujaDosha`, `_AspectedByClass`, `_ConjunctAnyMalefic`, `_PlanetInSigns`, `_LagnaInSigns`.
- **Single-chart Kuja-Dosha (H7.KD.1)** encoded WITH the corpus per-sign exemptions
  (HTJAH-II:2593-2601: 7th exempt in Cn/Cp, 2nd in Ge/Vi, 4th in Ar/Sc, 8th in Sg/Pi, 12th in
  Ta/Li; Leo/Aquarius wholly exempt; neutralised by Mars+Jupiter/Mars+Moon). Pinned by
  `tests/raman_saab/doctrine/test_house07_kuja_dosha.py` (5 tests). **Two-chart synastry (S1-S7)
  + dosha-units matching grid are LOCKED OUT-OF-SCOPE v1.**
- **Honest deferral (G13):** 6 descriptive `TODO(predicate)` — Navamsa-parity (rec.31/33/35),
  D60, Gulika/upagraha, planet strength/weak gates, sex-dependent splits, Dasa-timing (Phase-F).
- **Adversarial review:** doctrine reviewer FIX-FIRST → 5 doctrinal MEDIUMs fixed: (1) KD.1
  per-sign exemptions added (was over-firing on exempt placements); (2) H7.C.67 7th-leg excluded
  ({2,4,8,12}) — Mars-in-7th owned by C.60 (de-dup in coverture); (3) H7.C.41 polarity malefic→neutral
  (count-rule convention); (4) H7.C.52 coverture→spouse (remarriage is count, not partner-death);
  (5) rec.45 folded into H7.K.2 as two-branch rule, deleting H7.C.45 + correcting K.2 citation
  368→374 (368 was the Venus-exaltation line). Code reviewer SHIP (frozenset nit fixed). Citations:
  19/19 content-verified clean.
- **Ratchet 18/37 UNCHANGED** (no confirmed H7 Track-B goldens; no snapshot drift — existing
  goldens scope H1/H2/H3/H8). **Full suite 2111 passed, 21 skipped, 3 xfailed.**

### 2026-06-13 — Stage-4 H10 (Karma/Rajya) combination layer encoded
- **Subpackage split:** flat `house_10_karma.py` (21 rules) → `house_10_karma/` (lord_in_12 [12] +
  planets_in_10th [9] + new `combinations.py` [20]). 41 rules total. Placement rules split verbatim.
- **20 combination rules:** nature-of-profession anchors (Mercury/Sun-Rahu/Mars-Venus → fine
  `profession_learned`/`profession_trade` sigs to avoid double-counting `career` placements),
  structural Rajayogas (3+ exalted/own in kendras, benefics/malefics in all quadrants, benefics
  in 10/11/3), Rajabhanga (Mars+Saturn in 1/7/8/10, Saturn-in-10), vice (afflicted Moon, 2/7
  lords in 10), 4-planets-in-10 sanyasa. New leaves `_DignityInKendrasAtLeast`,
  `_AllKendrasHaveClass`, `_AspectedByClass`.
- **Honest deferral (G13):** 6 descriptive `TODO(predicate)` — Navamsa-dispositor-of-10th-lord
  routing + trade/sign lookups, Karakamsa/AK overlay (Stage-5), Varahamihira-32/vargottama
  Rajayogas, Neechabhanga variants, strength-gated sanyasa, dasa-phala rise/fall (Phase-F).
- **Adversarial doctrine review: FIX-FIRST → 2 HIGH fixed:** (1) H10.C.15 wrong citation 9969→10969
  (the Karakamsa statesman text is at corpus 10969, NOT 9969 — the methodology doc shared the same
  ~1000-line-off error; corrected doc section-B rows 15-25/42 + AK note to 10965-10992); (2) H10.C.54a
  double-counted H10.L.7 (`LordIn(10,7)` in `career`) → re-routed to `status_honour` (it's a
  conduct/vice verdict). 19/20 citations content-verified clean. Code lens self-reviewed (3 simple
  leaves, None-safe).
- **Ratchet 18/37 UNCHANGED** (no confirmed H10 Track-B goldens; no snapshot drift). **Full suite
  2156 passed, 21 skipped, 3 xfailed.**

### 2026-06-13 — FIX: orphaned combination significations (H8 death, H10 status/profession)
Self-caught during H4 prep (verified via `_bucket_fired`, house_template.py:482): a signification
only aggregates fired rules whose `rule.signification` ∈ its `rule_tags`. H8's `death` combos
(signification="death") and H10's `status_honour`/`profession_learned`/`profession_trade` combos
were ORPHANED — they fired but fed no verdict, because those sigs' rule_tags pointed only at the
aggregate bridge (`longevity`/`career`). Fix: added the fine key to each sig's rule_tags
(H1/H7 aggregate-bridge pattern) so each matter aggregates the shared placements AND its own
combos:
- H8 `death`: ("longevity",) → ("longevity","death") [still guard-clamped]
- H10 `status_honour`: ("career",) → ("career","status_honour")
- H10 `profession_trade`/`profession_learned`: ("career",) → ("career", "<key>")
Ratchet 18/37 unchanged. 7 H8 death-chart Tier-3 snapshots regenerated (pure evidence-additions —
death combos now bucketed; rollup/verdicts unchanged, guard holds). Suite 2156 passed.
(H7 unaffected — its fine sigs already had matching rule_tags.)

### 2026-06-13 — Stage-4 H4 (Sukha) combination layer encoded + fine-tagging
- **Subpackage split:** flat `house_04_sukha.py` (21 rules) → `house_04_sukha/` (lord_in_12 [12] +
  planets_in_4th [9] + new `combinations.py` [28]). 49 rules total. Placements split verbatim.
- **28 combination rules** across sections A (general/property/happiness), B (mother death-timing),
  C (education), D (vehicles), E (houses). New leaves `_AspectedByClass`, `_ConjunctAnyMalefic`,
  `_HouseHemmedBy`, `_PlanetInOrAspectsHouse` (uses drishti.aspects_house).
- **Fine-tagging (Stage-4 step-3):** extended each H4 sig's rule_tags to ("<key>","mother_home")
  for mother/happiness/education/vehicles/property so each matter aggregates the shared placements
  + its own combos (home_comforts left bare — no combos route there, per
  test_rule_tags_match_existing_buckets). Mother-death rules NOT longevity-guarded → measurable.
- **Honest deferral (G13):** 4 grouped descriptive `TODO(predicate)` — strength/weak/lord-friendship
  gates, Gopuramsa/shashtiamsa/thrimsamsa varga ranks, derived-Lagna (4th-as-mother's-Lagna),
  lords-associated-in-house.
- **Adversarial doctrine review: SHIP** (24/24 citations content-verified clean, 0 polarity
  reversals, routing sound). Fixed 1 MEDIUM: H4.C.18 (mother-death) was aspect-only → broadened to
  "joined OR aspected" (both arms of HTJAH-I:4224), closing the non-Saturn-malefic coverage hole;
  H4.C.30 (Saturn+Moon-in-4) demoted to descriptive (now owned by C.18's joined arm, avoids
  double-count); H4.C.21 (Rahu) likewise broadened. Code lens self-reviewed.
- **Ratchet 18/37 UNCHANGED** (no confirmed H4 goldens; no snapshot drift). **Full suite 2212
  passed, 21 skipped, 3 xfailed.**

### 2026-06-13 — Stage-4 H5 (Putra) combination layer encoded
- **Subpackage split:** flat `house_05_putra.py` (21) → `house_05_putra/` (lord_in_12 [12] +
  planets_in_5th [9] + combinations [28]). 49 rules total. Placements split verbatim.
- **28 combination rules** across A (birth), B (death/loss), C (extinction), D (sex of first
  child), E (count/timing), F (adoption), G (obedience), H (brain/intellect). Children/sex/count/
  adoption/obedience → `children` (passes the Beeja/Kshetra fertility gate); brain → `intellect`.
- **Adversarial doctrine review: FIX-FIRST → fixed:** (1) HIGH — `intellect` bridged to the live
  `children` bucket and double-counted Jupiter-in-5 (H5.P.Jupiter placement + H5.C.35 combo) →
  changed `intellect` rule_tags to ("intellect",) so it aggregates only its own combos (KEY LESSON:
  the aggregate-bridge only works against a DEDICATED placement tag like mother_home/longevity, not
  a live matter); (2) MEDIUM — H5.C.4 "aspected by Jupiter" was a conjunction → new `_PlanetAspectsLord`
  leaf; (3) MEDIUM — H5.C.8 (5th-lord-in-3/6/12) overlapped lord_in_12 placements under `children`
  → demoted to descriptive. Citations 26/26 content-verified clean. Routing + polarity PASS.
- **Honest deferral (G13):** Navamsa/Drekkana overlays, Beeja/Kshetra sphuta, strength gates,
  native-sex, Mandi — descriptive.
- **Ratchet 18/37 UNCHANGED** (no H5 goldens; no snapshot drift). **Full suite 2268 passed.**

### 2026-06-14 — Stage-4 H6/H9/H11/H12 combination layers (parallel workflow + doctrine-verify)
**COMPLETES all 12 houses' combination layers.** Ultracode multi-agent orchestration:
- **Encode workflow** (wf_d225b8b0): 4 builder agents drafted combinations.py per house from the
  methodology + corpus. Hit a session limit before returning structured output, but had already
  WRITTEN the draft files to disk (511/747/643/955 lines). Harvested the on-disk drafts.
- **Integration (orchestrator, serial):** fixed H11 invalid sig `acquisitions`→`gains`; split all
  4 placement layers verbatim (12 lord + 9 planet each); wrote __init__; deleted flats; fine-tagged
  14 significations to ("<fine>","<aggregate>") (H6 accidents/debts/disease_chronic/enemies;
  H9 father/dharma/higher_learning/long_journeys; H11 elder_siblings; H12 expenditure/
  foreign_residence/moksha/incarceration/left_eye). Structural gate (full suite) green.
- **Doctrine-verify workflow** (wf_b62ac90f): 4 bphs-doctrine-reviewer agents, EXHAUSTIVE
  (213/214 citations opened+read against corpus; 3 wrong-but-in-range caught & fixed). Verdicts all
  FIX-FIRST; corrected files applied:
  - **H6 (50 rules):** CRITICAL — H6.C.1 bare Or(LordIn(6,1/8/10)) double-counted L.1/L.8/L.10 in
    enemies_disease AND faked the "evil lord" gate → demoted to descriptive. Citations 6092→6093
    (Mandi heart/lung), 6126→6127 (Mars-afflicted accidents). C.13 over-fire flagged.
  - **H9 (72 rules):** 3 HIGH — A.13 faked an available predicate; B.23 & D.43 had leftover
    `if False` dead-code ternaries + wrong aspect direction → rewritten; B.31 misroute, D.37
    double-count fixed.
  - **H11 (75 rules):** C.15 routing; F-block (C.41/44/46–52/54) + C.53 double-count vs placements;
    dusthana-polarity verified.
  - **H12 (104 rules):** citation drift A.10 (16313→tail); A.2/C6/J9 under-encoding fixed; Mandi
    rules confirmed descriptive.
- Orchestrator post-check: re-fixed H11 `acquisitions` (reviewer re-introduced it as "more
  specific" — not a real H11 sig key → would orphan); full orphan-scan across all 4 houses = clean.
- **Ratchet 18/37 UNCHANGED** (no confirmed goldens for these houses; no snapshot drift).
  **Full suite 2702 passed, 21 skipped, 3 xfailed.** All 12 houses now carry combination layers.

### 2026-06-14 — Stage-2 pilot: H7 marriage goldens (12 DRAFT) + validation worksheet
First Stage-2 golden-extraction batch (makes the new combination layers measurable). 12 H7
worked charts from HTJAH-II Ch.XI drafted as `HTJAH-II.chart_01..12` (fresh-cast, full birth
data). **Birth-decode validated**: all 12 cast Lagnas match Raman's stated Lagna/7th-sign (0
mismatches, Track A green); chart 8 corrected to 7:35 PM (was AM → wrong Lagna). All
`verdict_review=DRAFT` → inert (CONFIRMED stays 38, ratchet 18/37 untouched). Engine matches the
DRAFT reading on 6/12; the other 6 (charts 03/04/05/06/08/09) are the H7 mismatch-target list once
confirmed. Worksheet: `docs/raman_saab/worksheets/H7_marriage_batch.md` for user validation
(confirm/correct sig + ordinal → flip to CONFIRMED → Track-B denominator 37→49). Suite 2738 passed.

### 2026-06-14 — Stage-2 batch 2: worked-chart extraction H4/H5/H7+/H9/H10/H11/H12 (80 DRAFT)
Parallel extraction workflow (wf_3d2ef71e, 8 agents) read each house's Example-Chart Insights and
drafted worked-chart verdicts + birth data. Orchestrator cast-verified EVERY chart (cast Lagna vs
stated Lagna/7th-sign) before appending:
- **80 DRAFT goldens appended** (ids `<vol>.h<N>_NN`). Verified-decode (cast Lagna == stated):
  H4 5, H5 12, H7 18, H10 6, H11 17 → track_eligibility ["A","B"]. Unverified (agent gave no stated
  Lagna): H9 29, H12 18(−1), H5 4 → ["B"] only, flagged in worksheet.
- **5 DECODE-MISMATCH charts EXCLUDED** (h5_03, h5_17, h7_08, h11_11, +1) — cast Lagna ≠ stated by a
  full sign → wrong birth-decode → invalid fresh-cast; flagged in worksheet for user to supply
  correct birth data. (Track-A hard-fails these, correctly — a wrong Lagna means wrong positions.)
- **H6: 0 extractable** — the methodology prints dates + derivable Lagnas but NO places/times for its
  worked charts; agent declined to invent coords (correct). Needs stated-positions or external coords.
- All DRAFT → inert: CONFIRMED stays 38, **ratchet 18/37 untouched**. records 57→137, TrackA→114.
  Suite 2936 passed. 8 validation worksheets in `docs/raman_saab/worksheets/`.
Awaiting user validation (confirm sig+ordinal per row → flip DRAFT→CONFIRMED → grows Track-B).

### 2026-06-14 — Stage-2 batch 2 verified + worksheets reconciled
Cast-verified the batch-2 decodes and regenerated accurate worksheets from the fixture:
- **H12**: re-derived each chart's Lagna (lordship/exaltation reasoning, workflow wf_5bbcc7d5) →
  cast-checked → **14 promoted** (decode sound, track ["A","B"]), **2 excluded** (cast Lagna ≠ stated
  → wrong birth data, dropped), **2 left unverified** (Lagna indeterminable from doc).
- **H9**: 0 goldens — its Example-Chart Insights print dates + lordship reasoning but NO birth
  times/places, so no chart is fresh-castable (same as H6). Candidates kept in the reference
  worksheet for when externally-verified coords can be supplied.
- Final Stage-2 golden inventory (all DRAFT, inert): H7 30 (12 pilot + 18), H5 16, H11 17, H12 16,
  H10 6, H4 5 = **90 worked-chart DRAFT goldens** across 6 houses; H6/H9 pending coords.
- records 135, CONFIRMED 38 (**ratchet 18/37 untouched**), TrackA 127 (decode-validated fresh-casts).
  Suite 2960 passed. Worksheets in docs/raman_saab/worksheets/ regenerated to match the fixture.
Awaiting user validation (confirm sig+ordinal → DRAFT→CONFIRMED → Track-B grows).

### 2026-06-14 — H7 marriage goldens CONFIRMED (user-validated) — ratchet 18/37 -> 24/49
User locked the H7 pilot (12 charts, marital_happiness). Flipped chart_01..12 to CONFIRMED:
- chart_05 override mixed->afflicted (isolated marital_happiness: "miserable" dominates "not broken").
- chart_06 kept marital_happiness/afflicted (NOT diluted to spouse/mixed — both-marriages-unhappy is a
  systemic happiness failure; left as a refinement target).
- chart_07 kept mixed; partner-loss logged as a Phase-E/Dasha event via _note (core valence unsplit).
- **+6 correct** (01/02/07/10/11/12 match engine) **+6 refinement targets** (03/04/05/06/08/09 mismatch).
Baseline re-based 18/37 -> **24/49** (G5-c: confirmations grow the corpus). CONFIRMED 38->50, TrackB 50.
H7 combination layer is now MEASURABLE; the 6 mismatches are the targeted Stage-3/4 refinement list.
Suite 2960 passed. (H9/H12 decode-verify done earlier: H12 14 verified/2 excluded/2 indeterminable;
H9 has no birth times/places in the doc -> not fresh-castable, needs corpus stated-positions/coords.)

### 2026-06-14 — Stage-2 completion: H6/H9 extracted from corpus + 4 held charts recovered
Per the approved plan (complete every house before calibration). Root cause of the earlier H6/H9
zero-yield: extractors read the abbreviated methodology docs; the raw CORPUS prints full
"Born on DD-MM-YYYY at H-MM a.m./p.m. (tz) (Lat/Long)" lines with explicit a.m./p.m. Re-extracted
from the corpus (workflow wyb1a1dsv stalled at 1/3 agents -> harvested H9 from transcript + ran H6
and held via direct file-writing agents — robust against the structured-output-return stall).
- **+29 DRAFT goldens**: H9 17 (h9_01..), H6 12 (h6_01..); decode cast-verified (cast Lagna ==
  text-derived Lagna); 2 full-sign mismatches excluded; H6 110/113 + H9 one indeterminable -> ["B"].
- **4 of 6 held charts RECOVERED** (decode now verified, still DRAFT pending verdict validation):
  h5_13 (Chart 103, Virgo), h5_15 (105, Gemini), h5_18 (108, Sagittarius), h12_14 (Chart 252 =
  Milton, Julian-date, Scorpio). Still held: h12_13 (251, prose Pisces vs computed Virgo) and
  h5_14 (104, computed-only Lagna, no text cross-check).
- All new/recovered records DRAFT/inert -> **ratchet 44/104 untouched**. records 135->165,
  CONFIRMED 105 unchanged, TrackA 127->158. Suite 3052 passed. Worksheets H6_ari_batch.md,
  H9_bhagya_batch.md written. Awaiting user validation to complete the 12-house array.

### 2026-06-14 — Stage-3 calibration: clause-2 favour-preponderance "V2" — ratchet 53/130 -> 62/130
First ENGINE calibration (all prior re-bases were golden-confirmations). Target: the dominant
mixed-bias failure — clause-2 of `house_template._decide` returned 'mixed' on EVERY benefic+malefic
contradiction (CONTRA_PILLAR knobs at the no-op 99/99).
- **Method**: isolated CONTRA_PILLAR sweep over the 130-verdict corpus (`scratch_contra_sweep.py`,
  `scratch_contra_guarded.py`), per-house before/after + explicit gain/regression list. Found the
  bare knob-flip (3/2) nets only +5 and INVERTS genuine afflictions to favourable — the decisive
  favour-vote preempts the navamsa down-modulation (mixed+weakens->afflicted) that was correctly
  reading the H9 father-death charts + H2 afflictions as afflicted.
- **Fix (user-signed-off "V2")**: `CONTRA_PILLAR_AFFLICT 99->3`, `CONTRA_PILLAR_FAVOUR 99->2`
  (total.py) + a NAVAMSA GUARD in clause-2 — the favour lift is skipped when
  `L.navamsa_status=='weakens'` (a weakening confirmation-varga is never painted over by Rasi
  pillar strength; same discipline the navamsa/yoga modulators already obey). The afflicted
  preponderance stays unguarded/decisive.
- **Result**: 53/130 -> **62/130** (+9, 40.8%->47.7%), ZERO afflicted->favourable inversions (all
  58 snapshot drifts are mixed->favourable). Per-house base->V2: H1 8->7, H2 7->9, H3 4->5,
  H4 3->5, H9 7->9, H10 5->3, H11 7->10, H12 4->6. The 7 residual misses are mild mixed->favourable
  over-commitments (notably H10 status_honour 5->3).
- Tests: rewrote `test_preponderance.py` (3 tests: the no-op `==99` pins -> `3`/`2`; the "favourable
  is decisive vs navamsa-weakens" rule INVERTED to the guard) + `test_house_template.py` clause-2
  contradiction trio (balanced->mixed, 2-strong->favourable, weakens->afflicted). Regenerated 15
  Tier-3 snapshots. Suite 3054 passed, 21 skipped, 3 xfailed.
- **Next**: the AFFLICTION side (H5 1/12, H6 2/10) — those goldens mostly do NOT reach clause-2
  (single-polarity / dusthana-overweight), needing the separate conditional-override / affliction-veto
  cluster (a distinct user sign-off).

### 2026-06-14 — Stage-3 DECISION 2: dusthana-affliction rule "B" — ratchet 62/130 -> 73/130
Affliction-side cluster (user-chosen). Diagnostic (`scratch_afflict_diag.py`) showed the H6/H12
misses split into two root causes: (1) DUSTHANA INVERSION — for the 6th/12th's malefic
significations a STRONG lord/karaka by Shadbala *strengthens* the evil, but clause-6 needs a WEAK
pillar to call afflicted, so all-strong + lone-malefic fell to clause-8 'mixed' (then navamsa
'confirms' could even lift to 'favourable'); (2) the H5 children problem (strong-pillar favourable
+ fertility gate only softening to mixed) — a DIFFERENT, harder design, deferred.
- **Fix (clause-1.5, after the karaka veto)**: an `AFFLICTION_MATTER` flag (set in
  `_build_frame_ledger` for the scoped keys) makes a fired malefic with NO benefic contradiction
  CONFIRM the affliction — decisive, pillar-strength-proof, not navamsa-liftable. A benefic
  contradiction (Vipareeta/Harsha/benefic aspect) routes back to clause-2. Deferred under the
  longevity guard. Scope: H6 {enemies_disease, accidents, debts, enemies, disease_chronic} + H12
  {incarceration, left_eye}; H8 EXCLUDED (legacies/sudden_gains are gains, death/longevity Phase-E).
- **Result**: 62/130 -> **73/130** (+11, 47.7%->56.2%), **ZERO regressions** (gains are pure):
  H6 2/10 -> 9/10, H12 incarceration/left_eye +4. The directional MIRROR of V2's navamsa guard —
  together they make Shadbala strength directional (helps a benefic significator, harms via a
  dusthana one). No Tier-3 snapshot drift (the H6/H12 affliction goldens are track ["A","B"] only).
- Tests: 4 new clause-1.5 unit tests in `test_house_template.py` (lone-malefic->afflicted;
  navamsa-confirms can't lift; benefic routes to preponderance; longevity guard defers). Suite green.
- **Next**: H5 children (1/12) — strong-pillar favourable not an inherent-affliction key; needs a
  children-specific beeja/kshetra design (its own sign-off). Held: h5_14, h12_13.

### 2026-06-14 — Stage-3 DECISION 3: H5 fertility-gate extension "O1" — ratchet 73/130 -> 78/130
Final affliction-side piece. Diagnostic (`scratch_h5_diag.py` + `scratch_h5_proto.py`) split the 11
H5 children afflicted-misses by sphuta state: 5 "both sphutas weak" (the gate already detects, but
only softened favourable->mixed) + 5 "one-weak/both-strong" (fertility not the cause — malefics ON
the 5th, harder) + 1 reverse (h5_16, Raman favourable). The decisive evidence: h5_08 (no malefic,
no benefic, neutral navamsa) and h5_11 (3 benefics, 0 malefics) are read **afflicted** by Raman
purely on barren sphutas — proving "both barren = denial" even with no other affliction.
- **Fix (`_fertility_gate`)**: a doctrinal REVERSAL of the gate's prior soften-only design — when
  BOTH beeja+kshetra sphutas are weak the children verdict is now DENIED to `afflicted` (decisive,
  overrides the placement-evidence favourable/mixed). A SINGLE weak sphuta is still only weighed
  (the 'numeric_partial' branch). The children-matter mirror of the dusthana rule: significator
  strength does not beget a child when both seeds are barren.
- **Result**: 73/130 -> **78/130** (+5, 56.2%->60.0%), **ZERO regressions**: H5 children 1/12 ->
  6/12. No Tier-3 snapshot drift (H5 children goldens are track ["A","B"]).
- Tests: `test_wiring.py` TestFertilityGate updated (clamp->deny: `test_weak_sphutas_deny_children_afflicted`,
  `test_gate_denies_on_both_barren_sphutas`) + class/module docstrings. Suite green.
- **Remaining H5**: h5_01/05/07/10/12 (one-or-zero weak sphutas — malefics-on-5th mechanism) and
  h5_16 (reverse-miss) — a separate cluster. Held: h5_14, h12_13.

### 2026-06-14 — Stage-3 DECISION 4: H11 Dhana-yoga floor — ratchet 78/130 -> 80/130
The salvaged kernel of an architecture-proposal review (a doc proposing a linear-scoring rewrite —
refuted: the engine is already a 13-mechanism non-linear clause tree; its triple-veto was refuted on
the H5 charts it targeted; its masking/signification ideas were already implemented; only the
Dhana-yoga floor survived). Diagnostic (`scratch_h11_diag.py`/`scratch_h11_proto.py`) refuted the
doc's specific claims (chart 218 has NO encoded Dhana yoga; 223 already correct; 232 wants mixed not
favourable) but found a clean +2 via a two-tier rule matching Raman's gradation.
- **Fix (`_dhana_floor`, new step after _yoga_modulate)**: scoped to H11 gains/acquisitions with a
  fired Dhana yoga — all three pillars strong -> favourable (an unshakeable wealth floor that
  OVERRIDES even a decisive afflicted, e.g. h11_12: Dhana exchange + weakening D9); else lift only
  afflicted -> mixed (a weak pillar tempers the yoga, e.g. h11_18). Never demotes favourable/mixed;
  deferred under the longevity guard. The ONE layer allowed to override a decisive afflicted (every
  other modulator only nudges a borderline 'mixed') — the doctrinal expansion signed off on.
- **Result**: 78/130 -> **80/130** (+2, 60.0%->61.5%), ZERO regressions: H11 10/17 -> 12/17. No
  Tier-3 snapshot drift. 6 new TestDhanaFloor unit tests. Suite green.
- **Remaining H11**: h11_09/h11_17 (gains, no Dhana yoga — navamsa-guard over-reach) + 3
  elder_siblings (co-born logic, not wealth). Held: h5_14, h12_13.

### Stage-3 calibration summary (4 user-signed-off decisions, one session): ratchet 53/130 -> 80/130
40.8% -> 61.5% (+27 verdicts), ZERO doctrinal inversions across all four. The unifying theme:
Shadbala strength is now DIRECTIONAL — V2's navamsa guard stopped strong pillars over-claiming
favourable on benefic houses; the dusthana rule stopped them under-claiming affliction on malefic
houses; the fertility gate stopped a strong 5th lord begetting a child when both seeds are barren;
the Dhana-yoga floor lets a verified wealth combination override an over-harsh afflicted on gains.
Strength helps a benefic significator and harms via a malefic/barren one — and a named yoga is a
structural floor a stray malefic cannot strip.
