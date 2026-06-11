# Raman Saab — Build Status & Resume Point

> Independent engine replicating **B.V. Raman's *How to Judge a Horoscope*** as a
> deterministic, fully-cited proforma. This file is the resume pointer between sessions.

**Branch:** `round8-unification` · **Run tests:** `py -3.12 -m pytest tests/raman_saab/ -q` (67 passing)
**Run CLI:** `py -3.12 -m app.raman_saab --name X --date 1990-07-15 --time 12:00 --tz 5.5 --lat 12.97 --lon 77.59 --format text`

## Done ✅

| Phase | What | Tests | Key commits |
|---|---|---|---|
| **Methodology** | `docs/raman_saab/methodology/` — overview + 12 houses; 700+ line-cited rules; audited + gap-filled; unaudited drafts quarantined in `_derived/` | — | corpus commit |
| **Predicate audit** | `docs/raman_saab/predicate_audit.md` — 12-house sweep of ~1,650 rule-atoms; finalized `conditions.py` v1 set; four-layer rule split | — | audit commit |
| **Spec** | `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md` — §1–§13, 2 arch-reviews + user review + audit-amended | — | spec commits |
| **Phase 0** | `app/raman_saab/chart/` — model, ayanamsa isolation, Sripati Chalita cusps, adapter (Raman ayanamsa, mean node), CLI, import guard | 17 | `8bb8c17…3326940` |
| **Phase 1a** | `app/raman_saab/primitives/` — relationships, compound dignity, graded combustion, sign-attrs, nakshatra+tara, dispositor chains; adapter fills `combust_fraction` | +23 (40 total) | `30692f5…c8e7658` |
| **Phase 1b** | `primitives/` — functional_nature (per-Lagna table + yogakaraka + kendradhipati), bhangas (neecha-bhanga/parivartana/kemadruma), special_points (Atmakaraka 7-karaka / Karakamsa / Arudha), maraka (tiered + 22nd-drekkana + 64th-navamsa), balarishta (HPA-14 gate); `chart/upagrahas.py` (Gulika/Mandi); adapter fills all 5 `Optional` fields | +27 (67 total) | `56b7c61…7d3825e` |

Every phase gated by independent review that **verified against reality** (ran pyswisseph; ran every formula). Phase 1b: plan-doc review (approved) + bphs-doctrine review caught 3 doctrine errors → fixed against Raman's printed text (64th-navamsa from the **Moon** HTJAH-II:4544; 22nd-drekkana offset **+22** pinned to 27°-Aquarius→Libra→Venus HTJAH-II:3692-3695; balarishta houses **7/8/12** + real HPA-14 antidotes); final code-quality + doctrine re-audit on the shipped source = sound.

## Phase 1c — GBB Shadbala (in progress)

The last Phase-1 primitive: re-derive Raman's six-fold strength to his *Graha & Bhava Balas*
(NOT `app/core/shadbala`). **Research done** — `docs/raman_saab/gbb_shadbala_reference.md` is the
authoritative, line-cited formula spec (4-agent corpus extraction + my Ch.4 read), with the two
key fidelity traps pinned (Sun/Moon get **no** Cheshta in the Shadbala total; Dig from the
bhava-**madhya** cusp; Ayana 24°/48° Sun-doubled; Paksha Moon-doubled; Kendra by sign;
Saptavargaja 45-only-in-D1) and a **validated worked fixture** (GBB "Standard Horoscope", 16 Oct
1918, Libra Lagna — full 6-component table in Rupas). The Drik 30-60 branch bug (`(K−30)/2`, not
`K−30`) was caught live. **Decomposed into 3 sub-plans, each pinned to the fixture:**

