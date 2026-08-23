---
title: "Raman doctrine → engine improvement backlog"
kind: record
topic: doctrine
measured: false
updated: 2026-08-04
words: 7546
tags: [raman-saab, record, doctrine]
---
# Raman doctrine → engine improvement backlog

Source: the Phase-1 doctrine-extraction sweep over the prioritized B.V. Raman corpus
(GBB, HTJAH-I, HTJAH-II, HPA, 3HC). Companion to `doctrine_compendium.md` (the full
per-book digests with quotes). Every item carries the corpus citation it rests on.

Channels: `judge-mechanism` (house_template._decide), `shadbala` (primitives/shadbala),
`threshold` (MIN_REQUIRED / marginal handling), `new-rule` (RuleRecord / yoga detector),
`cancellation` (bhanga), `golden` (validation array).

Engine state at sweep time: ratchet **87/130**; uses 3/13 Raman books; the hard tail is
H3 chart_59/60 (siblings) and H7 chart_03/08 (marriage over-harsh).

---

## Recommended Phase-2 order (accuracy-per-effort, lowest-risk first)

| # | Item | Channel | Targets | Effort | Risk | Key citation |
|---|---|---|---|---|---|---|
| **B1** | **Three-factor comparative weighing** | judge-mechanism | H3 chart_59/60; general | high | med | HTJAH-I:3713/3788/3815/2760/2111 |
| **B2** | **Marginal-strength band** (near MIN_REQUIRED) | threshold | H7 chart_03/08 (Venus 5.37); general | med | low | GBB-1:38-60 |
| **B3** | **Non-death-marital maraka guard** | judge-mechanism | H7 chart_03/08 | low | low | HTJAH-II:2579 (Kuja=death, distinct from happiness) |
| **B4** | **Blemishless-/Yogakaraka-Venus marriage override** | new-rule | H7 chart_03/08 | med | med | HTJAH-II:1207, 368, 1474 |
| **B5** | **Yoga additions** (HPA 16 + 3HC Dhana/Lakshmi/Adhi/Nabhasa) | new-rule | H1/H2/H9/H10/H11; chart health | low–med each | low | HPA-20:65-229; 3HC:7632/8184/4256/2442 |
| **B6** | **HPA/HTJAH house rules** (Mars-in-7th, 4th-lord-in-12, dual-sign multiplicity) | new-rule | H4/H7 | low | low | HPA-19:247; HTJAH-I:8170; HTJAH-II:484 |

---

## B1 — Three-factor comparative weighing  `judge-mechanism`  (Phase 2a)
**Doctrine.** Raman weighs the three factors {Bhava, Lord, Karaka} *comparatively* — the
strongest dominates, and conversely a weak/combust dominant factor drags the matter down
even when another factor is strong. The engine currently treats the three pillars as
independent booleans (preponderance count), never *comparing* them.
- **HTJAH-I:3713** "Of the three elements, the third lord is more powerful than the third house or Mars." → strongest factor decides (chart_54, already correct).
- **HTJAH-I:3788** "Though the Karaka Mars is well disposed, the fact of the ruler of the third becoming combust and hence powerless, renders the third house weak. This stands against his having any brothers." → **chart_59 verbatim**: a combust/weak LORD denies the matter despite a strong karaka.
- **HTJAH-I:3815** "Though Jupiter is well-disposed... the Karaka and the third house are subject to affliction. The native has no brothers." → **chart_60 verbatim**: house+karaka afflicted → denied even with a good lord.
- **HTJAH-I:2760** "all the three factors... strong and well-fortified → immense wealth"; **HTJAH-I:2111** "a steady flow of fortune is assured if at least two of the three are well disposed."
- **HTJAH-I:13961** "the reckoning made from the strongest of these three centers gives good results."

**Engine note.** chart_59's lord is **combust** (Raman reads it weak) yet the Shadbala
pillar reads it strong — so comparative weighing must fold *combustion/placement* into the
factor's effective strength, not just total Shadbala. This is the same Shadbala-vs-placement
divergence the dusthana/fertility fixes addressed.
**Plan.** Extend `_decide` so that, when the pillars conflict, the *effective* strength of
each factor (Shadbala adjusted for combustion / debilitation-uncancelled / dusthana) is
compared; a decisively-weak dominant factor denies, a decisively-strong one carries. Guard
hard against regressing chart_54 and the broad ratchet. Shared judge → user sign-off.

**Status 2026-08-03 — BUILT, MEASURED, and ENABLED (user-signed-off).**
`house_template.B1_DOMINANT_FACTOR_GUARD` (default **True** since 2026-08-03) blocks clause 2's strong-pillar
FAVOUR lift when the LORD is hard-afflicted — combust or debilitation-uncancelled, the two
afflictions Raman reads as making a planet powerless in itself (HTJAH-I:3788). Dusthana
placement is deliberately excluded: Raman's dusthana readings are matter-specific (a strong
dusthana lord *feeds* an affliction, clause 1.5), so folding it in double-counts.
`primitives/effective_strength.py` supplies the facts; `_lord_hard_afflicted` reads them.

Measured A/B on the golden corpus — it splits the two ratchets:

| metric | guard OFF | guard ON |
|---|---|---|
| strict exact | 261/293 = 0.891 | **259/293 = 0.884 — SHIPPED** |
| within-1 ordinal | 281/293 = 0.959 | **283/293 = 0.966 — SHIPPED** |
| real errors (dist>=2) | 12 | **10 — SHIPPED** |

Both golden baselines were re-based in the enabling commit (the human-bump rule requires the
re-base and the change that earns it to land together). This is the **first deliberate DOWNWARD
strict re-base** in the project's lineage — accepted because a favourable<->afflicted INVERSION is
a worse doctrinal failure than a favourable/mixed boundary call, and the ordinal headline improves.

Per-chart: **+2 exact** (chart_18 H1, chart_52 H3 — both favourable→mixed, matching Raman),
**2 real errors downgraded to off-by-one** (chart_20 H1, h12_05 H12), **−4 exact**
(chart_54 H3, NH.chart_43 H1, h12_17 + h12_18 H12/moksha).

Two observations for whoever revisits this:
- chart_52 H3 improves while chart_54 H3 regresses — same matter, opposite directions — so a
  blanket lord-guard is not the whole of Raman's comparative weighing.
- **Half the regressions are H12/moksha**, and H12 is an atlas-proven INVERTED channel. Scoping
  the guard away from inverted channels would likely win on both metrics — but that is fitting
  to the goldens, which the MEASURED TRUTH lock warns is not accuracy. Deliberate call, not a
  silent tweak.
  - **SCOPING MEASURED AND CLOSED 2026-08-03 — the speculation above was WRONG.** A/B via the
    new `B1_GUARD_EXEMPT_HOUSES` knob (empty by default, read live, human-set only): exempting
    H12 (or H3+H12, the atlas set) gives exact 259→261 but within-1 283→282 and **real-errors
    10→11** — h12_05 H12/expenditure un-softens back to a favourable↔afflicted inversion. It
    does NOT win on both metrics; it trades back the exact failure category the guard was
    enabled to fix. Neither variant dominates, and the enablement decision already ranked fewer
    inversions above strict exact — so the guard stays UNSCOPED and the knob stays empty, kept
    only so a future re-measurement is a one-line experiment.

The tuner cannot find this: `tune_thresholds --holdout-lock` converges at iteration 0 (fit
0.907, holdout 0.841, no improving neighbour) because B1 is a *comparison*, not a weight, and
no swept knob expresses "the dominant factor decides".

## B2 — Marginal-strength band  `threshold`  (Phase 2b) — ✅ SHIPPED 2026-06-27
**Status.** `_marginal_karaka_gate` (house_template.py): a MARRIAGE verdict afflicted PURELY by a
marginally-weak Venus karaka (within 0.2 rupa of MIN_REQUIRED) + a STRONG lord + NO real malefic
re-decides treating the karaka as not-decisively-weak (GBB-8:303-312 bars are reference values,
GBB-1:38-60 continuity). Scoped to marriage (general form clips chart_54 H10); with/without-gate
diff changes exactly 1 confirmed verdict (chart_08 H7 afflicted→favourable, a dist-2 real-error
resolved); 0 regressions; reviewer SOUND-WITH-CAVEAT (KEEP/FLAG: n=1 + 0.2 band + 2-level lift,
re-examine if a 2nd marriage golden enters the band). Ratchet 206/240 → 207/240, real-errors 14→13.
**Doctrine.** GBB-1:38-60 — strength scales continuously (0 at bhava-sandhi → full at
madhya); there is no hard cliff. The engine's `MIN_REQUIRED` is a hard cutoff, so Venus at
5.37 vs the 5.5 bar reads "decisively weak" and trips clause-6/maraka on chart_03/08.
**Plan.** Introduce a *borderline band* (e.g. within ~0.3 rupa of MIN_REQUIRED → "marginal,"
neither decisively strong nor decisively weak), so a marginally-weak karaka doesn't drive a
decisive affliction. Re-examine via `tools/raman_saab/tune_thresholds.py` (do not hand-set).
**Note.** paksha-bala is ALREADY in the stack (`kala.py:81`, GBB-5:215-223) — the Venus gap
is threshold handling, not a missing bala.

