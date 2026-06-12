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

## Where we are (top — keep current)

- **HEAD `e59fc2e`** · suite **1623 passed, 5 skipped, 3 xfailed** · **ratchet floor 7/12** ·
  pushed to GitHub (origin/round8-unification in sync).
- Phases A + B + A-deps + wiring + **Stage 1 (H1 combination layer) COMMITTED**.
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