| Sub-plan | Components | Status |
|---|---|---|
| **1c-1** | varga_lords + `shadbala/{naisargika,sthana,dig,drik}` (pure/cusp, Track-B) | **DONE** — 89 passed, 2 xfailed; commits `27599d4…9a56d7c`. Naisargika (all 7), Sthana (5/7 Saptavargaja exact), Dig (Saturn 56.7), Drik (anchors) pinned to fixture. |
| **1c-2** | `shadbala/{cheshta,kala}` — mean longitudes, declination, sunrise/ghatis, Ahargana (ephemeris) | **▶ RESUME: not started** |
| **1c-3** | total Shadbala assembly + min-required verdict; `bhava_bala`; `ishta_kashta`; wire `PlanetPos.shadbala_rupas/ishta/kashta`; **backfill** maraka `strength_rank`+weakest-planet, balarishta strength, navamsa64 external pin | not started |

**1c-1 carry-overs to resolve in 1c-3** (all diagnosed, none are engine bugs):
- **Mars D30 / Saturn D7 Saptavargaja** — `xfail(strict)`. Engine follows Raman's degree-band rules
  correctly; the book's worked example "bakes" own/neutral at those sub-degree cusps, inconsistent
  with its own §126 bands. Decide whether to honor the book's printed cell or the rule.