## B3 — Non-death-marital maraka guard  `judge-mechanism`  (Phase 2c)  — ✅ SHIPPED 2026-08-17
**Status.** `MARAKA_NON_DEATH_GUARD`: `_build_frame_ledger` flags `marital_happiness`;
`_decide` suppresses only maraka's verdict-driving effect under it (karaka veto, fired
malefics, every other clause keep force; the ledger still records `maraka_active`;
spouse/coverture/death/longevity unflagged). Companion: `_marginal_karaka_gate`'s trigger
widened {afflicted}→{afflicted, mixed} (same strict conditions) because the maraka/cliff
artefact B2 was built to lift no longer forms as 'afflicted' — chart_08's confirmed
favourable preserved through the mixed route. Anti-double-move added per doctrine-review
HIGH: a 'mixed' produced by the `_marital_bond_gate` demote (HTJAH-II:2664/2877) is never
re-lifted (`bond_demoted` mirror of `blem_lifted`).
**Measured.** Canonical ratchet banner byte-identical: exact 259/293, within-1 283/293,
real-errors 10. Full A/B over all 450 H7 sig-verdicts on 225 goldens: exactly 5 flips, all
on rows with NO confirmed expectation (guard-invisible): h4_04 mh favourable→
insufficient-evidence; chart_35 / NH.chart_43 / NH.chart_65 mh afflicted→
insufficient-evidence; h7_12 mh afflicted→favourable (widowhood chart — death≠happiness
under this very doctrine; eyeball h7_12's prose on the corpus machine). On evidence-empty
ledgers the old artefact now surfaces as insufficient-evidence (not mixed) — arguably more
honest; recorded per the reviewer's MEDIUM.
**Corpus-machine follow-ups (content verification impossible on the cloud machine):**
(1) HTJAH-II:2579 verbatim — death-of-spouse reading; RECONCILE with H7.KD.1 which cites
the same line for a marital_happiness affliction (possible pre-existing sig
mis-assignment); (2) h7_12 prose vs the new favourable happiness reading; (3)
HTJAH-II:1436 (chart_08) spot-check of the mixed-trigger gate route.
### (original)
**Doctrine.** Kuja-Dosha / maraka pressure is about the *death* of the spouse (HTJAH-II:2579
"the death of the husband/wife will occur"), NOT marital *happiness*. The 7th is a maraka
house, so Venus-the-karaka lands in the maraka set and clause-6 over-afflicts a barely-weak
Venus on the happiness sub-matter.
**Plan.** Suppress `maraka_drives` for the `marital_happiness` signification (a non-death
matter), mirroring the LONGEVITY_GUARD pattern. Pairs with B2 to fix chart_03/08.
**Note.** The Kuja-Dosha *cancellation* (sign exemptions Gemini/Virgo, Cancer/Capricorn, …;
Leo/Aquarius wholly exempt; Mars+Jupiter/Moon conjunction) is **already encoded** in
`_KujaDosha` (HTJAH-II:2593-2601) — so this is NOT a missing-cancellation gap.

## B4 — Blemishless-/Yogakaraka-Venus marriage override  `new-rule`  — arm 2 ✅ SHIPPED 2026-08-17 (arm 1 shipped 2026-06-15)
**Status.** `H7.C.87`: benefic `marital_happiness` testimony — `IsYogaKaraka("Venus")` AND
Venus in a fixed sign {Taurus, Leo, Scorpio, Aquarius} → "fixity of affections"
(HTJAH-II:1474). Venus is Yogakaraka only for Capricorn/Aquarius lagnas (HTJAH-I:606
kendra+trikona sense — the conservative, under-firing reading of "Yogakaraka"). Fires on
20/225 goldens, changes 0 confirmed verdicts (incl. firing WITHOUT flipping the h7_16
troubled-marriage golden — the right stress case surviving). Doctrine-review
KEEP-WITH-FLAG: the record re-frames the backlog's "override of the dual-sign stigma" as
the karaka-QUALITY testimony itself (unconditional benefic, not conditioned on dual-sign
context) — **corpus-machine follow-up**: verify HTJAH-II:1474 verbatim for (a) the
technical vs loose "Yogakaraka" sense, (b) whether the statement is conditional on the
multiplicity context, (c) whether its subject is constancy/happiness or number of
marriages.
### (original)
**Doctrine.** HTJAH-II:1207/368 — a *blemishless* Venus (exalted/own/good-vargas,
unafflicted) as karaka+7th-lord aspecting the 7th → chaste devoted wife (favourable).
HTJAH-II:1474 — a *Yogakaraka* Venus in a fixed sign overrides the dual-sign multiplicity
stigma ("fixity of affections"). A positive karaka-quality gate the engine lacks.
**Plan.** A `marital_happiness` benefic rule: blemishless/Yogakaraka Venus → favourable
(complements B2/B3 for the chart_03/08 over-harsh).

## B5 — Yoga additions  `new-rule`  (partly done 2026-06-15)
**Done (coverage):** added 3 cited 3HC Dhana yogas to the detector — Y.DHANA.BAHU (Bahudravyarjana
1-2-11 cyclic chain, 3HC:8184), Y.DHANA.122 (Venus-5th + Saturn-11th in a Venus 5th-sign,
3HC:7632), Y.DHANA.125 (Sun own-5th + Moon&Jupiter-11th, 3HC:7645). They fire on **0 of the 130
goldens** (ratchet unchanged at 89) — pure additive fidelity for real charts via the H2/H11 dhana
modulation + dhana-floor. **Deliberately NOT added** (un-faithful or noisy): Lakshmi (#72) — its
faithful form needs "lagna-lord powerful" (Shadbala), and the geometry-only form over-fires (17/130);
the Sun-based Vesi/Vasi/Ubhayachari — near-universal (~85/130), inert (kind=other), snapshot noise.
**HPA named yogas — partly done 2026-06-27 (Phase 1A):** added 3 as additive fidelity (cited HPA-20,
reviewer-KEEP, zero-regression) — **Y.CHAMARA** (HPA-20:65, strict arm), **Y.SREENATHA** (HPA-20:90),
**Y.KHADGA** (HPA-20:184). Deferred (over-fire under the is_powerful proxy → need B1 effective-strength):
Shankha (102/164), Kahala (48/164), Lakshmi (strict dignity arm 16/164). Rejected as noise: Sun-based
Vasi/Vesi/Obhayachari. Un-mined: Sarada, Matsya, Mridanga, Konrma, Kusimia, Daridra, Rajju.

**RE-ATTEMPT CLOSED 2026-08-03 (negative, measured).** The B1 effective-strength measure now
exists and was applied to all four deferred yogas on the full 225-chart corpus. It does NOT
rescue them: Shankha 126→113/225 (50%), Kahala 76→67/225 (30%), Bheri 94→85/225 (38%) under the
strictly tighter gate (band=="strong" AND not decisively_weak). The original diagnosis was wrong
— the proxy was never the problem; the GEOMETRY is common by construction (mutual kendras ~1/3
base rate, movable-sign lords ~1/3), so no strength refinement can make these rare. Lakshmi's
strict arm IS rare (7/225 geometric, 3/225 gated) but only under one resolution of the
sentence's comma-parse, which Raman does not disambiguate and whose readings differ by an order
of magnitude — registering one would be choosing doctrine for him. All four stay deferred; the
unblocking condition is now "a more specific reading of Raman's text", not a better strength
measure. Scan: yoga_refire (session scratch, 2026-08-03); full numbers in yogas.py's deferral
note.

### (original)
Add to the yoga detector / rule sets (each cited; mostly low-risk, additive):
- **3HC Dhana yogas** (H2/H11 wealth): #122 Venus-5th+Saturn-11th (3HC:7632); #125 Sun-5th-own
  + Moon/Jupiter-11th (3HC:7645); Bahudravyarjana #133 lagna→2nd→11th→lagna lord chain
  (3HC:8184). Lakshmi #72 (3HC:4256, H9/H11). Adhi #7 (3HC:2442 — already present as Y.ADHI).
- **3HC Nabhasa** (chart health): Rajju/Musala/Nala (3HC:7083), Srik/Sarpa (3HC:7175),
  Harsha/Sarala/Vimala (3HC:7320 — the Vipareeta family; Y.VIPAREETA exists, audit overlap).
- **HPA named yogas** (HPA-20): Chamara, Shankha, Sreenatha, Bheri, Sarada, Kesari, Kahala,
  Mridanga, Khadga, Lakshmi, Kusimia, Konrma (raja/wealth/virtue, H1/H9/H10); Sun-based
  Vasi/Vesi/Obhayachari (mirror of lunar Sunapha/Anapha/Durudhura); Daridra (poverty),
  Rajju (foreign). Wire kind-scoped like the existing dhana/raja/arishta modulation.

## B6 — HPA/HTJAH house rules  `new-rule`  ✅ RESOLVED-BY-AUDIT 2026-06-25
**Settled:** all three proposed rules are ALREADY encoded; adding them would double-count
(the judge dedups by `rule.id`, not by placement). bphs-doctrine-reviewer pass confirmed,
HIGH confidence on B6.1/B6.2, MEDIUM on B6.3. Coverage pinned by
`tests/raman_saab/doctrine/test_b6_house_rules_coverage.py` so the rules can't silently
regress nor be re-added as duplicates. ZERO engine change → ratchet unchanged (89/130).
- **B6.1** Mars-in-7th → clashes/tensions/two wives (HTJAH-I:8170) — **COVERED** by
  `H7.P.Mars` (planets_in_7th.py:35, HTJAH-II:532 — the SAME dictum, near-verbatim), with the
  placement partitioned into `coverture` (`H7.C.60`) and `marital_happiness` (`H7.KD.1`).
- **B6.2** 4th-lord-in-12 → loss of ancestral property (HPA-19:247) — **COVERED** by
  `H4.C.3` (combinations.py:116, HTJAH-I:4208, sig `property`) + `H4.L.12` (lord_in_12.py:84,
  HTJAH-I:4187). HPA is Raman's own condensation of the same HTJAH-I lines.
- **B6.3** dual-sign 7th & Venus → ≥2 marriages (HTJAH-II:484; HTJAH-I:8138) — **PARTIALLY
  COVERED**: `H7.C.38` (combinations.py:392) already scores the **7th-SIGN**-dual + Venus-dual
  signature from the SAME source (HTJAH-II:484). The reviewer FLAGGED the **7th-LORD**-in-dual-
  sign as a *genuinely distinct* but deliberately deferred refinement — encoding it now would
  inflate the over-harsh H7 marriage tail (the very thing B2/B3/B4 relieve) and needs the
  unencoded Jupiter↔Venus holding-factor exception first. Kept text-only, as the code already
  does. (HTJAH-I:8138 could not be verified on disk — confirm against a primary source before
  treating it as an independent testimony.)
- Planet results vary by avastha/disposition, not mere occupancy (HPA-19:47; HPA-7 the 10
  avasthas) — a longer-horizon `shadbala`/metadata item, **still deferred**.

### B6-adjacent observation — `H4.C.3` / `H4.L.12` same-placement double-fire  ✅ RESOLVED 2026-06-25
Surfaced during the B6.2 audit: the H4 `property` verdict (which aggregates the `property` and
`mother_home` rule_tags, significations.py:251) has TWO evaluable rules firing on the single
`LordIn(4,12)` placement — `H4.C.3` (sig `property`, HTJAH-I:4208) and `H4.L.12` (sig
`mother_home`, HTJAH-I:4187). They are two distinct corpus lines that happen to overlap on one
placement; the codebase elsewhere prevents this by making the overlapping rule `descriptive`
(cf. H4.C.30, H7.C.67's note). Whether this is a true double-count to collapse, or an acceptable
two-testimony overlap, is a verdict-affecting judgment for the user — deferred (it can move H4
`property` goldens; needs its own regression analysis + sign-off).
**Measured 2026-06-25:** making `H4.C.3` descriptive is **zero golden regression** — the
double-count is currently *inert* (no golden verdict depends on it), confirmed by running the
full harness with H4.C.3 disabled (only the B6.2 coverage assertion changed; all goldens held,
TrackB=131). So there is no ratchet cost or benefit today; the decision is purely the design call
above (combos-stack-on-bridge vs the H7 "no re-score" policy). Recommendation: align with the H7
policy (make `H4.C.3` descriptive, citation preserved) *before* Phase-3 adds H4-property goldens,
so the inflation can't bake a wrong verdict into a new golden.
**Applied 2026-06-25 (user-delegated):** `H4.C.3` is now `kind="descriptive"` (citation preserved,
ownership note added) — EVERY arm of its Or is already scored into `property` by the mother_home
bridge (H4.L.6/8/12, H4.P.Mars/Saturn), so the property-loss testimony survives via the bridge while
the double-count is removed. Zero golden regression (ratchet held 99/139, no snapshot drift — the
double-count was inert at the evidence level too). The B6.2 coverage test was updated to assert the
property loss flows through H4.L.12 and that H4.C.3 no longer fires.

## B7 — Reconcile the Venus/Saturn combustion doctrine  `threshold`  ✅ RESOLVED 2026-06-15
**Settled:** removed the non-Raman 0.85 Venus/Saturn exemption; `_combust_graded` now uses one
0.5 half-combust bar for all planets, matching H3.C.39. Zero golden regression (the exemption
only affected the karaka-intact triple-veto, and no golden sits in the 0.5–0.85 band with the
combined debil+maraka condition). Chart 59's powerless 0.79 Venus (HTJAH-I:3788) is the warrant.
Below is the original analysis, kept for provenance.

### (original)
**Origin.** bphs-doctrine-reviewer flag on H3.C.39 (Phase-2a). The engine carries TWO
Venus-combustion thresholds: `_combust_graded` uses 0.85 for Venus/Saturn (a NOVEL heuristic
explicitly "NOT cited to Raman", wired only into the `_karaka_intact` triple-veto), while
H3.C.39's `_ThirdLordSubstantiallyCombust` uses a flat 0.5. Chart_59's Venus is 0.79 — Raman
calls it "powerless" (HTJAH-I:3788), so the 0.5 bar is the more faithful one.
**Status.** No runtime collision (separate paths). But the project should pick ONE
Venus-combustion doctrine. Decision is the user's (it touches the karaka-intact veto, which
has its own blast radius): keep both (documented), lower the `_combust_graded` Venus/Saturn
exemption toward Raman's reading, or unify on a single combustion model. Deferred pending
user sign-off; H3.C.39 ships as-is (faithful, zero-regression).

## Golden expansion  `golden`  (Phase 3)
**Assessed 2026-06-25 (Item 3).** The fixture already holds **131 CONFIRMED** verdicts (the
ratchet) **+ 34 DRAFT verdicts awaiting user validation** — so the nearest Phase-3 lever is
VALIDATING the existing DRAFTs, not mining new charts. Worksheet:
`docs/raman_saab/worksheets/PHASE3_draft_validation.md`. Breakdown:
- **Ready to confirm (10)** — the engine already matches the recorded DRAFT verdict, so
  confirming the ones the user validates moves the ratchet 90/130 → up to 100/140:
  h7_01, h7_06, h7_12, h7_13, h7_14, h9_01, h12_14, h6_02, h6_05 (+ h12_13, currently HELD).
- **H8 death/longevity** — **DEATH MANNER OPENED 2026-06-25** (user-directed "do H8 like the other
  houses"). The death *manner* is read directly from the 8th-house affliction apparatus, like any
  dusthana house — NOT a Phase-E subsystem. Two-part judge change: narrowed `LONGEVITY_GUARD` to the
  `longevity` SPAN sig only; flagged `death` as an `AFFLICTION_MATTER` (a fired malefic on the 8th
  confirms the affliction; pillar strength can't rescue death — mirrors H6/H12). bphs-doctrine-reviewer
  VALIDATED (HIGH; HTJAH-II combos #1-2, Phaladeepika Ch.14). **5 death goldens confirmed = afflicted**
  (chart_73 Lincoln, chart_74 Gandhi, chart_75 JFK, chart_78 Hitler, chart_35 Poornayu-natural-via-maraka)
  → ratchet +5, H8 now 5/5. **Only the 2 LONGEVITY-SPAN charts remain** (`chart_33` Pindayu 86y,
  `chart_34` Amsayu 70y) — left DRAFT: the numeric span genuinely needs the ayurdaya engine (reviewer
  INSUFFICIENT-EVIDENCE; 8th-strength ≠ span class, proven by in-corpus charts 59/61). That span build
  is the one true Phase-E remnant below.
- **Engine mismatch (17)** — **VALIDATED 2026-06-25** against Raman's text: every recorded DRAFT
  verdict is CORRECT, the engine misses each, so NONE is confirmable (no wrong-DRAFT quick wins).
  Split: **10 over-lenient** (engine favourable/mixed where Raman afflicted/mixed — esp. the
  coverture/vaidhavya spouse-death charts h7_09/10/11 the V2 favour-preponderance over-lifts) +
  **7 over-harsh** (engine afflicted where Raman mixed — "unconventional but not ruined" marriages
  h7_17/18/19 the nodal/decisive affliction over-reads). This is the precise B2/B3/B4 + H5
  calibration spec (per-chart reasoning in `worksheets/PHASE3_draft_validation.md` §C). Each needs
  a faithful, cited, doctrine-reviewed, zero-regression increment — not a bulk pass.
- New-chart mining (HTJAH-I/II early chapters, full birth lines) via the existing
  DRAFT→worksheet→CONFIRMED pipeline remains available once the DRAFT backlog is cleared.
- **Notable Horoscopes** is only 2 of ~50 chapters present — an *acquisition* gap; the full
  edition would add ~48 fully-worked goldens. Flag for the user to source.

## Phase E — longevity SPAN engine  `shadbala`/`new-mechanism`  (narrowed 2026-06-25)
**Update:** the H8 death *manner* is now judged like any house (5/5 confirmed) — Phase E is no longer
needed for the death house in general, **only for the numeric life-SPAN** (`chart_33` Pindayu 86y,
`chart_34` Amsayu 70y, still DRAFT). The `longevity` sig keeps deferring. Remaining scope for the span: 
- **Already present** (partial infra to build on): `app/raman_saab/primitives/balarishta.py`
  (infant-mortality / early-death yogas), the `house_08_ayur/` rule sets (combinations, lord_in_12,
  planets_in_8th), and the maraka flags in the judge (`maraka_active`, `LONGEVITY_GUARD`).
- **Missing** (the build): (1) the classical **ayurdaya span computation** — Pindayu / Amsayu /
  Nisargayu year-counts with the haranas (Chakrapatha, Krurodaya, etc.) → the alpa/madhya/purna
  span class; (2) **maraka-dasha death-timing** — selecting the killing Dasa/Bhukti from the 2nd/7th
  lords + Saturn + the assembled marakas; (3) a verdict path that, once the span class is fixed,
  releases the `LONGEVITY_GUARD` to emit a real death/longevity verdict.
- **Death-timing branch relationship:** `feat/death-timing-predictor` / `data/vedastro-corpus` built
  an **empirical** longevity model (MortalityModel ECDF, alpa/madhya/purna *brackets* by age,
  composite×bracket risk) — it shares the bracket taxonomy and the maraka/significator concepts but
  is **statistical, not classical ayurdaya**. So it is a strong *reference* (bracket boundaries, the
  maraka head-to-head results, the Saturn-transit trigger) and a candidate to wrap as a secondary
  empirical lever, but the classical span computation must be built natively. **Major effort** — its
  own phase, not a single increment.

## Documented limits register  (confirmed misses the engine cannot faithfully reach today)
These are CONFIRMED goldens the engine misses; each is a deliberate limit, not a bug to hack:
- **chart_60** — H3 siblings *afflicted*, engine *favourable*. The lord (Jupiter) is well-disposed but
  the house + karaka are afflicted (HTJAH-I:3815, "no brothers"); the preponderance favours the good
  lord. The B1 three-factor comparative-weighing case — a faithful fix needs the general B1 mechanism
  and risks regressing chart_54 (also malefic-aspected 3rd that KEEPS brothers on a strong lord).
- **chart_52** — H3 siblings *mixed*, engine *favourable*. House good but lord Moon weak (6 born, 3
  died); contestable "favourable/mixed" golden (confidence 0.45). Same B1 comparative-weighing family.
- **chart_08** — H7 marital_happiness *favourable*, engine *afflicted*. Over-harsh: a separation/besiege
  rule fires, but Raman reads it favourable; the blemishless-Venus floor correctly does NOT rescue it
  (its Venus has Mars on it → not blemishless). Softening the decisive rule risks regression.
- **h12_13 / h5_14** — HELD DRAFTs (engine matches but deliberately not confirmed pending a fresh call).
- **chart_17** — H1 self *favourable*, engine *afflicted* (dist 2). ADDED 2026-08-22; this and
  chart_31 were the only two current dist-2 misses with NO prior register entry. Diagnosed, not
  guessed: the deciding frame is the **MOON** frame (lagna is the alternate), and in it all three
  pillars are strong (lord Jupiter strong, karaka Sun strong, bhava-bala strong, lord NOT
  hard-afflicted) with fired evidence **benefic-dominant 5:2**. No decisive-affliction rule fires;
  the arishta yoga drop correctly does NOT apply (its `not (fired_benefic and fired_malefic)`
  guard blocks it — both polarities fired). The verdict is `borderline_shifted=True` with
  **`navamsa_status='weakens'` and no yoga metadata**, so a borderline mixed was dropped to
  afflicted by the **D9 navamsa modulation** — against benefic-dominant rasi evidence and three
  strong pillars. Raman's prose is favourable-with-worry ("self-reliant, endurance and energy;
  high distinction in the legal line" — the negatives he names, "not happy regarding children",
  are H5 matters, not H1). Whether a navamsa drop should be able to outvote a benefic-dominant,
  all-pillars-strong rasi ledger is a real doctrinal question and NOT attempted here.
- **chart_31** — H1 self *afflicted*, engine *favourable* (dist 2). ADDED 2026-08-22. The mirror
  of chart_17 and why no single directional fix serves both: lagna frame, all three pillars
  strong, evidence an even 2:2, `navamsa_status='neutral'`, `borderline_shifted=False` — the
  engine reaches favourable by ordinary preponderance with nothing anomalous in the machinery.
  Raman reads afflicted on "lack of happiness" (stated twice) despite granting good build, honesty
  and a "clear quick mind". This is the `self`-as-wellbeing vs `self`-as-body/character boundary;
  the engine reads the latter. Likely not mechanically separable without an outcome layer.
The B1 comparative-weighing mechanism (backlog B1) is the single lever that would address chart_52 +
chart_60; it is high-risk (med) and was deliberately narrowed into the H3.C.39 combust-lord rule rather
than attempted wholesale. Deferred pending a careful, chart_54-guarded design.

---

## Layer-C cited-fix sweep (2026-06-25) — shipped + documented limits

The faithfulness program (graded `degree` + within-1 ordinal metric + cited fixes) reached its clean
ceiling. **Shipped (+4, all on GENERAL dicta, user-validated, doctrine-reviewed, over-fire-scanned):**

| Rule | Fixes | Cited dictum | Pattern |
|---|---|---|---|
| H9.A.20a | h9_13 | HTJAH-II:7916 "afflictions to the Sun → early death of father" | Sun-Pitrukaraka dusthana + papakartari (decisive) |
| H5.C.38 | h5_01, h5_07 | HTJAH-I:5619 "Jupiter… Papakarthari + malefic Rashi → blemished" | PutraKaraka papakartari + malefic-rashi (decisive) |
| H4.C.18a | h4_01 | HTJAH-I:4224 "Moon in 4th joined by evil planets → kills mother early" | Moon-Matrukaraka in 4th conjunct-malefic (decisive) |

Ratchet: **106/146 → 110/146 exact (0.753); 126/146 → 130/146 within-1 ordinal (0.890).**

**Documented limits — the irreducible real-error tail (do NOT force; each would overfit).**
The shipped fixes all rested on a GENERAL Raman dictum. The remainder do not — they are n=1
chart-conclusion-only readings or comparative-weighing/over-harsh cases where the favourable twin carries
MORE surface affliction. Forcing them violates the main goal (faithful, not golden-tuned):

- **chart_60 (H3 siblings), chart_52** — comparative-weighing limit. The favourable twin `chart_54` has 5
  malefics on/aspecting the 3rd (vs chart_60's 2); any "3rd/karaka afflicted" signature over-fires on
  chart_54. Only a chart_54-guarded narrow aspect-rule could help; deferred (backlog B1).
- **h12_05 (H12 expenditure)** — n=1, cite HTJAH-II:17170 is Chart-243's HEADER (no general dictum). The
  only discriminator vs the favourable twin `h12_03` (also 12th-lord-conjunct-node, Venus+Ketu) is the
  lord's nature (malefic Saturn vs benefic Venus) — an empirically-found twin-sparing gate = overfit risk.
- **h6_04 (H6 disease_chronic / eye)** — n=1, cite HTJAH-I:6664 is Chart-130's myopia CONCLUSION (6th lord
  in 2nd + 2nd-lord Moon in 12th with Saturn). Encoding this multi-factor configuration memorises one chart.
- **h11_01 (H11 elder_siblings)** — n=1, cite HTJAH-II:14804 is the Chart-210 CONCLUSION; a debilitated
  11th lord + aspect-affliction with no general dictum.
- **h11_09 (H11 gains, over-harsh fav→afflicted)** — the engine over-weights an afflicted karaka (Jupiter in
  dusthana + conj Ketu) and under-weights a strong 2nd/7th/9th/11th-lords-in-kendra dhana-yoga. Fixing needs
  a yoga-relief that risks regressing genuinely-afflicted gains; deferred.
- **h5_05 / h5_12 (H5 children)** — FIXED 2026-06-25 (Phase-2). The `_fertility_gate` one-weak-sphuta
  refinement denies on a corroborating affliction: Arm A (>=2 malefic 5th-rules = "5th house spoilt",
  h5_12) or Arm B (weak karaka pillar + Jupiter malefic-afflicted = "baneful PutraKaraka", h5_05). +2,
  zero over-fire; spares h5_16 via the `karaka_strong is False` AND. bphs-doctrine-reviewer SOUND.
- **h5_10 (H5 children)** — STILL a limit. Raman: "the lord is weak and the Karaka powerless"
  (HTJAH-I:5804), but the engine reads ALL pillars strong + 0 malefic rules — a pillar-layer strength
  DISAGREEMENT, not a gate gap. The gate must not invent an affliction the engine cannot see. Revisit only
  if the Shadbala/dignity strength reads are reconciled.
- **h5_16 / chart_08 (over-harsh fav→engine-afflicted)** — softening these un-afflicts genuine cases or
  needs the forbidden navamsa/CONTRA_PILLAR retune. Documented limits. (The Phase-2 gate explicitly SPARES
  h5_16 — does not make it worse.)
- **chart_09/17/20/31 (H1 self)** — holistic whole-chart prose with no single cited combination.
- **h9_02 (H9 father)** — INVESTIGATED + confirmed limit 2026-06-26. The clean candidate "Sun-in-9th +
  9th-house papakartari (malefics in 8th & 10th)" does NOT fire (9th-house is not hemmed that way); the
  affliction is Raman's COMPOUND "papakartari to 9th house/lord/karaka PLUS karaka-in-house" reading
  (HTJAH-II:7929) that no single predicate reproduces. 3 malefic father-rules already fire but strong
  pillars (exalted Sun, vargottama Jupiter, Mars in own kendra) override — a confluence case, not a
  missed cited rule.
- **chart_44 (H2 wealth)** — INVESTIGATED + confirmed limit 2026-06-26. The 2nd lord IS papakartari'd,
  but the over-fire scan shows "2nd-lord-papakartari" fires on chart_40/41/46 — all FAVOURABLE wealth
  twins. chart_44's poverty is the compound confluence (Dwirdwadasa from the Moon + Sun aspected by
  Saturn + 2nd-lord-with-malefic-turned-Venus + papakartari TOGETHER, HTJAH-I:2827-2848); the single
  papakartari signature over-fires on 3 favourable charts.

**Honest ceiling: ~77% exact / ~90% within-1 (114/148, 134/148 at 2026-06-26; the AYURDAYA longevity engine resolved the chart_33/34 span goldens); the within-1 figure is the
fairer headline and is at the projected ordinal ceiling.** The 20 distance-1 boundary near-hits are
subjective favourable-vs-mixed calls (handled by the graded `degree`), not errors. The two most-promising
remaining over-lenient cases (h9_02, chart_44) were empirically re-tested and both confirm as limits —
every faithful general-dictum / 2+-chart mechanism has been mined. Further rule-grinding overfits.

---

## H7-marriage (+H5) DRAFT backlog — validated 2026-06-26, awaiting engine work

bphs-doctrine-reviewer adjudicated all 16 remaining non-empty DRAFT goldens against Raman's
TEXT. **All 16 DRAFT labels are correct per Raman.** Progress: h12_13 (engine-match) CONFIRMED;
**h7_02 / h7_05 / h7_15 FIXED + CONFIRMED 2026-06-26** via the decisive **H7.C.86** (afflicted
7th lord -> vitiated spouse) — the 3 HIGH-confidence mode-B reversals. **12 validated DRAFTs
remain** (the mode-A benefic-relief lift + the residual mode-B 8th-marital-bond rule), kept DRAFT
per the project pattern (confirm engine-matches; DRAFT-until-fixed for mismatches). Confirming the
remaining 12 now would re-base the ratchet DOWN for zero engine benefit; BUILD the mechanisms,
then confirm.

**Two engine failure modes (the agent's diagnosis):**

**(A) Over-weights affliction, ignores Raman's stated benefic RELIEF -> engine wrongly `afflicted`
(correct = `mixed`):**
| golden | sig | Raman (correct) | engine | the relief the engine drops | conf |
|---|---|---|---|---|---|
| h5_13 | children | mixed | afflicted | "birth of children is not denied" (Jupiter unafflicted) HTJAH-I:5876 | HIGH |
| h5_14 | children | mixed | afflicted | "5th house is fairly well disposed" HTJAH-I:5889 | HIGH |
| h7_03 | marital_happiness | mixed | afflicted | "rule out... separation or divorce" (Venus+Jupiter) HTJAH-II:1818 | HIGH |
| h7_07 | coverture | mixed | afflicted | remarriage after the first husband's death HTJAH-II:1996 | MED |
| h7_17 | spouse | mixed | afflicted | realized (inter-faith) marriage, not destroyed HTJAH-II:2726 | MED |
| h7_18 | spouse | mixed | afflicted | "Jupiter... on karaka and 7th lord Venus" HTJAH-II:2768 | MED |

**(B) Over-weights a clean 7th-lord, misses the heavily-afflicted 8th / marital-bond / Navamsa ->
engine wrongly `favourable` (correct = `mixed`/`afflicted`):**
| golden | sig | Raman (correct) | engine | what the engine misses | conf |
|---|---|---|---|---|---|
| h7_02 | spouse | afflicted | favourable | both 7th-lords afflicted by Rahu; immoral spouse HTJAH-II:1773 | HIGH |
| h7_05 | spouse | afflicted | favourable | two wives; clandestine marriage; wife left HTJAH-II:1906 | HIGH |
| h7_15 | spouse | afflicted | favourable | 7th-lord+Venus much afflicted; profligate, VD HTJAH-II:2528 | HIGH |
| h7_04 | marital_happiness | mixed | favourable | "domestic bickerings" (Rahu-7th, Mars-Venus) HTJAH-II:1864 | MED |
| ~~h7_16~~ | spouse | mixed | ~~favourable~~ **FIXED** | 8th-from-Moon afflicted -- _marital_bond_gate 2026-06-26 | MED |
| ~~h7_19~~ | spouse | mixed | ~~favourable~~ **FIXED** | 8th-from-Moon afflicted -- _marital_bond_gate | MED |

**Also:** h5_15 (children, favourable — engine `mixed`, the single child-death over-weighted) and
h5_18 (children, mixed — engine `favourable`, "spoiling of the 5th house" missed).

**Status (2026-06-26): 5 of 15 fixed** (h7_02/05/15 via H7.C.86; h7_16/19 via the marital-bond gate).
**10 remain** — all MODE-A `afflicted`-should-be-`mixed` benefic-relief misses (h5_13/14, h7_03/07/17/18),
plus h7_04 (the lone weak mode-B, 1 malefic in 8th-from-Moon), h5_15/h5_18, and h7_11 (coverture).

### Mode-A path (diagnosed 2026-06-26) — a benefic-RELIEF LIFT (afflicted -> mixed), regression-aware
The mode-A reliefs are heterogeneous and the fix touches rules already shipped, so it needs careful,
dedicated work (NOT a tail-of-session rush). Per-target why-afflicted:
- **h5_13** (children): reads afflicted via the **fertility-gate Arm A (>=2 malefics)** I shipped — but
  Raman = mixed ("birth not denied", Jupiter unafflicted). **Arm A over-fires here** (the H5 over-fire
  scan only checked CONFIRMED goldens; h5_13 was DRAFT). FIX: gate Arm A with "karaka Jupiter NOT clean"
  (a clean/unafflicted karaka -> the affliction is tempered to mixed, not denied). Must NOT regress h5_12
  (Jupiter afflicted there -> stays afflicted). Verify h5_12/06/07 unchanged.
- **h5_14** (children): fertility-gate (nben=3, nmal=1) -> afflicted; Raman mixed ("5th house fairly well
  disposed"). Same karaka/bhava-relief family as h5_13.
- **h7_03** (marital_happiness): 1 malefic, 0 benefic-RULE -> afflicted; Raman = mixed ("Venus+Jupiter
  rule out separation"). The relief is a benefic INFLUENCE not captured as a rule -> needs a marital
  benefic-relief detector (unafflicted Jupiter/Venus on the 7th house/lord/karaka -> lift afflicted->mixed).
- **h7_07** (coverture): 4 malefics -> afflicted; Raman mixed (remarriage after the spouse's death) -- a
  recovery signature, harder; possibly leave as a documented near-hit.
- **h7_17 / h7_18** (spouse): the "unconventional-but-realized inter-faith marriage" pair -- afflicted
  configuration but a realized marriage; the inverse of the marital-bond demote (lift afflicted->mixed
  when the 7th LORD is clean and the marriage is realized). h7_18 reads afflicted with nmal=0/nben=0
  (investigate the source -- navamsa/maraka).
All are dist-1 near-hits (already within-1).

### Mode-A is a DOCUMENTED LIMIT — empirically proven not mechanically separable (2026-06-26)
A benefic-relief lift was BUILT AND TESTED (a blemishless Jupiter/Venus on the 5th/7th house, lord, or
karaka -> lift afflicted->mixed). It does NOT discriminate, in BOTH families:
- **Children:** h5_13 (mixed) has NO detectable benefic-on-5th relief, while h5_04/h5_08/h5_09 (all
  AFFLICTED) DO. The real mixed-vs-afflicted axis is child SURVIVAL ("born and lived" h5_13 vs "born and
  died" h5_04/08/09) -- an outcome the natal config cannot express.
- **Marriage:** h7_17/h7_18 (mixed) have a Jupiter relief, but so do chart_09, h7_02, h7_05 (all
  AFFLICTED -- and h7_02/h7_05 were JUST confirmed afflicted via H7.C.86). A relief lift would REGRESS
  those shipped fixes. h7_03 (mixed) has no detectable relief at all. The axis is marriage REALIZED-but-
  flawed (mixed) vs DESTROYED/immoral (afflicted) -- again an outcome, not a separable natal predicate.
CONCLUSION: the 10 mode-A items are the subjective afflicted-vs-mixed boundary the within-1 ordinal
metric was built to honor (all dist-1 near-hits). Forcing a relief mechanism over-fires on genuinely-
afflicted charts and regresses the H5/H7 afflicted fixes. LEFT as within-1 limits; do NOT pursue a
relief lift. (If ever fixed, it would need a Dasa/outcome layer the rule-engine deliberately excludes.)

**Engine work implied (future):** (1) a marital benefic-RELIEF mechanism that lifts an afflicted
spouse/marital verdict to `mixed` when Raman's named reliefs are present (no separation/divorce,
remarriage, benefic on the karaka) — complements the existing blemishless-Venus floor; (2) an
8th-house / Navamsa MARITAL-BOND affliction rule so a clean 7th-lord with a heavily-afflicted 8th
reads `mixed`/`afflicted`, not `favourable` (the h7_02/05/15 hard reversals are the priority — a
profligate-with-VD spouse must not read favourable). The three HIGH-confidence reversals
(h7_02/05/15) are the cleanest fix targets. The four "Unconventional Marriages" charts
(h7_16/17/18/19) are MEDIUM (afflicted-but-realized marriage = mixed) — tighten the spouse rubric
first.

---

## Dasha / outcome-timing layer (2026-06-26) — built + documented limits

The Vimshottari timing layer (vimshottari.py: maraka_set, death_window, significator_dasha_windows;
wired metadata-only via house_template._event_timing; rendered via the re-routed proforma) is ADDITIVE
and validated (death-Mahadasha matches Raman on all 5 dated deaths; the death falls in a maraka period
all 5). Honest limits, NOT to be force-fixed:

- **Strongest-maraka / single-date prediction** — the death's Mahadasha is reliably a maraka, but WHICH
  of the (broad) maraka set actually strikes — and the to-the-day date — is the chart-specific
  "strongest-maraka + Saturn-transit final-signal" judgement Raman makes by hand (chart_35 invokes a
  Saturn transit). The engine returns a RANKED WINDOW SET, never a date. `death_window` predicts the
  natural-death (alloted-span) region; premature/violent deaths (Lincoln 56, JFK 46) strike a strong
  EARLIER maraka well below the ayurdaya span and are not isolated.
- **General event-timing — RESOLVED 2026-06-26** (was: partial). A critical audit found the layer was
  death-biased (death 12/12; non-death ~10-29%). FIXED by `vimshottari.timer_set(chart, house)` — Raman's
  universal "Time of Fructification" significator set (H-lord + H-karaka + occupants + aspecters +
  H-lord-aspecters/conjuncts + H-lord-from-Moon + node-via-dispositor), wired into `_event_timing` for
  EVERY matter. Non-death event-MD recognition: **12/13 (92%)** across gains/career/acquisition/travel.
  Remaining edge: **h10_05 Napoleon (Rahu)** — needs the deeper Kujavad-Ketu *constellation-chaining*
  (Rahu in Ketu's star -> Ketu gives Mars' results -> Mars+Sun = empire); the engine adds a node by its
  sign-DISPOSITOR but not yet by its CONSTELLATION-lord chain. Future lift, low priority.
- **Birth-time sensitivity** — a Bhukti boundary shifts months per few minutes of birth error: the
  Mahadasha claim is robust (all 5 deaths), the Bhukti only for precisely-timed births (Lincoln/Hitler
  exact). Hence the layer reports a window, not a date.
- **Timing ANNOTATES, never resolves** the mode-A outcome ambiguity (born-and-lived vs born-and-died):
  the natal verdict is unchanged; timing only adds "when the significators/marakas are active".

## ASP ch.XV + ch.XVI mining record (2026-08-03) — so no future session re-mines blind

**ch.XVI (Illustrated Horoscopes) — CLOSED, whole-pipeline validated on 9 nativities, 63/63
printed Sodya Pindas exact.** The preamble states Illustrated No. 1's Sun Ashtakavarga cell-by-
cell, raw AND reduced (ASP-16:40-51): raw checksums to 48 and ALL SIX printed reduced cells
reproduce under `trikona_shodhana` exactly. Vision-re-extracted (PDF pp.84-87) all 12 remaining
nativities' printed longitudes + Sodya Pindas; ran the full pipeline (BAV -> Trikona ->
Ekadhipatya -> Rasi+Graha Gunakara -> Sodya Pinda) against each. Result (`test_asp_illustrated.py`):
- **9 nativities, 63 pindas, EXACT**: "An Eminent Indian", Roosevelt, Marx, Havelock Ellis,
  Sankaracharya of Govardhan Mutt, Wodiyar, Nehru, Mussolini, Narasimha Bharathi. This
  definitively settles the earlier ASP-14 Standard-Horoscope delta (Sun 182 printed vs 191
  computed): the rules are right, that one printed table was a hand-computation slip.
- **Windsor and Golwalkar, 6/7 exact, Venus off by +3 and +10 respectively** — re-verified
  2026-08-03 against a clean, fully-legible re-scan (positions cross-checked self-consistent via
  the printed table's own Rasi+Graha=Sodya arithmetic). Same deltas both times the chart was
  read independently -> CONFIRMED as isolated Venus-cell slips in Raman's own printed tables,
  the same error class as ASP-14, not a transcription or engine defect. Not encoded as exact
  fixtures (only 7/7 matches are); recorded here as closed with a known, bounded, reproducible
  delta.
- **Ford, 0/7 total mismatch — genuinely OPEN, re-classified.** Originally suspected as an OCR/
  vision transcription failure. Re-read on a clean scan (Sun 106°34', Moon 209°12', Mars
  127°35', Mercury 102°32', Jupiter 179°56', Venus 151°44', Saturn 160°32', Rahu 223°5', Asc
  211°52', ayanamsa 20°30' — ASP-16, book p.163) gave IDENTICAL positions to the first read, and
  the resulting raw Bhinnashtakavarga totals check out EXACTLY against the canonical checksums
  (Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39) — so the positions and
  the engine's raw-BAV stage are provably correct for this chart. The divergence therefore
  enters somewhere in Raman's own reduction (Trikona/Ekadhipatya) or Gunakara arithmetic for
  this one nativity, compounding across all 7 planets rather than one isolated cell — unlike
  every other slip found in this book, which was always a single planet. Not pursued further
  (no clean cited-fix pattern, per B1's precedent for not reverse-engineering a book's own
  errors); flagged for the golden track separately, since Ford may overlap an existing NH
  golden and any cross-check there should go through that discipline, not this one.

**ch.XV (Miscellaneous), classified per the content-scope rule (a live tag does not admit
out-of-scope content — the AFB-horary precedent):**
- Rules 1-22 (ASP-15:21-183): ELECTIONAL — choosing times/directions for journeys, marriage,
  studies, factories, conception via Sun/Moon/Mercury/Venus bindu-transits. (Corrected
  2026-08-03 from "1-19 / :21-168": rules 20-22 — Saturn-direction siting, least-SAV-rising
  treatment timing, >30-bindu-SAV-rising elections — are electional too.) Category (b),
  MUHURTHA firewall — deliberately NOT encoded at mining time; RELEASED to the electional
  subsystem by the same-day firewall lift (next record).
- Rahu Ashtakavarga (ASP-15:~240-260): Raman presents a variant Rahu AV with bindus, while
  noting "no Kakshya has been assigned to him". The first-edition preface says such
  controversial matters (Rahu/Lagna AVs) were deliberately avoided in the main exposition;
  the repo's 7-graha chayagraha lock stands. NOT encoded — recorded as a Raman-presented
  variant, not Raman doctrine.
- Rahu's 12-places-from-Moon transit results (ASP-15:263-271): benefic at (3), (6), (11) —
  CORROBORATES transits.py's existing Rahu Gochara set {3,6,11} exactly. No change needed;
  noted as an ASP confirmation of the encoded table.

## PRASNA + MUHURTHA firewall LIFT (2026-08-03) — user decision, binding scope rules

**Decision.** The user (via AskUserQuestion, 2026-08-03) explicitly chose to lift the horary
(PRASNA) and electional (MUHURTHA) divergence firewalls, alongside approving a report-only
medical read-out section. JAIMINI and VARSHA remain firewalled; Prasna Marga vols remain
unregistered. This overturns the "strictly Parashari-natal" project scope deliberately and
on the record — do not silently revert, and do not silently widen further.

**Standing scope rules (binding on all future sessions):**
1. Horary and electional are SEPARATE SUBSYSTEMS — `app/raman_saab/horary/` and
   `app/raman_saab/electional/`. They may import natal primitives; natal verdict code
   (judges, proforma, house_template, synthesis feeding verdicts) must NEVER import them.
   This extends the VERDICT-AUTHORITY invariant: the natal ratchet is untouchable by
   anything these subsystems compute.
2. The lift releases the content-scope quarantine on horary/electional chapters inside
   LIVE books — HPA-27 (Prasna Sastra), AFB-11 (horary), ASP-15 rules 1-22 — FOR THOSE
   SUBSYSTEMS ONLY. Natal rules still never cite them (the AFB-horary precedent stands
   for natal scope).
3. Subsystem outputs carry the Measured-Truth framing: "what Raman's method says", never a
   validated prediction. The horary judge excludes death/lifespan/serious-illness/self-harm
   queries IN CODE (the /ai-interpret precedent).
4. Doctrine-first still governs: every rule cites `PRASNA-<ch>:<line>` / `MUHURTHA-<ch>:<line>`
   verbatim; where Raman's text omits a technique the pasted plan wished for, the technique
   is NOT encoded (measured example: "Tyajyam" does not appear in the ingested Muhurtha text).

**Corpus actions taken (same day).** `muhurtha_raman` ingested for the FIRST time (its dir
had been empty since registration — the registered archive item `bwb_P9-EAH-659` is
access-restricted/401; the ETL entry was repointed to the open DLI scan
`in.ernet.dli.2015.128092`; 16 chapters, gaps in chapter numbering are OCR heading artifacts).
`prasna_tantra_raman` re-ingested COMPLETE from its existing identifier (the old ETL filename
had a spacing mismatch — "B. V. Raman" vs the served "B.V.Raman" — which is why only 5
partial chapters ever landed; the same 5 chapter files now carry the full text; the odd
`chapter_049` label is an OCR-artifact heading for the main Bhava-Prasna body and is
cosmetically wrong but citation-stable). Zero pre-existing citations targeted either tag
(grep-verified), so no line numbers shifted under anyone. Both registry entries flipped to
`live` with provenance comments.

**Citable anchors located (for the build phases):** Tajika yoga definitions
PRASNA-4:1068-1330 (Ithasala incl. Muthaseela + Vartamana/complete grades, Easarapha,
Naktha, Yamaya, Kamboola incl. quality grades); Deeptamsa orb table PRASNA-2:258-270
(Sun 15, Moon 12, Mars 7(8?—verify at encode time vs print), Mercury 7, Jupiter 9, Venus 7,
Saturn 9; aspects themselves have no orb); significator scheme (lagna lord = querent,
karyesa = house lord) PRASNA-2/49. Muhurtha: Tarabala/Chandrabala ~MUHURTHA-2 (raw ~881-1063),
Raja/Agni/Chora Panchaka (raw ~944-1037), Rahu Kalam weekday table (raw ~7318 — locate
post-split chapter at encode time), Durmuhurtha (index -> pp.31-32).

**Known dependency, decision PARKED for Phase 3:** Saham FORMULAS are not in Prasna Tantra —
Raman himself defers Tajika machinery to his Varshaphal (PRASNA-2:288-291), and the formula
table (Punya/Guru/Kirti/Mitra/Raja... with day/night variants and the +30° no-lagna-between
rule) sits in `varshaphal_raman` ch.7 — still firewalled. Encoding sahams therefore requires
EITHER a separate user decision to lift VARSHA (scoped to the saham/yoga-definition
chapters) OR leaving sahams out of the horary package. Punyasaham APPLICATION rules
(PRASNA-3, PRASNA-49) are citable either way. ASK THE USER AT PHASE 3, not before.

**RESOLVED same day — VARSHA LIFTED (user decision via AskUserQuestion, 2026-08-03,
Phase 3).** `varshaphal_raman` flipped to `live` with the same walled-subsystem scope.
JAIMINI is now the ONLY firewalled book. Phase 3 built `app/raman_saab/horary/`:
- `tajika_aspects.py` — the printed Deeptamsa table (PRASNA-2:262-264), the speed order
  (PRASNA-4:1085-1088), Ithasala/Poorna (stanzas 54-55), Easarapha (56), Naktha (57),
  Yamaya (60), Kamboola (61). **Orb rule = the SMALLER of the two deeptamsas** — fixed by
  VARSHA-7:43-47's own micro-example ("Guru's 9 and Sukra's 7 -> within 7 degrees"), since
  PRASNA-4's worked figure is OCR-damaged at the digit. Applying/separating resolved in the
  directed separation space (sep = slower−faster mod 360, strictly decreasing).
- `sahams.py` — the TEN sahams Raman prints (VARSHA-7:84-171) with day/night swaps, the
  +30 no-lagna-between rule, saham lords (VARSHA-7:190-192), and the worked Punya
  arithmetic (105°21'+285°9'=30°30') pinned. "Vidya"/"Karya" sahams (the pasted plan's
  wish-list) are NOT in Raman's table -> NOT encoded. Mitra's printed formula adds VENUS in
  place of the lagna term (encoded exactly); its Night line is OCR-mangled and the
  every-other-saham day/night-swap pattern is applied — recorded, not silently corrected.
- `prasna_judge.py` — Karyasiddhi: the four full-success configurations (PRASNA-49:107-116),
  Karyesa = query-house lord (:119-126), the 25/50/75/100% ladder (:137-190). Planet-planet
  checks use tajika orbs; planet-HOUSE checks are sign-granular (the book's charts are rasi
  diagrams). Death/lifespan/serious-illness/self-harm topics REFUSED IN CODE. Every verdict
  carries the Measured-Truth disclaimer.
Source-lock re-locked add-only (3 PRASNA chapters + VARSHA-7). Walled both directions by
test. HPA-27/AFB-11 remain citable-but-uncited (no rule needs them yet).

## JAIMINI lift (2026-08-04) — the last firewall falls

User decision (AskUserQuestion, the karmic-evolution chapter, items 6-16 arc):
`studies_jaimini_raman` flips live for a WALLED karmic-evolution layer — the same pattern
as PRASNA/MUHURTHA/VARSHA. **No book remains firewalled.** What the firewall used to
enforce is now carried entirely by the content-scope rule + the walled-subsystem import
tests: natal verdict code imports none of the lifted layers; the 2026-07-24 merge
re-lock's concern (Jaimini doctrine leaking into natal verdicts) remains enforced — the
soul layer's free-text Jaimini references may now also resolve as real citations, but
NOTHING in the verdict path may cite JAIMINI. Corpus re-ingested complete (the ETL
filename mismatch fixed — the prasna precedent); karakamsa combinations live in JAIMINI-9.

## Coherence audit + interpretation guide (2026-08-03) — report v18/v19

User concern: "many sections saying the same things — how to interpret when taking features
or output of the engine." A full coherence audit (agent-run, results verified) mapped the
38 contract sections into 8 clusters and found the report already states precedence in
ELEVEN places — but only locally, inside the section that yields; nothing collected them.
Exactly ONE overlapping pair had no shipped statement: dashboard vs house-by-house (the
former grades ONE named signification via its dedicated reader; the latter grades the whole
bhava by its WEAKEST decided signification — different grain, not disagreement). That
derived rule (PREC-1) was doctrine-reviewed before shipping and is tagged project
governance, not Raman doctrine, in its own rule text.

Encoded as `app/raman_saab/interpretation_guide.py` (chart-independent constant): 12
precedence records + 4 parallel-lens records + the 5-axis table + the 5-step reading
order, rendered as report section v18 ("How to read this report", after the honesty
headline) and shipped machine-readable as the JSON `interpretation_guide` key with a
CLOSED relation vocabulary (governs/corroborates/different_grain/re_read_of/parallel) so
the LLM-grounding path branches deterministically. Where no rule exists the guide says
"parallel lenses — side by side, never averaged"; it never invents precedence.

The audit also found the ranked digest (insight_digest.py) was shipped in JSON + the
interactive page but NEVER rendered in markdown/standalone HTML — a REPORT COMPLETENESS
violation, repaired as v19 ("What matters most"). Full amendment notes:
docs/raman_saab/REPORT_TEMPLATE.md v18/v19.

## The deterministic synthesis layer (2026-08-03) — S1-S5, report v20

The user proposed a 10-phase synthesis architecture ("no prose generated directly from
calculations"). Inventory: ~half already existed; the rest was built as five phases, all
report-layer pure re-reads (PREC-10), the verdict-path wall extended by test. Three user
decisions bind the deviations from the proposal as pasted:
1. **Conflicts NARRATED, never hidden** (the proposal's "never expose unresolved
   contradictions" was rejected as conflicting with REPORT COMPLETENESS/Measured-Truth):
   `tension_narrator.py` composes one sentence per already-detected tension naming BOTH
   poles + the governing v18 rule; a test pins both poles' words in every sentence.
2. **Two doctrine tiers**: Raman-citable core + the MODERN_SYNTHESIS-bannered layer
   (NON_RAMAN_GROUPINGS matter edges; NON_RAMAN_THEMES keywords) — bannered on every use,
   never bare (the pitru precedent).
3. **No numeric evidence weights** (the proposal's fixed weight table): numeric weighting
   was already MEASURED NULL (the tuner's holdout-locked convergence at iteration 0) and
   Raman states no numeric rule (HTJAH-I:495) — his comparative weighing (B1) + the v18
   axes ARE the ranking. Do not re-litigate by re-building weights.
Built: `judgment_graph.py` (S1), `planet_biographies.py` + section v20 (S2),
`PlainReading.reconciliations` (S3), bannered groupings (S4), `Nichod.turning_points`
(S5). Known recorded limitation: `FiredYoga` carries no participant field, so yoga graph
edges are citation-only until that field exists (a future append-only lift).

**Graha chapters + Yoga deep-read (same day, user-requested):** the v20 section grew into
full per-graha chapters and v21 added the per-yoga study — see REPORT_TEMPLATE.md's
v20/v21 amendment note for the complete record. Doctrinal decisions binding here:
verbatim-by-frozen-line-range rendering (zero transcription risk; ranges under the source
lock), stated-absences-never-guesses (the 2 OCR-defeated MD-sign cells, the nodes'
HPA-22/vocation rows), NO invented yoga percentage (measured rupas only — the
measured-null lock), and only Raman-stated cancellations. The HPA-24 mining derivation
(anchor walk over 82 sub-period anchors with 9 OCR aliases, zero Vimshottari-order breaks)
is reproducible from the module's docstring.

**Pipeline WIRED end-to-end (same day, follow-up commit):** the graph decoupled from
life_chapters (period nodes/timer edges now from the first-pass timeline, with grades);
the second pass re-ordered to the diagram (objects → graph → conflicts → themes →
narrative); the narrative engine consumes the layers (census-dominant sentence in Your
Reading's opening beside the Shadbala line — two dominance measures, both said;
reconciliations composed in, not attached; the dominant graha's own MD chapter marked);
`raman_style.py` names the writer stage. Order enforced by consumption tests.

**Report punch-list corrections 1-2 (2026-08-04).** (1) Rectification confidence
re-measured as a bidirectional per-pillar minute RANGE (a full ±60-min scan) instead of a
4-fixed-offset flip check, plus the combined "every pillar holds together" window — no
doctrine change, a pure measurement-precision upgrade to an already-honest instrument.
Two implementation bugs fixed in the same pass (an ayanamsa mismatch between the base
chart and the probe casts that could report false sensitivity; an invalid-hour bug in the
old offset arithmetic near midnight, unreachable at ±5 min but live at ±60). (2) The
judgment graph is now a first-class section (v32) beside "Your Reading" on all three
surfaces — it was already used there (the dominant-planet census sentence); this closes
the gap that it was never actually SHOWN on markdown/standalone HTML, and was shown too
late (after Planet biographies) on the interactive page. Pure re-read both ways; no new
astrology, no verdict touched. See `docs/raman_saab/REPORT_TEMPLATE.md`'s v32 note for
the full technical record.

**v33 Aptitude/intelligence/work-style chapter + an interactive-page completeness gap
(2026-08-14).** The three trait axes the report never had as output fields shipped as
one appended chapter (pure re-read; `REPORT_TEMPLATE.md` v33 note carries the record,
including the corpus-machine follow-up: pinning Raman's master Moon-mind instruction
range near HTJAH-I:1231 before its verbatim block can render). While wiring the fourth
surface, a standing REPORT COMPLETENESS violation surfaced: the interactive page
(`app/medini/templates/report.html`) had never rendered `psych` (v27) — repaired in the
same commit — and STILL does not render `profession` (v23), `wealth` (v24), `marriage`
(v25), `children` (v26), `arishta` (v22), `karmic` (v30), `decades` (v28), or
`life_synthesis` (v29), all of which the markdown and standalone-HTML surfaces carry in
full. Rendering them is a mechanical repair, but folio placement on that page is a
product-layout call — per the completeness rule ("surface it and ask"), this is
recorded here for the USER to schedule rather than done unilaterally.

**Interactive-page completeness repair COMPLETED (2026-08-14, user-directed "implement and
do next").** All eight remaining chapters — `arishta` (v22), `profession` (v23), `wealth`
(v24), `marriage` (v25), `children` (v26), `decades` (v28), `life_synthesis` (v29),
`karmic` (v30) — now render on `app/medini/templates/report.html` with every field, via the
page's safe-DOM helpers. Folio placement: arishta/marriage/children/profession/wealth in
folio 7 (matters & longevity, before the v33 aptitude chapter), decades closing folio 8
(life-narrative), karmic in folio 10 (divisional & soul, between Soul and Pitru), full life
synthesis opening the close of folio 11 (insights). Corpus-quote fields render only when
non-empty (honest absence off the corpus machine). With this, every chapter the report
computes appears on all four surfaces; the REPORT COMPLETENESS gap recorded above is closed.

## Prediction unblock (2026-08-17) — user decision, binding guard-policy record

The user directed "unblock prediction part"; two decisions were then taken via explicit
question-and-answer and are binding until a doctrine review WITH user sign-off says otherwise:

1. **Q1 — scope: "Timed indications."** The guard boundary moved from *timing* to *idiom*.
   Classical timed-indication phrasing is now ALLOWED on every surface, including dates,
   ages, and dasha/bhukti attribution: "marriage is indicated during the Venus bhukti,
   2027–2028", "the 10th house is activated at par-excellence grade in this period",
   "at age 30 the Saturn bhukti turns classically sensitive for health." This is Raman's
   own published voice (his worked nativities date their indications throughout HTJAH).
   The DECREE voice stays refused everywhere: "you will marry", third-person
   `he/she/they will|shall <verb>`, `is going to`, `destined/certain/guaranteed/bound
   to/sure to`, `I predict`. Implementation: `_FORBIDDEN_RE` in
   `app/llm/report_explainer.py` — the 2026-07-28 dated-indication arms were removed,
   every decree arm kept, and a decree-dated-death arm retained.
2. **Q2 — the death wall: "Lift fully."** Maraka periods and the longevity span may now be
   STATED as timed indications on the grounded surfaces ("the maraka periods 2031–2034
   are classically sensitive", "the span reads at the purna band, around the 83rd year").
   **The assistant's recorded recommendation was to keep the death wall** (mortality
   statements are the one category where a mis-read costs the most and the engine's
   real-outcome generalization is measured NULL); **the user overrode it knowingly** —
   this line preserves that record. Correspondingly `_EXCLUDED_RE` in
   `app/llm/ai_interpret.py` dropped its death/lifespan/longevity/maraka tokens.

What did NOT move (kept without being asked, as safety/honesty floor):
- **Suicide/self-harm and serious/terminal-illness exclusions stay in code** on the walled
  panel (`_EXCLUDED_RE`, `TOPIC_DEFERRAL`, `AI_INTERP_SYSTEM`) — no register lifts them.
- **Decree-dated death stays refused on every surface**: "death around 2031", "will die",
  "dies by 60" trip both `_FORBIDDEN_RE` and a purpose-added decree-death arm in
  `_EXCLUDED_RE` (so the walled panel cannot decree either).
- **The Measured-Truth disclosure layer is untouched** (add-only law): every timed
  indication still ships alongside the calibration framing — the engine answers "what
  would Raman say", it is not a validated predictor.

Tests pinning the new policy: `tests/test_report_explainer.py`
(`test_timed_indications_now_pass` allowed-list; decree suites trimmed to decree-only) and
`tests/test_ai_interpret.py` (`test_lifted_indication_idiom_passes`;
`test_selfharm_illness_and_decree_death_are_caught`). CLAUDE.md's guard-line and
ai-interpret bullets were amended the same day to point here.

## Corpus-gated worklist from the chapter audit (2026-08-18) — what the waves deliberately did NOT encode

Waves 0-2 of `REPORT_CRITIQUE_2026-08-17.md` were executed on a machine where the
doctrine corpus is ABSENT. Every shipped addition is a re-read of already-computed state
citing only line numbers already recorded in the codebase. The items below were REFUSED
by the implementers because encoding them would have required minting a citation from
memory — the one thing the PRIME DIRECTIVE forbids. Each needs a corpus machine to pin
its exact range, after which it becomes a normal (mostly small) encoding task.

**Doctrine that needs a verified citation before it can be encoded**

1. **10th-from-the-Moon (and from the Sun) career derivation.** `primitives/career.py` is
   Lagna-only. Raman judges the 10th from Lagna, Moon and Sun and takes the strongest;
   the profession chapter therefore misses two of his three reference frames. Needs the
   HTJAH-II / HPA passage that states the three-frame rule.
2. **Anatomical mapping for Health: sign -> body region (Kalapurusha) and planet ->
   disease tables.** Grep confirms NO such table exists anywhere in `app/raman_saab`.
   The health section's own subtitle asks "which body areas does the chart mark" and it
   answers with house numbers. HPA carries both tables; the chapter+line ranges must be
   verified before encoding. **This is the single largest genuine content gap in the
   report** (audit's own words).
3. **Studies-in-Jaimini chara-dasha x karakamsa pairing.** The dated chara sequence and
   the karakamsa reading now both render (Wave 1/2), but the sentence that reads the
   karakamsa indications THROUGH the running chara period is not composed — the passage
   is unpinned. A navigational cross-reference was shipped instead.
4. **Spouse-description block** (7th sign nature, the 7th lord's navamsa, the D-9 spouse
   significator's temperament) and the **computed early/delayed marriage-timing lean**.
   The primitives exist; the descriptive passages (HTJAH-II 7th-house chapter) need their
   ranges verified before the block can quote or paraphrase them.
5. **Balance-of-dasha-at-birth citation.** The row now renders (Wave 2, foundation) as
   disclosed JD arithmetic with NO citation, because Raman's casting chapter / the
   Mainpuri proforma line is unpinned.
6. **Deeptadi precedence rule.** `state()` is priority-ordered (dignity-first) and the
   report now discloses secondary states, but HPA Ch.7 states no explicit precedence —
   the ordering is disclosed as the engine's own convention, uncited by design.
7. **Per-component Shadbala minima (GBB-8).** The "weakest component" pointer shipped as
   explicitly arithmetic-only ("no per-component minima are encoded"). GBB-8's component
   requirement table needs verification to make it a real per-component verdict.
8. **Moderating-factor clause citation.** The clause ("the affliction is qualified - ...")
   composes from ledger flags (parivartana_resilient / intact karaka / catastrophic-gate)
   and carries NO citation: Raman's "the affliction is considerably reduced by..." device
   has no recorded line. Framed as the judge's own disclosure until one is pinned.
9. **Psych affliction-to-the-mind screen** (Moon/Mercury under malefic aspect, 5th-house
   affliction). The critique marked it FOR CORPUS VERIFICATION; not implemented.
10. **Kemadruma-bhanga extended branch** — the benefic-drishti branch is labelled
    not-3HC in code; if Raman states it elsewhere, pin it and relabel.
11. **Missing significations** the audit found thin against Raman's chapter tables: H1
    appearance/character, H3 writing/neighbours, H2 food/sustenance, H5 speculation and
    upasana, H6 servants/subordinates, H12 bed-comforts. Each is an add-only row in
    `significations.py` + a rule bucket, but each needs its chapter-table citation.
12. **HPA-26 pinda -> longevity application** and the **ASP transit-multiplier via pinda**
    remain deliberately unwired (the reduced tables and Sodya Pinda themselves now render,
    Wave 1); both were already recorded as deferred pending corpus.

**USER decisions still open** (unchanged by the waves; recorded here so they are not lost):
Sun `MIN_REQUIRED` 5.0 (tuned) vs GBB-8:303's printed 6.5 — retune or relabel; whether
raja/dhana yoga-lean should be house-conditional in the preponderance ledger (doctrine
review); the Jaimini overlay's aspect scheme (rasi drishti vs graha drishti); the decade
timeline's whole-life mode default; and the Stage-9 holdout gate + the 90% bar vs the
proven 88.4% ceiling.

**Side effect to be aware of:** the two new digest head items (governing factor,
longevity foundation) shift the positions of later digest items, so `chart_feedback` rows
stored under older qids no longer align with the current digest. Harmless for new feedback;
historical rows should be treated as position-stale if they are ever re-analysed.


## Directional parivartana (2026-08-19) — OPEN, needs doctrine review + user sign-off

Found while citing the moderating-factor clause with the corpus mounted. NOT actioned:
this sits in the verdict path and would move the golden ratchet, so it is recorded rather
than changed.

`house_template._decide` credits `parivartana_resilient` as flat relief — a lord or karaka
in an exchange has a debilitation penalty bypassed (`house_template.py:1009-1020`,
"treat a debil-but-exchanged pillar as not-weak"), **regardless of the condition of the
exchange partner**.

Raman's own worked charts run BOTH ways:

- benign: "Jupiter and Venus have exchanged signs (parivartana), mutually benefiting each
  other" (HTJAH-I:8837)
- transmitting affliction: "the 8th and 10th lords have exchanged signs so that Saturn who
  is the 7th lord **also is afflicted by this parivartana**" (HTJAH-I:9119)
- explicitly undesirable: "Although the 7th lord Jupiter is strongly placed, his exchange
  of signs with 5th lord Saturn **is not desirable as it can deny marriage or progeny**"
  (HTJAH-I:9143)

On that showing an exchange TRANSMITS the partner's condition; it does not shield by
itself. A direction-aware rule would credit resilience only where the partner is itself
unafflicted, and would let an exchange with an afflicted or dusthana lord carry affliction
across instead.

**Why it was not changed here:** `parivartana_resilient` feeds `_decide`, so any change
moves the ratchet and needs the doctrine-review + user-sign-off path that B1-B4 went
through. The reporting side WAS corrected in the same commit — the moderating-factor clause
no longer implies Raman grants relief unconditionally and now names his counter-examples.

**If actioned**, expect movement on charts where a debilitated lord/karaka sits in an
exchange with an afflicted partner; measure exact/within-1/real-errors before and after and
report both axes side by side per MEASURED TRUTH.


### CLOSED 2026-08-21 — WILL NOT SHIP (user sign-off). Both flags stay off, permanently.

Implemented in `judges/house_template.py` on the `B1_DOMINANT_FACTOR_GUARD` pattern
(module-level, read LIVE, default OFF) and measured. Nothing is enabled; the golden ratchet
is byte-identical at the shipped values.

Two arms, because "an exchange transmits the partner's condition" can mean two things:

* **Arm A — `PARIVARTANA_DIRECTIONAL`** withholds the existing relief when the exchange
  partner is itself in trouble.
* **Arm B — `PARIVARTANA_TRANSMITS`** goes further: the lord itself counts hard-afflicted,
  which is literally what HTJAH-I:9119 says, and is the channel the B1 guard already reads.

And three readings of "partner in trouble" (`PARIVARTANA_PARTNER_TEST`), because Raman's two
counter-examples do NOT name the same mechanism: `condition` (partner combust /
debilitated-uncancelled / a maraka), `dusthana` (partner lords the 6th, 8th or 12th — the
mechanism at :9119, where the 8th lordship is what travels), and `either`. HTJAH-I:9143
("exchange … with 5th lord Saturn is not desirable") fits neither and is deliberately not
encoded: the 5th is no dusthana and Saturn is not described as afflicted there.

Measured over the 225 golden charts, 12,600 significations, both ratchet axes:

| variant | exact | within-1 | real errors | significations moved |
|---|---|---|---|---|
| baseline (shipped) | 259/293 | 283/293 | 10 | — |
| A / partner=condition | 259/293 | 283/293 | 10 | 0 (0.00%) |
| A / partner=dusthana | 259/293 | 283/293 | 10 | 0 (0.00%) |
| A / partner=either | 259/293 | 283/293 | 10 | 0 (0.00%) |
| B / partner=condition | 259/293 | 283/293 | 10 | 159 (1.26%) |
| B / partner=dusthana | 259/293 | 283/293 | 10 | 74 (0.59%) |
| B / partner=either | 259/293 | 283/293 | 10 | 162 (1.29%) |
| A+B (any reading) | 259/293 | 283/293 | 10 | same as B alone |

**Every variant leaves all three fidelity numbers exactly unchanged.**

**Arm A is a measured no-op — 0 of 12,600.** The reason is not that the rule is right; it is
that the relief it would qualify almost never fires. Across 225 charts, 93 carry at least
one exchange, but only **5** exchange members are debilitated-and-uncancelled — the shipped
relief's actual trigger — and none of those five has an afflicted partner. The backlog's
doctrinal criticism stands; its practical consequence is nil, and no golden can test it.

**Arm B moves 0.59%–1.29% of all output, always one step downward** (161 favourable→mixed,
1 favourable→afflicted at `either`). On the pinned corpus it is an exact wash: it FIXES
`HTJAH-II.h10_05 H10/status_honour` (favourable→mixed, Raman: mixed) and BREAKS
`HTJAH-II.h11_05 H11/elder_siblings` (favourable→mixed, Raman: favourable).

**Recommendation: do not enable either arm.** Arm A cannot be justified because it changes
nothing. Arm B is a real change to 1.29% of every reading, tightening favourable verdicts
toward mixed, bought with one golden fixed and one golden broken — no measured fidelity gain
on either axis. The B1 precedent does not apply: B1 was enabled because it cut real errors
(inversions) 12 → 10 at a known strict cost. Arm B cuts nothing. Enabling it would be a
purely doctrinal act, and the doctrine itself is split — :8837 has exchanges benefiting,
:9119 has one transmitting affliction, :9143 objects to an exchange on neither ground.

If a human wants it anyway, `dusthana` is the reading with the best textual warrant (it is
the mechanism :9119 actually describes) and the smallest blast radius (0.59%), and it moves
no golden at all.

Reproduce: `tests/raman_saab/judges/test_directional_parivartana.py` pins the helpers and
the flags-off no-op; the sweep is committed as
`tools/raman_saab/measure_directional_parivartana.py` and rebinds the three module flags
directly. (This paragraph previously pointed at a session scratchpad file,
`measure_parivartana_full.py`, which was never committed — corrected 2026-08-21.)

**DECISION 2026-08-21 — closed, will not ship.** The user signed off on the recommendation
above. `PARIVARTANA_DIRECTIONAL` and `PARIVARTANA_TRANSMITS` stay `False`, and the code stays
in place as the record of a measurement rather than as a rule awaiting a switch.

The reasoning is worth keeping short and blunt so it is not re-opened on a whim. Arm A is a
measured no-op — 0 of 12,600 significations — because the relief it would qualify almost never
fires: 93 of 225 charts carry an exchange, only 5 exchange members are debilitated-and-uncancelled,
and none of those five has an afflicted partner. There is nothing to enable. Arm B is a real
change to 1.29% of every reading, always one step downward, and it buys one pinned golden fixed
against one broken with no movement on either fidelity axis. The B1 precedent does not transfer:
B1 shipped because it cut inversions 12 -> 10 at a known strict cost, and arm B cuts nothing.

Enabling either would be a purely doctrinal act on a doctrine that is itself split —
HTJAH-I:8837 has exchanges mutually benefiting, :9119 has one transmitting affliction, and
:9143 objects to an exchange on neither ground. Where the texts disagree and the measurement is
silent, the engine keeps what it already encodes.


## Kemadruma bhanga attribution (2026-08-19) — OPEN, needs doctrine review + user sign-off

`bhangas.kemadruma_bhanga` cites 3HC:2182-2185 for its three cancellation branches. The
quoted Remark does not end there. The full passage runs to 3HC:2188:

> "Some authors say that if planets are m a kendra from birth or from the Moon or if the
> Moon is in conjunction with a planet there is no Kemadruma. Theie are yet other authors
> who say that these yogas arise from kendras and navamsas **but these observations are not
> generally acceptable.**"

Two problems:

1. Raman **attributes** the cancellation to "some authors" — he never asserts in his own
   voice that there is no Kemadruma in these cases. The engine cites the line as though he
   did.
2. His dismissal at :2188 is grammatically ambiguous. "these observations" attaches most
   immediately to the SECOND group ("kendras and navamsas"), but can be read as covering
   both reported opinions, since he is reporting throughout rather than endorsing.

**Not actioned:** `kemadruma_bhanga` feeds the yoga layer and therefore the verdict path, so
narrowing or dropping the branches moves the golden ratchet and needs the doctrine-review +
sign-off path. The DOCSTRING was corrected in the same commit — the anchor is now quoted in
full including the dismissal, and the attribution is stated.

**If actioned**, the question to settle first is scope: does :2188 dismiss the kendra/
conjunction cancellations too, or only the kendra-and-navamsa claim? A reviewer with the
printed page (the OCR is poor here — "Theie", "m" for "in") should decide before any code
moves. Expect movement on charts carrying an otherwise-formed Kemadruma.

**Settled in the same pass:** the extended benefic-drishti branch is NOT Raman's. The
backlog asked "if Raman states it elsewhere, pin it and relabel" — searching the mounted
3HC finds Kemadruma only at :2170-2266 and no such statement. The NOT-3HC label is correct
and stays.

### RESOLVED 2026-08-20 (Track 4b) — the text settles it; no code change proposed

The scope question does NOT need a reviewer with the printed page. It is answerable from
the mounted corpus, and the earlier pass missed the answer for a mechanical reason: it
searched for "Kemadruma", and the two decisive passages are OCR'd as **"Kemadiuma"** and
**"Kemidiumi s"**. A spelling-tolerant search finds exactly six mentions in the whole book —
:2170, :2173, :2185, :2255, :2263, :2266 — and the last three were never read.

Immediately after the Remarks, Raman applies the cancellation **in his own voice, on worked
charts, in both directions**:

> 3HC:2263-2268 — "Here you will see that Kemadruma is present because the houses on either
> side of the Moon are vacant. But there is distinct cancellation of the Kemadruma because
> (a) the kendras from the Moon are occupied and (b) kendras from the Lagna are also
> occupied."

> 3HC:2255-2261 — the converse, on Chart No. 8: "The above is a typically Kemadruma Yoga
> horoscope. No planets are placed on either side of Chandra and no planets are to be found
> in kendras either from Lagna or from the Moon."

A man does not demonstrate a cancellation twice, once each way, and mean it to be "not
generally acceptable". **:2187-2188 attaches to the SECOND reported group only** ("yet other
authors … these yogas arise from kendras and navamsas"). Branches (a) and (b) are Raman's
own applied doctrine, not merely "some authors", and the attribution defect is a citation
fix, not a behaviour question.

(The two passages describe charts with opposite kendra occupancy and no chart header stands
between them, so :2263 discusses a chart the OCR did not carry. Which chart it is does not
affect the reading: both statements assert the same rule.)

**Two further findings, both measured over the 225 golden charts / 12,600 significations:**

| reading | bhanga fires | exact | within-1 | real errors | significations moved |
|---|---|---|---|---|---|
| R1 as measured — (a)(b)(c)+extended | 63/63 | 259/293 | 283/293 | 10 | — |
| R2 drop (c) conjunction | 63/63 | 259/293 | 283/293 | 10 | 0 |
| R3 drop extended drishti | 63/63 | 259/293 | 283/293 | 10 | 0 |
| R4 keep only what Raman works | 63/63 | 259/293 | 283/293 | 10 | 0 |
| R5 maximal dismissal — no bhanga | 0/63 | 259/293 | 283/293 | 10 | 0 |

1. **Branch (c) is provably dead**, not merely unused. `_in_kendra_from` scores the same
   rasi-house as distance 1, the 1st is a kendra, and the Sun is not excluded from branch
   (b) — so every conjunction (c) can see, (b) has already seen. The docstring's claim that
   (c) earned its keep through the Sun was wrong and is corrected. The extended
   benefic-drishti branch is different: it is NOT provably redundant (Jupiter in the 5th or
   9th from the Moon aspects it from outside every kendra) but never once supplies a
   cancellation (a)/(b) had not already made across these 225 charts.

2. **The whole question is currently inert in the verdict path.** Even R5 — cancel nothing,
   so Kemadruma stands on all 63 charts that form it — moves **zero significations** and
   leaves all three fidelity numbers untouched. It does change the yoga layer visibly:
   `Y.KEMADRUMA` fires on 63/63 instead of 0/63, which reaches the Yogas section, the
   Arishta chapter's kemadruma note, and the preponderance ledger (an arishta yoga leans
   adverse). So the stake is a REPORT claim, not a verdict.

**Recommendation: change no behaviour.** The doctrine came out in favour of what is already
encoded. What was actually wrong was the citation and two claims in the docstring, and those
are fixed in this commit. The one live question left for a human was cosmetic-but-honest:
branch (c) is dead code kept "for textual fidelity" — keep it as a mirror of the quoted line,
or delete it as provably unreachable? Either is defensible; it cannot change a reading.

**CLOSED 2026-08-21 — branch (c) DELETED on user sign-off.** The shipped reading is now
**(a)(b)+extended**; the table above records the measurement as it stood, so R1 names the
configuration measured, not the one shipped. Deletion moved nothing, exactly as R2 predicted:
259/293 · 283/293 · 10 real errors, 0 significations moved. `bhangas.kemadruma_bhanga`
quotes the line in full in its docstring, which is where fidelity to the text belongs — an
`if` that cannot fire records nothing a reader can check. The extended benefic-drishti branch
STAYS (it is not provably redundant) and keeps its NOT-3HC label; a test now builds the chart
only it can cancel — Moon in the 2nd, Jupiter in the 6th — so deleting it would fail loudly
rather than silently.

## Chara dasa x Karakamsa pairing (2026-08-19) — NOT ENCODABLE from the mounted text

The audit wanted the sentence that reads the karakamsa indications THROUGH the running
chara period. It cannot be composed from what is mounted, and the reason is the import, not
the doctrine:

* the JAIMINI import is PARTIAL — 6 chapters (4, 5, 6, 9, 11, 49), and chapter 5 is 48
  lines of OCR junk;
* "karakamsa" appears **only** in chapter 9 (the Summary), at :797-838, where Raman lists
  what the karakamsa reveals (appearance via its lord, character and mind, pre-disposition
  to troubles, education, profession) — a topic index, not a timing rule;
* chapter 4 is the Chara Dasa chapter and mentions karakamsa **zero times**.

So the pairing is either in a chapter that did not import or is not stated. The
navigational cross-reference that shipped instead remains the correct surface. A session
with a complete Studies-in-Jaimini scan should look for an article pairing the two before
re-opening this.


## Thin significations (2026-08-19) — CLOSED, measured, and closed AGAINST adding them

The audit's six thin significations were checked twice with the corpus mounted. Detail and
anchors live in the `doctrine/significations.py` module docstring; the summary:

* **Four of six ARE Raman's** (H1 character/environment, H2 food/literary gift,
  H3 writings/neighbours, H5 fame-and-position/discriminating-power) — HPA-19:64-67,
  :114-117, :190-193, :300-303.
* **Three are not his, in the bhava requested**: H5 speculation (absent), H5 upasana
  (worship is his 12th-house matter, HPA-19:785), H6 servants (absent), H12 bed-comforts
  (absent). BPHS/classical attributions, barred by the divergence firewall.
* **The four he does state were added and MEASURED, then reverted**: cross-layer agreement
  fell **0.475 → 0.439** and 62 tier-3 evidence snapshots churned. The scored golden
  ratchet did NOT move (259/293) because a new signification carries no golden expectation
  and is never scored — which is precisely why the ratchet alone was not a sufficient gate
  here, and the convergence test was.

**The doctrinal reason**: naming a matter is not giving rules to judge it. Raman lists
these in a definitional sentence and gives no combinations for them, so a signification
added here routes to no rule bucket and is decided by the polarity fallback — a verdict
manufactured from no evidence.

**To re-open**: the prerequisite is the RULE BUCKET, not the row. Find Raman's combinations
for the matter, encode those, and the signification follows. The audit's own phrasing ("an
add-only row + a rule bucket") had it right; only the row is cheap.


## H3.C.4 courage-favourable rule encoded (2026-08-22) — ✅ SHIPPED, two open caveats

**Trigger** (prioritization only, not justification — see below): a real-outcome study
(`docs/raman_saab/FAILURE_ATLAS.md`, AstroDatabank) found H3 `courage` reads AUC 0.480
against a "military service" indicator, labeled INVERTED. Per this project's own governance
(`tools/raman_saab/astrobank/METHODOLOGY.md`: "No engine constant, threshold, or rule may be
tuned from these results directly"), that finding is **not** the reason for this change — it
only motivated auditing H3's rule coverage, where a genuine, citation-backed gap turned out
to already exist independent of any real-outcome number.

**The gap**: `H3.C.4` (HTJAH-I:3421) — "3rd lord in a beneficial Nakshatra and Navamsha,
aspected by benefics, with Mars equally well disposed → a man of character and conviction,
brave and straightforward" — was `kind="descriptive", condition=None` since the rule set was
first written, the only rich *favourable* courage combination in the file (everything else
feeding courage is malefic-leaning "3rd lord with X" temperament atoms, or bridged in from
the `siblings` bucket).

**Encoding** (`house_03_sahaja/combinations.py`, four conjuncts, one per clause of Raman's
sentence, all reused from already-shipped primitives — no new invented threshold):
1. `_ThirdLordInBeneficialNakshatra` — 3rd lord's nakshatra ruled by a natural benefic
   (`primitives.nakshatra.nakshatra_lord`, the function `conditions.InStarOf` already uses).
2. `C.VargaDignity("LORD_OF:3", varga="D9", states={"exalt","own","friend"})` — beneficial
   Navamsha, the project's existing "beneficial" dignity-state set.
3. `_ThirdLordAspectedByBenefic` — Jupiter/Venus only, matching the identical-phrase
   precedent at `house_02_dhana/combinations.py:320` and `house_05_putra/combinations.py:228`.
4. `_NotDecisivelyWeak("Mars")` — `not effective_strength("Mars", chart).decisively_weak`,
   the shipped, golden-tuned B1 measure (this same file's `DOCTRINE_BACKLOG` B1 entry),
   deliberately NOT a stricter `is_powerful`-style gate (that shortcut is the one the B1
   module's own docstring records as over-firing Shankha/Kahala 102/164, 48/164).

**Measured**: full 293-chart golden corpus, before/after byte-identical — strict exact
259/293, within-1 283/293, real errors 10. The rule fired on exactly one golden
(HTJAH-I chart_61) as additional corroborating evidence for an already-correct
"courage: favourable" verdict; it changed zero verdicts anywhere in the corpus.
Evidence snapshot `HTJAH-I.chart_61.json` regenerated to include the new citation/fired-id.

**bphs-doctrine-reviewer verdict: SHIP-WITH-CAVEAT** (confidence MEDIUM). Two open caveats
recorded rather than silently resolved:
1. "Beneficial Nakshatra" has no formal BPHS anchor on disk (no gana/tara-from-Moon/named-list
   definition found in `data/knowledge_library/`) — nakshatra-lordship-by-nature is a
   *consistent*, not an *invented*, reading (it's the concept `InStarOf` already operationalizes
   elsewhere), but it is one plausible reading among others (a tara-from-Moon sense is the more
   common classical use of "auspicious star"). Revisit if a tara/gana-based source surfaces.
2. `decisively_weak=False` is a materially looser bar than the `{exalt,own,friend}` requirement
   the SAME sentence sets for the 3rd lord two clauses earlier — Raman's "equally well disposed"
   reads as parallel-positive, not merely "not ruined." Deliberate (matches the project's own
   anti-overfire precedent rather than risk a stricter gate over-firing), but asymmetric — a
   future tightening pass must re-run the golden ratchet before "fixing" this asymmetry, not
   assume tightening is free.

Not yet touched by this pass: the question of whether bridging courage's evidence through
the shared `rule_tags=("siblings","courage")` bucket is itself doctrinally correct
(HTJAH-I:3324 vs 3428 read as one combined reading or two) — deferred to a follow-up pass.


## H12.C.D6 "equal in strength" (2026-08-22) — INVESTIGATED and HELD, not shipped

**Attempted**: encode the last dead H12 combination, `H12.C.D6` (HTJAH-II:16444) — "rulers of
(2&12)/(5&9)/(6&12)/(3&11)/(4&10) equal in strength → criminal action (absent other
mitigation)" — using a new `_LordsEqualInStrength(house_a, house_b)` condition comparing two
D1 lords' total Shadbala rupas, `C.Or`-ed across the five cited house-pairs. "Equal" was read
as `abs(rupas_a - rupas_b) <= MARGINAL_BAND`, reusing the project's own shipped B2 constant
(0.2 rupas) rather than inventing a new number.

**Why it was held**: `MARGINAL_BAND` was tuned and golden-validated for a *different*
statistical question — one planet's total vs. its OWN fixed, planet-specific bar
(`MIN_REQUIRED`, 5.0-7.0 rupas) — not the spread between two independently-varying planets'
totals, which has different natural variance. Measured against the 209 Track-B golden
charts, the reused-tolerance version fired on **57/209 = 27%** of charts. The full 293-chart
ratchet stayed byte-identical (259/293 exact, 283/293 within-1, 10 real errors) throughout,
but that silence is NOT evidence of good calibration here: `incarceration` sits in
`house_template._DUSTHANA_AFFLICTION_KEYS`, so any single fired malefic with no benefic
contradiction already confirms "afflicted" — a 27%-firing rule can ride along on charts
already decided by other evidence and never be tested as the DECIDING factor on any golden.

**bphs-doctrine-reviewer verdict: INSUFFICIENT-EVIDENCE / HOLD-AS-DOCUMENTED-LIMIT.**
Back-of-envelope: rupas empirically span ~0-12 (`test_adapter.py`, `test_shadbala_compute.py`
pins); a uniform-spread estimate puts a single pair's P(|Δ|≤0.2) at roughly 3-4%, and only 7
grahas hold lordship across the 10 house-slots in play (a birthday-paradox-style crowding
effect across the 5 pairs) — ORing five such checks lands close to the observed 27% by
arithmetic alone, not because the combination is doctrinally common. The `C.Or` structure
itself is textually correct (Raman lists the pairs disjunctively); the defect is the
per-pair tolerance, reused from a context it was never validated for. DOCTRINE_BACKLOG's own
B2 entry already recorded once that widening that band beyond its original narrow scope
broke a golden (chart_54 H10) — this reuse repeated the same class of mistake without
re-testing against that precedent.

**Reverted**: `H12.C.D6` is back to `kind="descriptive", condition=None` (dead, as before),
its `afflicted=` text updated to record this investigation so a future session doesn't
re-attempt the same reuse. Confirmed the revert restores the byte-identical ratchet.

**To re-open** (per the reviewer's own conditions — either one, not a same-day constant
reuse):
1. Derive the pairwise "equal" tolerance empirically from this project's own chart corpus
   (e.g. the percentile spread of `|rupas_A - rupas_B|` per specific lord-pair across the
   golden/reference set) instead of reusing `MARGINAL_BAND`, then re-run the ratchet.
2. Build a test that isolates charts where this rule would be the SOLE fired evidence for
   `incarceration` (not merely corroborating alongside another malefic) and confirm it
   doesn't over-fire there — the ratchet's redundancy blindness means this has never
   actually been checked, for this rule or for how many of H12's other malefic rules ride
   the same confirmation mechanism.


## Dead-rule inventory (2026-08-22) — a systematic, citation-backed coverage gap

Measured across the whole rule corpus: **128 of 847 rules (15.1%) are dead** —
`kind="descriptive"` / `condition=None`, so they can never fire. By house:

| house | dead/total | | house | dead/total |
|---|---|---|---|---|
| H1 | 19/106 (17.9%) | | H7 | 6/73 (8.2%) |
| H2 | 19/92 (20.7%) | | H8 | 11/71 (15.5%) |
| H3 | 3/61 (4.9%) | | H9 | 7/73 (9.6%) |
| H4 | 6/50 (12.0%) | | H10 | 6/42 (14.3%) |
| H5 | 4/50 (8.0%) | | H11 | **21/75 (28.0%)** |
| H6 | 4/50 (8.0%) | | H12 | 22/104 (21.2%) |

**The load-bearing finding: many `TODO(predicate)` notes are STALE.** They were written when
the blocking primitive did not exist; the primitive was built later and nobody revisited the
rule. Confirmed present today: `primitives/maraka.py`, `primitives/arudha.py`,
`primitives/dispositor.py`, the `shadbala/` package. H2 alone has 4 Arudha-blocked rules
(C.39/40/46/68), 3 Maraka-blocked (C.41/42/43 — C.41 now encoded, below), 2 navamsa-dispositor
(C.33/34), 3 sign-modality (C.36/37/38, trivially computable), 1 Kalabala (C.35), 1 dispositor
(C.31). This is a real, doctrine-cited backlog independent of any real-outcome measurement,
and a future session should walk it house by house rather than trust the TODO text.

**Not a polarity story for H2** (checked, because it WAS the story for H3.C.4): H2 `wealth`'s
live rules are already balanced 25 benefic / 25 malefic / 12 neutral, and its dead rules are
proportionally balanced too (9/6/2). Encoding them would not systematically shift H2's
favourable/afflicted lean either way.


## H2.C.41 Lagna-lord-in-12 + Maraka (2026-08-22) — ✅ SHIPPED WITH CAVEAT, gate discharged

**Shipped**: the previously-dead `H2.C.41` (HTJAH-I:2526, POVERTY block) encoded as
`C.And(C.LordIn(1, 12), _LordTouchedByMaraka(1))`. The old `TODO(predicate): MarakaDetection`
was stale — `primitives/maraka.py` postdates the deferral.

**Doctrinal choice — PRIMARY maraka tier only.** `maraka_points()`'s all-tier set averages 5.5
of 7 grahas and would fire on ~all 19 Lagna-lord-in-12th goldens, rendering Raman's own explicit
"with/aspected by a Maraka" qualifier INERT — a reading that deletes a cited clause is worse
doctrine than a narrowing that preserves it. Secondary/tertiary hold benefics-conjunct-2/7-lords,
the 6th lord and the Shadbala-weakest planet (`00_method_overview.md:160`) — longevity-net
members, not "a Maraka planet" in a poverty rule. Primary averages 3.0 of 7. The local
inconsistency with `house_template._maraka_grahas` (all tiers) points the RIGHT way: B3 exists
precisely because the all-tier set over-afflicts non-death matters. HTJAH-I:783's within-primary
gradation ("associates kill hardest, lords least") is deliberately NOT modelled; #41's phrase
is bare.

**Measured.** Fires 14/209 Track-B goldens (6.7%). Full 293-chart ratchet byte-identical:
259/293 exact, 283/293 within-1, 10 real errors. Suite 605 passed. The primary tier is
Shadbala-independent, so Track-B and ephemeris charts behave identically (a point D6 lacked).

**Gate discharged — H2.C.29 double-count check.** The reviewer flagged that `H2.C.29`
(HTJAH-I:2475, `wealth`/malefic) also requires `C.LordIn(1, 12)`, so one placement could enter
the wealth ledger as two malefic testimonies — which would break the "one testimony among many,
preponderance contextualizes it" argument this ship rests on. **Measured: co-fire on 2/209
charts** (`HTJAH-I.h6_04`, `HTJAH-I.h6_12`) — 2 of C.41's 14 firings, 14%. Low, and the rules
are not substantively redundant: C.29 additionally requires evil planets in the 2nd AND
10th/11th-lord involvement, and reads "always in debt", a different combination and outcome
that merely shares one conjunct. Gate passes; ship stands.

**Caveat, recorded honestly — the ratchet CANNOT validate this rule.** Zero of the 14 firing
charts carries a scored H2 expectation. This is a plain coverage gap, NOT evidence-redundancy
(cf. H12.C.D6, where `incarceration`'s `_DUSTHANA_AFFLICTION_KEYS` membership caused the
blindness); `wealth` goes through normal preponderance weighing, so the ratchet WOULD be
sensitive if a scored chart existed. The B4 precedent (fires 20/225, changes 0 confirmed
verdicts) therefore does NOT cleanly extend: B4's basis included firing on `h7_16` WITHOUT
flipping it — a real stress case surviving. That element is absent here.

**Discrimination is weak, by arithmetic not by defect.** Lagna-lord-in-12th base rate is
19/209 = 9.1% (≈1/12); the maraka qualifier passes 74% of the time, so the rule is
~"Lagna-lord in 12th" minus a 26% haircut. With whole-sign drishti + Jupiter 5/9 + Mars 4/8 +
Saturn 3/10 + the locked Rahu/Ketu 5/9, ~3 primary marakas contacting one planet is near-certain.
Acceptable as a preponderance input; not a discriminating test.

**Corpus-machine follow-up**: HTJAH-I:2526 verbatim. All sourcing here is the repo's derived
methodology table (`house_02_dhana.md:135`), not Raman's printed line — verify (a) the exact
phrasing of "a Maraka planet" and whether Raman qualifies which maraka, (b) whether "extreme
poverty" is stated absolutely or conditioned on absence of mitigation like #44's Jupiter clause.

**Sibling rules NOT unblocked by this**: `H2.C.42` and `H2.C.43` cite the same maraka predicate
and remain descriptive; they need `Parivartana(1,6)`-with-maraka and a functional-nature-filtered
malefic set respectively. Encode only after this rule's corpus-machine follow-up is discharged.


## H7 marriage backlog re-checked (2026-08-22) — NO REMAINING WORK, closed

Picked up the "H7-marriage (+H5) DRAFT backlog" above expecting live rows to work. Re-reading it
against the current engine: **there are none.** Recorded so no future session re-opens it:

* **Mode-A (10 items)** is already closed as a DOCUMENTED LIMIT, by measurement, not opinion — a
  benefic-relief lift was built and tested and does not discriminate (the reliefs it keys on are
  present on genuinely-afflicted charts too, and enabling it would regress the shipped
  h7_02/05/15 fixes). The section's own verdict: "do NOT pursue a relief lift."
* **Mode-B** is fully shipped: h7_02/05/15 via `H7.C.86`, h7_16/19 via `_marital_bond_gate`.
* **Measured today**: of the engine's 10 remaining dist-2 errors, **zero are H7** (or any marriage
  signification). The marriage work genuinely landed.

The 10 current dist-2 errors are: H1 self ×3 (chart_09/17/31), H5 children ×2 (h5_10/h5_16), and
one each of H2 wealth (chart_44), H3 siblings (chart_60), H6 disease_chronic (h6_04), H9 father
(h9_02), H11 elder_siblings (h11_01). chart_44 and chart_60 were already registered limits;
chart_17 and chart_31 are newly registered above. **H1 `self` is now the largest single cluster
(3 of 10)** and is the natural next target for dedicated work — not H7.


## The 10 remaining dist-2 errors are ONE mechanism (2026-08-22) — measured, and already optimal

Profiled all 10 current dist-2 errors together (engine verdict, Raman's verdict, fired benefic /
malefic counts, and the three pillar-strength booleans). The result is far more concentrated than
the per-chart register entries suggest:

| chart | sig | engine | Raman | ben/mal | pillars L/K/B |
|---|---|---|---|---|---|
| chart_09 | self | favourable | insufficient-evidence | **1/4** | 1/1/1 |
| chart_31 | self | favourable | afflicted | 2/2 | 1/1/1 |
| chart_60 | siblings | favourable | afflicted | 3/3 | 1/1/1 |
| chart_44 | wealth | favourable | afflicted | **1/2** | 0/1/1 |
| h5_10 | children | favourable | afflicted | **0/0** | 1/1/1 |
| h11_01 | elder_siblings | favourable | afflicted | 2/0 | 1/1/1 |
| h9_02 | father | favourable | afflicted | 6/6 | 1/1/1 |
| h6_04 | disease_chronic | favourable | afflicted | 1/1 | 1/0/1 |
| chart_17 | self | afflicted | favourable | 5/2 | 1/1/1 |
| h5_16 | children | afflicted | favourable | 2/1 | 1/1/1 |

**8 of 10 are the engine reading favourable where Raman reads afflicted or abstains**; only 2 run
the other way. Nearly all carry all-three-pillars-strong.

**This is BY DESIGN, not a defect.** `_decide` clause 2 (`house_template.py:457-501`) deliberately
does NOT count fired-rule surplus — it weighs Raman's three strength PILLARS (lord, karaka,
Bhava-Bala) per the three-factors doctrine, thresholds `CONTRA_PILLAR_AFFLICT=3` /
`CONTRA_PILLAR_FAVOUR=2` ("Stage-3 calibration, user-signed-off V2"). So chart_09's 4:1 malefic
evidence is irrelevant by construction: 3 strong pillars ≥ 2 → favourable. Any apparent
"tie should read mixed" intuition is a red herring — counts never enter this clause.

**Threshold sweep — the current setting is already a local optimum.** The knobs are read live
specifically so a tuner can monkeypatch them; swept both:

| AFFLICT | FAVOUR | exact | within-1 | real errors |
|---|---|---|---|---|
| 2 | 2 | 256 | 282 | 11 |
| 2 | 3 | 252 | 283 | 10 |
| 2 | 4 | 234 | 285 | 8 |
| **3** | **2** | **259** | **283** | **10** ← current |
| 3 | 3 | 255 | 284 | 9 |
| 3 | 4 | 237 | 286 | 7 |

Raising FAVOUR trades strict accuracy for real errors at a poor rate: 2→3 costs **4 exact** to
save **1** real error (+1 within-1); 2→4 costs **22 exact** to save 3. Compare the B1 guard that
DID ship: −2 exact, **+2** within-1, −2 real errors — a genuinely two-sided gain. Nothing in this
sweep matches that shape. **Do not re-run this sweep; do not re-tune these knobs on this
evidence.** A real improvement here needs a NEW mechanism that separates these 8 charts from the
strong-pillar charts the engine currently gets right — not a threshold move, which trades one
error class for a larger one.

This supersedes the framing in the documented-limits register that B1 comparative-weighing is
"the single lever [for] chart_52 + chart_60": it is the lever for **8 of the 10** remaining
errors, which raises its value — and the sweep above shows the lever cannot be pulled by
threshold alone.


## Tier-3 bhava-rescue (2026-08-22) — gate MET, fix REFUTED twice, CLOSED

The FEEDBACK_UTILIZATION_PLAN Tier-3 item ("H3 over-affliction bhava-rescue", HTJAH-I:503-505,
gated on the wife's H3 as the n=2 counterexample) came due today: the wife's sibling facts
arrived (younger brother = very good relations → H3 siblings truth favourable; engine reads
afflicted — the same over-affliction shape as the anchor chart). **Condition (a) of the gate is
satisfied.** The fix itself was then investigated and is REFUTED, on two independent grounds:

**1. Refuted by the source's own conditions.** The verbatim passage (read today from
`knowledge_library/how_to_judge_a_horoscope_raman/chapter_001`, lines ~503-505): "But if in a
particular case, **the lord is badly placed**, and **the house itself has good conjunctions and
aspects** then evil results should not be predicted." Diagnosed both family charts against it:
father — H3 lord Saturn STRONG (house 2), H3 has ZERO occupants and ZERO benefic aspects;
mother — H3 lord Jupiter STRONG (house 5), H3 likewise empty of benefic conjunction/aspect.
Neither condition obtains on either chart. A faithful encoding of the citation **cannot fire on
the two charts it was pre-registered to fix.** Loosening the conditions until it does would be
citation-shopping — encoding the target, not the text.

**2. The actual mechanisms are load-bearing, by measurement.** What really produces the family
afflicted verdicts: father — the D9 `weakens` modulation dropping a contradiction-mixed to
afflicted (`_navamsa_modulate`; the SAME mechanism as registered golden miss chart_17, now two
independent counterexamples); mother — decisive rules H3.C.36/38/39. A/B on the goldens
(monkeypatch, nothing shipped): blocking the weakens-drop on contradiction-mixed alone costs
**exact 259→248 (−11)** for within-1 +1 and real-errors −1 (chart_17). Eleven goldens where
Raman HIMSELF reads afflicted depend on that drop. Decisively worse than any shippable trade
(B1 precedent: −2/+2/−2).

**Closure.** The family H3 misses are genuine documented limits of the chart_60 class: the
doctrine as encoded from Raman's own worked charts reads these configurations afflicted, and
the lives are favourable — the real-outcome generalization gap, not an implementation bug. The
n=2 pattern the gate was designed to detect is REAL; the pre-registered mechanism just does not
cover it, and no alternative mechanism survives the golden A/B. **Do not re-open without a
DIFFERENT verbatim citation whose conditions actually obtain on such charts.** Tier-1
(elicitation) is DONE; Tier-3 is CLOSED-REFUTED.


## H11 dead-rule sweep (2026-08-22) — pass 1 of the all-houses sweep: 2 shipped, 2 held, 17 correctly left

First house pass of the full dead-rule sweep (H11 first: worst dead-rate 21/75 = 28%, plus the
mother's confirmed elder_siblings miss). Full triage of all 21:

**Correctly descriptive, no action (13):** C.24-30 (seven source-of-gains flavour texts whose
conditions are ALREADY live as H11.P.* placement rules — kept descriptive precisely to avoid
double-counting); C.32-36 (five ear/health outputs with no H11 signification key — and the
"Thin significations" entry already closed AGAINST adding keys without rule buckets); C.40
(a co-born COUNT output, which the verdict engine cannot express, and which Raman himself
hedges — "students should test it for themselves").

**Genuinely still blocked (4):** C.12 (Navamsa-dispositor-of-lagna-lord multi-clause), C.16
(Vaiseshikamsa / multi-varga attainment — no such primitive in app/), C.17/C.18 (Dasa-timing
predicates — the rule engine is static-natal; no dasha context in EvalContext by design).

**✅ SHIPPED — H11.C.4** (HTJAH-II:14362, "fortified planets in the 11th"): encoded as any
11th-occupant with B1 `effective_strength` band "strong" AND not decisively-weak — per-planet-
vs-its-own-bar, the exact context B1 was tuned for. Reviewer: VALIDATED/SHIP, HIGH confidence —
Raman's "fortified" is a generic strength word (when he means dignity he names it, cf. the H12
`_LordHasDignity` precedent). Fires 62/209 (30%, blunt but placement-class-normal), and
**12 firing charts carry scored H11 expectations — the ratchet genuinely tested this rule**
(unlike H2.C.41's coverage-gap blindness) and stayed byte-identical. Designed behaviour, not a
gap: Rahu/Ketu (no Shadbala bar) and Track-B stated-position charts cannot fire it — "fortified"
is a strength claim such charts cannot substantiate.

**✅ SHIPPED WITH CAVEAT — H11.C.5** (HTJAH-II:14367, "weak planet in the 11th — eclipsed,
depressed, defeated in planetary war, or in inimical vargas"): encoded as any non-node
11th-occupant `decisively_weak` (weak band / combust="eclipsed" / debil-uncancelled=
"depressed" — the two facts B1 was literally built from). War-defeat carried indirectly (Yuddha
Bala depresses the Shadbala total). Fires 31/209 (15%), 4 scored firing charts, ratchet
unchanged. Caveats recorded: (a) the inimical-vargas leg is NOT modelled — disjunct-only, so
its absence causes only false negatives, disclosed in the rule text; pending a varga-dignity
predicate; (b) the weak-band leg reads Raman's em-dash list as examples of "weak" (head-noun
reading), a slight deliberate broadening.

**⛔ HELD (reverted same day) — H11.C.6 / H11.C.7** (HTJAH-II:14388/14390, friendly/inimical
lord-relationships): briefly encoded on NAISARGIKA relationships; the reviewer PROVED both
predicates unsatisfiable by enumerating all 12 lagnas (lordship fixed per lagna x naisargika
fixed per pair: no lagna yields three mutually-friendly 1/2/11 lords, none yields both 2nd+11th
lords natural enemies of the lagna lord — even one-directionally). An evaluable rule no chart
can satisfy is WORSE than a descriptive stub: it claims coverage the engine does not have. The
decisive doctrinal inference: Raman wrote these sentences about real nativities, so "friendly"/
"inimical" there cannot mean fixed natural friendship — it must be the chart-dependent COMPOUND
relation (naisargika x tatkalika), which exists in-repo as `dignity._compound_relation`
(private, already trusted by Sthana Bala) but is not exposed to the conditions algebra.
**Re-open path**: expose the compound relation as a condition, re-encode the PAIR together
(they are Raman's paired opposite sentences), measure firing + ratchet, re-review. Reverted to
descriptive with the proof noted in the rule file itself.

**New sweep lesson (added to the per-rule protocol):** for any predicate built ONLY from
lagna-fixed lordship and pair-fixed tables (naisargika, sign lords), CHECK SATISFIABILITY BY
ENUMERATION over the 12 lagnas before encoding — a 0% corpus firing rate on such a predicate is
a proof of impossibility, not a small-sample observation.

**H11 elder_siblings note (the mother's miss):** nothing in the dead inventory serves it — the
only dead elder_siblings rule (C.40) is a count-output. Her H11 miss remains a real-outcome
observation with no citation-backed engine gap behind it; per governance it stays a
prioritization signal only.


## H12 dead-rule sweep (2026-08-23) — pass 2: 3 shipped, 1 already-held, 18 correctly left

Second house pass (H12: 22 dead, second-worst rate; the mother's expenditure miss set the
order). Triage of all 22:

**Genuinely blocked (16):** the bulk of H12's dead inventory needs varga machinery the
conditions algebra does not carry — shashtyamsa/D60 class overlays (A23, B1, F3, I6-partial),
"benefic vargas" plural (A1, E2-half, F6), drekkana + vaiseshikamsa (B4), navamsa-dispositor-
of-house (A21, B1), karakamsa frame (G2), navamsa moolatrikona (F7 — EXCLUDED BY DESIGN,
`_VARGA_DIGNITY_STATES` deliberately omits it), comparative cross-planet strength (C4 — same
class as the held D6), multi-house affliction-grade aggregate (A5), amsa overlays (A22),
vague "beneficially disposed" gates (E1), and Dasa-free source reads needing verification
(B3's "(and variants)" compression). G1 (a single ultra-specific four-condition nativity)
is encodable but would assert one exact configuration — left descriptive as effort-vs-value.
D6 stays HELD (its own entry above).

**✅ SHIPPED — H12.C.C3** (HTJAH-II:16398, "a beggar is born"): the "Navamsa-debility overlay"
TODO was stale — `VargaDignity` covers it exactly (Sun D9-debil = Libra, Venus D9-debil =
Virgo, so "Venus in Virgo in Rasi AND Navamsa" is InSign+VargaDignity{debil} literally).
Reviewer: VALIDATED/SHIP, HIGH — printed text read verbatim, one-to-one transcription, no
dropped clause. Fires 2/209 (1%), zero scored-chart exposure, ratchet byte-identical.

**✅ SHIPPED WITH CAVEAT — H12.C.F1** (HTJAH-II:16491, Saturn/Mandi on 12th + 12th lord in
Vipat/Pratyak/Naidhana tara): the Tara TODO was stale — `TaraOf` has carried `LORD_OF:n`
support (its own docstring cites HTJAH-I:1142-1146); Mandi read from `chart.upagrahas`.
Reviewer: VALIDATED, HIGH — source parentheses ARE {3,5,7}; the 10% firing rate is the
predicate's own arithmetic (Saturn covers ~4/12 houses x 3/9 taras ≈ 11%), a severity
mismatch present in Raman's own text, accepted per the H2.C.41 preponderance reasoning.
Caveats: (i) Mandi leg absent on Track-B charts (no upagrahas) — disclosed in the rule text;
(ii) Mandi-ASPECT is unmodelled (occupancy only — Mandi is an upagraha point with no standard
drishti); both disjunct-only, false-negatives-only.

**✅ SHIPPED WITH CAVEAT — H12.C.F2** (HTJAH-II:16498, combust/debilitated malefic afflicting
the 12th): combust bar = the engine-wide B7 substantial threshold; debility bhanga-gated per
B1. Reviewer: VALIDATED, MEDIUM — "a state of eclipse" is read as combustion per Raman's own
usage in the SAME chapter (16381-16385 treats "eclipsed" and "combust" as one register) and
the H11.C.5 precedent; the alternative grahana reading (Sun/Moon under node-eclipse) is
unmodelled — concretely, a Sun-conjunct-Rahu afflicting the 12th will not fire (the Sun can
never be combust). Disjunct-only, false negatives only. Revisit if a corpus pass finds Raman
glossing "eclipse" with node language.

**Ratchet-blindness ledger for this pass** (per the cross-cutting entry below): only F2 was
genuinely ratchet-tested (one scored firing chart, HTJAH-II.h12_10, verdict unmoved); C3 and
F1 shipped on coverage-gap silence — their fidelity rests on the reviewer's verbatim source
reads, not on the ratchet. One tier-3 evidence snapshot regenerated (NH.chart_46 —
evidence-only, all six H12 verdicts identical).


## H1 dead-rule sweep (2026-08-23) — pass 3: 3 shipped (2 review-corrected), 1 reverted-by-measurement, 15 correctly left

Third house pass (H1: 19 dead; the golden corpus's largest error cluster and the mother's
health miss set the order). The most instructive pass so far — the ratchet caught a live
regression, and the reviewer corrected an encoding before it shipped wrong.

**Correctly left (15):** H1.M.G1/H1.M.MD (methodological prose, not predicates); H1.C.32
(vague "decent position"); H1.N.57/60/62 (vague "adverse Navamsha" summary rows); H1.C.23
(blocked: friendly-Drekkana class, no D3 in the algebra); H1.N.52 (comparative lord strength —
the held D6 class); H1.N.65 (navamsa-dispositor chain); H1.N.67 ("well disposed" holistic
gate); H1.C.22/24/25 (encodable but blunt/phase-output; deferred as effort-vs-value);
**H1.C.W33 — confirmed NOT a stale TODO**: its deferral note is a live design decision
(boolean malefic would double-count the chart-33 affliction the Sakata arishta already
carries) — and this pass PROVED that note right, see N.38 below.

**⛔ ENCODED AND REVERTED — H1.N.38** (HTJAH-I:1709, lord of Lagna weak/debilitated/combust →
sickly): the predicate is a faithful transcription ("weak, debilitated or combust" IS the B1
`decisively_weak` founding list) — and firing it as a context-free boolean malefic reproduced
EXACTLY the failure W33's deferral note predicted for this rule class: on chart_33 (lagna lord
neecha) it manufactured a benefic-vs-malefic contradiction that blocked the Y.SAKATA arishta
drop, flipping the golden's correct 'afflicted' to 'mixed'. **Measured: strict 259→258,
within-1 and real-errors unmoved — a pure one-sided loss.** Reverted; reviewer confirmed the
revert ("a change buying nothing on any axis cannot ship"). The working predicate class
(`_LagnaLordDecisivelyWeak`) is retained unused for promotion behind the same gate W33 names:
a lord-dignity-aware contradiction policy. THE RATCHET DID ITS JOB — first live catch of the
sweep.

**✅ SHIPPED (review-corrected) — H1.N.58** (HTJAH-I:1767, 1st/9th lord exalted → wealth
influx): first encoding was a standalone `Or(exalt-1st, exalt-9th)` firing 36/209 (17%). The
reviewer read the source paragraph and HELD it: "either of the lords" is scoped to the
paragraph's base configuration — Lagnadhipati JOINED WITH the 9th lord IN the 9th (:1764, the
base N.56 already encodes), per the file's own amplifier convention (N.50/N.53 =
And(base, qualifier)). Re-encoded with the gate: **fires 2/209 (1%)** — the rare event Raman
actually wrote, a 34-chart over-fire caught before shipping. Ratchet unchanged.

**✅ SHIPPED WITH CAVEAT — H1.N.66** (HTJAH-I:1972, contact between 1st and 6th lords →
health/defamation risk): `_LordsInContact(1,6)` — conjunction or aspect in EITHER direction.
Reviewer VALIDATED both scrutinized choices: identity→False (Raman's dictum is a two-place
relation; his worked Chart 18 is two planets; counting Taurus/Scorpio dual-lordship would
blanket-fire from the lagna alone) and either-direction aspect (the dictum is directionless;
restricting to the Chart-18 gloss's direction would encode the example, not the rule; and
mutual-only could fail Raman's own worked case under directional drishti). Fires 58/209
(28%) — honest arithmetic, accepted per the H2.C.41 preponderance class. Caveat: the
"health suffers" wording is signification-INFERRED (the printed lines support "fortunes
subject to much change" + defamation, not health verbatim).

**✅ SHIPPED WITH CAVEAT (review-corrected) — H1.C.37** (HTJAH-I:1146-1148, Lagnadhipati
strong but dispositor blemished): first encoding blemished on ALL of NATURAL_MALEFICS; the
reviewer flagged that the very precedent the docstring cited (B4 blemishless-Venus,
`_BLEMISH_MALEFICS`) EXCLUDES the Sun — the Sun blemishes only through combustion, which the
decisively-weak leg already carries. Corrected to Mars/Saturn/Rahu/Ketu touch + decisively-
weak dispositor. Fires 73/209 (35%, down from 37% — the Sun leg was precedent-inconsistent
surplus). Identity→False validated (a lord in own sign disposits itself; Raman's sentence is
about a DIFFERENT planet holding the lord's fate). Caveat: "blemished" is Raman-undefined at
this line; the encoding follows the project's settled register.

**Ratchet-blindness ledger:** H1 has the corpus's densest scored coverage (23 charts), so all
three shipped rules were GENUINELY ratchet-tested (6-9 scored firing charts each, no verdict
moved) — and N.38's regression was caught live. Snapshots regenerated twice (9 then 3,
verified evidence-only both times, zero verdict changes).


## H2 dead-rule sweep (2026-08-23) — pass 4: 5 shipped, 1 held-by-parity-proof, 12 left — AND THE SWEEP'S FIRST ACCURACY GAIN

Fourth house pass (H2's remaining 18 after C.41). **Strict ratchet 259/293 → 260/293** —
the first exact-accuracy gain since the ceiling was measured, earned by a dead rule whose
TODO went stale, and banked only after the reviewer's arithmetic proved it legitimate.

**Correctly left (12):** C.33/34 (navamsa-dispositor chain), C.35 (blocked by the SETTLED
"no per-component Shadbala minima exist" finding — "having Kalabala" has no bar), C.11
(absence-as-trigger, the N.66-note default-state concern), C.13 ("all good" vague), C.15
(encodable, deferred effort-vs-value), C.31 (multi-gate, deferred), C.42/C.43 (still gated
on the C.41 corpus-machine follow-up, per that entry's own condition), C.45 (deferred),
C.67 (routing note — already covered by H2.L.1-12), C.68 (vague composite outcome).

**✅ SHIPPED — the modality triplet H2.C.36/37/38** (HTJAH-I:2492-2496): 3rd lord in the 3rd
aspected by Jupiter/Venus, with the 3rd common/fixed/movable → wealth by thousands/hundreds/
within-two-hundred. The "SignModality" TODO was trivially computable all along. Reviewer:
VALIDATED×3, HIGH — source read verbatim, "its lord is situated there" = lord in the 3rd
confirmed, modality attaches to the house's sign, wealth routing explicit in the outcome
clause; Raman's own "naturally applies where movable signs ascend" remark is a consistency
note, correctly not encoded. Fires 0/1/0 of 209 (four-conjunct narrow rules, position-
dependent — NOT the lagna-fixed unsatisfiability class). The magnitude gradient survives
only in the fortified prose (RuleRecord carries no magnitude channel — framework limit).
Noted for a future precedent re-litigation: Jupiter/Venus-only for "benefics" is a corpus
precedent call; Raman names Mercury as a benefic 2nd-house resident two lines earlier.

**✅ SHIPPED WITH CAVEAT — H2.C.39** (HTJAH-I:2497, Saturn/Mars debilitated in the 11th
FROM ARUDHA LAGNA → good earnings): sign-from-AL confirmed verbatim; bhanga gate correctly
SKIPPED (debility is the TRIGGER of a benefic result here — a classical paradox rule — so
the guard that protects 'weak' readings points the wrong way; a bhanga'd planet satisfies
the rule more, not less). Fires 7/209, 2 scored charts, no verdict moved. **CAVEAT → NEW
AUDIT TICKET (arudha.py)**: Raman's own worked AL example (HTJAH-I:2518-2520, Aquarius
Lagna → Leo AL, kept in the 7th) does NOT apply the Jaimini same-sign/7th redirect that
`primitives/arudha.py:34-35` applies — for ~17% of charts (raw AL in 1st/7th) the code's AL
differs from Raman's. Per the Prime Directive (Raman wins) the primitive needs its own
review; C.39's fire-set is affected, C.40's provably is NOT (below).

**✅ SHIPPED — H2.C.40** (HTJAH-I:2498, AL in 11th/4th/5th/7th from Lagna → becomes rich):
**fixed golden chart_45 H2 wealth (mixed → favourable, Raman agrees) — strict 260/293, zero
new misses.** The 52% fire rate triggered full scrutiny and survived it: the reviewer
ENUMERATED the arithmetic — AL offset = 2·d mod 12 (d = lagna lord's offset) is ALWAYS
EVEN, so the attainable AL houses are {3,4,5,9,10,11} (after redirect), and Raman's four
named houses span exactly 3 of those 6 → ~50% is Raman's own arithmetic, the H12.C.F1
precedent class. Decisive robustness result: the fire-set is IDENTICAL under the code's
redirect convention and under Raman's own no-redirect construction (his set contains both
7 and 4, so the redirected case fires either way) — the chart_45 gain does not depend on
the open arudha.py question. Raman's own worked example is itself a C.40-firing chart.
Baseline bumped 259→260 in this change-set with the mechanism recorded in `_comment`.

**⛔ HELD BY PARITY PROOF — H2.C.46** (HTJAH-I:2535, AL in 6/8/12 → poverty): encoded and
reverted same day. The same enumeration proves it UNSATISFIABLE under BOTH conventions:
2·d mod 12 is always even; houses 6/8/12 sit at odd offsets and are unreachable. The
contradiction is INTERNAL TO THE SOURCE — Raman's poverty sentence cannot fire under his
own sign-based AL definition fourteen lines earlier (likely inherited from a tradition
computing Arudha differently, transcribed unreconciled). Per the H11.C.6 precedent, an
evaluable rule that cannot fire fakes coverage. Reverted to descriptive with the proof in
the rule text. C.40 does NOT revert with it — the pairing is superficial; the asymmetry is
arithmetic.

**Sweep protocol addendum (from the C.40/C.46 pair):** when a predicate is built on a
DERIVED point (Arudha, upagraha, sphuta), enumerate the derivation's reachable set first —
the same discipline as the lagna-fixed satisfiability check, one level up.


## H8-H3 dead-rule sweep finale (2026-08-23) — passes 5-12, closing the all-houses sweep

Final passes over the remaining eight houses (H8, H9, H10, H4, H5, H6, H7, H3 — 47 dead
rules). Full triage; six candidates encoded (verdicts below finalized after batch review).

**Correctly left, by blocking class:**
* Drekkana/D60/varga machinery absent: H8.C.21 (22nd drekkana), H8.C.22/C.27
  (navamsa-lagna-lord chains), H5.C.11 (drekkana dispositor), H4.C.47 (Gopura/shashtiamsa
  legs), H6.C.26 ("cruel Navamsha" 4-planet battle-death), H10.C.5/C.15 (navamsa-dispositor
  profession table, karakamsa overlay).
* Dasa-timing (Phase-F, no dasha context in EvalContext by design): H9.D.44/45/46,
  H10.C.60, H8.C.19-partial.
* Requires the FATHER'S chart (impossible from one nativity): H9.A.14, H9.A.16.
* Affliction-grade aggregates (no graded predicate): H8.C.4, H5.C.37.
* Deliberate dedups (refinements of already-scored placements, kept descriptive to avoid
  double-counting): H8.C.5, H8.C.6, H8.C.14, H4.C.3, H4.C.30, H5.C.8, H7.C.14 (promoted
  long ago into H7.C.86 branch (a)).
* Output-flavour / no verdict polarity: H8.C.20 (cause-by-planet table), H8.C.27 (place of
  death), H3.C.15/16/17 (co-born COUNT outputs — the whole of H3's remainder), H8.C.7
  (dual-polarity per-occupant flavour — does not fit one boolean; splitting would fork the
  rule id), H10.C.44 (ascetic counting), H9.A.10 (adoption, neutral), H9.A.12 ("beneficially
  disposed" vague), H4.C.24 (vague multi-clause), H4.C.26 ("strong 4th" house-strength gate),
  H7.C.81 (comparative-strength timing, the held D6 class), H10.C.27 (the 32-yoga royalty
  BANK — a yoga-file project, not one rule).
* **H7 deliberately untouched beyond the dedup note**: the marriage machinery is the
  project's densest-gated, most-scored surface with its backlog explicitly CLOSED; its
  remaining dead rules (C.5/C.8/C.31/C.35) include lagna-fixed blanket benefics (a benefic
  7th SIGN covers 7 of 12 lagnas → ~58% lagna-only fire) with real regression risk for no
  measured need. Recorded, not encoded.

**Encoded — all six SHIPPED (3 clean, 3 with caveats applied same-day):**

* **✅ H8.D.2** (HTJAH-II:3584, food-intake disease) — SHIP, exact three-conjunct
  transcription; the reviewer confirmed aspect-only on the Lagna leg is faithful ("aspected
  by", so a malefic IN the Lagna correctly does not fire). Fires 14/209. NH.chart_38's
  unpinned `death` manner moving insufficient-evidence → afflicted while its pinned
  `longevity` favourable stands is the established span-vs-manner dual reading.
* **✅ H10.C.56** (HTJAH-II:14214, Neechabhanga Rajayoga) — SHIP-WITH-CAVEAT. The
  broader-than-citation question was ruled FAITHFUL: the source introduces its list as
  "SOME important combinations" (non-exhaustive), `bhangas.py` anchors the 4-condition set
  as the standard doctrine Raman's method accepts, and a citation-trimmed fork would create
  two competing bhanga definitions in one engine. Caveat-fix applied: the separate
  `VargaDignity(D9,{exalt})` OR-branch was REMOVED as provably redundant (bhanga condition
  4 is the same test) — the docstring now states the unitary-doctrine reasoning instead of
  misdescribing the branch. Fires 80/209 (38%) — the doctrine's real breadth (any-of-7
  debil is ~40-50% of charts; Raman applies bhanga liberally in his own worked voice at
  14200), a weak testimony by construction; recorded for any future H10 re-weighing. Forms
  (1)/(4)/(5) of the citation remain unencoded (correct conservatism).
* **✅ H4.C.42** (HTJAH-I:4929, Vahana yoga) — SHIP, all three disjuncts parse-verified
  against the printed sentence; both identity→False guards ruled correct (Aquarius' Venus
  lords both 4 and 9 — "association of the lords" cannot be self-association; disjunct 3
  still covers those charts). Aquarius/Cancer → Venus-as-4th-lord derivations confirmed.
  Fires 22/209.
* **✅ H5.C.3** (HTJAH-I:5185, Jupiter as strong 5th lord) — SHIP-WITH-CAVEAT. Rasi core
  exact. Caveat-fix applied: the source's next sentence ("Birth of children is ALSO
  indicated when...") lists three INDEPENDENT combinations, not overlays — the rule text
  now says so explicitly, so a future encode makes them separate rules, never an And-gate
  here. Fires 0/209 (2/12-lagna × strength × aspect; satisfiable; liveness baseline
  consciously bumped 84→85).
* **✅ H6.C.1** (HTJAH-I:6073, evil 6th lord in 1/8/10) — SHIP-WITH-CAVEAT, and the caveat
  was decisive: the reviewer found Raman's own counter-citation for my `decisively_weak`
  arm — HTJAH-II:14229-14230, weak dusthana lords "if weak, produce Rajayoga" — weakness
  is classically FAVOURABLE for this signification. **The weak arm was DROPPED same-day**
  (fires 42→32/209); the surviving functional-malefic arm reads Raman's own per-lagna
  table (HTJAH-I:523-604) and is what keeps the rule from double-counting the ungated
  L.1/L.8/L.10 placements (double-count concern ruled adequately addressed — the gate is
  new testimony, not duplication). Weak arm re-addable only on explicit user ruling.
* **✅ H6.C.19** (HTJAH-I:6105, 6th lord in a benefic's sign → many friends) — SHIP;
  dispositor-∈-benefics is the standard "house of a benefic" reading; any-one-of
  Jupiter/Venus for "good planets" (plural) matches the corpus's loose class-plural usage.
  Fires 34/209.

Ratchet stable 260/293 · 283 · 10 through the whole finale; scored-house overlap
1/16/1/0/2/3 charts respectively — H10.C.56 was genuinely ratchet-tested on 16 scored
charts. 11 evidence snapshots regenerated (verdict changes: only the chart_38 dual-reading
above).

**THE ALL-HOUSES SWEEP IS COMPLETE.** Totals across all 12 houses: **19 rules shipped**
(H3.C.4; H2.C.41+36/37/38/39/40; H11.C.4/5; H12.C.C3/F1/F2; H1.N.58/66 + C.37; H8.D.2;
H10.C.56; H4.C.42; H5.C.3; H6.C.1/19 — counting the pair-corrected ships once), **6
held/reverted with a measured or proven reason** (H12.C.D6 tolerance-misuse; H11.C.6/7
naisargika-unsatisfiability; H1.N.38 chart_33 contradiction; H2.C.46 parity-proof; H6.C.1's
weak arm counter-citation), **1 golden chart fixed** (chart_45, strict 259→260 — the first
exact gain since the measured ceiling), **~78 dead rules correctly left** with their
blocking class named, and **3 standing audit tickets** (compound-relation exposure for
H11.C.6/7; arudha.py's Jaimini redirect vs Raman's worked example HTJAH-I:2518-2520; the
H2.C.41 corpus-machine verbatim check gating C.42/C.43).


## Cross-cutting: "ratchet unchanged" is NOT evidence of correctness (2026-08-22)

Three rules were encoded or attempted in one session; in **all three** the golden ratchet was
byte-identical, and in **none** did that silence carry evidential weight about correctness:

* `H3.C.4` — fired on 1 golden, corroborating an already-correct verdict. Ratchet blind
  because the rule never had to decide anything.
* `H12.C.D6` — fired on 27% of charts. Ratchet blind through **evidence redundancy**:
  `incarceration` sits in `_DUSTHANA_AFFLICTION_KEYS`, so any single fired malefic with no
  benefic contradiction already confirms "afflicted"; a badly-calibrated rule rides along
  invisibly. HELD on review.
* `H2.C.41` — fired on 14 charts. Ratchet blind through **coverage gap**: zero of those
  charts has a scored H2 expectation at all.

The ratchet is a strong guard against REGRESSION and remains sovereign for that purpose. It is
not, and was never designed as, a validator for newly-encoded rules. Any future dead-rule
encoding should measure (a) the firing rate, (b) whether any firing chart carries a scored
expectation for that house, and (c) co-fire against rules sharing a conjunct — before treating
a green ratchet as permission to ship.

## DRAFT golden pool fully adjudicated (2026-08-23) — 1 confirmed, 94 legitimate-mismatch backlog

All 95 remaining DRAFT verdicts were enumerated against the current engine. Exactly ONE is an
engine-match: **HTJAH-I.h5_15** (H5 children, favourable), reviewer CONFIRM/HIGH against
HTJAH-I:5906-5922 read verbatim (Chart No. 105: "5th house is unafflicted... fairly well
disposed"; the single infant death among ~9 counted / 8 born is a Navamsha-counting deduction in
Raman's own method, not an affliction verdict — the old "mixed" was exactly the over-weighting
the June backlog predicted). The engine's mixed→favourable movement pre-dates this adjudication
(D-7 confirm layer, PROGRESS_LOG "improves toward Raman's recorded verdict") — the engine moved
toward the text, not the label toward the engine. Ratchet: 260/293 → **261/294** exact,
283/293 → **284/294** within-1, real errors 10 (unchanged). The other 94 DRAFTs are the
legitimate mismatch backlog and stay DRAFT per the never-confirm-to-pad discipline; they are the
raw material for future mechanism work (the pillar-clause cluster chief among them), not for
label flips.

## Audit ticket DISCHARGED: H2.C.41 corpus-machine verbatim check → C.42/C.43 shipped (2026-08-23)

The H2 sweep's standing ticket (verify HTJAH-I:2526-2528 verbatim through the corpus machine
before encoding the gated siblings) was discharged after the corpus reconciliation made the
passage readable: all three poverty sentences read exactly as the rule prose claimed.
**H2.C.42** encoded as `Parivartana(1,6) AND (lord-1 OR lord-6 touched by primary maraka)` —
reviewer CONFIRM/HIGH (BPHS vol1 ch.42 v.3 corroborates; Raman's "either of these" broadens
BPHS's narrower attachment and Raman wins). Fires 1/211 (NH.chart_43). **H2.C.43** encoded as
`_MaleficNotOwning9or10InLagnaTouchedByMaraka` — reviewer REVISE→fixed same-day: the review
proved by enumeration that IF the counterpart node ever counted as a maraka, a node in the Lagna
would satisfy the maraka-touch qualifier on every chart (twin always in the 7th). The node-pair
guard was added as a **pinned invariant**; measurement then showed maraka.py already excludes
nodes from every tier (maraka.py:134), so the guard is defensive, not a live filter — fire rate
identical with and without (29/211, 4 scored-H2 overlaps, no verdict moved). Reviewer's two
side-questions settled: existential reading of "malefics" is correct (BPHS 42.8 generic plural);
nodes stay in the candidate-occupant set (the carve-out filters on ownership, and the house_11
node exclusion was a Shadbala-capability argument with no analogue here). Ratchet unchanged
261/294; liveness 739→741 evaluable, never-fired stays 85. H2's "left" count drops 12→10.

## Audit ticket DISCHARGED: arudha.py follows Raman, not the Jaimini 1st/7th redirect (2026-08-23)

Raman's own worked example (HTJAH-I:2521-2522: Aquarius Lagna, Saturn in Taurus → "the 4th from
Taurus, viz., Leo becomes Arudha Lagna") lands the AL in the **7th from Lagna and keeps it** —
strict Jaimini would redirect it to the 10th therefrom (Taurus), and `primitives/arudha.py` was
doing exactly that. The redirect was REMOVED: plain double-count, no exception, per the
definition sentence (HTJAH-I:2519-2521) and the Prime Directive (Raman wins). Consumer audit:
H2.C.39/C.40 verdict rules + report display only; the walled Jaimini subsystem does not consume
this primitive. Measured: Raman's example now reproduces (engine previously returned Taurus for
it); golden ratchet byte-identical (261/294, 284/294, 10); chart_45 still fires C.40. Parity
consequence recorded on C.40: the plain count reaches only ODD houses from Lagna, so of Raman's
four named houses {11,4,5,7} house 4 is now arithmetically unreachable (under the old redirect
it was house 7 — each formula kills exactly one). C.46's 6/8/12 unsatisfiability proof survives
under both formulas. Two tests that pinned the old exception were re-pinned to Raman's
arithmetic, including a new test reproducing the worked example verbatim.

**Review outcome (same day): VALIDATED/HIGH, with stronger evidence than dispatched.** The
reviewer found Raman keeps the plain count in FOUR independent passages covering BOTH exception
arms: the 7th-landing example above, the exception-free glossary definition (HTJAH-I:7187-7192,
generic per-house — the anchor for one formula across all 12 houses), Studies in Jaimini §19
(same definition + a second example), and decisively Studies in Jaimini **Ex. 48 (Hitler)**:
"lord of Lagna Sukra is in the 7th, and the 7th from the 7th, viz., Lagna itself will be Arudha
Lagna" — the SELF-landing case kept, where the exception would force Capricorn. So no flag is
needed for the walled Jaimini subsystem: Raman's own Jaimini book uses the plain count. The
exception's real home is **BPHS 29.4-5** (in-corpus, non-citable for natal verdicts), which on
Raman's own Aquarius configuration yields Taurus — exactly what the old code returned.

**Standing note before any Upapada-based verdict rule ships**: `upapada_lagna` has NO Raman
anchor (zero corpus hits in any Raman source — UL is defined only by BPHS ch.30 / KN Rao / Rath,
inside the ch.29 exception framework). Two open variants: (a) strict-classical UL would apply
the exception this fix removed; (b) Santhanam's BPHS 30.1-6 anchors UL to the 2nd house
("the bhava following the natal ascendant"), not the 12th the primitive uses (the Rao/Rath
reading). Today UL is display-only (special_points/synthesis); if a UL verdict rule is ever
proposed, resolve both variants through doctrine review first.

## Audit ticket DISCHARGED: compound_relation exposed, H11.C.6/C.7 re-encoded — both VALIDATED (2026-08-23)

The third and last standing ticket from the all-houses sweep. `dignity._compound_relation`
(naisargika x tatkalika via the standard ladder, previously private to Sthana Bala) is now
public as `dignity.compound_relation`, and the H11 pair whose naisargika encodings were proven
unsatisfiable over all 12 lagnas (2026-08-22) is re-encoded on it:

* **H11.C.6** = all three of the Lagna/2nd/11th lords pairwise MUTUALLY compound-friendly
  (identity pairs vacuous — Capricorn and Leo lagnas collapse to a two-planet test). Reviewer
  VALIDATED (MEDIUM-HIGH): mutual is the faithful reading of "the lords are friendly"; the one
  recorded LAXER variant — "friendly" = non-enemy both ways — is noted here per the review and
  re-opens only on new textual evidence. Fires 12/211, scored-H11 overlap on 2 goldens.
* **H11.C.7** = 2nd AND 11th lords each malefic-associated (conjunct/aspected, the codebase's
  standard "afflicted" floor) and compound-ENEMY one-way toward the Lagna lord, exactly as
  Raman's directional syntax reads ("inimical TO the Lagna lord"). Reviewer VALIDATED (HIGH):
  the neighbouring HTJAH-II:14367 sentence enumerates heavier weaknesses by name, proving bare
  "afflicted" here is the associational floor. Fires 17/211 with ZERO scored-H11 overlap —
  logged as a coverage-gap blindness mode per playbook rule 4: the ratchet cannot see this rule
  until a scored H11 chart fires it.

Satisfiability point for the record: the compound relation's temporal side is symmetric by
construction (whole-sign distances d and 14-d are in the friendly set together), so mutual
compound friendship needs only a friendly mutual placement plus no natural enmity — the
2026-08-22 unsatisfiability was purely a naisargika artifact, exactly as the hold note
predicted. Ratchet byte-identical (261/294, 284/294, 10); liveness 741→743, never-fired 85.
All three sweep audit tickets are now closed.

## H1-cluster mechanism design session (2026-08-23) — majority-loci affliction PROBED and REFUTED

The follow-up the threshold-sweep entry demanded: "a real improvement here needs a NEW mechanism
that separates these 8 charts from the strong-pillar charts the engine currently gets right."
A candidate was designed from the error charts' own printed reasoning and measured. It fails.
Recorded so the next session does not redesign it.

**The candidate (doctrine-anchored, not invented)**: per-locus CONTACT-affliction as an axis
separate from strength. Raman's own error-chart paragraphs weigh it exactly so — chart_60
(HTJAH-I:3802-3816): house (Mandi + Mars/Saturn aspects, Jupiter aspect "somewhat mitigates"
but "still the Bhava is not sufficiently strong") + lord (well-placed, D9-exalt, BUT Jupiter-
Ketu association + D9 Mars aspect) + karaka (good house BUT enemy sign + Sun + Saturn aspect)
→ "Though Jupiter is well-disposed... the Karaka and the third house are subject to affliction.
The native has no brothers." And h9_02 (HTJAH-II:7945-7985): "The Sun in exaltation with
Vargottama Jupiter... gave an exalted father — BUT the papakartari to the 9th house (from Rahu
and Mars), the 9th lord (from Saturn and Sun)..." — strength gave the QUALITY, contact gave the
VERDICT. Proposed clause: demote-only guard on the clause-2 FAVOUR lift when >=2 of the three
loci (bhava/lord/karaka) are contact-afflicted — the exact B1/navamsa-guard mold.

**The measurement (scratch probe, no engine change; all 294 confirmed Track-B verdicts)**:
four variants — {any-malefic-contact, hard-gates (>=2 distinct malefic contactors / papakartari
/ node-conjunction)} x {gross, net-of-benefic-contact}. NO variant separates:

| variant | threshold | errors caught (of 8) | correct favourables flagged |
|---|---|---|---|
| any-contact NET   | >=2 | 3 | 24 |
| any-contact GROSS | >=2 | 7 | 100 |
| any-contact GROSS | =3  | 3 | 38 |
| hard-gates NET    | >=2 | 0 | 9  |
| hard-gates GROSS  | >=2 | 1 | 31 |

The error charts sit at the SAME afflicted-loci counts as the correctly-favourable population —
the base-rate problem is structural, and it is the Measured-Truth mechanism operating inside
Raman's own corpus: malefic contact on a majority of loci is ordinary, therefore non-
differential. Raman's per-locus judgments in the very paragraphs above are finer than any
tally: WHICH malefic (functional nature), HOW (papakartari vs single aspect vs association),
mitigation weight ("somewhat mitigates" ≠ clears), D9 confirmation, enemy-sign placement,
Mandi/upagrahas (not modelled), and the Moon-reference check. His grading is the full reading,
not a countable proxy of it.

**Status: CLOSED-REFUTED** (same shape as the Tier-3 bhava-rescue: designed from citations,
killed by measurement — a success of the process). Together with the threshold sweep this
closes BOTH obvious mechanism families for the 10-error cluster. **Re-open path**: not a new
clause guess — systematic extraction of Raman's per-locus grading LANGUAGE from all worked
examples (the "sufficiently strong / not very good / quite afflicted" vocabulary) into a graded
per-locus dataset, then a mechanism designed against that dataset. That is golden-corpus work
(playbook rule 7), which is already the declared accuracy lever. Probe script preserved in the
session scratchpad; numbers above are the durable record.

## Workstream D DONE: parent-channel disclosure upgraded UNDER-POWERED → PURE-NOISE (2026-08-23)

The last deferred item from the real-people plan. The calibration table's H9_father/H4_mother
rows carried `*_died_early:UNDER-POWERED` (n=26/25) — a statement about the test, not the
engine — while the family data and the persona pilot both pointed at the father channel. The
legitimate route was taken end-to-end: (1) pre-registered mapping_version 3 in
`category_house_map.csv` (14 rows, 4 composite map_ids, supporting tier) using the childhood-
family tags as the powered proxy, with the SHARED-SOURCE confound (tags don't distinguish
parent — one measurement, two channels) and the prior ad-hoc null DISCLOSED in the registration
itself; (2) v2 results archived (`archive_mapping_v2/`); (3) full governed harness re-run —
sham gate PASSED, then H9_father AUC 0.511 (0.473-0.549) / H4_mother 0.506 (0.465-0.543) at
n=496 scored pairs: properly-powered NULL, replicating the ad-hoc result under sham-gated
governance; (4) failure atlas re-run → both channels classed PURE-NOISE at n≈570; calibration
table regenerated — rows now carry the powered class alongside the historical event rows, and
the reader-facing disclosure note upgrades automatically (`test_every_table_class_has_a_
reader_facing_note` green); (5) `update_baseline --confirm` → mapping_version 3, same 4 core
metrics (supporting tier never enters the ratchet), `test_astrobank_ratchet` green. FAILURE_
ATLAS.md carries the dated addendum. No verdict, threshold, or rule was touched — this is the
disclosure layer telling readers the truth at proper power, exactly what Workstream D was for.

## Golden corpus growth: the HTJAH extraction backlog, measured and opened (2026-08-23)

Prompted by the owner's question — "can't we increase the golden ratchet number, I think we
missed many examples." He was right, and the gap is now measured rather than estimated.

**The audit.** The two HTJAH volumes contain **502 worked-chart presentations** (a "Chart No. N"
followed by birth data); the golden corpus held **174** of them. That leaves **328 unextracted**,
and 136 "Conclusion" paragraphs — Raman's own graded judgments — sit on chart numbers the corpus
had never seen (81 in Vol I, 55 in Vol II). Corpus growth being the declared remaining accuracy
lever (playbook rule 7), this is the largest single piece of fidelity work still open.

**Why it was not simply automated before.** HTJAH prints birth DATA, not the printed longitudes
Notable Horoscopes gives, so records must be FRESH CAST out of OCR-damaged text. Observed
corruption in these very scans: `Born 24-3-7883` (mangled year), coordinates truncated by a line
break, `3/4-12-1953` (midnight-straddling date), unreadable zone markers. A mis-parsed birth line
produces a WRONG chart, and a wrong chart scored against Raman's verdict silently corrupts the
fidelity measurement.

**The gate that makes extraction safe.** Vol II prints, for most charts, *"Balance of <Lord> Dasa
at birth: N years, M months and D days"* — fixed by the Moon's longitude, therefore an independent
function of date, time and place. `tools/raman_saab/extract_htjah_goldens.py` parses the birth
line, casts, computes the Vimshottari balance, and emits ONLY when lord and duration reproduce
Raman's printed figure within tolerance. Worked proof: Chart No. 20 (HTJAH-II:2002) prints
"20 N 56, 75 E 55" and a Ketu balance of 6y 4m 4d; the parse lands the coordinates exactly and the
cast balance agrees to **3 days**. Failures are reported and skipped, never repaired by guesswork —
the 42 gate failures are scattered in magnitude (120d to 2289d) and direction, i.e. genuine OCR
damage rather than a systematic casting error.

**Batch 1 shipped: 57 charts.** Golden records 225 → 282. `expected_verdicts` deliberately EMPTY —
the tool extracts CHARTS; a verdict remains a doctrine judgment a reviewer makes by reading Raman,
and only CONFIRMED verdicts score. **The accuracy ratchet is therefore untouched at 261/294 by
construction**, which is the point: extraction can never inflate fidelity.

**The measured gain is liveness.** Dormant rules **85 → 71** — fourteen woke on the new nativities
(H11.C.22, H12.C.D5, H12.C.I5, H2.C.52, H2.C.63, H5.C.26, H5.C.29, H5.C.3, H6.C.16, H7.C.30,
H8.D.1, H8.K.28, H9.A.6, H9.B.27), plus one yoga (49 → 50). This is the empirical answer to "why
are rules dormant": for these fourteen it was CORPUS SIZE, not impossibility — including H5.C.3,
which the all-houses sweep shipped as a deliberate reviewer-validated dormant rule and which now
fires. It also retro-justifies that sweep decision: the honest hold was correct, and the corpus
caught up.

**What remains, in priority order.** (a) 105 charts parse cleanly but Vol I prints no dasha balance
to verify against — they need a different gate (Raman's stated Lagna sign, where the grid OCR
permits) before they can be trusted. (b) 118 fail to parse at all, dominated by line-break-truncated
longitudes and unreadable zone markers; a targeted OCR repair pass over the birth lines would
recover a large share. (c) The 57 shipped charts + the 136 known Conclusion paragraphs are now a
REVIEW queue: each verdict promoted DRAFT → CONFIRMED grows the ratchet's denominator honestly.
**That review is the only path that moves 261/294, and it must stay per-record against Raman's
text — never confirm to pad.**