- **Moon/Venus Sthana total ±15** — the **Ch.8 Ex.56 vs Ch.3 Ex.13** OCR divergence in the
  Ochcha/Drekkana columns (engine's Moon 126.639 matches Ch.3; §10 gold uses Ch.8 141.650). Pick the gold.
- **Full Dig column** needs real Sripati cusps (only Saturn pinned via the one stated madhya).
- **Drik Mercury benefic/malefic** ("well/badly associated") refinement — Mercury currently always benefic.

**Phase 1c-2 split:**
- **1c-2a — Cheshta — DONE** (commits `be49da0`,`00f1089`; 95 passed, 2 xfailed). `shadbala/cheshta.py`
  (Sripathi `CK = Seegrochcha − (Mean+True)/2`, OCR-corrected + validated to the decimal vs all 5
  worked values) + `chart/mean_longitudes.py` (Raman's epoch method, reproduces his means to ≤0.12°).
  Sun/Moon get NO Cheshta in the total. End-to-end test passes on a real ephemeris chart.
- **1c-2b — Kala — DONE** (commits `805d54a`,`3c10a83`; 112 passed, 3 xfailed). `shadbala/kala.py`
  (all 9 sub-components, `KalaContext`; 5-planet column pinned to ≤0.04 Sh) + `chart/kala_context.py`
  (real-chart weekday/sunrise/is_day/day_third/hora/birth_degrees). Mars/Venus Ayana `xfail` (book
  self-inconsistency: formula 1.90/24.30 vs Raman's printed 1.40/23.80). **Ahargana year_lord/month_lord
  flagged "UNKNOWN" → award 0 (never a wrong planet); carried to 1c-3.**

**ALL SIX Graha-Bala components now built** (Sthana, Naisargika, Dig, Drik, Cheshta, Kala), each
pinned to the GBB Standard-Horoscope fixture.

**1c-3 capstone — DONE** (commits `f5c0f4d`→`19905ff`; 117 passed, 3 xfailed). `shadbala/total.py`
(`assemble_shadbala` + `is_powerful` + `MIN_REQUIRED`) — **all 7 fixture Total-Rupas reconcile**
(6.288/6.936/5.381/**9.674**/7.381/5.949/6.196 — Mercury's printed 9.743 was a book OCR error vs its
own component sum 580.46; engine pins 9.674) and **all 7 powerful** per GBB thresholds.
`shadbala/ishta_kashta.py` — all 7 Ishta/Kashta reconcile to ≤0.05 Sh incl. the Sun/Moon Cheshta
surrogates. **The whole six-fold strength engine now reconciles to Raman's worked totals to the decimal.**

**1c-3 continuation — DONE** (commits `bb00234`→`85a9530`; 161 passed, 3 xfailed). `shadbala/bhava_bala.py`
(Bhavadhipati + Bhavadig[nil-house ref; 8th-in-Leo=40] + BhavaDrig); `chart/shadbala_compute.py` + a
3-pass adapter (combustion → Shadbala → maraka/balarishta) fills `PlanetPos.shadbala_rupas/ishta/kashta`
on ephemeris charts; maraka `strength_rank`+weakest-planet and the balarishta strong-lagna-lord antidote
now use real Shadbala. Bangalore chart: Sun 8.62R … Saturn 5.97R, all plausible.

---

# ✅ PHASE 1 COMPLETE

All chart primitives + the full six-fold **Shadbala** engine (Sthana, Dig, Kala, Cheshta, Naisargika,
Drik → total + verdict, Bhava-bala, Ishta/Kashta) are built, pinned to Raman's *Graha & Bhava Balas*
worked example, and wired onto real charts. **161 passed, 3 xfailed.** Six book self-inconsistencies were
caught + handled honestly (drekkana offset, Drik branch, Cheshta OCR, 2 Ayana cells, 2 Saptavargaja cusps,
Mercury total). The strength engine reconciles to the GBB Standard-Horoscope totals to the decimal.

**Small residuals (documented, none are bugs):** Ahargana Kala year/month lords (UNKNOWN→0, Kala
under-counts ≤0.75R); navamsa64 +63/+64 external pin; the Mars/Venus-Ayana + Saptavargaja-cusp `xfail`s
(engine follows Raman's stated rule; his book contradicts itself at those sub-degree cells).

## Phase 2 — doctrine/conditions + rule encoding (STARTED)

- **`doctrine/drishti.py` — DONE** (commit `a7a4430`; 5 tests). Whole-sign aspects: all 7th; Mars 4/8,
  Jupiter 5/9, Saturn 3/10; **Rahu/Ketu 7th-ONLY** (the locked divergence vs `app/core` 5/9, guard-tested).
  API: `aspects_planet(a,b,chart)`, `aspects_house(p,h,chart)`, `mutual_aspect`, `aspecting_planets`,
  `aspecting_house`. This unblocks the deferred aspect-based conditions.

- **Aspect backfills — DONE** (commit `93b8fd3`). `drishti` wired into the Phase-1 conjunction-only
  deferrals: neecha-bhanga aspect-by-dispositor + kemadruma benefic-aspect cancellation (`bhangas.py`),
  maraka aspect-associates (`maraka.py`), balarishta benefic-aspect protection (`balarishta.py`).
  3 aspect-path tests in `doctrine/test_aspect_backfills.py`; no fixture regression.
- **`doctrine/conditions.py` foundation — DONE** (commit `e41e9e6`; 4 tests). Composable `Condition`
  (`And`/`Or`/`Not`/`AtLeastN` + `& | ~`) over an `EvalContext(chart)`; **first batch** of leaf
  predicates (absolute, Lagna-frame, D1): `InRashiHouse`, `InHouse`(Chalita), `InSign`, `LordIn`,
  `Conjunct`, `Aspects`, `HasDignity`, `Retrograde`, `Combust`, `IsYogaKaraka`, `NeechaBhanga`.

- **`conditions.py` expanded — DONE** (commit `b708586`; 9 tests). Added C1 frame-relative
  `InHouseFrom` (LAGNA/MOON/planet/house origins), `InHouseClass` (H6), `Parivartana`/`Exchange`
  (C6), `HemmedBy` (H1), `MutualAspect`, `FunctionalNature` (C4), `InStarOf` (C3), `MoonPhase` (H4),
  `CountInHouse` (H10), `Vargottama`. ~22 leaf predicates total + combinators.
- **`RuleRecord` + Citation registry — DONE** (commit `7ab6c02`; 4 tests). `doctrine/rules.py`
  (`RuleRecord` = condition tree + house/signification/group/fortified-afflicted/frame/varga/polarity/
  source; `.fires(chart)`); `doctrine/sources.py` (`Citation(work,line)` + `verify()` resolving on-disk
  corpus lines — HTJAH-I/II, HPA-NN, GBB-N — confirmed against real lines).

**PHASE-2 INFRASTRUCTURE COMPLETE.** drishti + condition algebra + RuleRecord + citation verifier all
built. Now the bulk **rule ENCODING** can proceed.

- **Rule-encoding TEMPLATE — DONE** (commit `8a02985`). `doctrine/rule_sets/house_07_kalatra.py` — 5
  cited House-7 RuleRecords (from-Venus combinations + 7th-lord-in-house) proving the pattern;
  `ClassInHouseFrom` predicate added. `tests/.../test_rule_sets.py` **auto-guards every encoded rule**
  (parametrized: citation resolves on-disk + evaluable has a condition) — add new house modules to its
  `ALL_RULE_SETS` list.

- **Lord-in-12 layer COMPLETE for ALL 12 houses** (commits `6673978`,`6d622ee`). 147 cited RuleRecords
  in `doctrine/rule_sets/house_NN_*.py` (12×12 `LordIn` + 3 House-7 from-Venus), parallel-encoded by
  subagents, every citation guard-verified on-disk. `rule_sets/__init__.ALL_RULES` aggregates them.
- **Rule-firing bridge — DONE** (commit `485cd6a`; 3 tests). `judges/rule_firing.py`:
  `fire_rules(chart)` / `fire_house(chart, h)` fire every evaluable rule whose condition holds, choosing
  the **fortified vs afflicted branch by the bhava-lord's Shadbala** (`is_powerful`). **The engine now
  produces a cited, deterministic house reading from birth data** (demoed live on the Bangalore chart:
  per-house lord placement + branch + corpus citation).

- **Planets-in-house layer COMPLETE for ALL 12 houses** (commits `e0b3938`,`036906c`,`e26cd35`).
  108 occupant rules (`InRashiHouse(graha,N)`, 9 grahas × 12 houses). **Corpus now = 255 cited
  RuleRecords** (147 lord-in-12 + 108 planets-in-house), all guard-verified. Firing bug fixed
  (falls back to the available branch when a rule gives only one side, e.g. nodes). 698 tests green.

- **Phase 3 house judge — DONE** (commit `f11e8ae`; 4 tests). `doctrine/karakas.py` (bhava karakas,
  fixed naisargika) + `judges/house_judge.py`: `judge_house(chart, h)` / `judge_all_houses(chart)` →
  **ordinal `HouseVerdict`** (favourable/mixed/afflicted/insufficient-evidence) from the fired rules
  (split by polarity = cited evidence) + the Lord & Karaka Shadbala pillars (spec §6.3). Track-B charts
  decide on polarity alone (no Shadbala). **The engine now emits a full 12-house cited judgment** from
  birth data (demoed: Bangalore → H2/H9/H11 favourable, rest mixed).

- **Proforma + renderer + CLI surface — DONE** (commit `7e3519e`; 4 tests). `proforma.read_chart(birth)
  -> RamanReading` (12 HouseVerdicts); `render.to_text`/`to_markdown` (ASCII-safe book-style worksheet);
  CLI `--format reading|markdown`. **The engine is now end-to-end usable:**
  `py -3.12 -m app.raman_saab --name X --date 1990-07-15 --time 12:00 --tz 5.5 --lat 12.97 --lon 77.59
  --format reading` prints a full cited house-by-house judgment. **706 tests green.**

# ✅ FULL VERTICAL SLICE WORKING

birth data → chart (Phase 0/1) → Shadbala (Phase 1c) → conditions + 255 cited rules (Phase 2) →
fired-rule reading → ordinal house verdicts (Phase 3) → rendered cited worksheet (proforma/render/CLI).

# Accuracy-first rebuild (plan: C:\Users\S.C.C\.claude\plans\compressed-mixing-trinket.md)

The roadmap was re-planned **accuracy-first** (per-signification judge + golden harness BEFORE mass
rule encoding) and stress-tested by 3 independent reviews (doctrine/architecture/completeness) + 5
rounds of user doctrinal review. Key locked corrections live in the plan file: **harana order =
Chakrapatha → Satrukshetra (Mars+retro exempt) → Astangata (Venus/Saturn FULLY exempt) → Krurodaya
(absolute, Pindayu-only)**; Vipareeta = Raman's narrow form only; §6.3 thresholds are golden-tuned
heuristics (never cited to Raman); maraka tie-break = Chart-35 unit-counting; span bands 8-32/33-75/75-120.

## Phase A — per-signification judge (DONE)
- **A1 `doctrine/significations.py`** (commit `924d7b6`; 8 tests): 42 Signification records, all 12
  houses — fine matters → karaka(s) + mandatory frames (H4 mother→Moon, H7 spouse→Venus, H9
  father→Sun, H10 quad-karaka weights) + `rule_tags` bridge to the coarse rule buckets. Doctrinal
  spot-check: PASS (all karakas correct, zero node-karakas, citations on-topic).
- **A2/A3** (commit `60c7664`; 17 tests): `EvalContext` lazy `_cache` + `get_or_compute` +
  `functional_nature(planet)` accessor (per-Lagna table already existed in `primitives/functional_nature.py`).
- **A4-A6 `judges/house_template.py`** (commits `f81d051` + fixes `ff96590`; 33 tests): 3-frame
  immutable `FrameLedger` (Lagna/Moon/Karaka-as-Lagna), `_decide` 5-step ordinal rule (karaka-veto →
  contradiction-mixed → Track-B polarity fallback → favourable → afflicted with **bhava-rescue
  (HTJAH-I:503-505)** + **karaka-salvage (three-pillar, HTJAH-II:221)** → insufficient), navamsa
  modulation (borderline-only), lord==karaka pillar-collapse, parivartana resilience, **load-bearing
  longevity guard** (LONGEVITY_GUARD clamps death/longevity matters to insufficient-evidence until
  Phase E). Adversarial 3-lens review caught + fixed: citation misattribution (503-505 was the
  HOUSE-rescue, not karaka), inert longevity guard, as_house_verdict lord/strength frame mismatch.
  Legacy `house_judge.py` untouched (shim compat; Phase-G cutover).

## Phase B — golden harness (FOUNDATION DONE; user validation pending)
- **Framework** (commit `780ac15`): `docs/raman_saab/golden_schema.md`; `tools/raman_saab/
  extract_goldens.py` (prose→ordinal lexicon + condition-solver that escalates on Not()/unknown);
  `tests/raman_saab/test_goldens.py` (Track A astronomy sign-level + sandhi audit-log; Track B
  doctrine CONFIRMED-only; Tier-3 evidence snapshots with explicit UPDATE_RAMAN_SNAPSHOTS=1 switch;
  schema guard + DRAFT-gate); `tools/raman_saab/tune_thresholds.py` (bounded discrete tuner,
  0.5R/1.0R steps, --max-iterations --holdout-lock, emits diff never writes total.py).
- **First DRAFT batch** (commit `2506ad2`): 19 worked-example goldens — H1 charts 9,10,12,15,17,18,
  20,24,29,31,33,35 (HTJAH-I) + H8 longevity 33/34/35 (86y2m20d Pindayu / 68y10m5d Amsayu / death
  1966-02-07) + Gandhi/Lincoln/JFK/Hitler death charts. ALL verdict_review=DRAFT (non-asserting).
- **Objective review fixes** (commit `0eb5af8`): chart_33 tz→5.5 IST; chart_10+33 lagna→Aquarius
  (HTJAH-II:4253 prints "Aquarius 9°42'" — the methodology "Capricorn" label was wrong, fresh-cast
  agreed); Lincoln lon/tz→Western (book OCR dropped the W); Track A now ASSERTS fresh-cast Lagna vs
  printed lagna_sign (sandhi-tolerant); schema guard #11 (rule_level/doctrine_statement can't smuggle
  verdicts); tuner Final removed; extractor self-test in CI. **855 passed, 5 skipped, 3 xfailed.**

**▶ RESUME next:**
1. **USER VALIDATION (blocking the ratchet, not the build):** review the 19 DRAFT prose→ordinal
   mappings in `tests/fixtures/raman_goldens.jsonl` → flip to CONFIRMED (or correct). The doctrine
   reviewer's suggested corrections (charts 33/20→afflicted, 29→favourable, 10→mixed, 31→mixed,
   35→favourable, 24→favourable-or-mixed) are in the session log; "insufficient-evidence" is reserved
   for ABSENT testimony, not negative testimony.
2. **Phase-A deps in flight** (workflow `wf_ed2702cc-bdc`): `doctrine/yogas.py` (Raman-cited yoga
   catalogue + detect_yogas), `primitives/sphutas.py` (Beeja/Kshetra gate, Special-Dhana-Lagna,
   Sahams), `doctrine/lookups/` (decanate-cause, source-of-gains, Bhavartha-Ratnakara, confinement
   modes, disease map) — parallel-built, then doctrine+code review, orchestrator commits.
3. Then: wire yogas/sphutas/lookups into the judge + proforma metadata; **Phase C** combinations
   encoding (harness-gated); **Phase D** predicates (C2 varga-overlay `InVargaHouseFrom`, TaraOf,
   KARAKAMSA origins); **Phase E** longevity (corrected harana matrix, 3 to-the-day goldens);
   **Phase F** timing (+ `stated_dasha_balance` drift guard); **Phase G** surfaces + shim cutover.

## Locked decisions / gotchas (do NOT relitigate)
- **Ayanamsa = Raman default**, isolated via `chart/ayanamsa.py` context manager — NEVER mutates the global (app/core stays Lahiri). `pyswisseph 2.10.x has no get_sid_mode()` — uses hasattr + Lahiri-restore fallback.
- **No `app/core` imports** — enforced by `tests/raman_saab/test_import_guard.py`. Re-derive Shadbala to GBB, don't import core's.
- **Bhava (Chalita) not Rashi** for result judgment; `rasi_house` for lordship/aspects/yogas. Both carried on `PlanetPos`.
- **Nodes cast only the 7th aspect** (no 5/9); **mean node** (not true node) — Raman's hand-calcs.
- **A rule is not always a boolean**: condition predicates → `doctrine/conditions.py`; lookup tables → `doctrine/lookups/`; numeric sub-engines → `primitives/`; timing → `judges/timing.py`; output meta-modifiers → `proforma.py`.
- **Verdict is an ordinal** (favourable/mixed/afflicted/insufficient-evidence), never a false-precision score (spec §6.3).
- Test data tables (exaltation, friendships, nakshatra lords, drekkana) verified live — Mercury moolatrikona is **Virgo 16-20** (Raman/Santhanam), not a typo.
- **Phase 1b doctrine locks (pinned to Raman's printed text, do NOT "correct" to textbook):**
  - **22nd drekkana = lagna decanate + 22** (mod 36), pinned to Raman's worked example 27° Aquarius → 1st-of-Libra → Venus (HTJAH-II:3692-3695). The textbook "8th-house +21" is the alternative; Raman's printed example is the authority.
  - **64th navamsa is reckoned from the MOON** (HTJAH-II:4544), not the Lagna. Offset +63 is the textbook default but **unpinned** (no Raman worked example) → external-pin (JH/drikpanchang) is a Phase-1c backfill.
  - **Atmakaraka = 7 visible planets only** (`special_points._SEVEN`), never Rahu/Ketu — load-bearing because the adapter DOES inject nodes into `chart.planets` (CLAUDE.md lock).
  - **Functional nature = Raman's printed per-Lagna table is the authority** (it embeds his hand-tuned calls, e.g. Libra-Mars "feeble benefic" = neutral); 3 unprinted holes (Aries-Moon, Gemini-Saturn = neutral; Aquarius-Saturn = benefic) are generating-rule derivations.
  - **Balarishta Moon-affliction houses = 7/8/12** (HPA-14:96-98), NOT 6/8/12; antidotes are the real HPA-14 list (no "malefics in upachaya").
  - Aspect-based conditions (neecha-bhanga aspect-by-dispositor, kemadruma/balarishta benefic-aspect, maraka aspect-association) use a **conjunction proxy** in 1b → refined in Phase 2 (drishti engine). `strength_rank`/weakest-planet maraka → Phase 1c.
